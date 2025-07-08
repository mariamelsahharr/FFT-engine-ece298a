`default_nettype none
`timescale 1ns / 1ps

module tt_um_FFT_engine_tb (
    // To DUT
    input  wire [7:0] ui_in,
    input  wire [7:0] uio_in,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n,

    // From DUT
    output wire [7:0] uo_out,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe
);

logic [7:0] current_test_id = 0;

    // Dump signals for waveform viewing
    string vcd_name;
    initial begin
`ifdef VCD_PATH
        vcd_name = `VCD_PATH;
`else
        vcd_name = {"tt_um_FFT_engine_tb_", `TIMESTAMP, ".vcd"};
`endif
        $dumpfile(vcd_name);
        $dumpvars(0, tt_um_FFT_engine_tb);
        #1;
    end

    // Instantiate the top-level DUT
    tt_um_FFT_engine dut (
        .ui_in(ui_in),
        .uo_out(uo_out),
        .uio_in(uio_in),
        .uio_out(uio_out),
        .uio_oe(uio_oe),
        .ena(ena),
        .clk(clk),
        .rst_n(rst_n)
    );

endmodule