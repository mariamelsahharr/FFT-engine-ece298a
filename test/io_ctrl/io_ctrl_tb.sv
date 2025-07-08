`default_nettype none
`timescale 1ns / 1ps

module io_ctrl_tb (
    // Control and Input signals
    input  logic clk,
    input  logic rst,
    input  logic ena,
    input  logic ui_in0,
    input  logic ui_in1,

    // Output signals
    output logic load_pulse,
    output logic output_pulse,
    output logic [1:0] addr
);

logic [7:0] current_test_id = 0;

    // Dump signals for waveform viewing
    string vcd_name;
    initial begin
`ifdef VCD_PATH
        vcd_name = `VCD_PATH;
`else
        vcd_name = {"io_ctrl_tb_", `TIMESTAMP, ".vcd"};
`endif
        $dumpfile(vcd_name);
        $dumpvars(0, io_ctrl_tb);
        #1;
    end

    // Instantiate the DUT
    io_ctrl dut (
        .clk(clk),
        .rst(rst),
        .ena(ena),
        .ui_in0(ui_in0),
        .ui_in1(ui_in1),
        .load_pulse(load_pulse),
        .output_pulse(output_pulse),
        .addr(addr)
    );

endmodule