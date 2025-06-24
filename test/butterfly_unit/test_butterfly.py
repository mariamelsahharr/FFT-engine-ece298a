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
    """Butterfly with only T = -1 or T = -j."""
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

    if T == 0x8000:  # -1 + 0j
        wb_r = -b_r
        wb_i = -b_i
    elif T == 0x0080:  # 0 - j
        wb_r = b_i
        wb_i = -b_r
    else:
        raise ValueError("Unsupported T value: only -1 or -j allowed")

    plus = pack(a_r + wb_r, a_i + wb_i)
    minus = pack(a_r - wb_r, a_i - wb_i)

    return plus, minus

@cocotb.test()
async def test_neg1_twiddle(dut):
    """Test with T = 0x8000 (-1)"""
    dut.A.value = pack_complex(10, 20)
    dut.B.value = pack_complex(5, 15)
    dut.T.value = 0x8000
    await Timer(1, units='ns')
    pos_val = int(dut.Pos.value)
    neg_val = int(dut.Neg.value)
    expected_pos, expected_neg = butterfly(int(dut.A.value), int(dut.B.value), 0x8000)
    print(f"T=0x8000: A=(10,20), B=(5,15)")
    print(f"  DUT Pos={hex(pos_val)} {unpack_complex(pos_val)}, Neg={hex(neg_val)} {unpack_complex(neg_val)}")
    print(f"  REF Pos={hex(expected_pos)} {unpack_complex(expected_pos)}, Neg={hex(expected_neg)} {unpack_complex(expected_neg)}")
    assert pos_val == expected_neg, f"T=0x8000 Pos mismatch: got {hex(pos_val)}, expected {hex(expected_neg)}"
    assert neg_val == expected_pos, f"T=0x8000 Neg mismatch: got {hex(neg_val)}, expected {hex(expected_pos)}"

@cocotb.test()
async def test_negj_twiddle(dut):
    """Test with T = 0x0080 (-j)"""
    dut.A.value = pack_complex(10, 20)
    dut.B.value = pack_complex(5, 15)
    dut.T.value = 0x0080
    await Timer(1, units='ns')
    pos_val = int(dut.Pos.value)
    neg_val = int(dut.Neg.value)
    expected_pos, expected_neg = butterfly(int(dut.A.value), int(dut.B.value), 0x0080)
    print(f"T=0x0080: A=(10,20), B=(5,15)")
    print(f"  DUT Pos={hex(pos_val)} {unpack_complex(pos_val)}, Neg={hex(neg_val)} {unpack_complex(neg_val)}")
    print(f"  REF Pos={hex(expected_pos)} {unpack_complex(expected_pos)}, Neg={hex(expected_neg)} {unpack_complex(expected_neg)}")
    assert pos_val == expected_neg, f"T=0x0080 Pos mismatch: got {hex(pos_val)}, expected {hex(expected_neg)}"
    assert neg_val == expected_pos, f"T=0x0080 Neg mismatch: got {hex(neg_val)}, expected {hex(expected_pos)}"

@cocotb.test()
async def test_random_supported_twiddles(dut):
    """Randomized test with only supported twiddle factors (-1, -j)"""
    twiddle_factors = [0x8000, 0x0080]
    for i in range(5):
        a_real = random.randint(-128, 127)
        a_imag = random.randint(-128, 127)
        b_real = random.randint(-128, 127)
        b_imag = random.randint(-128, 127)
        T = random.choice(twiddle_factors)
        A = pack_complex(a_real, a_imag)
        B = pack_complex(b_real, b_imag)
        dut.A.value = A
        dut.B.value = B
        dut.T.value = T
        await Timer(1, units='ns')
        pos_val = int(dut.Pos.value)
        neg_val = int(dut.Neg.value)
        expected_pos, expected_neg = butterfly(A, B, T)
        print(f"[{i+1}] A=({a_real},{a_imag}), B=({b_real},{b_imag}), T={hex(T)}")
        print(f"     DUT Pos={hex(pos_val)} {unpack_complex(pos_val)}, Neg={hex(neg_val)} {unpack_complex(neg_val)}")
        print(f"     REF Pos={hex(expected_pos)} {unpack_complex(expected_pos)}, Neg={hex(expected_neg)} {unpack_complex(expected_neg)}")
        assert pos_val == expected_neg, f"[{i+1}] Pos mismatch: got {hex(pos_val)}, expected {hex(expected_neg)}"
        assert neg_val == expected_pos, f"[{i+1}] Neg mismatch: got {hex(neg_val)}, expected {hex(expected_pos)}"

@cocotb.test()
async def test_basic_butterfly(dut):
    """Basic butterfly test with T = 0x8000 (-1) -> Plus=A-B, Minus=A+B"""
    dut.A.value = pack_complex(1, 1)
    dut.B.value = pack_complex(2, 2)
    dut.T.value = 0x8000  # -1
    await Timer(1, units='ns')
    pos_val = int(dut.Pos.value)
    neg_val = int(dut.Neg.value)
    expected_pos, expected_neg = butterfly(int(dut.A.value), int(dut.B.value), 0x8000)
    print(f"Basic: A=(1,1), B=(2,2), T=0x8000 (-1)")
    print(f"  DUT Pos={hex(pos_val)} {unpack_complex(pos_val)}, Neg={hex(neg_val)} {unpack_complex(neg_val)}")
    print(f"  REF Pos={hex(expected_pos)} {unpack_complex(expected_pos)}, Neg={hex(expected_neg)} {unpack_complex(expected_neg)}")
    assert pos_val == expected_neg, f"Basic Pos mismatch: got {hex(pos_val)}, expected {hex(expected_neg)}"
    assert neg_val == expected_pos, f"Basic Neg mismatch: got {hex(neg_val)}, expected {hex(expected_pos)}"

@cocotb.test()
async def test_simple_multiply(dut):
    """Simple multiply test with T = 0x0080 (-j) -> complex multiplication"""
    dut.A.value = pack_complex(0, 0)
    dut.B.value = pack_complex(2, 0)
    dut.T.value = 0x0080  # -j
    await Timer(1, units='ns')
    pos_val = int(dut.Pos.value)
    neg_val = int(dut.Neg.value)
    expected_pos, expected_neg = butterfly(int(dut.A.value), int(dut.B.value), 0x0080)
    print(f"Simple: A=(0,0), B=(2,0), T=0x0080 (-j)")
    print(f"  DUT Pos={hex(pos_val)} {unpack_complex(pos_val)}, Neg={hex(neg_val)} {unpack_complex(neg_val)}")
    print(f"  REF Pos={hex(expected_pos)} {unpack_complex(expected_pos)}, Neg={hex(expected_neg)} {unpack_complex(expected_neg)}")
    assert pos_val == expected_neg, f"Simple Pos mismatch: got {hex(pos_val)}, expected {hex(expected_neg)}"
    assert neg_val == expected_pos, f"Simple Neg mismatch: got {hex(neg_val)}, expected {hex(expected_pos)}"
