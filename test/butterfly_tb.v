`default_nettype none
`timescale 1ns / 1ps

module butterfly_tb ();

  // Dump the signals to a VCD file
  initial begin
    $dumpfile("butterfly_tb.vcd");
    $dumpvars(0, butterfly_tb);
    #1;
  end
  
  // Testbench signals
  reg  signed [7:0] A_tb;
  reg  signed [7:0] B_tb;
  reg  signed [7:0] W_tb;
  wire signed [7:0] plus_tb;
  wire signed [7:0] minus_tb;

  // Instantiate the butterfly unit with WIDTH=8
  // This means 4-bit real and 4-bit imaginary parts
  butterfly #(.WIDTH(8)) dut (
      .A     (A_tb),
      .B     (B_tb),
      .W     (W_tb),
      .plus  (plus_tb),
      .minus (minus_tb)
  );

endmodule 