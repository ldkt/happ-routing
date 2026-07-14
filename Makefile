.PHONY: build configs test clean

PYTHON ?= python3

build:
	./scripts/build.sh

configs:
	$(PYTHON) scripts/generate_configs.py

test:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) scripts/validate.py --dist dist --allow-missing-dat

clean:
	rm -rf dist .cache
