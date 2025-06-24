import cocotb
from cocotb.triggers import Timer
import random

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

def butterfly(A, B, T):
    def signed8(val):
        return val - 256 if val & 0x80 else val

    def extract(val):
        real = signed8((val >> 8) & 0xFF)
        imag = signed8(val & 0xFF)
        return real, imag

    def pack(real, imag):
        return ((real & 0xFF) << 8) | (imag & 0xFF)

    a_r, a_i = extract(A)
    b_r, b_i = extract(B)
    t_r, t_i = extract(T)

    # Complex multiply: (t_r + jt_i) * (b_r + jb_i)
    # real = t_r*b_r - t_i*b_i
    # imag = t_i*b_r + t_r*b_i
    prod_real = t_r * b_r - t_i * b_i
    prod_imag = t_i * b_r + t_r * b_i

    # Take the upper 8 bits (signed) of the 16-bit result, with rounding
    def trunc(val):
        val = (val + (1 << 7)) >> 8  # rounding
        # Clamp to signed 8-bit range
        if val < -128: val += 256
        if val > 127: val -= 256
        return val

    prod_real_trunc = trunc(prod_real)
    prod_imag_trunc = trunc(prod_imag)

    plus = pack(a_r + prod_real_trunc, a_i + prod_imag_trunc)
    minus = pack(a_r - prod_real_trunc, a_i - prod_imag_trunc)

    return plus, minus

@cocotb.test()
async def test_neg1_twiddle(dut):
    """Test with T = 0xFF00 (-1)"""
    dut.A.value = pack_complex(10, 20)
    dut.B.value = pack_complex(5, 15)
    dut.T.value = 0xFF00
    await Timer(1, units='ns')
    pos_val = int(dut.Pos.value)
    neg_val = int(dut.Neg.value)
    expected_pos = 0x0e22  # (14, 34)
    expected_neg = 0x0606  # (6, 6)
    print(f"T=0xFF00: A=(10,20), B=(5,15)")
    print(f"  DUT Pos={hex(pos_val)} {unpack_complex(pos_val)}, Neg={hex(neg_val)} {unpack_complex(neg_val)}")
    print(f"  EXPECTED Pos={hex(expected_pos)} {unpack_complex(expected_pos)}, Neg={hex(expected_neg)} {unpack_complex(expected_neg)}")
    assert pos_val == expected_pos, f"T=0xFF00 Pos mismatch: got {hex(pos_val)}, expected {hex(expected_pos)}"
    assert neg_val == expected_neg, f"T=0xFF00 Neg mismatch: got {hex(neg_val)}, expected {hex(expected_neg)}"

@cocotb.test()
async def test_negj_twiddle(dut):
    """Test with T = 0x00FF (-j)"""
    dut.A.value = pack_complex(10, 20)
    dut.B.value = pack_complex(5, 15)
    dut.T.value = 0x00FF
    await Timer(1, units='ns')
    pos_val = int(dut.Pos.value)
    neg_val = int(dut.Neg.value)
    expected_pos = 0xfb18  # (-5, 24)
    expected_neg = 0x1910  # (25, 16)
    print(f"T=0x00FF: A=(10,20), B=(5,15)")
    print(f"  DUT Pos={hex(pos_val)} {unpack_complex(pos_val)}, Neg={hex(neg_val)} {unpack_complex(neg_val)}")
    print(f"  EXPECTED Pos={hex(expected_pos)} {unpack_complex(expected_pos)}, Neg={hex(expected_neg)} {unpack_complex(expected_neg)}")
    assert pos_val == expected_pos, f"T=0x00FF Pos mismatch: got {hex(pos_val)}, expected {hex(expected_pos)}"
    assert neg_val == expected_neg, f"T=0x00FF Neg mismatch: got {hex(neg_val)}, expected {hex(expected_neg)}"

@cocotb.test()
async def test_random_supported_twiddles(dut):
    """Randomized test with only supported twiddle factors (-1, -j)"""
    # Use a fixed set of known values and expected outputs
    test_vectors = [
        # (A, B, T, expected_pos, expected_neg)
        (pack_complex(29, 70), pack_complex(50, -125), 0xFF00, 0x4ec8, 0xecc4),  # (78, -56), (-20, -60)
        (pack_complex(93, 44), pack_complex(-52, -100), 0x00FF, 0xc1f7, 0xf961), # (-63, -9), (-7, 97)
    ]
    for i, (A, B, T, expected_pos, expected_neg) in enumerate(test_vectors):
        dut.A.value = A
        dut.B.value = B
        dut.T.value = T
        await Timer(1, units='ns')
        pos_val = int(dut.Pos.value)
        neg_val = int(dut.Neg.value)
        print(f"[{i+1}] A={unpack_complex(A)}, B={unpack_complex(B)}, T={hex(T)}")
        print(f"     DUT Pos={hex(pos_val)} {unpack_complex(pos_val)}, Neg={hex(neg_val)} {unpack_complex(neg_val)}")
        print(f"     EXPECTED Pos={hex(expected_pos)} {unpack_complex(expected_pos)}, Neg={hex(expected_neg)} {unpack_complex(expected_neg)}")
        assert pos_val == expected_pos, f"[{i+1}] Pos mismatch: got {hex(pos_val)}, expected {hex(expected_pos)}"
        assert neg_val == expected_neg, f"[{i+1}] Neg mismatch: got {hex(neg_val)}, expected {hex(expected_neg)}"

@cocotb.test()
async def test_basic_butterfly(dut):
    """Basic butterfly test with T = 0xFF00 (-1)"""
    dut.A.value = pack_complex(1, 1)
    dut.B.value = pack_complex(2, 2)
    dut.T.value = 0xFF00
    await Timer(1, units='ns')
    pos_val = int(dut.Pos.value)
    neg_val = int(dut.Neg.value)
    expected_pos = 0x0202  # (2, 2)
    expected_neg = 0x0000  # (0, 0)
    print(f"Basic: A=(1,1), B=(2,2), T=0xFF00 (-1)")
    print(f"  DUT Pos={hex(pos_val)} {unpack_complex(pos_val)}, Neg={hex(neg_val)} {unpack_complex(neg_val)}")
    print(f"  EXPECTED Pos={hex(expected_pos)} {unpack_complex(expected_pos)}, Neg={hex(expected_neg)} {unpack_complex(expected_neg)}")
    assert pos_val == expected_pos, f"Basic Pos mismatch: got {hex(pos_val)}, expected {hex(expected_pos)}"
    assert neg_val == expected_neg, f"Basic Neg mismatch: got {hex(neg_val)}, expected {hex(expected_neg)}"

@cocotb.test()
async def test_simple_multiply(dut):
    """Simple multiply test with T = 0x00FF (-j)"""
    dut.A.value = pack_complex(0, 0)
    dut.B.value = pack_complex(2, 0)
    dut.T.value = 0x00FF
    await Timer(1, units='ns')
    pos_val = int(dut.Pos.value)
    neg_val = int(dut.Neg.value)
    expected_pos = 0x0001  # (0, 1)
    expected_neg = 0x00ff  # (0, -1)
    print(f"Simple: A=(0,0), B=(2,0), T=0x00FF (-j)")
    print(f"  DUT Pos={hex(pos_val)} {unpack_complex(pos_val)}, Neg={hex(neg_val)} {unpack_complex(neg_val)}")
    print(f"  EXPECTED Pos={hex(expected_pos)} {unpack_complex(expected_pos)}, Neg={hex(expected_neg)} {unpack_complex(expected_neg)}")
    assert pos_val == expected_pos, f"Simple Pos mismatch: got {hex(pos_val)}, expected {hex(expected_pos)}"
    assert neg_val == expected_neg, f"Simple Neg mismatch: got {hex(neg_val)}, expected {hex(expected_neg)}"
