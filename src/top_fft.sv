module tt_um_FFT_engine (
    input  wire [7:0] ui_in,
    output logic [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output logic [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);
    // System signals
    wire rst = ~rst_n;
    
    // Control signals
    wire load_pulse, output_pulse;
    wire [1:0] addr;
    
    // Data paths - individual signals
    logic signed [7:0] sample0_real, sample0_imag;
    logic signed [7:0] sample1_real, sample1_imag;
    logic signed [7:0] sample2_real, sample2_imag;
    logic signed [7:0] sample3_real, sample3_imag;
    
    // FFT outputs - individual signals
    logic signed [7:0] fft0_real, fft0_imag;
    logic signed [7:0] fft1_real, fft1_imag;
    logic signed [7:0] fft2_real, fft2_imag;
    logic signed [7:0] fft3_real, fft3_imag;
    
    // State tracking
    logic processing, done;
    logic [1:0] output_counter;
    
    // Module instantiations
    io_ctrl io_inst (
        .clk(clk), .rst(rst), .ena(ena),
        .ui_in0(ui_in[0]), .ui_in1(ui_in[1]),
        .load_pulse(load_pulse),
        .output_pulse(output_pulse),
        .addr(addr)
    );
    
    memory_ctrl mem_inst (
        .clk(clk), .rst(rst), .ena(ena),
        .load_pulse(load_pulse),
        .addr(addr),
        .data_in(uio_in),
        .real0_out(sample0_real), .imag0_out(sample0_imag),
        .real1_out(sample1_real), .imag1_out(sample1_imag),
        .real2_out(sample2_real), .imag2_out(sample2_imag),
        .real3_out(sample3_real), .imag3_out(sample3_imag)
    );
    
    // Create packed arrays for FFT input
    logic signed [7:0] fft_in_real [0:3];
    logic signed [7:0] fft_in_imag [0:3];
    
    always_comb begin
        fft_in_real[0] = sample0_real;
        fft_in_real[1] = sample1_real;
        fft_in_real[2] = sample2_real;
        fft_in_real[3] = sample3_real;
        fft_in_imag[0] = sample0_imag;
        fft_in_imag[1] = sample1_imag;
        fft_in_imag[2] = sample2_imag;
        fft_in_imag[3] = sample3_imag;
    end
    
    fft_engine fft_inst (
        .clk(clk), .rst(rst),
        .in_real(fft_in_real),
        .in_imag(fft_in_imag),
        .out0_real(fft0_real), .out0_imag(fft0_imag),
        .out1_real(fft1_real), .out1_imag(fft1_imag),
        .out2_real(fft2_real), .out2_imag(fft2_imag),
        .out3_real(fft3_real), .out3_imag(fft3_imag)
    );
    
    display_ctrl disp_inst (
        .sample_counter(addr),
        .output_counter(output_counter),
        .processing(processing), .done(done),
        .seg_out(uo_out)
    );
    
    // Output control
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            processing <= '0;
            done <= '0;
            output_counter <= '0;
            uio_oe <= '0;
        end else if (ena) begin
            // Set processing flag when last sample loaded
            if (load_pulse && addr == 2'd3) 
                processing <= '1;
            else if (processing) 
                processing <= '0;
            
            // Set done flag when processing completes
            if (addr == 2'd3 && !processing)
                done <= '1;
            else if (output_counter == 2'd3)
                done <= '0;
            
            // Handle output counter
            if (output_pulse && done) begin
                uio_oe <= '1;
                if (output_counter == 2'd3)
                    output_counter <= '0;
                else
                    output_counter <= output_counter + 1;
            end else begin
                uio_oe <= '0;
            end
        end
    end
    
    // Create packed array for output selection
    logic signed [7:0] fft_out_real [0:3];
    logic signed [7:0] fft_out_imag [0:3];
    
    always_comb begin
        fft_out_real[0] = fft0_real;
        fft_out_real[1] = fft1_real;
        fft_out_real[2] = fft2_real;
        fft_out_real[3] = fft3_real;
        fft_out_imag[0] = fft0_imag;
        fft_out_imag[1] = fft1_imag;
        fft_out_imag[2] = fft2_imag;
        fft_out_imag[3] = fft3_imag;
    end
    
    // Output multiplexer
    assign uio_out = {fft_out_real[output_counter][7:4], 
                     fft_out_imag[output_counter][7:4]};
endmodule