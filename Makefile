.PHONY: build configs registry compare-registry test clean

PYTHON ?= python3

build:
	./scripts/build.sh

configs:
	$(PYTHON) scripts/generate_configs.py

registry:
	$(PYTHON) -m routing_engine.registry_cli summary

compare-registry:
	$(PYTHON) -m routing_engine.registry_cli compare

test:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) scripts/validate.py --dist dist --allow-missing-dat

clean:
	rm -rf dist .cache
