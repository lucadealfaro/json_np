.PHONY: clean venv test build deploy install-no-pip
clean:
	rm -rf venv
	rm -rf dist
	rm -rf json_np.egg-info
venv: clean
	python3 -m venv venv
	venv/bin/pip install ./
test: venv
	venv/bin/python tests.py
build: venv
	python3 -m pip install --upgrade build
	python3 -m pip install --upgrade twine
	python3 -m build
deploy: test build
	python3 -m twine upload dist/*
install-no-pip:
	python3 -m pip install ./
