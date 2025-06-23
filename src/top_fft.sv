// nano_fft_top.sv
// This top-level module is specifically designed to control the provided
// fft_4point_16bit engine, which uses a start/done handshake and array I/O.

module tt_um_FFT_engine ( // Using the TinyTapeout wrapper name
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output logic [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

    // --- Signal Declarations ---
    wire rst = ~rst_n;

    // Switch Interface signals
    wire load_pulse;
    wire output_pulse;

    // Memory Interface signals (using a simpler single-port memory now)
    logic [1:0]  mem_addr;
    logic        mem_we;
    logic [15:0] mem_wdata;
    wire  [15:0] mem_rdata;

    // FFT Engine Interface signals
    logic        fft_start;
    wire         fft_done;
    logic [15:0] fft_samples [0:3]; // Array to match engine's input
    wire  [15:0] fft_freqs   [0:3]; // Array to match engine's output

    // --- System FSM States ---
    localparam [3:0]
        S_IDLE          = 4'd0,
        S_LOAD          = 4'd1,
        S_FFT_READ_MEM  = 4'd2,
        S_FFT_START     = 4'd3,
        S_FFT_WAIT      = 4'd4,
        S_FFT_WRITE_MEM = 4'd5, // This state is no longer needed since engine outputs directly
        S_OUTPUT_WAIT   = 4'd6,
        S_OUTPUT_DRIVE  = 4'd7;
    
    logic [3:0] state, next_state;
    
    // --- Counters ---
    logic [1:0] load_counter;
    logic [1:0] output_counter;
    logic [1:0] mem_read_counter;

    // --- Module Instantiations ---

    switch_interface sw_if_load (.clk(clk), .rst(rst), .sw_in(ui_in[0]), .pulse_out(load_pulse));
    switch_interface sw_if_output (.clk(clk), .rst(rst), .sw_in(ui_in[1]), .pulse_out(output_pulse));

    // Using a simpler single-port RAM as dual-port is not needed for this FSM flow
    // and this saves area.
    fft_memory_single_port memory (
        .clk(clk), .addr(mem_addr), .we(mem_we), .wdata(mem_wdata), .rdata(mem_rdata)
    );

    // Instantiate your specific FFT engine
    fft_4point_16bit fft_core (
        .clk(clk), .reset(rst),
        .samples(fft_samples),
        .start(fft_start),
        .freqs(fft_freqs),
        .done(fft_done)
    );

    display_controller disp_ctrl ( .fsm_state_in(display_code), .seg_out(uo_out) );
    // --- Display Logic ---
    // Translates FSM state and counters into the correct display code.
    always_comb begin
        case (state)
            S_IDLE, S_LOAD:
                display_code = load_counter + 1;

            S_FFT_READ_MEM, S_FFT_WAIT, S_FFT_WRITE_MEM:
                // Any of the computation states should display 'C'.
                display_code = 9;

            S_OUTPUT_WAIT, S_OUTPUT_DRIVE:
                // output_counter will be 0, 1, 2, or 3. We want to display 5, 6, 7, or 8.
                display_code = output_counter + 5;
            
            default:
                display_code = 0;
        endcase
    end
    // --- FSM Sequential Logic ---
    always_ff @(posedge clk) begin
        if (rst) begin
            state <= S_IDLE;
            load_counter <= 0;
            output_counter <= 0;
            mem_read_counter <= 0;
        end else if (ena) begin
            state <= next_state;
            
            if (next_state != state) begin // On state change, reset counters
                if (next_state == S_FFT_READ_MEM) mem_read_counter <= 0;
            end else begin
                if (state == S_LOAD)         load_counter <= load_counter + 1;
                if (state == S_FFT_READ_MEM) mem_read_counter <= mem_read_counter + 1;
                if (state == S_OUTPUT_DRIVE) output_counter <= output_counter + 1;
            end

            // Latch the memory read data into the correct array slot
            if (state == S_FFT_READ_MEM) begin
                fft_samples[mem_read_counter] <= mem_rdata;
            end
            
            if (next_state == S_IDLE && state == S_OUTPUT_WAIT) begin
                load_counter <= 0;
                output_counter <= 0;
            end
        end
    end
    
    // --- FSM Combinational Logic ---
    always_comb begin
        next_state   = state;
        uio_oe       = 8'h00;
        mem_addr     = '0;
        mem_we       = 1'b0;
        mem_wdata    = '0;
        fft_start    = 1'b0;

        case (state)
            S_IDLE: if (load_pulse && load_counter < 4) next_state = S_LOAD;
                    else if (load_counter == 4) next_state = S_FFT_READ_MEM;

            S_LOAD: begin
                mem_we    = 1'b1;
                mem_addr  = load_counter;
                mem_wdata = {{4{uio_in[7]}}, uio_in[7:4], {4{uio_in[3]}}, uio_in[3:0]};
                next_state = S_IDLE;
            end

            S_FFT_READ_MEM: begin
                // Sequentially read 4 samples from memory into the fft_samples array
                mem_addr = mem_read_counter;
                if (mem_read_counter == 3) begin
                    next_state = S_FFT_START;
                end else begin
                    next_state = S_FFT_READ_MEM;
                end
            end
            
            S_FFT_START: begin
                // All samples are now in the fft_samples array. Pulse start.
                fft_start = 1'b1;
                next_state = S_FFT_WAIT;
            end

            S_FFT_WAIT: begin
                // The engine's FSM is now running. Wait for the 'done' signal.
                if (fft_done) begin
                    // The 'fft_freqs' output array now holds the valid results.
                    // We can go directly to outputting them. No need to write back to RAM.
                    next_state = S_OUTPUT_WAIT;
                end else begin
                    next_state = S_FFT_WAIT;
                end
            end
            
            // S_FFT_WRITE_MEM is no longer needed. We will output directly from fft_freqs.

            S_OUTPUT_WAIT: if (output_pulse && output_counter < 4) next_state = S_OUTPUT_DRIVE;
                           else if (output_counter == 4) next_state = S_IDLE;

            S_OUTPUT_DRIVE: begin
                uio_oe = 8'hFF;
                // No memory read needed here.
                next_state = S_OUTPUT_WAIT;
            end
        endcase
    end
    
    // --- Output Logic ---
    // The uio_out now comes directly from the FFT engine's output register.
    // This saves us from having to write the results back to memory first.
    assign uio_out = {fft_freqs[output_counter][15:12], fft_freqs[output_counter][7:4]};

endmodule