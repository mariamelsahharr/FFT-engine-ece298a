# Makefile
# See https://docs.cocotb.org/en/stable/quickstart.html for more info

# defaults
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
SRC_DIR = $(PWD)/../src

PROJECT_SOURCES = top_fft.sv \
                  fft_engine.sv \
                  fft_memory.sv \
                  display_controller.sv \
                  butterfly_unit.sv \
                  bit_reversal.sv 
				  
ifneq ($(GATES),yes)

# RTL simulation:
SIM_BUILD				= sim_build/rtl
VERILOG_SOURCES += $(addprefix $(SRC_DIR)/,$(PROJECT_SOURCES))

else

# Gate level simulation:
SIM_BUILD				= sim_build/gl
COMPILE_ARGS    += -DGL_TEST
COMPILE_ARGS    += -DFUNCTIONAL
COMPILE_ARGS    += -DSIM
VERILOG_SOURCES += $(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_io/verilog/sg13g2_io.v
VERILOG_SOURCES += $(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog/sg13g2_stdcell.v

# this gets copied in by the GDS action workflow
VERILOG_SOURCES += $(PWD)/gate_level_netlist.v

endif

# Allow sharing configuration between design and testbench via `include`:
COMPILE_ARGS 		+= -I$(SRC_DIR)

# Include the testbench sources:
VERILOG_SOURCES += $(PWD)/tb.v
TOPLEVEL = tb

# MODULE is the basename of the Python test file
MODULE = test

.PHONY: test-butterfly test-memory test-bitrev test-fft

test-butterfly:
	$(MAKE) sim MODULE=butterfly_unit_test TOPLEVEL=butterfly_tb VERILOG_SOURCES="$(SRC_DIR)/butterfly_unit.sv $(PWD)/butterfly_tb.v"

test-memory:
	$(MAKE) sim MODULE=memory_test TOPLEVEL=fft_memory VERILOG_SOURCES="$(SRC_DIR)/fft_memory.sv"

test-bitrev:
	$(MAKE) sim MODULE=bit_reversal_test TOPLEVEL=bit_reversal VERILOG_SOURCES="$(SRC_DIR)/bit_reversal.sv"

test-fft:
	$(MAKE) sim MODULE=fft_engine_test TOPLEVEL=tt_um_FFT_engine VERILOG_SOURCES="$(addprefix $(SRC_DIR)/,$(PROJECT_SOURCES))"

# Default test target
test: test-fft

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim
