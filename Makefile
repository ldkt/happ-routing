.PHONY: build configs keenetic registry compare-registry coverage test clean

PYTHON ?= python3

build:
	./scripts/build.sh

configs:
	$(PYTHON) scripts/generate_configs.py

keenetic:
	$(PYTHON) scripts/generate_keenetic.py

registry:
	$(PYTHON) -m routing_engine.registry_cli summary

compare-registry:
	$(PYTHON) -m routing_engine.registry_cli compare

coverage:
	$(PYTHON) -m routing_engine.coverage

test:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) scripts/validate.py --dist dist --allow-missing-dat

clean:
	rm -rf dist .cache
