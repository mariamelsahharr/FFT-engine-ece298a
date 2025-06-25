module butterfly #(
    parameter WIDTH = 8
)(
    input  logic signed [WIDTH-1:0] A_real, A_imag,
    input  logic signed [WIDTH-1:0] B_real, B_imag,
    input  logic signed [WIDTH-1:0] W_real, W_imag,
    output logic signed [WIDTH-1:0] Pos_real, Pos_imag,
    output logic signed [WIDTH-1:0] Neg_real, Neg_imag
);
    // Complex multiplication: W * B
    logic signed [15:0] product_real, product_imag;
    
    assign product_real = (W_real * B_real) - (W_imag * B_imag);
    assign product_imag = (W_real * B_imag) + (W_imag * B_real);
    
    // Scale and add/subtract
    assign Pos_real = A_real + (product_real >>> (WIDTH-1));
    assign Pos_imag = A_imag + (product_imag >>> (WIDTH-1));
    assign Neg_real = A_real - (product_real >>> (WIDTH-1));
    assign Neg_imag = A_imag - (product_imag >>> (WIDTH-1));
endmodule