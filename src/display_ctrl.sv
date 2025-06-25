module display_ctrl (
    input  logic [1:0] sample_counter,
    input  logic [1:0] output_counter,
    input  logic processing, done,
    output logic [7:0] seg_out
);
    // 7-segment encodings
    localparam [7:0] 
        D_1 = 8'b00001100, D_2 = 8'b01011010,
        D_3 = 8'b01001110, D_4 = 8'b01100100,
        D_C = 8'b00111000, D_5 = 8'b01101100,
        D_6 = 8'b01111100, D_7 = 8'b00001110;
    
    always_comb begin
        if (processing) seg_out = D_C;
        else if (done) begin
            case(output_counter + 1)
                2'd1: seg_out = D_5;
                2'd2: seg_out = D_6;
                2'd3: seg_out = D_7;
                default: seg_out = D_5;
            endcase
        end else begin
            case(sample_counter + 1)
                2'd1: seg_out = D_1;
                2'd2: seg_out = D_2;
                2'd3: seg_out = D_3;
                2'd4: seg_out = D_4;
                default: seg_out = 8'b0;
            endcase
        end
    end
endmodule