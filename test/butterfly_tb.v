`default_nettype none
`timescale 1ns / 1ps

module butterfly_tb ();

  // Dump the signals to a VCD file
  initial begin
    $dumpfile("butterfly_tb.vcd");
    $dumpvars(0, butterfly_tb);
    #1;
  end

  // Clock and control signals
  reg clk;
  reg rst;
  reg en;
  
  // Input data signals (8-bit packed complex)
  reg [7:0] A;
  reg [7:0] B;
  reg [7:0] T;
  
  // Output signals
  wire [7:0] Pos;
  wire [7:0] Neg;
  wire        valid;

  // Golden Model outputs
  wire [7:0] Pos_golden;
  wire [7:0] Neg_golden;

  // Instantiate the butterfly unit
  butterfly_unit dut (
      .clk(clk),
      .rst(rst),
      .en(en),
      .A(A),
      .B(B),
      .T(T),
      .Pos(Pos),
      .Neg(Neg),
      .valid(valid)
  );

  // 2. The combinational "source of truth" (Golden Model)
  butterfly_golden #(.WIDTH(8)) golden_model (
      .A_in(A),
      .B_in(B),
      .W_in(T),      // T maps to W
      .plus_out(Pos_golden),
      .minus_out(Neg_golden)
  );

endmodule 