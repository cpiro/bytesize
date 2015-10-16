from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from setuptools import setup, find_packages

# (hurry.filesize) A simple Python library for human readable file sizes (or anything sized in bytes).
# (hfilesize) Human Readable File Sizes
# (datasize) Python integer subclass to handle arithmetic and formatting of integers with data size units

# module docstring, readme.md, readthedocs (https://github.com/mtik00/obfuscator)
# travis, coverall

setup(
    name = 'bytesize',
    version = '0',
    packages = find_packages(),
    extras_require = {
        'pint': 'pint>=0.6'
    },

    # metadata for upload to PyPI
    author = "Chris Piro",
    author_email = "cpiro@cpiro.com",
    description = "xxx",
    license = "GPL",
    keywords = "byte size file data units parser formatter xxx",
    url = "xxx",
)
