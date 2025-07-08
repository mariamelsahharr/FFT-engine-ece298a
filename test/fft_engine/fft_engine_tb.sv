`default_nettype none
`timescale 1ns / 1ps

module fft_engine_tb (
    input  logic clk, rst,
    input  logic signed [7:0] in0_real, in0_imag,
    input  logic signed [7:0] in1_real, in1_imag,
    input  logic signed [7:0] in2_real, in2_imag,
    input  logic signed [7:0] in3_real, in3_imag,
    output logic signed [7:0] out0_real, out0_imag,
    output logic signed [7:0] out1_real, out1_imag,
    output logic signed [7:0] out2_real, out2_imag,
    output logic signed [7:0] out3_real, out3_imag
);

logic [7:0] current_test_id = 0;

    // Dump signals
    string vcd_name;
    initial begin
`ifdef VCD_PATH
        vcd_name = `VCD_PATH;
`else
        vcd_name = {"fft_engine_", `TIMESTAMP, ".vcd"};
`endif
        $dumpfile(vcd_name);
        $dumpvars(0, fft_engine_tb);
        #1;
    end

    // Instantiate DUT
    fft_engine dut (
        .clk(clk),
        .rst(rst),
        .in0_real(in0_real),
        .in0_imag(in0_imag),
        .in1_real(in1_real),
        .in1_imag(in1_imag),
        .in2_real(in2_real),
        .in2_imag(in2_imag),
        .in3_real(in3_real),
        .in3_imag(in3_imag),
        .out0_real(out0_real),
        .out0_imag(out0_imag),
        .out1_real(out1_real),
        .out1_imag(out1_imag),
        .out2_real(out2_real),
        .out2_imag(out2_imag),
        .out3_real(out3_real),
        .out3_imag(out3_imag)
    );

endmodule