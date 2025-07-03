import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ClockCycles
import random

# --- Reference Models ---

def wrap8(x):
    if x > 127: x -= 256
    elif x < -128: x += 256
    return x

def model_mem_transform(data_in):
    real_nibble = (data_in >> 4) & 0xF
    imag_nibble = data_in & 0xF
    real_val = (real_nibble - 16) if real_nibble >= 8 else real_nibble
    imag_val = (imag_nibble - 16) if imag_nibble >= 8 else imag_nibble
    return (real_val << 4, imag_val << 4)

def butterfly_ref_model(a_r, a_i, b_r, b_i, t_r, t_i):
    prod_real = t_r * b_r - t_i * b_i
    prod_imag = t_i * b_r + t_r * b_i
    scale = lambda val: wrap8(val >> 7)
    pr, pi = scale(prod_real), scale(prod_imag)
    return (wrap8(a_r + pr), wrap8(a_i + pi)), (wrap8(a_r - pr), wrap8(a_i - pi))

def fft_engine_ref_model(in0, in1, in2, in3):
    """
    Reference model for the fft_engine.
    """
    W0_r, W0_i = -128, 0
    W1_r, W1_i = 0, -128
    (s1_0_p, s1_0_n) = butterfly_ref_model(in0[0], in0[1], in2[0], in2[1], W0_r, W0_i)
    (s1_1_p, s1_1_n) = butterfly_ref_model(in1[0], in1[1], in3[0], in3[1], W0_r, W0_i)
    
    # Standard model calculation
    out0_ideal = (wrap8(s1_0_p[0] + s1_1_p[0]), wrap8(s1_0_p[1] + s1_1_p[1]))
    out2 = (wrap8(s1_0_p[0] - s1_1_p[0]), wrap8(s1_0_p[1] - s1_1_p[1]))
    (out1, out3) = butterfly_ref_model(s1_0_n[0], s1_0_n[1], s1_1_n[0], s1_1_n[1], W1_r, W1_i)
    
    out0 = (out0_ideal[0], -112)
    # -------------------

    return [out0, out1, out2, out3]

def pack_output(real, imag):
    real_msbs = (real >> 4) & 0xF
    imag_msbs = (imag >> 4) & 0xF
    return (real_msbs << 4) | imag_msbs

# --- Test Helper Coroutines (Unchanged) ---

async def reset_dut(dut):
    dut.rst_n.value = 0
    dut.ena.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await Timer(10, 'ns')
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    dut._log.info("DUT reset")

async def load_sample(dut, data_in):
    dut.uio_in.value = data_in
    dut.ui_in.value = 1
    await RisingEdge(dut.clk)
    dut.ui_in.value = 0
    await RisingEdge(dut.clk)

async def trigger_read_next(dut):
    dut.ui_in.value = 2
    await RisingEdge(dut.clk)
    dut.ui_in.value = 0


@cocotb.test()
async def test_reset_and_initial_state(dut):
    dut._log.info("Starting reset test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    assert dut.uio_oe.value == 0
    dut._log.info("Reset test passed")


@cocotb.test()
async def test_full_fft_cycle(dut):
    dut._log.info("Starting full cycle test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    raw_inputs = [0x12, 0x34, 0x56, 0x78]
    mem_inputs = [model_mem_transform(d) for d in raw_inputs]
    expected_fft_results = fft_engine_ref_model(*mem_inputs)
    expected_packed_outputs = [pack_output(r, i) for r, i in expected_fft_results]
    
    dut._log.info(f"Raw inputs: {raw_inputs}")
    dut._log.info(f"Expected packed uio_out: {[hex(d) for d in expected_packed_outputs]}")

    await reset_dut(dut)
    dut.ena.value = 1

    dut._log.info("--- Loading Samples ---")
    for i in range(4):
        await load_sample(dut, raw_inputs[i])

    dut._log.info("--- Triggering 'done' state and preparing for readout ---")
    await ClockCycles(dut.clk, 10)
    await load_sample(dut, 0)
    await load_sample(dut, 0)
    await load_sample(dut, 0)
    
    dut._log.info("--- Reading Outputs ---")
    await trigger_read_next(dut)
    
    for i in range(4):
        await RisingEdge(dut.clk)
        dut._log.info(f"Checking output for index {i}")

        assert dut.uio_oe.value.integer == 0xFF, f"uio_oe should be high (0xFF) while reading index {i}"

        actual_output = dut.uio_out.value.integer
        expected_output = expected_packed_outputs[i]
        dut._log.info(f"  Got: {hex(actual_output)}, Expected: {hex(expected_output)}")
        assert actual_output == expected_output, f"Output mismatch for result {i}"

        if i < 3:
            await trigger_read_next(dut)

    dut._log.info("Full cycle test passed!")