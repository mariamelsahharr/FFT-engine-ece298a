module fft_4point_16bit (
    input             clk,
    input             reset,
    input      [15:0] sample0_in,
    input      [15:0] sample1_in,
    input      [15:0] sample2_in,
    input      [15:0] sample3_in,
    input             start,
    output logic [15:0] freq0_out,
    output logic [15:0] freq1_out,
    output logic [15:0] freq2_out,
    output logic [15:0] freq3_out,
    output logic      done
);

    // Twiddle factors
    wire [15:0] W_0_2 = 16'b1000000000000000; // 1
    wire [15:0] W_0_4 = 16'b1000000000000000; // 1
    wire [15:0] W_1_4 = 16'b0000000010000000; // j (for example, placeholder)

    // Butterfly instance
    reg  [15:0] b_A, b_B, b_W;
    wire [15:0] b_plus, b_minus;
    butterfly #(16) b1(b_A, b_B, b_W, b_plus, b_minus);

    // State machine
    typedef enum logic [2:0] {
        RESET    = 3'd0,
        LOAD     = 3'd1,
        STAGE1_0 = 3'd2,
        STAGE1_1 = 3'd3,
        STAGE2_0 = 3'd4,
        STAGE2_1 = 3'd5,
        STAGE2_2 = 3'd6,
        DONE     = 3'd7
    } state_t;

    state_t state, next_state;

    // Registers for intermediate values
    reg [15:0] X0, X1, X2, X3;
    reg [15:0] Y0, Y1, Y2, Y3;

    always_ff @(posedge clk or posedge reset) begin
        if (reset) begin
            state      <= RESET;
            done       <= 0;
            freq0_out  <= 0;
            freq1_out  <= 0;
            freq2_out  <= 0;
            freq3_out  <= 0;
        end else begin
            state <= next_state;

            case (state)
                LOAD: begin
                    X0 <= sample0_in;
                    X1 <= sample1_in;
                    X2 <= sample2_in;
                    X3 <= sample3_in;
                    done <= 0;
                end

                STAGE1_0: begin
                    b_A <= X0;
                    b_B <= X2;
                    b_W <= W_0_2;
                end
                STAGE1_1: begin
                    Y0 <= b_plus;
                    Y2 <= b_minus;
                    b_A <= X1;
                    b_B <= X3;
                    b_W <= W_0_2;
                end
                STAGE2_0: begin
                    Y1 <= b_plus;
                    Y3 <= b_minus;
                    b_A <= Y0;
                    b_B <= Y1;
                    b_W <= W_0_4;
                end
                STAGE2_1: begin
                    freq0_out <= b_plus;
                    freq2_out <= b_minus;
                    b_A <= Y2;
                    b_B <= Y3;
                    b_W <= W_1_4;
                end
                STAGE2_2: begin
                    freq1_out <= b_plus;
                    freq3_out <= b_minus;
                end

                DONE: begin
                    done <= 1;
                end
            endcase
        end
    end

    // Next state logic
    always_comb begin
        case (state)
            RESET:      next_state = start ? LOAD : RESET;
            LOAD:       next_state = STAGE1_0;
            STAGE1_0:   next_state = STAGE1_1;
            STAGE1_1:   next_state = STAGE2_0;
            STAGE2_0:   next_state = STAGE2_1;
            STAGE2_1:   next_state = STAGE2_2;
            STAGE2_2:   next_state = DONE;
            DONE:       next_state = start ? DONE : RESET;
            default:    next_state = RESET;
        endcase
    end

endmodule
