import cocotb
from cocotb.triggers import Timer

def signed(val, bits):
    """Convert unsigned to signed."""
    if val >= (1 << (bits - 1)):
        return val - (1 << bits)
    return val

def wrap8(x):
    """Wrap to signed 8-bit range (-128 to 127) as 2's complement."""
    if x > 127:
        x -= 256
    elif x < -128:
        x += 256
    return x

def pack_complex(r, i):
    """Pack signed 8-bit real and imag into 16-bit int."""
    return ((r & 0xFF) << 8) | (i & 0xFF)

def unpack_complex(val):
    """Unpack signed 8-bit real and imag from 16-bit int."""
    r = (val >> 8) & 0xFF
    i = val & 0xFF
    if r & 0x80:
        r -= 0x100
    if i & 0x80:
        i -= 0x100
    return r, i

def butterfly_reference(a_r, a_i, b_r, b_i, t_r, t_i):
    """Reference butterfly logic matching Verilog behavior (signed 8-bit, WIDTH=8)."""
    # Complex multiply: (t_r + jt_i) * (b_r + jb_i)
    prod_real = t_r * b_r - t_i * b_i
    prod_imag = t_i * b_r + t_r * b_i

    # Arithmetic shift right with rounding: >>> (WIDTH - 1) = >>> 7
    def trunc(val):
        return wrap8(val >> 7)  # no rounding


    pr = trunc(prod_real)
    pi = trunc(prod_imag)

    pos_r = wrap8(a_r + pr)
    pos_i = wrap8(a_i + pi)
    neg_r = wrap8(a_r - pr)
    neg_i = wrap8(a_i - pi)

    return (pos_r, pos_i), (neg_r, neg_i)

async def run_test(dut, A, B, T):
    a_r, a_i = unpack_complex(A)
    b_r, b_i = unpack_complex(B)
    t_r, t_i = unpack_complex(T)

    dut.A_real.value = a_r
    dut.A_imag.value = a_i
    dut.B_real.value = b_r
    dut.B_imag.value = b_i
    dut.W_real.value = t_r
    dut.W_imag.value = t_i

    await Timer(1, units='ns')

    pos_r = signed(int(dut.Pos_real.value), 8)
    pos_i = signed(int(dut.Pos_imag.value), 8)
    neg_r = signed(int(dut.Neg_real.value), 8)
    neg_i = signed(int(dut.Neg_imag.value), 8)

    expected_pos, expected_neg = butterfly_reference(a_r, a_i, b_r, b_i, t_r, t_i)

    print(f"A={a_r}+j{a_i}, B={b_r}+j{b_i}, T={t_r}+j{t_i}")
    print(f"  DUT Pos=({pos_r}, {pos_i}), Neg=({neg_r}, {neg_i})")
    print(f"  EXPECTED Pos={expected_pos}, Neg={expected_neg}")

    assert (pos_r, pos_i) == expected_pos, f"Pos mismatch: got ({pos_r}, {pos_i}), expected {expected_pos}"
    assert (neg_r, neg_i) == expected_neg, f"Neg mismatch: got ({neg_r}, {neg_i}), expected {expected_neg}"

@cocotb.test()
async def test_neg1_twiddle(dut):
    """Test with T = 0xFF00 (-1 + 0j)"""
    await run_test(dut,
        A=pack_complex(10, 20),
        B=pack_complex(5, 15),
        T=0xFF00
    )

@cocotb.test()
async def test_negj_twiddle(dut):
    """Test with T = 0x00FF (0 - 1j)"""
    await run_test(dut,
        A=pack_complex(10, 20),
        B=pack_complex(5, 15),
        T=0x00FF
    )

@cocotb.test()
async def test_basic_butterfly(dut):
    """Basic test with A=(1,1), B=(2,2), T=-1"""
    await run_test(dut,
        A=pack_complex(1, 1),
        B=pack_complex(2, 2),
        T=0xFF00
    )

@cocotb.test()
async def test_simple_multiply(dut):
    """Simple test with A=(0,0), B=(2,0), T=-j"""
    await run_test(dut,
        A=pack_complex(0, 0),
        B=pack_complex(2, 0),
        T=0x00FF
    )

@cocotb.test()
async def test_random_supported_twiddles(dut):
    """Randomized test with supported fixed twiddles"""
    test_vectors = [
        (pack_complex(29, 70), pack_complex(50, -125), 0xFF00),
        (pack_complex(93, 44), pack_complex(-52, -100), 0x00FF),
        (pack_complex(-64, 127), pack_complex(-64, -64), 0xFF00),
        (pack_complex(100, -100), pack_complex(10, 10), 0x00FF),
    ]
    for i, (A, B, T) in enumerate(test_vectors):
        print(f"\n--- Running random test {i+1} ---")
        await run_test(dut, A, B, T)
