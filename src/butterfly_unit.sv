module butterfly_unit #(parameter WIDTH = 8) (
    input  logic        clk, // system clock
    input  logic        rst, // synch reset
    input  logic        en,  // enable signal
    input  logic signed [WIDTH-1:0] A,   // 4-bit Real, 4-bit Imag
    input  logic signed [WIDTH-1:0] B,   // Complex input B (complex)
    input  logic signed [WIDTH-1:0] T,   // Twiddle factor (complex)
    output logic signed [WIDTH-1:0] Pos, // A + T*B
    output logic signed [WIDTH-1:0] Neg, // A - T*B
    output logic        valid // output is valid when high
);

    // This logic is based on the combinational reference designs,
    // adapted for a sequential wrapper. WIDTH determines the total
    // packed size, so for 8-bit, real/imag parts are 4-bit.

    localparam HALF_WIDTH = WIDTH / 2;

// calculation enable
        wire calc_enable = en && !rst;

    wire signed [HALF_WIDTH-1:0] a_real, a_imag;
    wire signed [HALF_WIDTH-1:0] b_real, b_imag;
    wire signed [HALF_WIDTH-1:0] t_real, t_imag;

//full width multip
    wire signed [WIDTH-1:0] product_real;
    wire signed [WIDTH-1:0] product_imag;

    // Wires for the scaled-down multiplication result
    wire signed [HALF_WIDTH-1:0] product_real_scaled;
    wire signed [HALF_WIDTH-1:0] product_imag_scaled;
    
    // Unpack inputs into real and imaginary components
    assign a_real = A[WIDTH-1 : HALF_WIDTH];
    assign a_imag = A[HALF_WIDTH-1 : 0];
    assign b_real = B[WIDTH-1 : HALF_WIDTH];
    assign b_imag = B[HALF_WIDTH-1 : 0];
    assign t_real = T[WIDTH-1 : HALF_WIDTH];
    assign t_imag = T[HALF_WIDTH-1 : 0];

    //complex mult
    assign product_real = calc_enable ? (t_real * b_real) - (t_imag * b_imag) : '0;
    assign product_imag = calc_enable ? (t_imag * b_real) + (t_real * b_imag) : '0;

    //scale back down take msb only
    assign product_real_scaled = product_real[WIDTH-1 : HALF_WIDTH];
    assign product_imag_scaled = product_imag[WIDTH-1 : HALF_WIDTH];

    wire signed [WIDTH-1:0] pos_comb, neg_comb;
    assign pos_comb  = calc_enable ? { a_real + product_real_scaled, a_imag + product_imag_scaled } : '0;
    assign neg_comb  = calc_enable ? { a_real - product_real_scaled, a_imag - product_imag_scaled } : '0;

//outputs on clk edge
        always_ff @(posedge clk) begin
        Pos <= pos_comb;
        Neg <= neg_comb;
        valid <= calc_enable;
    end

endmodule