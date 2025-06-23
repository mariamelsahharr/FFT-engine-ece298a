`default_nettype none
`timescale 1ns / 1ps

module gate_level_tb;

    // Clock and reset signals
    reg clk;
    reg rst_n;

    // I/O signals for the DUT
    reg  [7:0] ui_in;
    wire [7:0] uo_out;
    reg  [7:0] uio_in;
    wire [7:0] uio_out;
    wire [7:0] uio_oe;

    // Instantiate the DUT
    tt_um_FFT_engine dut (
        .ui_in      (ui_in),
        .uo_out     (uo_out),
        .uio_in     (uio_in),
        .uio_out    (uio_out),
        .uio_oe     (uio_oe),
        .ena        (1'b1), // Ena always high for this test
        .clk        (clk),
        .rst_n      (rst_n)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 100MHz clock
    end

    // VCD dumping
    initial begin
        $dumpfile("gate_level_tb.vcd");
        $dumpvars(0, gate_level_tb);
    end

endmodule 