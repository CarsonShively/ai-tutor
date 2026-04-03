ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
VENV := $(ROOT)ml-server/.venv
PY := $(VENV)/bin/python
UV := $(VENV)/bin/uv
STAMP := $(VENV)/installed

$(PY):
	python3 -m venv $(VENV)

$(UV): $(PY)
	$(PY) -m pip install uv

lock: $(UV)
	cd $(ROOT)ml-server && $(UV) lock

$(STAMP): $(ROOT)ml-server/uv.lock $(UV)
	cd $(ROOT)ml-server && $(UV) sync
	touch $(STAMP)

install: $(STAMP)