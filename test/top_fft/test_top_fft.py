import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ClockCycles
import random

# --- Helper Functions ---

def wrap8(x):
    """Wrap a Python integer to the signed 8-bit range [-128, 127]."""
    if x > 127:
        x -= 256
    elif x < -128:
        x += 256
    return x

def pack_input(real, imag):
    """
    Packs 8-bit signed real/imag parts into a single 8-bit value for uio_in.
    This models the format expected by the DUT's memory_ctrl, which unpacks
    two 4-bit signed nibbles.
    """
    # The DUT's memory controller effectively right-shifts by 4.
    real_nibble_signed = real >> 4
    imag_nibble_signed = imag >> 4
    # Convert to unsigned 4-bit representation for packing.
    real_nibble_unsigned = real_nibble_signed & 0xF
    imag_nibble_unsigned = imag_nibble_signed & 0xF
    return (real_nibble_unsigned << 4) | imag_nibble_unsigned

def pack_output(real, imag):
    """
    Packs the MSBs of the 8-bit real/imag results into an 8-bit output value.
    This matches the DUT's output logic: {fft_real[7:4], fft_imag[7:4]}.
    """
    real_msbs = (real >> 4) & 0xF
    imag_msbs = (imag >> 4) & 0xF
    return (real_msbs << 4) | imag_msbs

# --- Reference Models ---

def model_mem_transform(data_in):
    """
    Models the memory_ctrl logic that unpacks a byte from uio_in into
    two 8-bit signed numbers (with lower 4 bits as zero).
    """
    real_nibble = (data_in >> 4) & 0xF
    imag_nibble = data_in & 0xF
    # Convert 4-bit unsigned to 4-bit signed
    real_val = (real_nibble - 16) if real_nibble >= 8 else real_nibble
    imag_val = (imag_nibble - 16) if imag_nibble >= 8 else imag_nibble
    # Scale to 8-bit value (as the DUT does)
    return (real_val << 4, imag_val << 4)

def butterfly_ref_model(a_r, a_i, b_r, b_i, t_r, t_i):
    """Reference model for one butterfly calculation, matching Verilog."""
    prod_real = t_r * b_r - t_i * b_i
    prod_imag = t_i * b_r + t_r * b_i
    # Scale by shifting right, simulating Verilog's `>>> 7`
    scale = lambda val: wrap8(val >> 7)
    pr, pi = scale(prod_real), scale(prod_imag)
    return (wrap8(a_r + pr), wrap8(a_i + pi)), (wrap8(a_r - pr), wrap8(a_i - pi))

def fft_engine_ref_model(in0, in1, in2, in3):
    """Reference model for the fft_engine, matching the DUT's specific wiring."""
    W0_r, W0_i = -128, 0   # Represents -1.0
    W1_r, W1_i = 0, -128   # Represents -j

    # Stage 1: Note DUT uses W=-1, which differs from standard FFT but is modeled here
    (s1_0_pos, s1_0_neg) = butterfly_ref_model(in0[0], in0[1], in2[0], in2[1], W0_r, W0_i)
    (s1_1_pos, s1_1_neg) = butterfly_ref_model(in1[0], in1[1], in3[0], in3[1], W0_r, W0_i)

    # Stage 2
    # First butterfly (W=+1)
    out0 = (wrap8(s1_0_pos[0] + s1_1_pos[0]), wrap8(s1_0_pos[1] + s1_1_pos[1]))
    out2 = (wrap8(s1_0_pos[0] - s1_1_pos[0]), wrap8(s1_0_pos[1] - s1_1_pos[1]))
    # Second butterfly (W=-j)
    (out1, out3) = butterfly_ref_model(s1_0_neg[0], s1_0_neg[1], s1_1_neg[0], s1_1_neg[1], W1_r, W1_i)

    return [out0, out1, out2, out3]

def top_fft_ref_model(raw_inputs):
    """
    A full reference model for the tt_um_FFT_engine DUT.
    It chains the input transformation, FFT core, and output packing models.
    """
    # 1. Simulate the input transformation of memory_ctrl
    transformed_inputs = [model_mem_transform(pack_input(r, i)) for r, i in raw_inputs]

    # 2. Run the transformed inputs through the FFT engine model
    fft_results = fft_engine_ref_model(
        transformed_inputs[0],
        transformed_inputs[1],
        transformed_inputs[2],
        transformed_inputs[3]
    )

    # 3. Pack the FFT results like the DUT's output logic
    packed_outputs = [pack_output(r, i) for r, i in fft_results]
    return packed_outputs

# --- Test Helper Coroutines ---

async def reset_dut(dut):
    """Resets the DUT with an active-low reset."""
    dut.rst_n.value = 0
    dut.ena.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    dut._log.info("DUT reset")

async def load_sample(dut, data_in):
    """Loads one 8-bit sample into the DUT."""
    dut.uio_in.value = data_in
    dut.ui_in.value = 1  # ui_in[0] = 1 to trigger load
    await RisingEdge(dut.clk)
    dut.ui_in.value = 0
    # Allow address to increment before next load
    await RisingEdge(dut.clk)

async def trigger_read_next(dut):
    """Triggers the DUT to output the next result."""
    dut.ui_in.value = 2  # ui_in[1] = 1 to trigger output
    await RisingEdge(dut.clk)
    dut.ui_in.value = 0

async def run_full_fft_test(dut, inputs):
    """A complete test sequence: load 4 samples, wait, read 4 samples, and verify."""
    # Calculate expected results
    expected_outputs = top_fft_ref_model(inputs)
    dut._log.info(f"Inputs: {inputs}")
    dut._log.info(f"Expected packed outputs: {[hex(x) for x in expected_outputs]}")

    # --- Load Phase ---
    dut.ena.value = 1
    for i in range(4):
        packed_val = pack_input(inputs[i][0], inputs[i][1])
        await load_sample(dut, packed_val)
    
    # Wait for internal processing.
    # 1 cycle for `load_pulse` to set `processing` flag.
    # 1 cycle for `fft_engine` pipeline.
    # 1 cycle for `done` flag to be set.
    await ClockCycles(dut.clk, 5)

    # --- Read and Verify Phase ---
    actual_outputs = []
    for i in range(4):
        await trigger_read_next(dut)
        # Wait for the output enable to be asserted
        await RisingEdge(dut.uio_oe)
        
        # Sample the output
        dut_out = dut.uio_out.value.integer
        actual_outputs.append(dut_out)
        
        # Check against the expected value for this specific output
        assert dut_out == expected_outputs[i], \
            f"Output {i} mismatch: DUT={hex(dut_out)}, Expected={hex(expected_outputs[i])}"
        
        # Wait for the cycle to finish before triggering the next read
        await RisingEdge(dut.clk)

    dut._log.info(f"Actual packed outputs: {[hex(x) for x in actual_outputs]}")
    dut._log.info("Test case passed.")


# --- Testbenches ---

@cocotb.test()
async def test_reset_and_initial_state(dut):
    """Tests reset and ensures outputs are initially disabled."""
    dut._log.info("Starting reset test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    
    # After reset, output enable should be low
    assert dut.uio_oe.value == 0, "uio_oe should be low after reset"
    assert dut.uo_out.value == 0, "uo_out should be zero after reset"
    
    dut._log.info("Reset test passed")


@cocotb.test()
async def test_full_cycle_complex(dut):
    """Tests a full load-process-read cycle with complex inputs."""
    dut._log.info("Starting full cycle test with complex values")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    # Inputs must be multiples of 16 due to DUT's memory format
    inputs = [
        (16, 32),
        (-48, -64),
        (80, -96),
        (-112, 112)
    ]
    await run_full_fft_test(dut, inputs)


@cocotb.test()
async def test_fft_impulse(dut):
    """Tests the FFT of an impulse signal [16, 0, 0, 0]."""
    dut._log.info("Starting impulse response test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    
    # Input is (16,0) because of the `<< 4` scaling in memory_ctrl
    inputs = [(16, 0), (0, 0), (0, 0), (0, 0)]
    await run_full_fft_test(dut, inputs)


@cocotb.test()
async def test_fft_dc_input(dut):
    """Tests the FFT of a DC signal [16, 16, 16, 16]."""
    dut._log.info("Starting DC input test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    
    inputs = [(16, 0), (16, 0), (16, 0), (16, 0)]
    await run_full_fft_test(dut, inputs)


@cocotb.test()
async def test_randomized_end_to_end(dut):
    """Runs several full FFT cycles with randomized inputs."""
    dut._log.info("Starting randomized end-to-end test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    # Valid input values are multiples of 16 from -128 to 112
    valid_values = list(range(-128, 128, 16))
    num_tests = 15

    for i in range(num_tests):
        dut._log.info(f"--- Randomized Test Iteration {i+1}/{num_tests} ---")
        inputs = [
            (random.choice(valid_values), random.choice(valid_values)),
            (random.choice(valid_values), random.choice(valid_values)),
            (random.choice(valid_values), random.choice(valid_values)),
            (random.choice(valid_values), random.choice(valid_values))
        ]
        await run_full_fft_test(dut, inputs)
        await ClockCycles(dut.clk, 5) # Add a small delay between tests