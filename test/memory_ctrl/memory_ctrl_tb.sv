`default_nettype none
`timescale 1ns / 1ps

module memory_ctrl_tb (
    // Control Signals
    input  logic clk,
    input  logic rst,
    input  logic ena,
    input  logic load_pulse,

    // Write Port
    input  logic [1:0] addr,
    input  logic [7:0] data_in,

    // Read Outputs
    output logic signed [7:0] real0_out, imag0_out,
    output logic signed [7:0] real1_out, imag1_out,
    output logic signed [7:0] real2_out, imag2_out,
    output logic signed [7:0] real3_out, imag3_out
);

logic [7:0] current_test_id = 0;

    // Dump the signals to a VCD file for debugging
    string vcd_name;
    initial begin
`ifdef VCD_PATH
        vcd_name = `VCD_PATH;
`else
        vcd_name = {"memory_ctrl_tb_", `TIMESTAMP, ".vcd"};
`endif
        $dumpfile(vcd_name);
        $dumpvars(0, memory_ctrl_tb);
        #1;
    end

    // Instantiate the memory controller (DUT)
    memory_ctrl #(
        .WIDTH(8)
    ) dut (
        .clk(clk),
        .rst(rst),
        .ena(ena),
        .load_pulse(load_pulse),
        .addr(addr),
        .data_in(data_in),
        .real0_out(real0_out),
        .imag0_out(imag0_out),
        .real1_out(real1_out),
        .imag1_out(imag1_out),
        .real2_out(real2_out),
        .imag2_out(imag2_out),
        .real3_out(real3_out),
        .imag3_out(imag3_out)
    );

endmodule