`default_nettype none
`timescale 1ns/1ps

/*
this testbench just instantiates the module and makes some convenient wires
that can be driven / tested by the cocotb test.py
*/

module tb (
    // testbench is controlled by test.py
    input clk,
    input rst_n,
    input [1:0] clk_config,
    input input_pulse,
    output [6:0] segments,
    output prox_select
   );

    // this part dumps the trace to a vcd file that can be viewed with GTKWave
    initial begin
        $dumpfile ("tb.vcd");
        $dumpvars (0, tb);
        #1;
    end

    // wire up the inputs and outputs
    wire [7:0] uio_oe = 8'hff;
    wire [7:0] uio_in = 8'b0;
    wire [7:0] uio_out;
    wire ena = 1'b1;
    
    
    
    // wire up the inputs and outputs
    wire [7:0] inputs = {3'b0, input_pulse, clk_config[1], clk_config[0], 2'b0};
    wire [7:0] outputs;
    assign prox_select = outputs[7];
    assign segments = outputs[6:0];

    // instantiate the DUT
    tt_um_psychogenic_neptuneproportional neptune(
        `ifdef GL_TEST
            .vccd1( 1'b1),
            .vssd1( 1'b0),
        `endif
        .ui_in  (inputs),
        .uo_out (outputs),
        .uio_in (uio_in),
        .uio_out (uio_out),
        .uio_oe (uio_oe),
        .ena (ena),
        .clk (clk),
        .rst_n (rst_n)
        );

endmodule
