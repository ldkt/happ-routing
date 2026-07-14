.PHONY: build configs test clean

build:
	./scripts/build.sh

configs:
	python3 scripts/generate_configs.py

test:
	python3 -m unittest discover -s tests -v
	python3 scripts/validate.py --dist dist --allow-missing-dat

clean:
	rm -rf dist .cache
