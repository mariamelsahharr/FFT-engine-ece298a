import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from decimal import Decimal

@cocotb.test()
async def test_gate_level_startup(dut):
    """
    A basic test that asserts reset and waits for a few clock cycles.
    This is just to ensure the gate-level simulation starts correctly.
    """
    # Start the clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    dut._log.info("Applying reset")
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await Timer(Decimal(20), units="ns")

    dut._log.info("Releasing reset")
    dut.rst_n.value = 1
    await Timer(Decimal(50), units="ns")

    dut._log.info("Gate-level simulation started successfully!") 