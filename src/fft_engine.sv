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
    
    // Create internal arrays from individual ports
    logic signed [WIDTH-1:0] in_real[0:3];
    logic signed [WIDTH-1:0] in_imag[0:3];
    logic signed [WIDTH-1:0] out_real[0:3];
    logic signed [WIDTH-1:0] out_imag[0:3];
    
    always_comb begin
        in_real = '{in0_real, in1_real, in2_real, in3_real};
        in_imag = '{in0_imag, in1_imag, in2_imag, in3_imag};
        
        // Assign outputs from internal arrays
        out0_real = out_real[0];
        out0_imag = out_imag[0];
        out1_real = out_real[1];
        out1_imag = out_imag[1];
        out2_real = out_real[2];
        out2_imag = out_imag[2];
        out3_real = out_real[3];
        out3_imag = out_imag[3];
    end
    
    // Stage 1 results
    logic signed [WIDTH-1:0] s1_real[0:3], s1_imag[0:3];
    
    // Instantiate butterfly units
    butterfly #(WIDTH) bfly_stage1_0 (
        .A_real(in_real[0]), .A_imag(in_imag[0]),
        .B_real(in_real[2]), .B_imag(in_imag[2]),
        .W_real(W0_real), .W_imag(W0_imag),
        .Pos_real(s1_real[0]), .Pos_imag(s1_imag[0]),
        .Neg_real(s1_real[1]), .Neg_imag(s1_imag[1])
    );
    
    butterfly #(WIDTH) bfly_stage1_1 (
        .A_real(in_real[1]), .A_imag(in_imag[1]),
        .B_real(in_real[3]), .B_imag(in_imag[3]),
        .W_real(W0_real), .W_imag(W0_imag),
        .Pos_real(s1_real[2]), .Pos_imag(s1_imag[2]),
        .Neg_real(s1_real[3]), .Neg_imag(s1_imag[3])
    );
    
    // Stage 2 butterflies
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            for (int i = 0; i < 4; i++) begin
                out_real[i] <= '0;
                out_imag[i] <= '0;
            end
        end else begin
            // First butterfly (no multiplication needed)
            out_real[0] <= s1_real[0] + s1_real[2];
            out_imag[0] <= s1_imag[0] + s1_imag[2];
            out_real[2] <= s1_real[0] - s1_real[2];
            out_imag[2] <= s1_imag[0] - s1_imag[2];
            
            // Second butterfly (with twiddle factor)
            butterfly #(WIDTH) bfly_stage2_1 (
                .A_real(s1_real[1]), .A_imag(s1_imag[1]),
                .B_real(s1_real[3]), .B_imag(s1_imag[3]),
                .W_real(W1_real), .W_imag(W1_imag),
                .Pos_real(out_real[1]), .Pos_imag(out_imag[1]),
                .Neg_real(out_real[3]), .Neg_imag(out_imag[3])
            );
        end
    end
endmodule

