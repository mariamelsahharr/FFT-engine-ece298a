module bit_reversal (
    input  logic        clk,
    input  logic        rst,
    input  logic        en,
    input  logic [15:0] in0, in1, in2, in3,
    output logic [15:0] out0, out1, out2, out3 
);

// FROM wikipedia: https://en.wikipedia.org/wiki/Bit-reversal_permutation?#:~:text=Fourier%20transforms.-,Example,-%5Bedit%5D
// mapping for 4 bit:
// 0 -> 0, 1 -> 2, 2 -> 1, 3 -> 3

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            out0 <= 16'd0;
            out1 <= 16'd0;
            out2 <= 16'd0;
            out3 <= 16'd0;
        end else if (en) begin
            out0 <= in0; // index 0 → 0
            out1 <= in2; // index 1 → 2
            out2 <= in1; // index 2 → 1
            out3 <= in3; // index 3 → 3
        end
    end

endmodule
