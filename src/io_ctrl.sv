module io_ctrl (
    input  logic clk, rst, ena,
    input  logic ui_in0, ui_in1,
    output logic load_pulse,
    output logic output_pulse,
    output logic [1:0] addr
);
    logic [1:0] counter;
    logic prev_in0, prev_in1;
    
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            counter <= '0;
            prev_in0 <= '0;
            prev_in1 <= '0;
        end else if (ena) begin
            prev_in0 <= ui_in0;
            prev_in1 <= ui_in1;
            
            if (ui_in0 && !prev_in0) begin
                counter <= counter + 1;
            end
        end
    end
    
    assign load_pulse = ui_in0 && !prev_in0;
    assign output_pulse = ui_in1 && !prev_in1;
    assign addr = counter;
endmodule