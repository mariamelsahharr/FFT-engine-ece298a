module display_controller (
    input  wire [3:0] fsm_state_in, // TBD, TODO: reconsider?
    output logic [7:0] seg_out
);

    // 7-segment patterns for 1-8, C
    localparam [7:0]
        D_1 = 8'b00001100, // 1
        D_2 = 8'b01011010, // 2
        D_3 = 8'b01001110, // 3
        D_4 = 8'b01100110, // 4
        D_5 = 8'b01101100, // 5
        D_6 = 8'b01111100, // 6
        D_7 = 8'b00001110, // 7
        D_8 = 8'b01111110, // 8
        D_C = 8'b00111000, // C
        D_BLANK = 8'b0;

    always_comb begin
        case (fsm_state_in)
            4'd1:  seg_out = D_1;
            4'd2:  seg_out = D_2;
            4'd3:  seg_out = D_3;
            4'd4:  seg_out = D_4;
            4'd5:  seg_out = D_C;
            4'd6:  seg_out = D_5;
            4'd7:  seg_out = D_6;
            4'd8:  seg_out = D_7;
            4'd9:  seg_out = D_8;
            default: seg_out = D_BLANK;
        endcase
    end
endmodule