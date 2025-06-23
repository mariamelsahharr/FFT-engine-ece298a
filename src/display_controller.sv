module display_controller (
    input  logic        clk,
    input  logic        rst,
    input  logic [2:0]  main_state,
    input  logic        switch_0_latched_once,
    input  logic        switch_0_latched_twice,
    input  logic        switch_1_latched_once,
    input  logic        switch_1_latched_twice,
    output logic [7:0]  display_out
);

    // Segment encodings
    localparam SEG_1 = 8'b00000110; // '1'
    localparam SEG_2 = 8'b01011011; // '2'
    localparam SEG_3 = 8'b01001111; // '3'
    localparam SEG_4 = 8'b01100110; // '4'
    localparam SEG_C = 8'b00111001; // 'C'
    localparam SEG_BLANK = 8'b00000000;

    always_ff @(posedge clk) begin
        if (rst) begin
            display_out <= SEG_BLANK;
        end else begin
            case (1'b1)
                // Input phase
                (main_state == 3'd1 && !switch_0_latched_once):    display_out <= SEG_1;
                (main_state == 3'd1 && switch_0_latched_once && !switch_0_latched_twice): display_out <= SEG_2;
                
                // Computing FFT
                (main_state == 3'd2):                              display_out <= SEG_C;

                // Output phase
                (main_state == 3'd3 && !switch_1_latched_once):    display_out <= SEG_3;
                (main_state == 3'd3 && switch_1_latched_once && !switch_1_latched_twice): display_out <= SEG_4;

                default:                                           display_out <= SEG_BLANK;
            endcase
        end
    end

endmodule
