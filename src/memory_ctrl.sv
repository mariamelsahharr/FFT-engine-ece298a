module memory_ctrl #(
    parameter WIDTH = 8
)(
    input  logic clk, rst, ena,
    input  logic load_pulse,
    input  logic [1:0] addr,
    input  logic [7:0] data_in,
    output logic signed [WIDTH-1:0] real_out[0:3],
    output logic signed [WIDTH-1:0] imag_out[0:3]
);
    // Sample storage
    logic signed [WIDTH-1:0] real_mem[0:3];
    logic signed [WIDTH-1:0] imag_mem[0:3];
    
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            for (int i = 0; i < 4; i++) begin
                real_mem[i] <= '0;
                imag_mem[i] <= '0;
            end
        end else if (ena && load_pulse) begin
            real_mem[addr] <= $signed(data_in[7:4]) << 4;
            imag_mem[addr] <= $signed(data_in[3:0]) << 4;
        end
    end
    
    assign real_out = real_mem;
    assign imag_out = imag_mem;
endmodule