`default_nettype none
`timescale 1ns / 1ps

module memory_tb;

  // Dump the signals to a VCD file
  string vcd_name;
  initial begin
`ifdef VCD_PATH
    vcd_name = `VCD_PATH;
`else
    vcd_name = {"memory_tb_", `TIMESTAMP, ".vcd"};
`endif
    $dumpfile(vcd_name);
    $dumpvars(0, memory_tb);
    #1;
  end

  // Clock and control signals
  reg clk;
  reg rst;
  reg en;
  reg read_en;
  reg write_en;
  
  // Write port signals
  reg [1:0] addr_w;
  reg [15:0] data_in;
  
  // Read port A signals
  reg [1:0] addr_a;
  wire [15:0] data_out_a;
  
  // Read port B signals
  reg [1:0] addr_b;
  wire [15:0] data_out_b;
  
  // Output valid signal
  wire read_valid;

  // Test counter signal - will be set by Python test
  reg [7:0] test_counter;
  wire [7:0] current_test;

  // Assign the test counter to a wire for monitoring
  assign current_test = test_counter;

  // Instantiate the memory module (DUT)
  fft_memory dut (
      .clk(clk),
      .rst(rst),
      .en(en),
      .read_en(read_en),
      .write_en(write_en),
      .addr_w(addr_w),
      .data_in(data_in),
      .addr_a(addr_a),
      .data_out_a(data_out_a),
      .addr_b(addr_b),
      .data_out_b(data_out_b),
      .read_valid(read_valid)
  );

endmodule 