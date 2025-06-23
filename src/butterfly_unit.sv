module butterfly_unit #(parameter WIDTH = 8) (
    input  logic        clk,
    input  logic        rst,
    input  logic        en,
    input  logic signed [WIDTH-1:0] A,
    input  logic signed [WIDTH-1:0] B,
    input  logic signed [WIDTH-1:0] T,
    output logic signed [WIDTH-1:0] Pos,
    output logic signed [WIDTH-1:0] Neg,
    output logic        valid
);

    localparam HALF_WIDTH = WIDTH / 2;

    // Unpack inputs 
    wire [HALF_WIDTH-1:0] a_real = A[WIDTH-1:HALF_WIDTH];
    wire [HALF_WIDTH-1:0] a_imag = A[HALF_WIDTH-1:0];
    wire [HALF_WIDTH-1:0] b_real = B[WIDTH-1:HALF_WIDTH];
    wire [HALF_WIDTH-1:0] b_imag = B[HALF_WIDTH-1:0];
    wire [HALF_WIDTH-1:0] t_real = T[WIDTH-1:HALF_WIDTH];
    wire [HALF_WIDTH-1:0] t_imag = T[HALF_WIDTH-1:0];

    // Complex multiplication 
    wire [WIDTH-1:0] product_real = (t_real * b_real) - (t_imag * b_imag);
    wire [WIDTH-1:0] product_imag = (t_imag * b_real) + (t_real * b_imag);
    
    // Truncation 
    wire [HALF_WIDTH-1:0] product_real_trunc = product_real[WIDTH-1 : WIDTH-1-HALF_WIDTH];
    wire [HALF_WIDTH-1:0] product_imag_trunc = product_imag[WIDTH-1 : WIDTH-1-HALF_WIDTH];

    // Combinational results 
    wire [WIDTH-1:0] pos_comb = { a_real + product_real_trunc, a_imag + product_imag_trunc };
    wire [WIDTH-1:0] neg_comb = { a_real - product_real_trunc, a_imag - product_imag_trunc };

    Sequential output stage - only update when enabled
    always_ff @(posedge clk) begin
        if (rst) begin
            Pos   <= '0;
            Neg   <= '0;
            valid <= 1'b0;
        end else if (en) begin
            Pos   <= pos_comb;
            Neg   <= neg_comb;
            valid <= 1'b1;
        end else begin
            valid <= 1'b0;
        end
    end

endmodule 