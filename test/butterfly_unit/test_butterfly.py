import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock

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