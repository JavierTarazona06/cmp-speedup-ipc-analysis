GEM5 ?= /home/g/gbusnot/ES201/tools/TP5/gem5-stable
N ?= 2
T ?= 2
SIZE ?= 64
BINARY ?= ./test_omp
OUTDIR ?= results/$(N)_t$(T)_s$(SIZE)

GEM5_BIN := $(GEM5)/build/ARM/gem5.fast
SE_SCRIPT := $(GEM5)/configs/example/se.py

.PHONY: run results help

run: results
	$(GEM5_BIN) \
		--outdir=$(OUTDIR) \
		$(SE_SCRIPT) \
		--num-cpus=$(N) \
		-c $(BINARY) \
		-o "$(T) $(SIZE)"

results:
	mkdir -p results

help:
	@echo "Usage:"
	@echo "  make run GEM5=/path/to/gem5-stable N=2 T=2 SIZE=64"
	@echo ""
	@echo "Defaults:"
	@echo "  GEM5=$(GEM5)"
	@echo "  N=$(N), T=$(T), SIZE=$(SIZE)"
	@echo "  BINARY=$(BINARY)"
	@echo "  OUTDIR=$(OUTDIR)"
