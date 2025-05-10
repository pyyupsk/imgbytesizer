build:
	python -m build

lint:
	flake8 imgbytesizer; vulture imgbytesizer