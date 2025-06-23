// nano_fft_top.sv (Final Version)
// This top-level module is designed to control:
// 1. The provided fft_4point_16bit engine (FSM-based, start/done).
// 2. A dual-port read memory for faster data loading.
// 3. A purely combinational butterfly unit (used inside the engine).

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

    // Dual-Port Memory Interface signals
    logic        mem_en;
    logic        mem_read_en;
    logic        mem_write_en;
    logic  [1:0] mem_addr_w;
    logic [15:0] mem_data_in;
    logic  [1:0] mem_addr_a;
    logic  [1:0] mem_addr_b;
    wire  [15:0] mem_data_out_a;
    wire  [15:0] mem_data_out_b;
    wire         mem_read_valid;

    // FFT Engine Interface signals
    logic        fft_start;
    wire         fft_done;
    logic [15:0] fft_samples [0:3]; // Array to match engine's input
    wire  [15:0] fft_freqs   [0:3]; // Array to match engine's output

    // --- System FSM States ---
    localparam [3:0]
        S_IDLE          = 4'd0,
        S_LOAD          = 4'd1,
        S_FFT_READ      = 4'd2, // A single state can read 2x samples
        S_FFT_START     = 4'd3,
        S_FFT_WAIT      = 4'd4,
        S_OUTPUT_WAIT   = 4'd5,
        S_OUTPUT_DRIVE  = 4'd6;
    
    logic [3:0] state, next_state;
    
    // --- Counters ---
    logic [1:0] load_counter;
    logic [1:0] output_counter;
    logic       mem_read_cycle; // A simple 0/1 to track which pair of samples to read

    // --- Module Instantiations ---
    switch_interface sw_if_load (.clk(clk), .rst(rst), .sw_in(ui_in[0]), .pulse_out(load_pulse));
    switch_interface sw_if_output (.clk(clk), .rst(rst), .sw_in(ui_in[1]), .pulse_out(output_pulse));

    fft_memory memory (
        .clk(clk), .rst(rst), .en(mem_en),
        .read_en(mem_read_en), .write_en(mem_write_en),
        .addr_w(mem_addr_w), .data_in(mem_data_in),
        .addr_a(mem_addr_a), .data_out_a(mem_data_out_a),
        .addr_b(mem_addr_b), .data_out_b(mem_data_out_b),
        .read_valid(mem_read_valid)
    );

    // Your specific FSM-based FFT engine
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

            S_FFT_READ, S_FFT_WAIT, S_FFT_START:
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
            mem_read_cycle <= 0;
            for (int i = 0; i < 4; i++) fft_samples[i] <= '0;
        end else if (ena) begin
            state <= next_state;

            // Increment counters on state transitions
            if (next_state == S_LOAD)         load_counter <= load_counter + 1;
            if (next_state == S_FFT_READ)     mem_read_cycle <= ~mem_read_cycle;
            if (next_state == S_OUTPUT_DRIVE) output_counter <= output_counter + 1;
            
            // Latch the memory read data into the correct array slots
            // This happens one cycle after the read addresses are set.
            if (state == S_FFT_READ) begin
                if (mem_read_cycle == 0) begin // We just read x0 and x1
                    fft_samples[0] <= mem_data_out_a;
                    fft_samples[1] <= mem_data_out_b;
                end else begin // We just read x2 and x3
                    fft_samples[2] <= mem_data_out_a;
                    fft_samples[3] <= mem_data_out_b;
                end
            end
            
            if (next_state == S_IDLE && state == S_OUTPUT_WAIT) begin
                load_counter <= 0;
                output_counter <= 0;
                mem_read_cycle <= 0;
            end
        end
    end
    
    // --- FSM Combinational Logic ---
    always_comb begin
        next_state   = state;
        uio_oe       = 8'h00;
        mem_en       = 1'b0;
        mem_read_en  = 1'b0;
        mem_write_en = 1'b0;
        mem_addr_w   = '0;
        mem_data_in  = '0;
        mem_addr_a   = '0;
        mem_addr_b   = '0;
        fft_start    = 1'b0;

        case (state)
            S_IDLE: if (load_pulse && load_counter < 4) next_state = S_LOAD;
                    else if (load_counter == 4) next_state = S_FFT_READ;

            S_LOAD: begin
                mem_en       = 1'b1;
                mem_write_en = 1'b1;
                mem_addr_w   = load_counter;
                mem_data_in  = {{4{uio_in[7]}}, uio_in[7:4], {4{uio_in[3]}}, uio_in[3:0]};
                next_state   = S_IDLE;
            end

            S_FFT_READ: begin
                // This state runs for two cycles to read all 4 samples
                mem_en      = 1'b1;
                mem_read_en = 1'b1;
                if (mem_read_cycle == 0) begin // First cycle: read x0 and x1
                    mem_addr_a = 2'b00;
                    mem_addr_b = 2'b01;
                    next_state = S_FFT_READ;
                end else begin // Second cycle: read x2 and x3
                    mem_addr_a = 2'b10;
                    mem_addr_b = 2'b11;
                    // After this read, we are ready to start the FFT
                    next_state = S_FFT_START;
                end
            end
            
            S_FFT_START: begin
                // All samples are now latched in the fft_samples array. Pulse start.
                fft_start  = 1'b1;
                next_state = S_FFT_WAIT;
            end

            S_FFT_WAIT: begin
                if (fft_done) next_state = S_OUTPUT_WAIT;
                else next_state = S_FFT_WAIT;
            end

            S_OUTPUT_WAIT: if (output_pulse && output_counter < 4) next_state = S_OUTPUT_DRIVE;
                           else if (output_counter == 4) next_state = S_IDLE;

            S_OUTPUT_DRIVE: begin
                uio_oe       = 8'hFF;
                mem_en       = 1'b1;
                mem_read_en  = 1'b1;
                // Use Port A of the memory for single-value output reads
                mem_addr_a   = output_counter;
                next_state   = S_OUTPUT_WAIT;
            end
        endcase
    end
    
    // --- Display and Output Logic ---
    logic [3:0] display_code;
    always_comb begin
        case (state)
            S_IDLE, S_LOAD:
                display_code = load_counter + 1;
            S_FFT_READ, S_FFT_START, S_FFT_WAIT:
                display_code = 9; // Code for 'C'
            S_OUTPUT_WAIT, S_OUTPUT_DRIVE:
                display_code = output_counter + 5;
            default:
                display_code = 0;
        endcase
    end
    
    assign disp_ctrl.fsm_state_in = display_code;
    // Output directly from the FFT engine's registered output
    assign uio_out = {fft_freqs[output_counter][15:12], fft_freqs[output_counter][7:4]};

endmodule