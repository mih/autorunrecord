clean:
	rm -rf build dist

release-pypi:
	# better safe than sorry
	test ! -e dist
	python setup.py sdist
	python setup.py bdist_wheel --universal
	twine upload dist/*


.PHONY: clean release-pypi
