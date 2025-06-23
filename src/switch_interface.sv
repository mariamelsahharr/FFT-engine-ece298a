module switch_interface #(
    parameter DEBOUNCE_BITS = 16,
    parameter DEBOUNCE_MAX = 16'd50000 // 1ms assuming 50 MHz clock
)(
    input  wire clk,
    input  wire rst,
    input  wire sw_in,
    output wire pulse_out
);
            
    logic [DEBOUNCE_BITS-1:0] debounce_counter;
    logic state_debounced;
    logic state_prev;
    
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            debounce_counter <= '0;
            state_debounced  <= 1'b0;
            state_prev       <= 1'b0;
        end else begin
            state_prev <= state_debounced;
            
            if (sw_in[i] != state_debounced) begin
                debounce_counter <= debounce_counter + 1;
                if (debounce_counter == DEBOUNCE_MAX) begin
                    state_debounced <= ~state_debounced;
                    debounce_counter <= '0;
                end
            end else begin
                debounce_counter <= '0;
            end
        end
    end
    
    assign pulse_out[i] = state_debounced & ~state_prev; // Rising edge detection

endmodule