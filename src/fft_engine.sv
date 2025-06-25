module fft_engine #(
    parameter WIDTH = 8
)(
    input  logic clk, rst,
    // Individual input ports
    input  logic signed [WIDTH-1:0] in0_real, in0_imag,
    input  logic signed [WIDTH-1:0] in1_real, in1_imag,
    input  logic signed [WIDTH-1:0] in2_real, in2_imag,
    input  logic signed [WIDTH-1:0] in3_real, in3_imag,
    // Individual output ports
    output logic signed [WIDTH-1:0] out0_real, out0_imag,
    output logic signed [WIDTH-1:0] out1_real, out1_imag,
    output logic signed [WIDTH-1:0] out2_real, out2_imag,
    output logic signed [WIDTH-1:0] out3_real, out3_imag
);
    // Twiddle factors
    localparam logic signed [WIDTH-1:0] W0_real = 8'sh80; // 1.0
    localparam logic signed [WIDTH-1:0] W0_imag = 8'sh00;
    localparam logic signed [WIDTH-1:0] W1_real = 8'sh00;  // -j
    localparam logic signed [WIDTH-1:0] W1_imag = 8'sh80;
    
    // Stage 1 results
    logic signed [WIDTH-1:0] s1_real[0:3];
    logic signed [WIDTH-1:0] s1_imag[0:3];
    
    // Stage 2 butterfly outputs
    logic signed [WIDTH-1:0] bfly_pos_real, bfly_pos_imag;
    logic signed [WIDTH-1:0] bfly_neg_real, bfly_neg_imag;
    
    // Instantiate butterfly units for stage 1
    butterfly bfly_stage1_0 (
        .A_real(in0_real), .A_imag(in0_imag),
        .B_real(in2_real), .B_imag(in2_imag),
        .W_real(W0_real), .W_imag(W0_imag),
        .Pos_real(s1_real[0]), .Pos_imag(s1_imag[0]),
        .Neg_real(s1_real[1]), .Neg_imag(s1_imag[1])
    );
    
    butterfly bfly_stage1_1 (
        .A_real(in1_real), .A_imag(in1_imag),
        .B_real(in3_real), .B_imag(in3_imag),
        .W_real(W0_real), .W_imag(W0_imag),
        .Pos_real(s1_real[2]), .Pos_imag(s1_imag[2]),
        .Neg_real(s1_real[3]), .Neg_imag(s1_imag[3])
    );
    
    // Instantiate butterfly for stage 2
    butterfly bfly_stage2_1 (
        .A_real(s1_real[1]), .A_imag(s1_imag[1]),
        .B_real(s1_real[3]), .B_imag(s1_imag[3]),
        .W_real(W1_real), .W_imag(W1_imag),
        .Pos_real(bfly_pos_real), .Pos_imag(bfly_pos_imag),
        .Neg_real(bfly_neg_real), .Neg_imag(bfly_neg_imag)
    );
    
    // Stage 2 processing
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            out0_real <= '0; out0_imag <= '0;
            out1_real <= '0; out1_imag <= '0;
            out2_real <= '0; out2_imag <= '0;
            out3_real <= '0; out3_imag <= '0;
        end else begin
            // First butterfly (no multiplication needed)
            out0_real <= s1_real[0] + s1_real[2];
            out0_imag <= s1_imag[0] + s1_imag[2];
            out2_real <= s1_real[0] - s1_real[2];
            out2_imag <= s1_imag[0] - s1_imag[2];
            
            // Second butterfly outputs
            out1_real <= bfly_pos_real;
            out1_imag <= bfly_pos_imag;
            out3_real <= bfly_neg_real;
            out3_imag <= bfly_neg_imag;
        end
    end
endmodule