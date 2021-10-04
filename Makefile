lint:
	flake8 ./

test:
	coverage run test.py
	coverage report -m

ship:
	rm -rf build/
	rm -rf dist/
	python setup.py sdist bdist_wheel
	twine upload dist/* --skip-existing

.PHONY: lint test ship
