import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock

@cocotb.test()
async def butterfly_vs_golden_test(dut):
    """
    Tests the 8-bit sequential butterfly unit against a combinational golden model.
    """
    # --- Setup ---
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # --- Reset DUT ---
    dut._log.info("Resetting DUT")
    dut.rst.value = 1
    dut.en.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    dut._log.info("Reset complete")

    # --- Test Vector (4-bit real, 4-bit imag) ---
    A_val = 0x11 # 1 + 1j
    B_val = 0x22 # 2 + 2j
    T_val = 0x10 # 1 + 0j
    
    # Drive inputs for both DUT and golden model
    dut.A.value = A_val
    dut.B.value = B_val
    dut.T.value = T_val
    dut.en.value = 1
    dut._log.info(f"Applied inputs A=0x{A_val:02x}, B=0x{B_val:02x}, T=0x{T_val:02x}")

    # Let the DUT calculate for one cycle
    await RisingEdge(dut.clk)
    
    dut.en.value = 0 # De-assert enable

    # Wait for all signals to settle
    await Timer(1, 'ns')
    
    # --- Get actual and expected values ---
    actual_pos = dut.Pos.value.signed_integer
    actual_neg = dut.Neg.value.signed_integer
    
    expected_pos = dut.Pos_golden.value.signed_integer
    expected_neg = dut.Neg_golden.value.signed_integer
    
    dut._log.info(f"DUT Valid: {dut.valid.value}")
    dut._log.info(f"--- Golden Model ---")
    dut._log.info(f"Expected: Pos=0x{expected_pos:02x}, Neg=0x{expected_neg:02x}")
    dut._log.info(f"--- DUT ---")
    dut._log.info(f"Actual:   Pos=0x{actual_pos:02x}, Neg=0x{actual_neg:02x}")
    
    assert dut.valid.value == 1, f"DUT valid signal was not high"
    assert actual_pos == expected_pos, f"Pos mismatch: DUT returned {actual_pos:02x}, Golden model expected {expected_pos:02x}"
    assert actual_neg == expected_neg, f"Neg mismatch: DUT returned {actual_neg:02x}, Golden model expected {expected_neg:02x}" 