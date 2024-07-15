mkdir -p dist
twine_exists=$(pip show twine)
if [[ -z "${twine_exists}" ]]; then
  echo "pip install twine"
  pip install twine
fi

rm -f dist/*.tar.gz && python setup.py sdist && twine upload -r nexus dist/*.tar.gz
