from setuptools import setup, find_packages

# (hurry.filesize) A simple Python library for human readable file sizes (or anything sized in bytes).
# (hfilesize) Human Readable File Sizes
# (datasize) Python integer subclass to handle arithmetic and formatting of integers with data size units
# (byteformat)

# module docstring, readme.md, readthedocs (https://github.com/mtik00/obfuscator)
# travis, coverall
# https://pypi.python.org/pypi/datasize/0.1 (model)
# https://github.com/pypa/pip (pypi badge)
# https://pypi.python.org/pypi/coverage (lots of badges)


setup(
    name = 'bytesize',
    version = '0.1',
    packages = ['bytesize'],
    extras_require = {
        'pint': 'pint>=0.6'
    },

    # metadata for upload to PyPI
    author = "Chris Piro",
    author_email = "cpiro@cpiro.com",
    description = "Generate human-readable string representations of quantities of bytes",
    license = "GPL",
    keywords = "byte size file data units formatter human pretty",
    url = "https://github.com/cpiro/bytesize",
    bugtrack_url = "https://github.com/cpiro/bytesize/issues",
)
