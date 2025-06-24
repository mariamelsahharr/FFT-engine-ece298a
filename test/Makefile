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


.PHONY: test-butterfly test-memory test-fft

test-butterfly:
	$(MAKE) clean
	$(MAKE) sim \
		MODULE=test_butterfly \
		TOPLEVEL=butterfly_tb \
		VERILOG_SOURCES="./butterfly_unit/butterfly_tb.sv ../src/butterfly_unit.sv" \
		PYTHONPATH=$(PWD)/butterfly_unit \
		WAVES_DIR=$(PWD)/butterfly_unit/wave \
		COMPILE_ARGS='$(COMPILE_ARGS) -DVCD_PATH="\"$(PWD)/butterfly_unit/wave/butterfly_tb_$(TIMESTAMP).vcd\""'

test-switch:
	$(MAKE) clean
	$(MAKE) sim \
		MODULE=test_switch \
		TOPLEVEL=switch_tb \
		VERILOG_SOURCES="./switch_interface/switch_tb.sv ../src/switch_interface.sv" \
		PYTHONPATH=$(PWD)/switch_interface \
		WAVES_DIR=$(PWD)/butterfly_interface/wave \
		COMPILE_ARGS='$(COMPILE_ARGS) -DVCD_PATH="\"$(PWD)/switch_interface/wave/switch_tb_$(TIMESTAMP).vcd\""'

test-memory:
	$(MAKE) clean
	$(MAKE) sim \
		MODULE=memory_test \
		TOPLEVEL=memory_tb \
		VERILOG_SOURCES="./memory_test/memory_tb.sv ../src/fft_memory.sv" \
		PYTHONPATH=$(PWD)/memory_test \
		WAVES_DIR=$(PWD)/memory_test/wave \
		COMPILE_ARGS='$(COMPILE_ARGS) -DVCD_PATH="\"$(PWD)/memory_test/wave/memory_tb_$(TIMESTAMP).vcd\""'

test-fft:
	$(MAKE) clean
	$(MAKE) sim \
		MODULE=fft_simple_test \
		TOPLEVEL=fft_tb \
		VERILOG_SOURCES="./fft_test/fft_tb.sv ./fft_test/fft_4point_16bit.sv ./butterfly_unit/butterfly_golden.sv ../src/fft_engine.sv ../src/butterfly_unit.sv" \
		PYTHONPATH=$(PWD)/fft_test \
		WAVES_DIR=$(PWD)/fft_test/wave \
		COMPILE_ARGS='$(COMPILE_ARGS) -DVCD_PATH="\"$(PWD)/fft_test/wave/fft_tb_$(TIMESTAMP).vcd\""'

# Phony target for cleaning up
.PHONY: clean
clean::
	rm -rf sim_build* results.xml
# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim