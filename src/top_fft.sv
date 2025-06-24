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
    
    // Data paths
    logic signed [7:0] samples_real[0:3];
    logic signed [7:0] samples_imag[0:3];
    logic signed [7:0] fft_real[0:3];
    logic signed [7:0] fft_imag[0:3];
    
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
        .real_out(samples_real),
        .imag_out(samples_imag)
    );
    
    fft_engine fft_inst (
        .clk(clk), .rst(rst),
        .in_real(samples_real),
        .in_imag(samples_imag),
        .out_real(fft_real),
        .out_imag(fft_imag)
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
    
    // Output multiplexer
    assign uio_out = {fft_real[output_counter][7:4], 
                    fft_imag[output_counter][7:4]};
endmodule