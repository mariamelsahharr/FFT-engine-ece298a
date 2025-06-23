import cocotb
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock

@cocotb.test()
async def test_memory_basic(dut):
    """Basic memory test - write and read"""
    dut._log.info("--- Basic Memory Test ---")
    
    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # Enable memory
    dut.en.value = 1
    
    # Write data to address 0
    dut.write_en.value = 1
    dut.addr_w.value = 0
    dut.data_in.value = 0x1234
    await RisingEdge(dut.clk)
    
    # Read from address 0
    dut.write_en.value = 0
    dut.addr_a.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # Wait for read_valid
    
    # Check the result
    assert dut.read_valid.value == 1, "read_valid should be high"
    assert dut.data_out_a.value == 0x1234, f"Expected 0x1234, got {dut.data_out_a.value:04x}"
    
    dut._log.info("Basic memory test passed!")
