module butterfly #( WIDTH = 16 ) (
    input signed  [ WIDTH - 1 : 0 ] A,
    input signed  [ WIDTH - 1 : 0 ] B,
    input signed  [ WIDTH - 1 : 0 ] T,
    output signed [ WIDTH - 1 : 0 ] Pos, // A + T*B
    output signed [ WIDTH - 1 : 0 ] Neg // A - T*B
);

    wire [ WIDTH/2 - 1 : 0 ] w_real;
    wire [ WIDTH/2 - 1 : 0 ] w_imag;
    wire [ WIDTH/2 - 1 : 0 ] b_real;
    wire [ WIDTH/2 - 1 : 0 ] b_imag;
    
    assign w_real = T[ WIDTH - 1   : WIDTH/2 ] ;
    assign w_imag = T[ WIDTH/2 - 1 : 0 ];
    assign b_real = B[ WIDTH - 1   : WIDTH/2 ];
    assign b_imag = B[ WIDTH/2 - 1 : 0 ];
    
    wire [ WIDTH - 1 : 0 ] product;

    wire [ WIDTH - 1 : 0 ] product_real;
    wire [ WIDTH - 1 : 0 ] product_imag;
    
    wire [ WIDTH/2 - 1 : 0] product_real_trunc;
    wire [ WIDTH/2 - 1 : 0] product_imag_trunc;

    assign product_real = (w_real * b_real) - (w_imag * b_imag);
    assign product_imag = (w_imag * b_real) + (w_real * b_imag);

    assign product_real_trunc = product_real[ WIDTH - 1 : WIDTH/2 ];
    assign product_imag_trunc = product_imag[ WIDTH - 1 : WIDTH/2 ];

    assign Pos  = {
        A[ WIDTH - 1 : WIDTH/2 ] + product_real_trunc,
        A[ WIDTH/2 - 1 : 0] + product_imag_trunc
    };
    assign Neg = {
        A[ WIDTH - 1 : WIDTH/2 ] - product_real_trunc,
        A[ WIDTH/2 - 1 : 0] - product_imag_trunc
    };
endmodule