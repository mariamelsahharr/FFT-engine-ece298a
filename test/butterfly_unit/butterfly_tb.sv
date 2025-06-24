`default_nettype none
`timescale 1ns / 1ps

module butterfly_tb (
    input  logic [15:0] A,
    input  logic [15:0] B,
    input  logic [15:0] T,
    output logic [15:0] Pos,
    output logic [15:0] Neg
);

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
    butterfly #(.WIDTH(16)) dut (
        .A(A),
        .B(B),
        .T(T),
        .Pos(Pos),
        .Neg(Neg)
    );

endmodule 