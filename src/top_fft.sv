module tt_um_FFT_engine (
    input  wire [7:0] ui_in,    // Control: ui_in[0]=load, ui_in[1]=output
    output logic [7:0] uo_out,  // 7-segment display
    input  wire [7:0] uio_in,   // Bidirectional data port (input when loading)
    output wire [7:0] uio_out,  // Bidirectional data port (output when displaying)
    output logic [7:0] uio_oe,  // Output enable (all 1s when displaying)
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

    // System control signals
    wire rst = ~rst_n;
    wire load_pulse = ui_in[0];
    wire output_pulse = ui_in[1];
    
    // Sample storage (4 complex 8-bit samples)
    logic [7:0] samples_real[0:3];
    logic [7:0] samples_imag[0:3];
    
    // FFT output storage
    logic [7:0] fft_real[0:3];
    logic [7:0] fft_imag[0:3];
    
    // Control state
    logic [1:0] sample_counter;
    logic [1:0] output_counter;
    logic processing, done;
    
    // Twiddle factors (W4^0 = 1, W4^1 = -j)
    localparam [7:0] W0_real = 8'h80; // 1.0 fixed-point (Q1.7)
    localparam [7:0] W0_imag = 8'h00;
    localparam [7:0] W1_real = 8'h00;
    localparam [7:0] W1_imag = 8'h80; // -j fixed-point
    
    // Display state encoding
    logic [3:0] display_state;
    always_comb begin
        if (processing) display_state = 4'd5; // 'C' for computing
        else if (done) display_state = 4'd5 + output_counter + 1;
        else display_state = sample_counter + 1;
    end
    
    // Simple 7-segment display encoder
    always_comb begin
        case(display_state)
            4'd1: uo_out = 8'b00001100; // 1
            4'd2: uo_out = 8'b01011010; // 2
            4'd3: uo_out = 8'b01001110; // 3
            4'd4: uo_out = 8'b01100100; // 4
            4'd5: uo_out = 8'b00111000; // C
            4'd6: uo_out = 8'b01101100; // 5
            4'd7: uo_out = 8'b01111100; // 6
            4'd8: uo_out = 8'b00001110; // 7
            default: uo_out = 8'b0;
        endcase
    end
    
    // Main control FSM
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            sample_counter <= 0;
            output_counter <= 0;
            processing <= 0;
            done <= 0;
            samples_real <= '{default:0};
            samples_imag <= '{default:0};
            uio_oe <= 8'h00;
        end else if (ena) begin
            // Input handling
            if (load_pulse && !processing && !done) begin
                samples_real[sample_counter] <= uio_in[7:4] << 4; // Real part (upper nibble)
                samples_imag[sample_counter] <= uio_in[3:0] << 4; // Imag part (lower nibble)
                
                if (sample_counter == 3) begin
                    processing <= 1;
                    sample_counter <= 0;
                end else begin
                    sample_counter <= sample_counter + 1;
                end
            end
            
            // FFT computation (2-stage pipeline)
            if (processing) begin
                // Stage 1: First two butterflies
                fft_real[0] <= samples_real[0] + samples_real[2];
                fft_imag[0] <= samples_imag[0] + samples_imag[2];
                fft_real[1] <= samples_real[0] - samples_real[2];
                fft_imag[1] <= samples_imag[0] - samples_imag[2];
                fft_real[2] <= samples_real[1] + samples_real[3];
                fft_imag[2] <= samples_imag[1] + samples_imag[3];
                fft_real[3] <= samples_real[1] - samples_real[3];
                fft_imag[3] <= samples_imag[1] - samples_imag[3];
                
                // Stage 2: Final butterflies with twiddle factors
                // X0 = f0 + f2 (already done)
                // X1 = f1 + W1*f3
                fft_real[1] <= fft_real[1] + (fft_imag[3] * W1_imag >> 7);
                fft_imag[1] <= fft_imag[1] - (fft_real[3] * W1_imag >> 7);
                // X2 = f0 - f2
                fft_real[2] <= fft_real[0] - fft_real[2];
                fft_imag[2] <= fft_imag[0] - fft_imag[2];
                // X3 = f1 - W1*f3
                fft_real[3] <= fft_real[1] - (fft_imag[3] * W1_imag >> 7);
                fft_imag[3] <= fft_imag[1] + (fft_real[3] * W1_imag >> 7);
                
                processing <= 0;
                done <= 1;
            end
            
            // Output handling
            if (output_pulse && done) begin
                uio_oe <= 8'hFF; // Enable output drivers
                if (output_counter == 3) begin
                    output_counter <= 0;
                    done <= 0;
                end else begin
                    output_counter <= output_counter + 1;
                end
            end else begin
                uio_oe <= 8'h00;
            end
        end
    end
    
    // Output multiplexer
    assign uio_out = {fft_real[output_counter][7:4], fft_imag[output_counter][7:4]};
    
endmodule