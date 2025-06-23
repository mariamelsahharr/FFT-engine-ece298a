import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
import random

async def reset_dut(dut):
    """Helper function to reset the DUT"""
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

@cocotb.test()
async def test_memory_read_write_validity(dut):
    """Test memory read/write validity - verify read_valid signal behavior"""
    dut.test_counter.value = 1
    dut._log.info("--- Memory Read/Write Validity Test ---")
    
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    
    # Enable memory operations
    dut.en.value = 1
    
    # Test 1: Write operation - read_valid should be low during write
    dut.read_en.value = 1
    dut.write_en.value = 1
    dut.addr_w.value = 0
    dut.data_in.value = 0x1234
    await RisingEdge(dut.clk)
    
    assert dut.read_valid.value == 0, "read_valid should be low during write"
    
    # Test 2: Read operation - read_valid should be high during read
    dut.write_en.value = 0
    dut.read_en.value = 1
    dut.addr_a.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # Wait for read_valid
    
    assert dut.read_valid.value == 1, "read_valid should be high during read"
    
    # Test 3: Disable memory - read_valid should be low
    dut.en.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # Wait for read_valid to respond
    
    assert dut.read_valid.value == 0, "read_valid should be low when disabled"
    
    dut._log.info("Memory read/write validity test passed!")

@cocotb.test()
async def test_write_known_data_read_back(dut):
    """Write known data and read back - verify data integrity"""
    dut.test_counter.value = 2
    dut._log.info("--- Write Known Data Read Back Test ---")
    
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    dut.en.value = 1
    
    # Test data patterns
    test_data = [0x1234, 0x5678, 0x9ABC, 0xDEF0]
    
    # Write known data to all addresses
    for addr in range(4):
        dut.read_en.value = 0
        dut.write_en.value = 1
        dut.addr_w.value = addr
        dut.data_in.value = test_data[addr]
        await RisingEdge(dut.clk)
    
    # Read back and verify
    for addr in range(4):
        dut.write_en.value = 0
        dut.read_en.value = 1
        dut.addr_a.value = addr
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)  # Wait for read_valid
        
        assert dut.read_valid.value == 1, f"read_valid should be high for addr {addr}"
        assert dut.data_out_a.value == test_data[addr], f"Addr {addr}: Expected {test_data[addr]:04x}, got {dut.data_out_a.value:04x}"
    
    dut._log.info("Write known data read back test passed!")

@cocotb.test()
async def test_initial_zero_write(dut):
    """Test initial zero write - verify memory starts with zeros"""
    dut.test_counter.value = 3
    dut._log.info("--- Initial Zero Write Test ---")
    
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    dut.en.value = 1
    
    # Read all addresses without any writes - should be zeros
    for addr in range(4):
        dut.write_en.value = 0
        dut.read_en.value = 1
        dut.addr_a.value = addr
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        
        assert dut.read_valid.value == 1, f"read_valid should be high for addr {addr}"
        assert dut.data_out_a.value == 0, f"Addr {addr}: Expected 0, got {dut.data_out_a.value:04x}"
    
    dut._log.info("Initial zero write test passed!")

@cocotb.test()
async def test_write_zeros_to_all_addresses(dut):
    """Write 0s to all addresses - verify zero writes work correctly"""
    dut.test_counter.value = 4
    dut._log.info("--- Write 0s to All Addresses Test ---")
    
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    dut.en.value = 1
    
    # First write some non-zero data
    for addr in range(4):
        dut.read_en.value = 0
        dut.write_en.value = 1
        dut.addr_w.value = addr
        dut.data_in.value = 0xFFFF
        await RisingEdge(dut.clk)
    
    # Now write zeros to all addresses
    for addr in range(4):
        dut.read_en.value = 0
        dut.write_en.value = 1
        dut.addr_w.value = addr
        dut.data_in.value = 0
        await RisingEdge(dut.clk)
    
    # Read back and verify all are zeros
    for addr in range(4):
        dut.write_en.value = 0
        dut.read_en.value = 1
        dut.addr_a.value = addr
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        
        assert dut.read_valid.value == 1, f"read_valid should be high for addr {addr}"
        assert dut.data_out_a.value == 0, f"Addr {addr}: Expected 0, got {dut.data_out_a.value:04x}"
    
    dut._log.info("Write 0s to all addresses test passed!")

@cocotb.test()
async def test_initial_zero_read(dut):
    """Read without any writes - verify initial state"""
    dut.test_counter.value = 5
    dut._log.info("--- Initial Zero Read Test ---")
    
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    dut.en.value = 1
    
    # Read all addresses immediately after reset
    for addr in range(4):
        dut.write_en.value = 0
        dut.read_en.value = 1
        dut.addr_a.value = addr
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        
        assert dut.read_valid.value == 1, f"read_valid should be high for addr {addr}"
        assert dut.data_out_a.value == 0, f"Addr {addr}: Expected 0, got {dut.data_out_a.value:04x}"
    
    dut._log.info("Initial zero read test passed!")

@cocotb.test()
async def test_read_without_writes(dut):
    """Read without any writes - verify read behavior with no prior writes"""
    dut.test_counter.value = 6
    dut._log.info("--- Read Without Writes Test ---")
    
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    dut.en.value = 1
    
    # Read from random addresses without any writes
    for _ in range(10):
        addr = random.randint(0, 3)
        dut.write_en.value = 0
        dut.read_en.value = 1
        dut.addr_a.value = addr
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        
        assert dut.read_valid.value == 1, f"read_valid should be high for addr {addr}"
        assert dut.data_out_a.value == 0, f"Addr {addr}: Expected 0, got {dut.data_out_a.value:04x}"
    
    dut._log.info("Read without writes test passed!")

@cocotb.test()
async def test_write_when_full(dut):
    """Write when full - should overwrite address specified"""
    dut.test_counter.value = 7
    dut._log.info("--- Write When Full Test ---")
    
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    dut.en.value = 1
    
    # Fill memory with pattern
    for addr in range(4):
        dut.read_en.value = 0
        dut.write_en.value = 1
        dut.addr_w.value = addr
        dut.data_in.value = 0x1000 + addr
        await RisingEdge(dut.clk)
    
    # Overwrite specific address
    dut.read_en.value = 0
    dut.write_en.value = 1
    dut.addr_w.value = 2  # Overwrite address 2
    dut.data_in.value = 0x9999
    await RisingEdge(dut.clk)
    
    # Read all addresses and verify
    expected_data = [0x1000, 0x1001, 0x9999, 0x1003]  # Address 2 should be overwritten
    
    for addr in range(4):
        dut.write_en.value = 0
        dut.read_en.value = 1
        dut.addr_a.value = addr
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        
        assert dut.read_valid.value == 1, f"read_valid should be high for addr {addr}"
        assert dut.data_out_a.value == expected_data[addr], f"Addr {addr}: Expected {expected_data[addr]:04x}, got {dut.data_out_a.value:04x}"
    
    dut._log.info("Write when full test passed!")

@cocotb.test()
async def test_address_alignment(dut):
    """Test address alignment - verify all address bits work correctly"""
    dut.test_counter.value = 8
    dut._log.info("--- Address Alignment Test ---")
    
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    dut.en.value = 1
    
    # Test all possible address combinations
    test_data = [0x1111, 0x2222, 0x3333, 0x4444]
    
    # Write to all addresses
    for addr in range(4):
        dut.read_en.value = 0
        dut.write_en.value = 1
        dut.addr_w.value = addr
        dut.data_in.value = test_data[addr]
        await RisingEdge(dut.clk)
    
    # Read from all addresses using both read ports
    for addr in range(4):
        dut.write_en.value = 0
        dut.read_en.value = 1
        dut.addr_a.value = addr
        dut.addr_b.value = (addr + 1) % 4  # Different address for port B
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        
        assert dut.read_valid.value == 1, f"read_valid should be high for addr {addr}"
        assert dut.data_out_a.value == test_data[addr], f"Port A addr {addr}: Expected {test_data[addr]:04x}, got {dut.data_out_a.value:04x}"
        assert dut.data_out_b.value == test_data[(addr + 1) % 4], f"Port B addr {(addr + 1) % 4}: Expected {test_data[(addr + 1) % 4]:04x}, got {dut.data_out_b.value:04x}"
    
    dut._log.info("Address alignment test passed!")

@cocotb.test()
async def test_resets(dut):
    """Test resets - should fully reset and not keep any partial data"""
    dut.test_counter.value = 9
    dut._log.info("--- Resets Test ---")
    
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Initial reset
    await reset_dut(dut)
    dut.en.value = 1
    
    # Write data to all addresses
    for addr in range(4):
        dut.read_en.value = 0
        dut.write_en.value = 1
        dut.addr_w.value = addr
        dut.data_in.value = 0xAAAA + addr
        await RisingEdge(dut.clk)
    
    # Verify data was written
    for addr in range(4):
        dut.write_en.value = 0
        dut.read_en.value = 1
        dut.addr_a.value = addr
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        
        assert dut.data_out_a.value == (0xAAAA + addr), f"Before reset addr {addr}: Expected {0xAAAA + addr:04x}, got {dut.data_out_a.value:04x}"
    
    # Apply reset
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # Verify all data is cleared
    for addr in range(4):
        dut.write_en.value = 0
        dut.read_en.value = 1
        dut.addr_a.value = addr
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        
        assert dut.read_valid.value == 1, f"read_valid should be high for addr {addr}"
        assert dut.data_out_a.value == 0, f"After reset addr {addr}: Expected 0, got {dut.data_out_a.value:04x}"
    
    # Verify read_valid is properly reset by disabling reads
    dut.read_en.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # Wait for read_valid to respond
    
    assert dut.read_valid.value == 0, "read_valid should be low after disabling reads"
    
    dut._log.info("Resets test passed!")

@cocotb.test()
async def test_dual_port_reads(dut):
    """Test dual port reads - verify both read ports work independently"""
    dut.test_counter.value = 10
    dut._log.info("--- Dual Port Reads Test ---")
    
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    dut.en.value = 1
    
    # Write different data to each address
    test_data = [0x1111, 0x2222, 0x3333, 0x4444]
    for addr in range(4):
        dut.read_en.value = 0
        dut.write_en.value = 1
        dut.addr_w.value = addr
        dut.data_in.value = test_data[addr]
        await RisingEdge(dut.clk)
    
    # Test simultaneous reads from both ports
    dut.write_en.value = 0
    dut.read_en.value = 1
    dut.addr_a.value = 0
    dut.addr_b.value = 2
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    assert dut.read_valid.value == 1, "read_valid should be high"
    assert dut.data_out_a.value == test_data[0], f"Port A: Expected {test_data[0]:04x}, got {dut.data_out_a.value:04x}"
    assert dut.data_out_b.value == test_data[2], f"Port B: Expected {test_data[2]:04x}, got {dut.data_out_b.value:04x}"
    
    # Test reading same address from both ports
    dut.addr_a.value = 1
    dut.addr_b.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    assert dut.read_valid.value == 1, "read_valid should be high"
    assert dut.data_out_a.value == test_data[1], f"Port A same addr: Expected {test_data[1]:04x}, got {dut.data_out_a.value:04x}"
    assert dut.data_out_b.value == test_data[1], f"Port B same addr: Expected {test_data[1]:04x}, got {dut.data_out_b.value:04x}"
    
    dut._log.info("Dual port reads test passed!")

@cocotb.test()
async def test_data_overflow(dut):
    """Test data overflow - verify behavior when data exceeds 16-bit range"""
    dut.test_counter.value = 11
    dut._log.info("--- Data Overflow Test ---")
    
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    dut.en.value = 1
    
    # Test writing data that would overflow 16 bits (though input is already 16-bit)
    # Test boundary values: 0x0000, 0xFFFF, and some large values
    test_data = [0x0000, 0xFFFF, 0x8000, 0x7FFF]
    
    for addr in range(4):
        dut.read_en.value = 0
        dut.write_en.value = 1
        dut.addr_w.value = addr
        dut.data_in.value = test_data[addr]
        await RisingEdge(dut.clk)
    
    # Read back and verify boundary values are handled correctly
    for addr in range(4):
        dut.write_en.value = 0
        dut.read_en.value = 1
        dut.addr_a.value = addr
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        
        assert dut.read_valid.value == 1, f"read_valid should be high for addr {addr}"
        assert dut.data_out_a.value == test_data[addr], f"Addr {addr}: Expected {test_data[addr]:04x}, got {dut.data_out_a.value:04x}"
    
    dut._log.info("Data overflow test passed!")

@cocotb.test()
async def test_read_write_conflict(dut):
    """Test read/write conflict - verify read_valid behavior when both read and write are enabled"""
    dut.test_counter.value = 12
    dut._log.info("--- Read/Write Conflict Test ---")
    
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    dut.en.value = 1
    
    # Write some initial data
    dut.read_en.value = 0
    dut.write_en.value = 1
    dut.addr_w.value = 0
    dut.data_in.value = 0x1234
    await RisingEdge(dut.clk)
    
    # Test read/write conflict - both read and write enabled
    dut.read_en.value = 1
    dut.write_en.value = 1
    dut.addr_w.value = 1
    dut.data_in.value = 0x5678
    dut.addr_a.value = 0
    await RisingEdge(dut.clk)
    
    # read_valid should be low during conflict
    assert dut.read_valid.value == 0, "read_valid should be low during read/write conflict"
    
    # Test normal read after conflict
    dut.write_en.value = 0
    dut.read_en.value = 1
    dut.addr_a.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    assert dut.read_valid.value == 1, "read_valid should be high for normal read"
    assert dut.data_out_a.value == 0x1234, f"Expected 0x1234, got {dut.data_out_a.value:04x}"
    
    dut._log.info("Read/write conflict test passed!")

@cocotb.test()
async def test_read_enable_control(dut):
    """Test read enable control - verify read behavior when read_en is low"""
    dut.test_counter.value = 13
    dut._log.info("--- Read Enable Control Test ---")
    
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    dut.en.value = 1
    
    # Write some data
    dut.read_en.value = 0
    dut.write_en.value = 1
    dut.addr_w.value = 0
    dut.data_in.value = 0xABCD
    await RisingEdge(dut.clk)
    
    # Try to read with read_en low
    dut.write_en.value = 0
    dut.read_en.value = 0
    dut.addr_a.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    # read_valid should be low when read_en is low
    assert dut.read_valid.value == 0, "read_valid should be low when read_en is low"
    
    # Now read with read_en high
    dut.read_en.value = 1
    dut.addr_a.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    assert dut.read_valid.value == 1, "read_valid should be high when read_en is high"
    assert dut.data_out_a.value == 0xABCD, f"Expected 0xABCD, got {dut.data_out_a.value:04x}"
    
    dut._log.info("Read enable control test passed!")


