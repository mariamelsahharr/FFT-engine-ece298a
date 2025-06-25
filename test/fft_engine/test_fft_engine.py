import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

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

def fft_reference(inputs):
    """Reference 4-point FFT implementation matching hardware"""
    # Stage 1 butterflies (W = 1)
    s1 = []
    for i in range(2):
        a_r, a_i = inputs[i*2]
        b_r, b_i = inputs[i*2+1]
        s1.append((a_r + b_r, a_i + b_i))  # pos
        s1.append((a_r - b_r, a_i - b_i))  # neg
    
    # Stage 2 butterflies
    # First pair (W = 1)
    out0_r, out0_i = s1[0][0] + s1[2][0], s1[0][1] + s1[2][1]
    out2_r, out2_i = s1[0][0] - s1[2][0], s1[0][1] - s1[2][1]
    
    # Second pair (W = -j)
    (out1_r, out1_i), (out3_r, out3_i) = butterfly_reference(
        s1[1][0], s1[1][1],  # A
        s1[3][0], s1[3][1],  # B
        0x00, 0x80           # W = -j (0 - 1j)
    )
    
    return [
        (out0_r, out0_i),
        (out1_r, out1_i),
        (out2_r, out2_i),
        (out3_r, out3_i)
    ]

async def reset(dut):
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

async def run_test(dut, inputs):
    # Apply inputs
    for i in range(4):
        setattr(dut, f"in{i}_real", inputs[i][0])
        setattr(dut, f"in{i}_imag", inputs[i][1])
    
    # Wait for computation (2 clock cycles for pipeline)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # Extra cycle for safety
    
    # Get outputs
    outputs = []
    for i in range(4):
        r = signed(int(dut._id(f"out{i}_real", extended=False).value),8)
        i_val = signed(int(dut._id(f"out{i}_imag", extended=False).value),8)
        outputs.append((r, i_val))
    
    # Check against reference
    expected = fft_reference(inputs)
    for i, (out, exp) in enumerate(zip(outputs, expected)):
        assert out == exp, f"Output {i} mismatch: got {out}, expected {exp}"

@cocotb.test()
async def test_basic_fft(dut):
    """Test with simple inputs"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    await reset(dut)
    
    inputs = [
        (64, 0),   # DC
        (0, 0),
        (0, 0),
        (0, 0)
    ]
    await run_test(dut, inputs)

@cocotb.test()
async def test_complex_inputs(dut):
    """Test with complex inputs"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    await reset(dut)
    
    inputs = [
        (10, 20),
        (30, 40),
        (50, 60),
        (70, 80)
    ]
    await run_test(dut, inputs)

@cocotb.test()
async def test_random_inputs(dut):
    """Test with random inputs"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    await reset(dut)
    
    import random
    inputs = [(random.randint(-32, 31), random.randint(-32, 31)) for _ in range(4)]
    await run_test(dut, inputs)