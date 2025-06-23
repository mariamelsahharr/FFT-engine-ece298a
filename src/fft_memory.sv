// A simple single-port RAM. Create this file if you don't have it.
module fft_memory_single_port (
    input  logic clk,
    input  logic [1:0]  addr,
    input  logic        we,
    input  logic [15:0] wdata,
    output logic [15:0] rdata
);
    (* ram_style = "registers" *)
    logic [15:0] mem [0:3];
    always_ff @(posedge clk) begin
        if (we) mem[addr] <= wdata;
        rdata <= mem[addr]; // Registered output
    end
endmodule