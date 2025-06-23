/*
 * Copyright (c) 2025, Mariam & Hadi
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_FFT_engine (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output logic [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

    // --- Signal Declarations ---
    wire rst = ~rst_n;

    // I/O signals
    logic [3:0] display_code; // This will hold the value to be displayed (1-8, C, etc.)
    // Switch Interface signals
    wire load_pulse;
    wire output_pulse;

    // Memory Interface signals
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
    logic        fft_en;
    wire         fft_valid;
    logic [15:0] fft_in_x0, fft_in_x1, fft_in_x2, fft_in_x3;
    wire  [15:0] fft_out_X0, fft_out_X1, fft_out_X2, fft_out_X3;

    // --- System FSM States ---
    localparam [3:0]
        S_IDLE          = 4'd0,
        S_LOAD          = 4'd1,
        S_FFT_READ_MEM  = 4'd2,
        S_FFT_WAIT      = 4'd3,
        S_FFT_WRITE_MEM = 4'd4,
        S_OUTPUT_WAIT   = 4'd5,
        S_OUTPUT_DRIVE  = 4'd6;
    
    logic [3:0] state, next_state;
    
    // --- Counters ---
    logic [1:0] load_counter;
    logic [1:0] output_counter;
    logic [1:0] mem_op_counter; // A generic counter for read/write sequences

    // --- Module Instantiations ---

    // Instantiate two switch interfaces, one for each switch
    switch_interface sw_if_load (
        .clk(clk), .rst(rst), .sw_in(ui_in[0]), .pulse_out(load_pulse)
    );
    switch_interface sw_if_output (
        .clk(clk), .rst(rst), .sw_in(ui_in[1]), .pulse_out(output_pulse)
    );

    // Instantiate the dual-port memory
    fft_memory memory (
        .clk(clk), .rst(rst), .en(mem_en),
        .read_en(mem_read_en), .write_en(mem_write_en),
        .addr_w(mem_addr_w), .data_in(mem_data_in),
        .addr_a(mem_addr_a), .data_out_a(mem_data_out_a),
        .addr_b(mem_addr_b), .data_out_b(mem_data_out_b),
        .read_valid(mem_read_valid)
    );

    // Instantiate the FFT engine
    fft_engine #(.WIDTH(16)) fft_core (
        .clk(clk), .rst(rst), .en(fft_en), .valid(fft_valid),
        .x0_in(fft_in_x0), .x1_in(fft_in_x1), .x2_in(fft_in_x2), .x3_in(fft_in_x3),
        .X0_out(fft_out_X0), .X1_out(fft_out_X1), .X2_out(fft_out_X2), .X3_out(fft_out_X3)
    );

    // Instantiate the display controller
    display_controller disp_ctrl ( .fsm_state_in(display_code), .seg_out(uo_out) );

    // --- FSM Sequential Logic ---
    always_ff @(posedge clk) begin
        if (rst) begin
            state <= S_IDLE;
            load_counter <= 0;
            output_counter <= 0;
            mem_op_counter <= 0;
        end else if (ena) begin
            state <= next_state;

            if (next_state != state) begin
                mem_op_counter <= 0; // Reset generic counter on state change
            end else begin
                // Increment counters based on state
                if (state == S_LOAD)          load_counter <= load_counter + 1;
                if (state == S_FFT_READ_MEM)  mem_op_counter <= mem_op_counter + 1;
                if (state == S_FFT_WRITE_MEM) mem_op_counter <= mem_op_counter + 1;
                if (state == S_OUTPUT_DRIVE)  output_counter <= output_counter + 1;
            end
            
            // Special case for full loop reset
            if (next_state == S_IDLE && state == S_OUTPUT_WAIT) begin
                load_counter <= 0;
                output_counter <= 0;
            end
        end
    end

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

    // --- FSM Combinational Logic ---
    always_comb begin
        // Default assignments
        next_state   = state;
        uio_oe       = 8'h00;
        mem_en       = 1'b0;
        mem_read_en  = 1'b0;
        mem_write_en = 1'b0;
        mem_addr_w   = '0;
        mem_data_in  = '0;
        mem_addr_a   = '0;
        mem_addr_b   = '0;
        fft_en       = 1'b0;
        
        // Latch memory outputs into FFT core inputs
        fft_in_x0 = mem_data_out_a;
        fft_in_x1 = mem_data_out_b;
        fft_in_x2 = mem_data_out_a;
        fft_in_x3 = mem_data_out_b;

        case (state)
            S_IDLE: if (load_pulse && load_counter < 4) next_state = S_LOAD;
                    else if (load_counter == 4) next_state = S_FFT_READ_MEM;

            S_LOAD: begin
                mem_en = 1'b1;
                mem_write_en = 1'b1;
                mem_addr_w = load_counter;
                mem_data_in = {{4{uio_in[7]}}, uio_in[7:4], {4{uio_in[3]}}, uio_in[3:0]};
                next_state = S_IDLE;
            end

            S_FFT_READ_MEM: begin
                mem_en = 1'b1;
                mem_read_en = 1'b1;
                if (mem_op_counter == 0) begin // Cycle 1: Read x0 and x1
                    mem_addr_a = 2'b00;
                    mem_addr_b = 2'b01;
                    next_state = S_FFT_READ_MEM;
                end else if (mem_op_counter == 1) begin // Cycle 2: Read x2 and x3
                    mem_addr_a = 2'b10;
                    mem_addr_b = 2'b11;
                    next_state = S_FFT_WAIT;
                    fft_en = 1'b1; // Start the engine now that all inputs are ready
                end
            end

            S_FFT_WAIT: begin
                fft_en = 1'b1; // Keep engine enabled while it computes
                if (fft_valid) begin
                    fft_en = 1'b0; // Computation is done
                    next_state = S_FFT_WRITE_MEM;
                end else begin
                    next_state = S_FFT_WAIT;
                end
            end

            S_FFT_WRITE_MEM: begin
                mem_en = 1'b1;
                mem_write_en = 1'b1;
                mem_addr_w = mem_op_counter;
                case(mem_op_counter)
                    2'b00: mem_data_in = fft_out_X0;
                    2'b01: mem_data_in = fft_out_X1;
                    2'b10: mem_data_in = fft_out_X2;
                    2'b11: mem_data_in = fft_out_X3;
                endcase
                if (mem_op_counter == 3) next_state = S_OUTPUT_WAIT;
                else next_state = S_FFT_WRITE_MEM;
            end
            
            S_OUTPUT_WAIT: if (output_pulse && output_counter < 4) next_state = S_OUTPUT_DRIVE;
                           else if (output_counter == 4) next_state = S_IDLE;

            S_OUTPUT_DRIVE: begin
                uio_oe = 8'hFF;
                mem_en = 1'b1;
                mem_read_en = 1'b1;
                mem_addr_a = output_counter; // Use Port A for output reads
                next_state = S_OUTPUT_WAIT;
            end
        endcase
    end
    
    // Connect memory output Port A to the bidirectional pins for output
    assign uio_out = {mem_data_out_a[15:12], mem_data_out_a[7:4]};

endmodule