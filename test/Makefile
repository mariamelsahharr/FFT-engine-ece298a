# Makefile
# See https://docs.cocotb.org/en/stable/quickstart.html for more info

# defaults
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
SRC_DIR = $(PWD)/../src

# Add timestamp for unique VCD files in US/Eastern timezone with colons between HH, MM, SS
TIMESTAMP = $(shell TZ=US/Eastern date +%Y%m%d_%H:%M:%S)
COMPILE_ARGS += -DTIMESTAMP=\"$(TIMESTAMP)\"

PROJECT_SOURCES = top_fft.sv \
                  fft_engine.sv \
                  fft_memory.sv \
                  display_controller.sv \
                  butterfly_unit.sv \
                  switch_interface.sv
				  
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

.PHONY: all test test-butterfly test-memory test-fft

# Define sources for the butterfly test to simplify the rule
BUTTERFLY_SOURCES = ./butterfly_unit/butterfly_tb.sv ./butterfly_unit/butterfly_golden.sv ../src/butterfly_unit.sv

all: test-butterfly test-memory test-fft

# This rule is simplified to avoid path expansion issues.
# It runs all tests found in the butterfly_unit directory.
test-butterfly:
	$(MAKE) sim \
		MODULE=test_butterfly \
		TOPLEVEL=butterfly_tb \
		VERILOG_SOURCES="./butterfly_unit/butterfly_tb.sv ./butterfly_unit/butterfly_golden.sv ../src/butterfly_unit.sv" \
		PYTHONPATH=$(PWD)/butterfly_unit \
		WAVES_DIR=$(PWD)/butterfly_unit/wave \
		COMPILE_ARGS='$(COMPILE_ARGS) -DVCD_PATH="\"$(PWD)/butterfly_unit/wave/butterfly_tb_$(TIMESTAMP).vcd\""'

test-memory:
	$(MAKE) sim \
		MODULE=memory_test \
		TOPLEVEL=memory_tb \
		VERILOG_SOURCES="./memory_test/memory_tb.sv ../src/fft_memory.sv" \
		PYTHONPATH=$(PWD)/memory_test \
		WAVES_DIR=$(PWD)/memory_test/wave \
		COMPILE_ARGS='$(COMPILE_ARGS) -DVCD_PATH="\"$(PWD)/memory_test/wave/memory_tb_$(TIMESTAMP).vcd\""'

#test-fft:
#	$(MAKE) sim MODULE=fft_engine_test TOPLEVEL=tt_um_FFT_engine VERILOG_SOURCES="$(addprefix $(SRC_DIR)/,$(PROJECT_SOURCES))" WAVES_DIR=$(PWD)/wave

# Default test target
test: all

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim
