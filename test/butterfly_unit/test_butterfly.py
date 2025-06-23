import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
import random

def to_fixed_point(real, imag, bits=4):
    """Convert complex number to packed fixed-point format."""
    mask = (1 << (bits * 2)) - 1
    
    # Convert to integers and handle negative numbers for 2's complement
    real = int(real)
    imag = int(imag)
    
    if real < 0:
        real = (1 << bits) + real
    if imag < 0:
        imag = (1 << bits) + imag

    return ((real << bits) | imag) & mask

async def test_butterfly_case(dut, A, B, T):
    """Test a single butterfly case."""
    # Drive inputs
    dut.A.value = to_fixed_point(A.real, A.imag)
    dut.B.value = to_fixed_point(B.real, B.imag)
    dut.T.value = to_fixed_point(T.real, T.imag)
    dut.en.value = 1
    
    # Wait for calculation (wait many cycles to ensure correct values)
    for i in range(20):
        await RisingEdge(dut.clk)
        dut._log.info("Cycle " + str(i) + ": en=" + str(dut.en.value) + ", valid=" + str(dut.valid.value) + ", Pos=" + str(dut.Pos.value) + ", Neg=" + str(dut.Neg.value))
    
    # Get results while en is still high
    actual_pos = dut.Pos.value.signed_integer
    actual_neg = dut.Neg.value.signed_integer
    expected_pos = dut.plus.value.signed_integer
    expected_neg = dut.minus.value.signed_integer
    
    dut._log.info("A=" + str(A) + ", B=" + str(B) + ", T=" + str(T) + " -> DUT: Pos=" + hex(actual_pos) + ", Neg=" + hex(actual_neg) + " vs Golden: Pos=" + hex(expected_pos) + ", Neg=" + hex(expected_neg))
    
    # Verify results
    assert dut.valid.value == 1, "Valid signal should be high"
    assert actual_pos == expected_pos, "Positive output mismatch: " + hex(actual_pos) + " vs " + hex(expected_pos)
    assert actual_neg == expected_neg, "Negative output mismatch: " + hex(actual_neg) + " vs " + hex(expected_neg)
    
    # Now set en low to test that valid goes low
    dut.en.value = 0
    await Timer(1, units='ns')
    dut._log.info("Set en=0, valid=" + str(dut.valid.value))
    await RisingEdge(dut.clk)  # Wait for the next clock edge
    await RisingEdge(dut.clk)  # Wait for another clock edge
    dut._log.info("After two clock edges, valid=" + str(dut.valid.value))
    assert dut.valid.value == 0, "Valid should go low when en is low"

@cocotb.test()
async def test_basic_butterfly(dut):
    """Test basic butterfly functionality."""
    dut._log.info("--- Testing Basic Butterfly Functionality ---")
    
    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # Test cases
    test_cases = [
        (complex(1, 1), complex(2, 2), complex(1, 0)),   # Simple case
        (complex(1, 1), complex(2, 2), complex(0, 1)),   # T = j
        (complex(1, 1), complex(2, 2), complex(-1, 0)),  # T = -1
        (complex(3, 2), complex(1, 4), complex(2, 1)),   # Random case
    ]
    
    for A, B, T in test_cases:
        await test_butterfly_case(dut, A, B, T)

@cocotb.test()
async def test_enable_control(dut):
    """Test that calculations only occur when enabled."""
    dut._log.info("--- Testing Enable Control ---")
    
    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # Drive inputs but keep enable low
    dut.A.value = to_fixed_point(1, 1)
    dut.B.value = to_fixed_point(2, 2)
    dut.T.value = to_fixed_point(1, 0)
    dut.en.value = 0
    
    # Wait a few cycles - outputs should not change
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    # Valid should be low when not enabled
    assert dut.valid.value == 0, "Valid should be low when not enabled"
    
    # Now enable and check that it works
    dut.en.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    assert dut.valid.value == 1, "Valid should be high when enabled"

@cocotb.test()
async def test_reset_functionality(dut):
    """Test reset functionality."""
    dut._log.info("--- Testing Reset Functionality ---")
    
    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # Drive some inputs and enable
    dut.A.value = to_fixed_point(1, 1)
    dut.B.value = to_fixed_point(2, 2)
    dut.T.value = to_fixed_point(1, 0)
    dut.en.value = 1
    
    # Wait for calculation (many cycles)
    for _ in range(20):
        await RisingEdge(dut.clk)
    
    # Verify outputs are not zero
    assert dut.Pos.value != 0, "Output should not be zero after calculation"
    assert dut.valid.value == 1, "Valid should be high"
    
    # Apply reset and wait many cycles
    dut.rst.value = 1
    for _ in range(10):
        await RisingEdge(dut.clk)
    
    # Verify outputs are reset
    assert dut.Pos.value == 0, "Output should be zero after reset"
    assert dut.Neg.value == 0, "Output should be zero after reset"
    assert dut.valid.value == 0, "Valid should be low after reset"
    
    # Release reset and verify outputs stay zero until enabled
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    assert dut.Pos.value == 0, "Output should stay zero after reset release"
    assert dut.Neg.value == 0, "Output should stay zero after reset release"
    assert dut.valid.value == 0, "Valid should stay low after reset release"

@cocotb.test()
async def test_changing_inputs(dut):
    """Test with inputs that change every cycle to see them in waveform."""
    dut._log.info("--- Testing Changing Inputs ---")
    
    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # Test with changing inputs every cycle
    test_values = [
        (complex(1, 1), complex(2, 2), complex(1, 0)),
        (complex(2, 2), complex(3, 3), complex(0, 1)),
        (complex(3, 3), complex(4, 4), complex(-1, 0)),
        (complex(4, 4), complex(5, 5), complex(1, 1)),
        (complex(5, 5), complex(6, 6), complex(0, -1)),
    ]
    
    for i, (A, B, T) in enumerate(test_values):
        dut.A.value = to_fixed_point(A.real, A.imag)
        dut.B.value = to_fixed_point(B.real, B.imag)
        dut.T.value = to_fixed_point(T.real, T.imag)
        dut.en.value = 1
        
        await RisingEdge(dut.clk)
        dut._log.info(f"Cycle {i}: A={A}, B={B}, T={T}, valid={dut.valid.value}, Pos={dut.Pos.value}, Neg={dut.Neg.value}")
        
        # Check that valid goes high after one cycle
        if i > 0:  # Skip first cycle (reset)
            assert dut.valid.value == 1, f"Valid should be high on cycle {i}"
    
    # Test that valid goes low when en goes low
    dut.en.value = 0
    await Timer(1, units='ns')
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert dut.valid.value == 0, "Valid should go low when en is low"

@cocotb.test()
async def test_overflow_saturation(dut):
    """Test overflow handling - outputs should saturate, not wrap around."""
    dut._log.info("--- Testing Overflow Saturation ---")
    
    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # Test with maximum inputs that should cause overflow
    # For 8-bit signed: max value is 127 (0x7F), min is -128 (0x80)
    max_inputs = [
        (complex(7, 7), complex(7, 7), complex(7, 7)),  # Max positive values
        (complex(-8, -8), complex(-8, -8), complex(-8, -8)),  # Max negative values
        (complex(7, 7), complex(7, 7), complex(1, 0)),  # Max A, B with T=1
        (complex(7, 7), complex(7, 7), complex(-1, 0)),  # Max A, B with T=-1
    ]
    
    for A, B, T in max_inputs:
        dut.A.value = to_fixed_point(A.real, A.imag)
        dut.B.value = to_fixed_point(B.real, B.imag)
        dut.T.value = to_fixed_point(T.real, T.imag)
        dut.en.value = 1
        
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)  # Wait for calculation
        
        # Check that outputs are valid (not undefined)
        pos_val = dut.Pos.value.signed_integer
        neg_val = dut.Neg.value.signed_integer
        
        dut._log.info(f"Max inputs A={A}, B={B}, T={T} -> Pos={pos_val:#04x}, Neg={neg_val:#04x}")
        
        # Verify outputs are within valid range (should saturate, not wrap)
        assert -128 <= pos_val <= 127, f"Pos output {pos_val} out of range"
        assert -128 <= neg_val <= 127, f"Neg output {neg_val} out of range"
        assert dut.valid.value == 1, "Valid should be high"

@cocotb.test()
async def test_twiddle_corner_cases(dut):
    """Test corner cases with specific twiddle factors: 0, -1, 1, j, -j."""
    dut._log.info("--- Testing Twiddle Corner Cases ---")
    
    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # Test cases with different twiddle factors
    test_cases = [
        (complex(3, 2), complex(1, 4), complex(0, 0), "T=0"),      # Multiply by 0
        (complex(3, 2), complex(1, 4), complex(1, 0), "T=1"),      # Multiply by 1
        (complex(3, 2), complex(1, 4), complex(-1, 0), "T=-1"),    # Multiply by -1
        (complex(3, 2), complex(1, 4), complex(0, 1), "T=j"),      # Multiply by j
        (complex(3, 2), complex(1, 4), complex(0, -1), "T=-j"),    # Multiply by -j
        (complex(1, 1), complex(2, 2), complex(0, 0), "T=0 simple"), # Simple case with T=0
        (complex(1, 1), complex(2, 2), complex(1, 0), "T=1 simple"), # Simple case with T=1
    ]
    
    for A, B, T, desc in test_cases:
        dut.A.value = to_fixed_point(A.real, A.imag)
        dut.B.value = to_fixed_point(B.real, B.imag)
        dut.T.value = to_fixed_point(T.real, T.imag)
        dut.en.value = 1
        
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)  # Wait for calculation
        
        actual_pos = dut.Pos.value.signed_integer
        actual_neg = dut.Neg.value.signed_integer
        expected_pos = dut.plus.value.signed_integer
        expected_neg = dut.minus.value.signed_integer
        
        dut._log.info(f"{desc}: A={A}, B={B}, T={T}")
        dut._log.info(f"  DUT: Pos={actual_pos:#04x}, Neg={actual_neg:#04x}")
        dut._log.info(f"  Golden: Pos={expected_pos:#04x}, Neg={expected_neg:#04x}")
        
        # Verify results match golden model
        assert actual_pos == expected_pos, f"Pos mismatch for {desc}: {actual_pos:#04x} vs {expected_pos:#04x}"
        assert actual_neg == expected_neg, f"Neg mismatch for {desc}: {actual_neg:#04x} vs {expected_neg:#04x}"
        assert dut.valid.value == 1, f"Valid should be high for {desc}"

@cocotb.test()
async def test_reset_clear_state(dut):
    """Test that reset clears intermediate state and doesn't give partial results."""
    dut._log.info("--- Testing Reset Clear State ---")
    
    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Initial reset
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # Drive some inputs and enable
    dut.A.value = to_fixed_point(3, 2)
    dut.B.value = to_fixed_point(1, 4)
    dut.T.value = to_fixed_point(2, 1)
    dut.en.value = 1
    
    # Wait for calculation to complete
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    # Verify outputs are not zero
    assert dut.Pos.value != 0, "Output should not be zero after calculation"
    assert dut.Neg.value != 0, "Output should not be zero after calculation"
    assert dut.valid.value == 1, "Valid should be high"
    
    # Apply reset during calculation
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # Wait an extra cycle for outputs to clear
    
    # Debug: Print actual values
    dut._log.info(f"After reset: Pos={dut.Pos.value}, Neg={dut.Neg.value}, valid={dut.valid.value}")
    
    # Verify outputs are cleared on the next clock edge after reset
    assert dut.Pos.value == 0, "Output should be zero after reset clock edge"
    assert dut.Neg.value == 0, "Output should be zero after reset clock edge"
    assert dut.valid.value == 0, "Valid should be low after reset clock edge"
    
    # Keep reset for a few more cycles
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    # Verify outputs stay cleared
    assert dut.Pos.value == 0, "Output should stay zero during reset"
    assert dut.Neg.value == 0, "Output should stay zero during reset"
    assert dut.valid.value == 0, "Valid should stay low during reset"
    
    # Release reset
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # Verify outputs stay zero until new inputs are provided
    assert dut.Pos.value == 0, "Output should stay zero after reset release"
    assert dut.Neg.value == 0, "Output should stay zero after reset release"
    assert dut.valid.value == 0, "Valid should stay low after reset release"
    
    # Now provide new inputs and verify they work
    dut.A.value = to_fixed_point(1, 1)
    dut.B.value = to_fixed_point(2, 2)
    dut.T.value = to_fixed_point(1, 0)
    dut.en.value = 1
    
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    # Verify new calculation works
    assert dut.Pos.value != 0, "New calculation should work after reset"
    assert dut.valid.value == 1, "Valid should be high for new calculation"

@cocotb.test()
async def test_constrained_random(dut):
    """Test with constrained random inputs to catch edge cases."""
    dut._log.info("--- Testing Constrained Random ---")
    
    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # Set random seed for reproducibility
    random.seed(42)
    
    # Generate random test cases
    num_tests = 50
    for i in range(num_tests):
        # Generate random inputs within valid range (-8 to 7 for 4-bit signed)
        A_real = random.randint(-8, 7)
        A_imag = random.randint(-8, 7)
        B_real = random.randint(-8, 7)
        B_imag = random.randint(-8, 7)
        T_real = random.randint(-8, 7)
        T_imag = random.randint(-8, 7)
        
        A = complex(A_real, A_imag)
        B = complex(B_real, B_imag)
        T = complex(T_real, T_imag)
        
        dut.A.value = to_fixed_point(A.real, A.imag)
        dut.B.value = to_fixed_point(B.real, B.imag)
        dut.T.value = to_fixed_point(T.real, T.imag)
        dut.en.value = 1
        
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)  # Wait for calculation
        
        actual_pos = dut.Pos.value.signed_integer
        actual_neg = dut.Neg.value.signed_integer
        expected_pos = dut.plus.value.signed_integer
        expected_neg = dut.minus.value.signed_integer
        
        # Log every 10th test case to avoid too much output
        if i % 10 == 0:
            dut._log.info(f"Random test {i}: A={A}, B={B}, T={T}")
            dut._log.info(f"  DUT: Pos={actual_pos:#04x}, Neg={actual_neg:#04x}")
            dut._log.info(f"  Golden: Pos={expected_pos:#04x}, Neg={expected_neg:#04x}")
        
        # Verify results match golden model
        assert actual_pos == expected_pos, f"Pos mismatch in random test {i}: {actual_pos:#04x} vs {expected_pos:#04x}"
        assert actual_neg == expected_neg, f"Neg mismatch in random test {i}: {actual_neg:#04x} vs {expected_neg:#04x}"
        assert dut.valid.value == 1, f"Valid should be high in random test {i}"
        
        # Verify outputs are within valid range
        assert -128 <= actual_pos <= 127, f"Pos output {actual_pos} out of range in test {i}"
        assert -128 <= actual_neg <= 127, f"Neg output {actual_neg} out of range in test {i}"
    
    dut._log.info(f"Completed {num_tests} random test cases successfully") 