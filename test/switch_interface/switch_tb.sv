`default_nettype none
`timescale 1ns / 1ps

module switch_tb ();

  // Dump the signals to a VCD file
  string vcd_name;
  initial begin
`ifdef VCD_PATH
    vcd_name = `VCD_PATH;
`else
    vcd_name = {"switch_tb_", `TIMESTAMP, ".vcd"};
`endif
    $dumpfile(vcd_name);
    $dumpvars(0, switch_tb);
    #1;
  end

  // Clock and control signals
  logic clk;
  logic rst;
  
  // Input signals
  wire sw_in;

  // Output signals
  wire pulse_out;

  // DUT
  switch_interface #(
      .DEBOUNCE_BITS(10),
      .DEBOUNCE_MAX(10'd5)  // Small value for fast test
  ) dut (
      .clk(clk),
      .rst(rst),
      .sw_in(sw_in),
      .pulse_out(pulse_out)
  );

endmodule