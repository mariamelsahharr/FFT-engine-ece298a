module fft_engineee #(parameter WIDTH = 16) (Add commentMore actions
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
    // Twiddle Factors
    localparam [15:0] W_1_0 = 16'h8000;
    localparam [15:0] W_1_1 = 16'h0080;

    // FSM States for sequencing the 4 butterfly ops
    localparam [2:0]
        S_IDLE   = 3'd0,
        S_S1_B0  = 3'd1, // Stage 1, Butterfly 0 (x0, x2)
        S_S1_B1  = 3'd2, // Stage 1, Butterfly 1 (x1, x3)
        S_S2_B0  = 3'd3, // Stage 2, Butterfly 0
        S_S2_B1  = 3'd4, // Stage 2, Butterfly 1
        S_DONE   = 3'd5;

    logic [2:0] state, next_state;

    // Registers to hold the intermediate results between stages
    reg signed [WIDTH-1:0] s1_p0, s1_n0, s1_p1, s1_n1;

    // Wires to feed the single butterfly unit
    logic signed [WIDTH-1:0] bfly_A_in, bfly_B_in, bfly_T_in;
    wire  signed [WIDTH-1:0] bfly_Pos_out, bfly_Neg_out;
    wire  bfly_valid;

    // Instantiate Butterfly Unit
    butterfly_unit #(.WIDTH(WIDTH)) the_one_butterfly (
        .clk(clk), .rst(~rst_n), .en(state != S_IDLE && state != S_DONE),
        .A(bfly_A_in), .B(bfly_B_in), .T(bfly_T_in),
        .Pos(bfly_Pos_out), .Neg(bfly_Neg_out), .valid(bfly_valid)
    );

    // --- FSM and Datapath Control ---
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            state <= S_IDLE;
            valid <= 1'b0;
            X0_out <= '0; X1_out <= '0; X2_out <= '0; X3_out <= '0;
            s1_p0 <= '0; s1_n0 <= '0; s1_p1 <= '0; s1_n1 <= '0;
        end else begin
            state <= next_state;
            valid <= (next_state == S_DONE);
            
            // Latch results when the butterfly is valid
            if (bfly_valid) begin
                case(state)
                    S_S1_B0: begin s1_p0 <= bfly_Pos_out; s1_n0 <= bfly_Neg_out; end
                    S_S1_B1: begin s1_p1 <= bfly_Pos_out; s1_n1 <= bfly_Neg_out; end
                    S_S2_B0: begin X0_out <= bfly_Pos_out; X2_out <= bfly_Neg_out; end
                    S_S2_B1: begin X1_out <= bfly_Pos_out; X3_out <= bfly_Neg_out; end
                endcase
            end
        end
    end

    always_comb begin
        next_state = state;
        // Default inputs to butterfly
        bfly_A_in = '0; bfly_B_in = '0; bfly_T_in = '0;
        
        case(state)
            S_IDLE: if (en) next_state = S_S1_B0;
            S_S1_B0: if (bfly_valid) next_state = S_S1_B1;
            S_S1_B1: if (bfly_valid) next_state = S_S2_B0;
            S_S2_B0: if (bfly_valid) next_state = S_S2_B1;
            S_S2_B1: if (bfly_valid) next_state = S_DONE;
            S_DONE:  if (!en) next_state = S_IDLE;
        endcase
        
        // Mux inputs to the butterfly based on current FSM state
        case(state)
            S_S1_B0: begin bfly_A_in=x0_in;  bfly_B_in=x2_in;  bfly_T_in=W_1_0; end
            S_S1_B1: begin bfly_A_in=x1_in;  bfly_B_in=x3_in;  bfly_T_in=W_1_0; end
            S_S2_B0: begin bfly_A_in=s1_p0;  bfly_B_in=s1_p1;  bfly_T_in=W_1_0; end
            S_S2_B1: begin bfly_A_in=s1_n0;  bfly_B_in=s1_n1;  bfly_T_in=W_1_1; end
        endcase
    end
endmodule