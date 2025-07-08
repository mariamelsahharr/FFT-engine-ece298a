import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

TEST_IDS = {
    "reset":      1,
    "counter":    2,
    "output":     3,
    "ena":        4,
    "simul":      5,
}

async def reset_dut(dut):
    """Helper function to reset the DUT and initialize inputs to a known state."""
    dut.rst.value = 1
    dut.ena.value = 0
    dut.ui_in0.value = 0
    dut.ui_in1.value = 0
    await Timer(5, 'ns')
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    dut._log.info("DUT has been reset")

@cocotb.test()
async def test_reset(dut):
    """Verify the asynchronous reset behavior."""
    dut.current_test_id.value = TEST_IDS["reset"]          
    dut._log.info("Starting reset test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    dut.ena.value = 1
    dut.ui_in0.value = 1
    dut.ui_in1.value = 1
    await RisingEdge(dut.clk)
    
    assert dut.addr.value != 0

    dut.rst.value = 1
    dut.ui_in0.value = 0
    dut.ui_in1.value = 0
    await Timer(5, 'ns')  # Wait for reset to propagate

    dut._log.info("Checking outputs during reset")
    assert dut.addr.value == 0
    assert dut.load_pulse.value == 0
    assert dut.output_pulse.value == 0
    
    # Release reset
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    dut._log.info("Reset released, checking outputs remain zero")
    assert dut.addr.value == 0

    dut._log.info("Reset test passed")
    dut.current_test_id.value = 0                           

@cocotb.test()
async def test_counter_and_load_pulse(dut):
    """Verify counter increments and load_pulse fires on ui_in0 rising edge."""
    dut.current_test_id.value = TEST_IDS["counter"]        
    dut._log.info("Starting counter and load_pulse test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    
    dut.ena.value = 1

    for i in range(5):
        current_addr = dut.addr.value.integer
        expected_addr = (current_addr + 1) % 4
        dut._log.info(f"Test cycle {i}. Current addr={current_addr}. Expecting next addr={expected_addr}")

        # Drive rising edge on ui_in0
        dut.ui_in0.value = 1
        
        await RisingEdge(dut.clk)
        
        assert dut.load_pulse.value == 1, f"load_pulse should be 1 right after ui_in0 rising edge (cycle {i})"
        assert dut.addr.value == current_addr, f"addr should still be {current_addr} immediately after edge (cycle {i})"
        
        await RisingEdge(dut.clk)
        assert dut.load_pulse.value == 0, f"load_pulse should be 0 when ui_in0 is held high (cycle {i})"
        assert dut.addr.value == expected_addr, f"addr should now be {expected_addr} one cycle later (cycle {i})"

        dut.ui_in0.value = 0
        await RisingEdge(dut.clk)
        assert dut.addr.value == expected_addr, f"addr should not change on ui_in0 falling edge (cycle {i})"

    dut._log.info("Counter and load_pulse test passed")
    dut.current_test_id.value = 0                           

@cocotb.test()
async def test_output_pulse(dut):
    """Verify output_pulse fires on ui_in1 rising edge and does not affect counter."""
    dut.current_test_id.value = TEST_IDS["output"]          
    dut._log.info("Starting output_pulse test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    
    dut.ena.value = 1

    dut.ui_in1.value = 1
    await RisingEdge(dut.clk)

    assert dut.output_pulse.value == 1, "output_pulse should be 1 after ui_in1 rising edge"
    assert dut.addr.value == 0, "addr should not change on ui_in1 edge"
    
    await RisingEdge(dut.clk)
    assert dut.output_pulse.value == 0, "output_pulse should be 0 when ui_in1 is held high"
    assert dut.addr.value == 0, "addr should remain unchanged"
    
    dut._log.info("output_pulse test passed")
    dut.current_test_id.value = 0                           

@cocotb.test()
async def test_ena_gate(dut):
    """Verify state changes are correctly gated by ena."""
    dut.current_test_id.value = TEST_IDS["ena"]             
    dut._log.info("Starting ena gate test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    dut.ena.value = 0
    
    dut.ui_in0.value = 1
    dut.ui_in1.value = 1
    await RisingEdge(dut.clk)

    assert dut.load_pulse.value == 1, "BUG: load_pulse fires even when ena is low"
    assert dut.output_pulse.value == 1, "BUG: output_pulse fires even when ena is low"
    
    dut._log.info("Verifying that registered address does not change.")
    assert dut.addr.value == 0, "addr should not change when ena is low"
    
    await RisingEdge(dut.clk)
    assert dut.addr.value == 0, "addr should remain stable when ena is low"

    dut._log.info("Ena gate test passed")
    dut.current_test_id.value = 0                           

@cocotb.test()
async def test_simultaneous_pulses(dut):
    """Verify behavior when both inputs have a rising edge at the same time."""
    dut.current_test_id.value = TEST_IDS["simul"]           
    dut._log.info("Starting simultaneous pulses test")
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    
    dut.ena.value = 1
    
    dut.ui_in0.value = 1
    dut.ui_in1.value = 1
    await RisingEdge(dut.clk)
    
    assert dut.load_pulse.value == 1, "load_pulse should fire on simultaneous edge"
    assert dut.output_pulse.value == 1, "output_pulse should fire on simultaneous edge"
    assert dut.addr.value == 0, "addr should not have updated yet"
    
    await RisingEdge(dut.clk)
    assert dut.addr.value == 1, "addr should increment one cycle after simultaneous edge"
    assert dut.load_pulse.value == 0, "load_pulse should clear"
    assert dut.output_pulse.value == 0, "output_pulse should clear"

    dut._log.info("Simultaneous pulses test passed")
    dut.current_test_id.value = 0                           
