`default_nettype none
`timescale 1ns / 1ps

module butterfly_tb (
    input  logic signed [7:0] A_real, A_imag,
    input  logic signed [7:0] B_real, B_imag,
    input  logic signed [7:0] W_real, W_imag,
    output logic signed [7:0] Pos_real, Pos_imag,
    output logic signed [7:0] Neg_real, Neg_imag
);

logic [7:0] current_test_id = 0;
    // Dump the signals to a VCD file
    string vcd_name;
    initial begin
`ifdef VCD_PATH
        vcd_name = `VCD_PATH;
`else
        vcd_name = {"butterfly_tb_", `TIMESTAMP, ".vcd"};
`endif
        $dumpfile(vcd_name);
        $dumpvars(0, butterfly_tb);
        #1;
    end

    // Instantiate the butterfly unit (DUT)
    butterfly dut (
        .A_real(A_real),
        .A_imag(A_imag),
        .B_real(B_real),
        .B_imag(B_imag),
        .W_real(W_real),
        .W_imag(W_imag),
        .Pos_real(Pos_real),
        .Pos_imag(Pos_imag),
        .Neg_real(Neg_real),
        .Neg_imag(Neg_imag)
    );

endmodule