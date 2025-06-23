`default_nettype none
`timescale 1ns / 1ps

module butterfly_tb (
  output logic [7:0] plus,
  output logic [7:0] minus
);

  // Dump the signals to a VCD file
  string vcd_name;
  initial begin
    vcd_name = $sformatf("butterfly_tb_%0t.vcd", $time);
    $dumpfile(vcd_name);
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

  // Instantiate the butterfly unit (DUT)
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

  // Instantiate the golden model for comparison
  butterfly_golden #(.WIDTH(8)) golden_model (
      .A(A),
      .B(B),
      .W(T),      // T maps to W
      .plus(plus),
      .minus(minus)
  );

endmodule 