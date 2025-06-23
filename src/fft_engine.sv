module fft_engine #(parameter WIDTH = 16) (
    input  logic        clk,
    input  logic        rst,
    input  logic        en,
    output logic        valid,
    
    input  logic signed [WIDTH-1:0] x0_in,
    input  logic signed [WIDTH-1:0] x1_in,
    input  logic signed [WIDTH-1:0] x2_in,
    input  logic signed [WIDTH-1:0] x3_in,
    output logic signed [WIDTH-1:0] X0_out,
    output logic signed [WIDTH-1:0] X1_out,
    output logic signed [WIDTH-1:0] X2_out,
    output logic signed [WIDTH-1:0] X3_out
);
    // Twiddle factors
    localparam [15:0] W_1_0 = 16'h8000;
    localparam [15:0] W_1_1 = 16'h0080;

    // FSM States
    localparam [1:0] S_IDLE    = 2'b00;
    localparam [1:0] S_STAGE_1 = 2'b01;
    localparam [1:0] S_STAGE_2 = 2'b10;
    localparam [1:0] S_VALID   = 2'b11;

    logic [1:0] state, next_state;

    logic signed [WIDTH-1:0] s1_p0, s1_n0; // Stage 1, butterfly 0 results
    logic signed [WIDTH-1:0] s1_p1, s1_n1; // Stage 1, butterfly 1 results

    // Butterfly I/O
    logic bfly0_en, bfly1_en;
    wire  bfly0_valid, bfly1_valid;
    logic signed [WIDTH-1:0] bfly0_A_in, bfly0_B_in, bfly0_T_in;
    logic signed [WIDTH-1:0] bfly1_A_in, bfly1_B_in, bfly1_T_in;
    wire  signed [WIDTH-1:0] bfly0_Pos_out, bfly0_Neg_out;
    wire  signed [WIDTH-1:0] bfly1_Pos_out, bfly1_Neg_out;

    butterfly_unit #(.WIDTH(WIDTH)) bfly0 (
        .clk(clk), .rst(rst), .en(bfly0_en),
        .A(bfly0_A_in), .B(bfly0_B_in), .T(bfly0_T_in),
        .Pos(bfly0_Pos_out), .Neg(bfly0_Neg_out), .valid(bfly0_valid)
    );
    butterfly_unit #(.WIDTH(WIDTH)) bfly1 (
        .clk(clk), .rst(rst), .en(bfly1_en),
        .A(bfly1_A_in), .B(bfly1_B_in), .T(bfly1_T_in),
        .Pos(bfly1_Pos_out), .Neg(bfly1_Neg_out), .valid(bfly1_valid)
    );

    // Control
    always_ff @(posedge clk) begin
        if (rst) begin
            state <= S_IDLE;
            X0_out <= '0; X1_out <= '0; X2_out <= '0; X3_out <= '0;
            s1_p0 <= '0; s1_n0 <= '0; s1_p1 <= '0; s1_n1 <= '0;
        end else begin
            state <= next_state;

            // Latch intermediate results when butterfly outputs are valid
            if (bfly0_valid && bfly1_valid) begin
                if (state == S_STAGE_1) begin
                    s1_p0 <= bfly0_Pos_out;
                    s1_n0 <= bfly0_Neg_out;
                    s1_p1 <= bfly1_Pos_out;
                    s1_n1 <= bfly1_Neg_out;
                end else if (state == S_STAGE_2) begin
                    X0_out <= bfly0_Pos_out;
                    X2_out <= bfly0_Neg_out;
                    X1_out <= bfly1_Pos_out;
                    X3_out <= bfly1_Neg_out;
                end
            end
        end
    end

    always_comb begin
        next_state = state;
        valid = 1'b0;
        
        // Default butterfly inputs
        bfly0_en = 1'b0; bfly1_en = 1'b0;
        bfly0_A_in = '0; bfly0_B_in = '0; bfly0_T_in = '0;
        bfly1_A_in = '0; bfly1_B_in = '0; bfly1_T_in = '0;
        
        case (state)
            S_IDLE:
                if (en) begin
                    next_state = S_STAGE_1;
                end
            
            S_STAGE_1: begin
                // Enable butterflies and provide Stage 1 inputs
                bfly0_en = 1'b1; bfly1_en = 1'b1;
                bfly0_A_in = x0_in; bfly0_B_in = x2_in; bfly0_T_in = W_1_0;
                bfly1_A_in = x1_in; bfly1_B_in = x3_in; bfly1_T_in = W_1_0;
                
                if (bfly0_valid && bfly1_valid) begin
                    next_state = S_STAGE_2;
                end
            end
            
            S_STAGE_2: begin
                // Enable butterflies and provide Stage 2 inputs from our registers
                bfly0_en = 1'b1; bfly1_en = 1'b1;
                bfly0_A_in = s1_p0; bfly0_B_in = s1_p1; bfly0_T_in = W_1_0;
                bfly1_A_in = s1_n0; bfly1_B_in = s1_n1; bfly1_T_in = W_1_1;
                
                if (bfly0_valid && bfly1_valid) begin
                    next_state = S_VALID;
                end
            end

            S_VALID: begin
                valid = 1'b1;
                if (!en) begin // Wait for master to de-assert enable before resetting
                    next_state = S_IDLE;
                end
            end
        endcase
    end

endmodule