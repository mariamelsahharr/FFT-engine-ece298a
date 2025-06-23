module butterfly_golden #(parameter WIDTH = 8) (
    input  signed [WIDTH-1:0] A_in,
    input  signed [WIDTH-1:0] B_in,
    input  signed [WIDTH-1:0] W_in,
    output signed [WIDTH-1:0] plus_out,
    output signed [WIDTH-1:0] minus_out
);

    localparam HALF_WIDTH = WIDTH / 2;

    wire signed [HALF_WIDTH-1:0] a_real = A_in[WIDTH-1 : HALF_WIDTH];
    wire signed [HALF_WIDTH-1:0] a_imag = A_in[HALF_WIDTH-1 : 0];
    wire signed [HALF_WIDTH-1:0] b_real = B_in[WIDTH-1 : HALF_WIDTH];
    wire signed [HALF_WIDTH-1:0] b_imag = B_in[HALF_WIDTH-1 : 0];
    wire signed [HALF_WIDTH-1:0] w_real = W_in[WIDTH-1 : HALF_WIDTH];
    wire signed [HALF_WIDTH-1:0] w_imag = W_in[HALF_WIDTH-1 : 0];

    wire signed [WIDTH-1:0] product_real = (w_real * b_real) - (w_imag * b_imag);
    wire signed [WIDTH-1:0] product_imag = (w_imag * b_real) + (w_real * b_imag);

    wire signed [HALF_WIDTH-1:0] product_real_scaled = product_real[WIDTH-1 : HALF_WIDTH];
    wire signed [HALF_WIDTH-1:0] product_imag_scaled = product_imag[WIDTH-1 : HALF_WIDTH];

    assign plus_out  = { a_real + product_real_scaled, a_imag + product_imag_scaled };
    assign minus_out = { a_real - product_real_scaled, a_imag - product_imag_scaled };

endmodule