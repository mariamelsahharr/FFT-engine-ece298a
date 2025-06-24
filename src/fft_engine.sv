module fft_4point_16bit (
    input             clk,
    input             reset,
    input      [15:0] sample0_in,
    input      [15:0] sample1_in,
    input      [15:0] sample2_in,
    input      [15:0] sample3_in,
    input             start,
    // Flattened output ports
    output logic [15:0] freq0_out,
    output logic [15:0] freq1_out,
    output logic [15:0] freq2_out,
    output logic [15:0] freq3_out,
    output logic      done
);
    wire [15:0] W_0_2 = 16'b1000000000000000;
    wire [15:0] W_0_4 = 16'b1000000000000000;
    wire [15:0] W_1_4 = 16'b0000000010000000;

    reg [15:0] b1_A;
    reg [15:0] b1_B;
    reg [15:0] b1_W;
    reg [15:0] b1_plus;
    reg [15:0] b1_minus;

    reg [15:0] b2_A;
    reg [15:0] b2_B;
    reg [15:0] b2_W;
    reg [15:0] b2_plus;
    reg [15:0] b2_minus;

    reg [1:0] current_stage = RESET;
    reg [1:0] current_stage_d;

    parameter RESET   = 2'b00;
    parameter STAGE_1 = 2'b01;
    parameter STAGE_2 = 2'b10;
    parameter DONE    = 2'b11;

    butterfly #(16) b1(b1_A, b1_B, b1_W, b1_plus, b1_minus);
    butterfly #(16) b2(b2_A, b2_B, b2_W, b2_plus, b2_minus);

    

    always @(posedge clk) begin

        if (reset) begin // Add reset for outputs here
            freq0_out <= '0;
            freq1_out <= '0;
            freq2_out <= '0;
            freq3_out <= '0;
            done      <= 1'b0;
            current_stage <= RESET;
        end else begin
            current_stage <= current_stage_d;
            
            case (current_stage)
                RESET: begin
                    // No need to reset freqs here anymore, done in main reset
                    done <= 1'b0; // Ensure done is low when not in DONE state
                end
                STAGE_1: begin
                // assign values
                // run first butterfly units
                // bA - X0, bB - X2, fA - X1, fB - X3
                b1_A <= sample0_in;
                b1_B <= sample2_in;
                b2_A <= sample1_in;
                b2_B <= sample3_in;
                b1_W <= W_0_2;
                b2_W <= W_0_2;

            end
            STAGE_2: begin
                // reassign values
                // run second butterfly units
                b1_A <= b1_plus;
                b1_B <= b2_plus;
                b2_A <= b1_minus;
                b2_B <= b2_minus;
                b1_W <= W_0_4;
                b2_W <= W_1_4;
            end
                DONE: begin
                    // Assign to the new flattened outputs
                    freq0_out <= b1_plus;
                    freq1_out <= b2_plus;
                    freq2_out <= b1_minus;
                    freq3_out <= b2_minus;
                    done      <= 1'b1;
                end
            endcase
        end

    end
    always_comb begin
        case(current_stage)
            RESET: begin
                if (start) current_stage_d = STAGE_1;
                else current_stage_d = RESET;
            end
            STAGE_1: begin
                current_stage_d = STAGE_2;
            end
            STAGE_2: begin
                current_stage_d = DONE;
            end
            DONE: begin
                if (!start) current_stage_d = RESET;
                else current_stage_d = DONE;
            end
        endcase
    end

endmodule