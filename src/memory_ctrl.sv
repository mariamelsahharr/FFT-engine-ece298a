module memory_ctrl #(
    parameter WIDTH = 8
)(
    input  logic clk, rst, ena,
    input  logic load_pulse,
    input  logic [1:0] addr,
    input  logic [7:0] data_in,
    output logic signed [WIDTH-1:0] real0_out, imag0_out,
    output logic signed [WIDTH-1:0] real1_out, imag1_out,
    output logic signed [WIDTH-1:0] real2_out, imag2_out,
    output logic signed [WIDTH-1:0] real3_out, imag3_out
);
    // Sample storage
    logic signed [WIDTH-1:0] real_mem[0:3];
    logic signed [WIDTH-1:0] imag_mem[0:3];
    
    // Initialize arrays properly
    integer i;
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            for (i = 0; i < 4; i = i + 1) begin
                real_mem[i] <= 0;
                imag_mem[i] <= 0;
            end
        end else if (ena && load_pulse) begin
            real_mem[addr] <= $signed(data_in[7:4]) << 4;
            imag_mem[addr] <= $signed(data_in[3:0]) << 4;
        end
    end
    
    // Continuous assignments for outputs
    assign real0_out = real_mem[0];
    assign imag0_out = imag_mem[0];
    assign real1_out = real_mem[1];
    assign imag1_out = imag_mem[1];
    assign real2_out = real_mem[2];
    assign imag2_out = imag_mem[2];
    assign real3_out = real_mem[3];
    assign imag3_out = imag_mem[3];
endmodule