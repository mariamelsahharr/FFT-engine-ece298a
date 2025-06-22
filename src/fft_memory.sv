module fft_memory (
    input  logic        clk,
    input  logic        rst,            // synch reset (see if we want to change this to async)
    input  logic        en,             // read enable (1 = read/write, 0 = hold previous outputs)
    input  logic        write_en,       // write enable (only used when en = 1)
    input  logic  [1:0] addr_w,         // write address
    input  logic [15:0] data_in,        // data to write

    input  logic  [1:0] addr_a,         // read port A address
    output logic [15:0] data_out_a,     // read port A output

    input  logic  [1:0] addr_b,         // read port B address
    output logic [15:0] data_out_b,     // read port B output

    output logic        read_valid           // output is valid when high (1 cycle after en=1)
);

    // 4-word x 16-bit memory
    logic [15:0] mem [0:3];

    // internal data registers for read outputs
    logic [15:0] reg_a, reg_b;
    logic        valid;

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            mem[0] <= 16'd0;
            mem[1] <= 16'd0;
            mem[2] <= 16'd0;
            mem[3] <= 16'd0;
            reg_a  <= 16'd0;
            reg_b  <= 16'd0;
            valid  <= 1'b0;
        end else if (en) begin

            if (write_en) begin
                mem[addr_w] <= data_in;
            end

            reg_a <= mem[addr_a];
            reg_b <= mem[addr_b];
            valid <= 1'b1;

        end else begin
            valid <= 1'b0;
        end
    end

    //dual port read outputs
    assign data_out_a = reg_a;
    assign data_out_b = reg_b;
    assign read_valid = valid;


endmodule
