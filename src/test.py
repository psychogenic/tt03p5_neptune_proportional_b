import math
import cocotb
import os 

from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles


ConfiguredSamplingTimeSecs = 0.5
DumpVerbose = False
FullSpectrumScan = False

displayNotes = {
            'NA':     0b00000010, # -
            'A':      0b11101110, # A
            'B':      0b00111110, # b
            'C':      0b10011100, # C
            'D':      0b01111010, # d
            'E':      0b10011110, # E
            'F':      0b10001110, # F
            'G':      0b11110110, # g
            }
            
displayProx = {
            'lowfar':       0b00111000,
            'lowclose':     0b00101010,
            'exact':        0b00000001,
            'hiclose':      0b01000110,
            'hifar':        0b11000100

}

SegmentMask = 0xFF
ProxSegMask = 0xFE

def dumpNoteForValue(dut, val):
    for note,v in displayNotes.items():
        if val == v:
            if DumpVerbose:
                dut._log.info(f"GOT note {note} ({val})")
            return 
            
    dut._log.info(f"NO note for {val}")
    
def dumpProxForValue(dut, val):
    for prox,v in displayProx.items():
        if val == v:
            if DumpVerbose:
                dut._log.info(f"GOT prox {prox} ({val})")
            return 
            
    dut._log.info(f"NO prox for {val}")
    

def assertNoteIs(val, expectedKey, dut):
    #dut._log.info(f'XXXXXXXXXXXXXXXXXXXX looking for note {expectedKey}')
    dumpNoteForValue(dut, val)
    assert val == (displayNotes[expectedKey] & SegmentMask)
    
def assertProximityIs(val, expectedKey, dut):
    #dut._log.info(f'XXXXXXXXXXXXXXXXXXXX looking for prox {expectedKey}')
    dumpProxForValue(dut, val)
    assert val == (displayProx[expectedKey] & ProxSegMask)
    

# os.environ['COCOTB_RESOLVE_X'] = 'RANDOM'
async def reset(dut):
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    dut.clk_config.value = 2 # 2khz clock
    await ClockCycles(dut.clk, 5)
    dut._log.info("reset")
    dut.input_pulse.value = 1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.input_pulse.value = 0
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
   
    
async def startup(dut):
    clock = Clock(dut.clk, 250, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)
    dut.input_pulse.value = 0
            
async def getDisplayValues(dut):
    displayedValues = [None, None]
    attemptCount = 0
    while None in displayedValues or attemptCount < 3:
        displayedValues[int(dut.prox_select.value)] = int(dut.segments.value) << 1
        
        await ClockCycles(dut.clk, 1)
        
        attemptCount += 1
        if attemptCount > 100:
            dut._log.error(f"NEVER HAVE {displayedValues}")
            return displayedValues
            
    # dut._log.info(f'Display Segments: {displayedValues} ( [ {bin(displayedValues[0])} , {bin(displayedValues[1])}])')
    return displayedValues
    
async def inputPulsesFor(dut, tunerInputFreqHz:int, inputTimeSecs=ConfiguredSamplingTimeSecs*2):
    numPulses = tunerInputFreqHz * inputTimeSecs 
    pulsePeriod = 1/tunerInputFreqHz
    pulseHalfCycleUs = round(1e6*pulsePeriod/2.0)
    
    displayedValues = [None, None]
        
    for _pidx in range(round(numPulses)):
        dut.input_pulse.value = 1
        await Timer(pulseHalfCycleUs, units='us')
        dut.input_pulse.value = 0
        await Timer(pulseHalfCycleUs, units='us')
        
    dispV = await getDisplayValues(dut)
    
    return dispV
    


async def setup_tuner(dut):
    dut._log.info("start")
    await startup(dut)
    

async def note_toggle(dut, freq, delta=0, msg="", toggleTime=ConfiguredSamplingTimeSecs*2.1):
    dut._log.info(msg)
    await startup(dut)
    dispValues = await inputPulsesFor(dut, freq + delta, toggleTime)  
    return dispValues
    
    

async def note_e(dut, eFreq=330, delta=0, msg=""):
    
    dut._log.info(f"E @ {eFreq} delta {delta}")
    dispValues = await note_toggle(dut, freq=eFreq, delta=delta, msg=msg);
    assertNoteIs(dispValues[1], 'E', dut)
    return dispValues


async def note_a(dut, delta=0, msg=""):
    aFreq = 110
    
    dut._log.info(f"A delta {delta}")
    dispValues = await note_toggle(dut, freq=aFreq, delta=delta, msg=msg);
    assertNoteIs(dispValues[1], 'A', dut)
    return dispValues
    
    
async def note_d(dut, delta=0, msg=""):
    dFreq = 147
    
    dut._log.info(f"D delta {delta}")
    dispValues = await note_toggle(dut, freq=dFreq, delta=delta, msg=msg);
    assertNoteIs(dispValues[1], 'D', dut)
    return dispValues
    

async def note_g(dut, delta=0, msg=""):
    gFreq = 196
    
    dut._log.info(f"G delta {delta}")
    dispValues = await note_toggle(dut, freq=gFreq, delta=delta, msg=msg);
    assertNoteIs(dispValues[1], 'G', dut)
    return dispValues
    
    
async def note_b(dut, delta=0, msg=""):
    gFreq = 247
    
    dut._log.info(f"B delta {delta}")
    dispValues = await note_toggle(dut, freq=gFreq, delta=delta, msg=msg);
    assertNoteIs(dispValues[1], 'B', dut)
    return dispValues
    
    
    
    
    
    

 
@cocotb.test()
async def full_spectrum_scan(dut):
    if not FullSpectrumScan:
        dut._log.info("FullSpectrumScan not enabled, skipping")
        return 
    
    dut._log.info("FullSpectrumScan enabled.  Will take a while")
    await startup(dut)
    for i in range(70, 350, 1):
        dispValues = await inputPulsesFor(dut, i, ConfiguredSamplingTimeSecs+0.005)  
 





    
@cocotb.test()
async def note_fatE_lowfar(dut):
    dispValues = await note_e(dut, eFreq=83, delta=-7, msg="fat E low/far")
    assertProximityIs(dispValues[0], 'lowfar', dut)
    
    
 
@cocotb.test()
async def note_fatE_exact(dut):
    dispValues = await note_e(dut, eFreq=83, delta=-1, msg="fat E -1Hz")
    assertProximityIs(dispValues[0], 'exact', dut)
    


@cocotb.test()
async def note_a_exact(dut):
    dispValues = await note_a(dut, delta=0, msg="A exact")
    assertProximityIs(dispValues[0], 'exact', dut)
    
@cocotb.test()
async def note_a_highfar(dut):
    dispValues = await note_a(dut, delta=5, msg="A high/far")
    
    assertProximityIs(dispValues[0], 'hifar', dut)
   




@cocotb.test()
async def note_d_lowfar(dut):
    dispValues = await note_d(dut,delta=-10, msg="D low far")
    assertProximityIs(dispValues[0], 'lowfar', dut)






    
@cocotb.test()
async def note_g_highfar(dut):
    dispValues = await note_g(dut, delta=6, msg="High/far")
    assertProximityIs(dispValues[0], 'hifar', dut)
    


@cocotb.test()
async def note_g_lowclose(dut):
    dispValues = await note_g(dut, delta=-2, msg="G low/close")
    assertProximityIs(dispValues[0], 'lowclose', dut)
   

    
@cocotb.test()
async def note_g_lowfar(dut):
    dispValues = await note_g(dut, delta=-10, msg="G low/far")
    assertProximityIs(dispValues[0], 'lowfar', dut)
    
     
 



@cocotb.test()
async def note_b_high(dut):
    dispValues = await note_b(dut, delta=4, msg="B high/close")
    
    assertProximityIs(dispValues[0], 'hiclose', dut)
    assert dispValues[0] == (displayProx['hiclose'] & ProxSegMask) 
 
   


@cocotb.test()
async def note_b_exact(dut):
    dispValues = await note_b(dut, delta=0, msg="B exact")
    assertProximityIs(dispValues[0], 'exact', dut)

    

    
@cocotb.test()
async def note_e_highfar(dut):
    dispValues = await note_e(dut, eFreq=330, delta=20, msg="little E high/far")
    assertProximityIs(dispValues[0], 'hifar', dut)
    

    
@cocotb.test()
async def note_e_lowclose(dut):
    dut._log.info("NOTE: delta same as for fat E, but will be close...")
    dispValues = await note_e(dut, eFreq=330, delta=-7, msg="E exact")
    assertProximityIs(dispValues[0], 'lowclose', dut)


    
@cocotb.test()
async def note_e_exact(dut):
    dispValues = await note_e(dut, eFreq=330, delta=1, msg="E exact")
    
    assertProximityIs(dispValues[0], 'exact', dut)



    
@cocotb.test()
async def success_test(dut):
    
    await note_toggle(dut, freq=20, delta=0, msg="just toggling -- end");
