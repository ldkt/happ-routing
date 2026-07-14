.PHONY: build configs keenetic test clean

PYTHON ?= python3

build:
	./scripts/build.sh

configs:
	$(PYTHON) scripts/generate_configs.py

keenetic:
	$(PYTHON) scripts/generate_keenetic.py

test:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) scripts/validate.py --dist dist --allow-missing-dat

clean:
	rm -rf dist .cache
