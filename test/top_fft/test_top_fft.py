import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ClockCycles
import random

# --- Helper Functions (Unchanged) ---
def wrap8(x):
    if x > 127: x -= 256
    elif x < -128: x += 256
    return x

def pack_input(real, imag):
    real_nibble_signed = real >> 4
    imag_nibble_signed = imag >> 4
    real_nibble_unsigned = real_nibble_signed & 0xF
    imag_nibble_unsigned = imag_nibble_signed & 0xF
    return (real_nibble_unsigned << 4) | imag_nibble_unsigned

def pack_output(real, imag):
    real_msbs = (real >> 4) & 0xF
    imag_msbs = (imag >> 4) & 0xF
    return (real_msbs << 4) | imag_msbs

# --- Reference Models (Unchanged) ---
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
    W0_r, W0_i = -128, 0
    W1_r, W1_i = 0, -128
    (s1_0_pos, s1_0_neg) = butterfly_ref_model(in0[0], in0[1], in2[0], in2[1], W0_r, W0_i)
    (s1_1_pos, s1_1_neg) = butterfly_ref_model(in1[0], in1[1], in3[0], in3[1], W0_r, W0_i)
    out0 = (wrap8(s1_0_pos[0] + s1_1_pos[0]), wrap8(s1_0_pos[1] + s1_1_pos[1]))
    out2 = (wrap8(s1_0_pos[0] - s1_1_pos[0]), wrap8(s1_0_pos[1] - s1_1_pos[1]))
    (out1, out3) = butterfly_ref_model(s1_0_neg[0], s1_0_neg[1], s1_1_neg[0], s1_1_neg[1], W1_r, W1_i)
    return [out0, out1, out2, out3]

def top_fft_ref_model(raw_inputs):
    transformed_inputs = [model_mem_transform(pack_input(r, i)) for r, i in raw_inputs]
    fft_results = fft_engine_ref_model(
        transformed_inputs[0], transformed_inputs[1], transformed_inputs[2], transformed_inputs[3]
    )
    packed_outputs = [pack_output(r, i) for r, i in fft_results]
    return packed_outputs

# --- Test Helper Coroutines ---

async def reset_dut(dut):
    dut.rst_n.value = 0
    dut.ena.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    dut._log.info("DUT reset")

async def load_sample(dut, data_in):
    dut.uio_in.value = data_in
    dut.ui_in.value = 1
    await RisingEdge(dut.clk)
    dut.ui_in.value = 0
    await RisingEdge(dut.clk)

async def run_full_fft_test(dut, inputs):
    """A complete test sequence: load 4 samples, wait, read 4 samples, and verify."""
    expected_outputs = top_fft_ref_model(inputs)
    dut._log.info(f"Inputs: {inputs}")
    dut._log.info(f"Expected packed outputs: {[hex(x) for x in expected_outputs]}")

    # --- Load Phase ---
    dut.ena.value = 1
    for i in range(4):
        packed_val = pack_input(inputs[i][0], inputs[i][1])
        await load_sample(dut, packed_val)
    
    # --- Wait for processing to finish ---
    dut._log.info("Waiting for DUT to signal completion...")
    IDLE_STATUS = 0x0C
    timeout_cycles = 15
    for i in range(timeout_cycles):
        # The 'done' state is indicated by the display showing the first output address '4'
        if dut.uo_out.value == 0x24: 
            dut._log.info(f"DUT indicates 'done' after {i+1} cycles.")
            break
        await RisingEdge(dut.clk)
    else: 
        assert False, f"Timeout: DUT did not signal completion after {timeout_cycles} cycles."


    # --- Read and Verify Phase (CORRECTED LOGIC) ---
    actual_outputs = []
    for i in range(4):
        # 1. Assert the read trigger
        dut.ui_in.value = 2
        await RisingEdge(dut.clk)
        
        # 2. Check the output enable *before* de-asserting the trigger.
        assert dut.uio_oe.value == 0xFF, f"uio_oe was not asserted for output {i}."
        
        # 3. Sample the output data and check it
        dut_out = dut.uio_out.value.integer
        actual_outputs.append(dut_out)
        
        assert dut_out == expected_outputs[i], \
            f"Output {i} mismatch: DUT={hex(dut_out)}, Expected={hex(expected_outputs[i])}"

        # 4. Now, de-assert the read trigger.
        dut.ui_in.value = 0

        # 5. Wait one more clock cycle to allow the DUT to de-assert its output enable.
        await RisingEdge(dut.clk)
        assert dut.uio_oe.value == 0, f"uio_oe did not de-assert after reading output {i}"


    dut._log.info(f"Actual packed outputs: {[hex(x) for x in actual_outputs]}")
    dut._log.info("Test case passed.")

# --- Testbenches ---

@cocotb.test()
async def test_reset_and_initial_state(dut):
    dut._log.info("Starting reset test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    assert dut.uio_oe.value == 0, "uio_oe should be low after reset"
    dut._log.info("Reset test passed")


@cocotb.test()
async def test_full_cycle_complex(dut):
    dut._log.info("Starting full cycle test with complex values")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    inputs = [(16, 32), (-48, -64), (80, -96), (-112, 112)]
    await run_full_fft_test(dut, inputs)


@cocotb.test()
async def test_fft_impulse(dut):
    dut._log.info("Starting impulse response test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    inputs = [(16, 0), (0, 0), (0, 0), (0, 0)]
    await run_full_fft_test(dut, inputs)


@cocotb.test()
async def test_fft_dc_input(dut):
    dut._log.info("Starting DC input test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    inputs = [(16, 0), (16, 0), (16, 0), (16, 0)]
    await run_full_fft_test(dut, inputs)


@cocotb.test()
async def test_randomized_end_to_end(dut):
    dut._log.info("Starting randomized end-to-end test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    valid_values = list(range(-128, 128, 16))
    num_tests = 5 # Reduced for speed
    for i in range(num_tests):
        dut._log.info(f"--- Randomized Test Iteration {i+1}/{num_tests} ---")
        await reset_dut(dut)
        inputs = [
            (random.choice(valid_values), random.choice(valid_values)),
            (random.choice(valid_values), random.choice(valid_values)),
            (random.choice(valid_values), random.choice(valid_values)),
            (random.choice(valid_values), random.choice(valid_values))
        ]
        await run_full_fft_test(dut, inputs)