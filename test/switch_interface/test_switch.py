import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import random


@cocotb.test()
async def test_switch_interface(dut):
    """Test switch_interface with clean and bouncing edges"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Initialize

    # Reset
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    dut.sw_in.value = 0
    await Timer(20, units="ns")
    await RisingEdge(dut.clk)

    #Press and release a switch cleanly
    dut.sw_in.value = 1
    for _ in range(10):
        await RisingEdge(dut.clk)
        if dut.pulse_out.value:
            break
    else:
        assert False, f"Pulse never asserted"
    await Timer(100, units="ns")
    dut.sw_in.value = 0
    await Timer(100, units="ns")
    # Confirm pulse disappears
    await RisingEdge(dut.clk)
    assert dut.pulse_out.value == 0, f"Pulse didn't clear"

    # Then make sure it returns low the next cycle
    await RisingEdge(dut.clk)
    assert dut.pulse_out.value == 0, f"Pulse didn't clear"

    for _ in range(3):
        dut.sw_in.value = 1
        await Timer(3, units="ns")
        dut.sw_in.value = 0
        await Timer(3, units="ns")

    # Final press (clean)
    dut.sw_in.value = 1
    pulse_seen = False

    for cycle in range(20):  # Enough time for debounce to complete
        await RisingEdge(dut.clk)
        if dut.pulse_out.value:
            if pulse_seen:
                raise AssertionError("Multiple pulses seen during debounce")
            print(f"Pulse seen at cycle {cycle}")
            pulse_seen = True

    # Now release switch
    dut.sw_in.value = 0
    await Timer(100, units="ns")
    await RisingEdge(dut.clk)

    assert pulse_seen, "Expected 1 pulse after bounce resolution"