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


.PHONY: test-butterfly test-fft-engine test-memory test-io test-top

test-butterfly:
	$(MAKE) clean
	$(MAKE) sim \
		MODULE=test_butterfly \
		TOPLEVEL=butterfly_tb \
		VERILOG_SOURCES="./butterfly_unit/butterfly_tb.sv ../src/butterfly.sv" \
		PYTHONPATH=$(PWD)/butterfly_unit \
		WAVES_DIR=$(PWD)/butterfly_unit/wave \
		COMPILE_ARGS='$(COMPILE_ARGS) -DVCD_PATH="\"$(PWD)/butterfly_unit/wave/butterfly_tb_$(TIMESTAMP).vcd\""'

test-fft-engine:
	$(MAKE) clean
	$(MAKE) sim \
		MODULE=test_fft_engine \
		TOPLEVEL=fft_engine_tb \
		VERILOG_SOURCES="./fft_engine/fft_engine_tb.sv ../src/fft_engine.sv ../src/butterfly.sv" \
		PYTHONPATH=$(PWD)/fft_engine \
		WAVES_DIR=$(PWD)/fft_engine/wave \
		COMPILE_ARGS='$(COMPILE_ARGS) -DVCD_PATH="\"$(PWD)/fft_engine/wave/fft_engine_tb_$(TIMESTAMP).vcd\""'

test-memory:
	$(MAKE) clean
	$(MAKE) sim \
		MODULE=test_memory_ctrl \
		TOPLEVEL=memory_ctrl_tb \
		VERILOG_SOURCES="./memory_ctrl/memory_ctrl_tb.sv ../src/memory_ctrl.sv" \
		PYTHONPATH=$(PWD)/memory_ctrl \
		WAVES_DIR=$(PWD)/memory_ctrl/wave \
		COMPILE_ARGS='$(COMPILE_ARGS) -DVCD_PATH="\"$(PWD)/memory_ctrl/wave/memory_ctrl_tb_$(TIMESTAMP).vcd\""'

test-io:
	$(MAKE) clean
	$(MAKE) sim \
		MODULE=test_io_ctrl \
		TOPLEVEL=io_ctrl_tb \
		VERILOG_SOURCES="./io_ctrl/io_ctrl_tb.sv ../src/io_ctrl.sv" \
		PYTHONPATH=$(PWD)/io_ctrl \
		WAVES_DIR=$(PWD)/io_ctrl/wave \
		COMPILE_ARGS='$(COMPILE_ARGS) -DVCD_PATH="\"$(PWD)/io_ctrl/wave/io_ctrl_tb_$(TIMESTAMP).vcd\""'

test-top:
	$(MAKE) clean
	$(MAKE) sim \
		MODULE=test_top_fft \
		TOPLEVEL=top_fft_tb \
		VERILOG_SOURCES="./top_fft/top_fft_tb.sv ../src/io_ctrl.sv" ../src/butterfly.sv ../src/display_ctrl.sv ../src/fft_engine.sv ../src/memory_ctrl.sv ../src/top_fft.sv\
		PYTHONPATH=$(PWD)/top_fft \
		WAVES_DIR=$(PWD)/top_fft/wave \
		COMPILE_ARGS='$(COMPILE_ARGS) -DVCD_PATH="\"$(PWD)/top_fft/wave/top_fft_tb_$(TIMESTAMP).vcd\""'

# Phony target for cleaning up
.PHONY: clean
clean::
	rm -rf sim_build* results.xml
# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim