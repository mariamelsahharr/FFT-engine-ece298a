import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import random


def signed(val, bits):
    if val >= (1 << (bits - 1)):
        return val - (1 << bits)
    return val

def wrap8(x):
    if x > 127:
        x -= 256
    elif x < -128:
        x += 256
    return x


def butterfly_ref_model(a_r, a_i, b_r, b_i, t_r, t_i, width=8):
    # Complex multiply: (t_r + jt_i) * (b_r + jb_i)
    prod_real = t_r * b_r - t_i * b_i
    prod_imag = t_i * b_r + t_r * b_i

    # Scale by shifting right
    def scale(val):
        scaled_val = val >> (width - 1)
        return wrap8(scaled_val)

    pr = scale(prod_real)
    pi = scale(prod_imag)

    # Calculate butterfly outputs with 8-bit wrapping
    pos_r = wrap8(a_r + pr)
    pos_i = wrap8(a_i + pi)
    neg_r = wrap8(a_r - pr)
    neg_i = wrap8(a_i - pi)

    return (pos_r, pos_i), (neg_r, neg_i)

def fft_engine_ref_model(in0, in1, in2, in3):
    in0_r, in0_i = in0
    in1_r, in1_i = in1
    in2_r, in2_i = in2
    in3_r, in3_i = in3

    # Twiddle factors used in the DUT (Q1.7 format: -128 represents -1.0)
    W0_r, W0_i = -128, 0  # Represents -1.0
    W1_r, W1_i = 0, -128   # Represents -j

    # --- Stage 1 ---
    # bfly_stage1_0: A=in0, B=in2, W=W0
    (s1_0_pos_r, s1_0_pos_i), (s1_0_neg_r, s1_0_neg_i) = butterfly_ref_model(
        in0_r, in0_i, in2_r, in2_i, W0_r, W0_i
    )
    # bfly_stage1_1: A=in1, B=in3, W=W0
    (s1_1_pos_r, s1_1_pos_i), (s1_1_neg_r, s1_1_neg_i) = butterfly_ref_model(
        in1_r, in1_i, in3_r, in3_i, W0_r, W0_i
    )

    # --- Stage 2 ---
    # This stage uses a butterfly with W=+1 (simple add/subtract) and another
    # with W=-j (W1).

    # First butterfly (W=+1) on s1 outputs
    # A = (s1_0_pos_r, s1_0_pos_i), B = (s1_1_pos_r, s1_1_pos_i)
    out0_r = wrap8(s1_0_pos_r + s1_1_pos_r)
    out0_i = wrap8(s1_0_pos_i + s1_1_pos_i)
    out2_r = wrap8(s1_0_pos_r - s1_1_pos_r)
    out2_i = wrap8(s1_0_pos_i - s1_1_pos_i)
    
    # Second butterfly (W=-j) on other s1 outputs
    # A = (s1_0_neg_r, s1_0_neg_i), B = (s1_1_neg_r, s1_1_neg_i)
    (out1_r, out1_i), (out3_r, out3_i) = butterfly_ref_model(
        s1_0_neg_r, s1_0_neg_i, s1_1_neg_r, s1_1_neg_i, W1_r, W1_i
    )

    return {
        'out0': (out0_r, out0_i),
        'out1': (out1_r, out1_i),
        'out2': (out2_r, out2_i),
        'out3': (out3_r, out3_i),
    }



async def run_test_case(dut, in0, in1, in2, in3):
    dut.in0_real.value, dut.in0_imag.value = in0
    dut.in1_real.value, dut.in1_imag.value = in1
    dut.in2_real.value, dut.in2_imag.value = in2
    dut.in3_real.value, dut.in3_imag.value = in3
    
    await RisingEdge(dut.clk)
    await Timer(1, 'ns')

    dut_out = {
        'out0': (signed(dut.out0_real.value.integer, 8), signed(dut.out0_imag.value.integer, 8)),
        'out1': (signed(dut.out1_real.value.integer, 8), signed(dut.out1_imag.value.integer, 8)),
        'out2': (signed(dut.out2_real.value.integer, 8), signed(dut.out2_imag.value.integer, 8)),
        'out3': (signed(dut.out3_real.value.integer, 8), signed(dut.out3_imag.value.integer, 8)),
    }

    expected_out = fft_engine_ref_model(in0, in1, in2, in3)

    dut._log.info(f"IN: in0={in0}, in1={in1}, in2={in2}, in3={in3}")
    dut._log.info(f"DUT OUT:    {dut_out}")
    dut._log.info(f"EXPECTED:   {expected_out}")
    
    for i in range(4):
        key = f'out{i}'
        assert dut_out[key] == expected_out[key], \
            f"Output mismatch for {key}: DUT={dut_out[key]}, Expected={expected_out[key]}"


@cocotb.test()
async def test_reset(dut):
    """Test the reset functionality of the FFT engine."""
    dut._log.info("Starting reset test")
    
    # Start the clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Apply reset
    dut.rst.value = 1
    dut.in0_real.value = 50
    dut.in0_imag.value = 50
    # Set other inputs to non-zero to ensure reset overrides them
    dut.in1_real.value = -20
    dut.in2_imag.value = 100
    
    await RisingEdge(dut.clk)
    
    # Check that all outputs are zero
    assert dut.out0_real.value == 0
    assert dut.out0_imag.value == 0
    assert dut.out1_real.value == 0
    assert dut.out1_imag.value == 0
    assert dut.out2_real.value == 0
    assert dut.out2_imag.value == 0
    assert dut.out3_real.value == 0
    assert dut.out3_imag.value == 0
    
    # Release reset
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    dut._log.info("Reset test passed")


@cocotb.test()
async def test_impulse_response(dut):
    """Test with an impulse input: [1, 0, 0, 0]."""
    dut._log.info("Starting impulse response test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst.value = 0
    
    await run_test_case(dut,
        in0=(1, 0),
        in1=(0, 0),
        in2=(0, 0),
        in3=(0, 0)
    )

@cocotb.test()
async def test_dc_input(dut):
    """Test with a DC input: [1, 1, 1, 1]."""
    dut._log.info("Starting DC input test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst.value = 0
    
    await run_test_case(dut,
        in0=(1, 0),
        in1=(1, 0),
        in2=(1, 0),
        in3=(1, 0)
    )

@cocotb.test()
async def test_complex_values(dut):
    """Test with a mix of positive, negative, and complex values."""
    dut._log.info("Starting complex values test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst.value = 0

    await run_test_case(dut,
        in0=(10, 20),
        in1=(-30, -40),
        in2=(50, -60),
        in3=(-70, 80)
    )

@cocotb.test()
async def test_randomized(dut):
    """Run multiple iterations with randomized inputs."""
    dut._log.info("Starting randomized test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst.value = 0
    
    num_tests = 20
    for i in range(num_tests):
        dut._log.info(f"--- Randomized Test Iteration {i+1}/{num_tests} ---")
        in0 = (random.randint(-128, 127), random.randint(-128, 127))
        in1 = (random.randint(-128, 127), random.randint(-128, 127))
        in2 = (random.randint(-128, 127), random.randint(-128, 127))
        in3 = (random.randint(-128, 127), random.randint(-128, 127))
        
        await run_test_case(dut, in0, in1, in2, in3)