import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import random

# --- Helper and Model Functions ---

def signed(val, bits):
    """Convert an unsigned value from a Verilog sim to a signed Python integer."""
    if val >= (1 << (bits - 1)):
        return val - (1 << bits)
    return val

def model_data_transform(data_in):
    """
    A bit-accurate Python model of the Verilog data transformation:
    `$signed(nibble) << 4`. This is the "golden reference".
    """
    # Extract upper and lower 4-bit nibbles
    real_nibble = (data_in >> 4) & 0xF
    imag_nibble = data_in & 0xF

    # Convert 4-bit nibbles to signed integers (-8 to 7)
    if real_nibble >= 8:
        real_val = real_nibble - 16
    else:
        real_val = real_nibble

    if imag_nibble >= 8:
        imag_val = imag_nibble - 16
    else:
        imag_val = imag_nibble
        
    # Apply the left shift by 4 (multiply by 16)
    return (real_val << 4, imag_val << 4)

class MemoryModel:
    """A simple Python model to shadow the DUT's memory."""
    def __init__(self):
        self.mem = [(0, 0)] * 4

    def write(self, addr, data_in):
        self.mem[addr] = model_data_transform(data_in)

    def read(self, addr):
        return self.mem[addr]

    def get_all(self):
        return self.mem

    def reset(self):
        self.mem = [(0, 0)] * 4

# --- Testbenches ---

@cocotb.test()
async def test_reset(dut):
    """Verify asynchronous reset clears all memory locations."""
    dut._log.info("Starting reset test")
    
    # Start clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Set some initial non-zero values
    dut.ena.value = 1
    dut.load_pulse.value = 1
    dut.addr.value = 1
    dut.data_in.value = 0x12
    await RisingEdge(dut.clk)
    dut.load_pulse.value = 0 # De-assert pulse

    # Assert asynchronous reset
    dut.rst.value = 1
    await Timer(5, 'ns') # Wait for reset to propagate

    dut._log.info("Checking outputs are zero during reset")
    for i in range(4):
        assert signed(getattr(dut, f"real{i}_out").value.integer, 8) == 0
        assert signed(getattr(dut, f"imag{i}_out").value.integer, 8) == 0
    
    # De-assert reset
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    dut._log.info("Reset released, checking outputs remain zero")
    for i in range(4):
        assert signed(getattr(dut, f"real{i}_out").value.integer, 8) == 0
        assert signed(getattr(dut, f"imag{i}_out").value.integer, 8) == 0

    dut._log.info("Reset test passed")

@cocotb.test()
async def test_single_write_and_data_transform(dut):
    """Test a single write and verify the data transformation logic."""
    dut._log.info("Starting single write test")
    await test_reset(dut) # Start from a known-good reset state

    addr = 2
    data_in = 0x96 # real=9 (-7), imag=6 (6)
    
    expected_real, expected_imag = model_data_transform(data_in)
    dut._log.info(f"Writing {data_in=:#x} to addr {addr}. Expecting ({expected_real}, {expected_imag})")

    # Perform a write
    dut.ena.value = 1
    dut.load_pulse.value = 1
    dut.addr.value = addr
    dut.data_in.value = data_in
    await RisingEdge(dut.clk)
    dut.load_pulse.value = 0 # Pulse is for one cycle

    await Timer(1, 'ns') # Let outputs settle

    # Check the written location
    assert signed(dut.real2_out.value.integer, 8) == expected_real
    assert signed(dut.imag2_out.value.integer, 8) == expected_imag

    # Check that other locations were not affected
    assert signed(dut.real0_out.value.integer, 8) == 0
    assert signed(dut.imag1_out.value.integer, 8) == 0

    dut._log.info("Single write test passed")

@cocotb.test()
async def test_write_inhibited(dut):
    """Verify writes are blocked if ena=0 or load_pulse=0."""
    dut._log.info("Starting write inhibit test")
    await test_reset(dut)

    addr = 3
    data_in = 0xFF

    # Case 1: ena is low
    dut._log.info("Attempting write with ena=0")
    dut.ena.value = 0
    dut.load_pulse.value = 1
    dut.addr.value = addr
    dut.data_in.value = data_in
    await RisingEdge(dut.clk)
    dut.load_pulse.value = 0

    await Timer(1, 'ns')
    assert signed(dut.real3_out.value.integer, 8) == 0, "Write occurred when ena was low"

    # Case 2: load_pulse is low
    dut._log.info("Attempting write with load_pulse=0")
    dut.ena.value = 1
    dut.load_pulse.value = 0 # Already low
    await RisingEdge(dut.clk)

    await Timer(1, 'ns')
    assert signed(dut.real3_out.value.integer, 8) == 0, "Write occurred when load_pulse was low"

    dut._log.info("Write inhibit test passed")

@cocotb.test()
async def test_randomized_writes(dut):
    """Perform a series of randomized writes and check against a model."""
    dut._log.info("Starting randomized write test")
    await test_reset(dut)
    
    model = MemoryModel()
    num_writes = 50

    for i in range(num_writes):
        # Generate random stimulus
        addr = random.randint(0, 3)
        data_in = random.randint(0, 255)
        do_write = random.choice([True, False])

        dut.addr.value = addr
        dut.data_in.value = data_in
        dut.ena.value = 1
        dut.load_pulse.value = 1 if do_write else 0

        # Update model if the write is expected to happen
        if do_write:
            model.write(addr, data_in)
        
        await RisingEdge(dut.clk)
        dut.load_pulse.value = 0 # Always de-assert pulse after clock

        await Timer(1, 'ns') # Allow outputs to update

        # Verify entire memory state
        dut_state = [
            (signed(dut.real0_out.value, 8), signed(dut.imag0_out.value, 8)),
            (signed(dut.real1_out.value, 8), signed(dut.imag1_out.value, 8)),
            (signed(dut.real2_out.value, 8), signed(dut.imag2_out.value, 8)),
            (signed(dut.real3_out.value, 8), signed(dut.imag3_out.value, 8)),
        ]
        model_state = model.get_all()
        
        dut._log.info(f"Iter {i}: Write {'Enabled' if do_write else 'Disabled'}. Addr={addr}, Data={data_in:#x}")
        assert dut_state == model_state, f"Mismatch at iter {i}\nDUT: {dut_state}\nModel: {model_state}"
    
    dut._log.info("Randomized write test passed")