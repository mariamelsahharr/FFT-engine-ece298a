module butterfly_unit (
    input  logic        clk, // system clock
    input  logic        rst, // synch reset
    input  logic [15:0] A,   // Complex input A: [15:8] = Real, [7:0] = Imag 
    input  logic [15:0] B,   // Complex input B (complex)
    input  logic [15:0] T,   // Twiddle factor (complex)
    output logic [15:0] Pos, // A + T*B
    output logic [15:0] Neg  // A - T*B
);

    //A, B real and imaginary parts, twiddle factor T real and imaginary parts
    logic signed [7:0] Ar, Ai, Br, Bi, Tr, Ti;

    //interm results of T*B
    logic signed [15:0] Tr_int, Ti_int; 

    // T * B = (Tr + jWi)(Br + jBi)

    // FINAL!! Outputs for positive and negative results
    logic signed [15:0] real_pos, imag_pos;
    logic signed [15:0] real_neg, imag_neg;

    // extract real + imag parts,, upper 8 bits = real, lower 8 bits = imag?
    assign Ar = A[15:8];
    assign Ai = A[7:0];
    assign Br = B[15:8];
    assign Bi = B[7:0];
    assign Tr = T[15:8];
    assign Ti = T[7:0];

    // comp multiply
    // T * B = (Tr*Br - Ti*Bi) + j(Tr*Bi + Ti*Br)
    always_comb begin
        Tr_int = (Tr * Br) - (Ti * Bi); // Real part
        Ti_int = (Tr * Bi) + (Ti * Br); // Imag part
    end

    // Add/Sub
    always_comb begin
        real_pos = Ar + Tr_int[15:8];
        imag_pos = Ai + Ti_int[15:8];
        real_neg = Ar - Tr_int[15:8];
        imag_neg = Ai - Ti_int[15:8];
    end

    // Output assignment with optional saturation
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            Pos <= 16'd0;
            Neg <= 16'd0;
        end else begin
            Pos <= {real_pos[15:8], imag_pos[15:8]};
            Neg <= {real_neg[15:8], imag_neg[15:8]};
        end
    end

endmodule
