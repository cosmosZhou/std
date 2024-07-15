from setuptools import setup

if __name__ == "__main__":
    setup(package_data={'': [
        'lib/eigen.dll',
        'lib/libeigen.so',
        'assets/cn/segment/vocab.csv',
        'assets/jp/segment/vocab.csv',
    ]})

# usage of twine:
# pip install twine
# python setup.py install
# pip uninstall -y std.algorithm && pip install --upgrade --no-cache-dir std.algorithm
# pip install --upgrade --retries=50 std.algorithm -i https://pypi.Python.org/simple/