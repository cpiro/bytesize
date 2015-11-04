.. bytesize documentation master file, created by
   sphinx-quickstart on Fri Oct 23 18:52:05 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. xxx nice docs http://nose.readthedocs.org/en/latest/index.html
   http://pytest.org/latest/

.. module:: bytesize

Overview
========
Generate human-readable strings for quantities of bytes:

>>> import bytesize
>>> size = bytesize.Quantity('2 terabytes')
>>> "Device: {} ({})".format('sda', size)
'Device: sda (1.818 TiB)'

>>> fmt = bytesize.formatter()
>>> fmt(1400605)
'1.335 MiB'

If pint_ is installed, we support parsing strings like ``'100 megabytes'`` or
``'25 GiB'``. We also support values of :class:`pint.Quantity`, so long as
they convert to a whole number of ``'bytes'``.

Features
========
- **Binary and decimal units**: Choose between `binary IEC and decimal SI unit
  prefixes <https://en.wikipedia.org/wiki/Binary_prefix>`_, or allow
  *bytesize* to guess. The units are chosen automatically to keep the
  magnitude between 0 and 1,000 (or optionally 1,024 for binary units. Units
  are your choice of abbreviated symbols or full names.
- **Pedantic**: We omit a decimal point if and only if the quantity is
  exact. Approximations will never be greater than the actual value -- we use
  only integer math *xxx ref* to avoid floating point rounding errors.
- **  :pep:`3101`  xxx formatting language, tables
- **Operators**: arithmetic operators (except floating-point division) and
  comparison operators are defined
- **Pint integration**: If installed, use pint_ to parse string representations,
  and allow formatting of any :class:`pint.Quantity` that converts to a whole
  number of ``'bytes'``.
- **Python 2/3**: tested on Python 2.7+ and 3.4+.

Examples
========

  .. xxx short

>>> from bytesize import Quantity as Q
>>> "{0:i} | {0:d} | {0:a}".format(Q('2 TiB'))
'2 TiB | 2.199 TB | 2 TiB'

>>> "{0:i} | {0:d} | {0:a}".format(Q('2 TB'))
'1.818 TiB | 2 TB | 2 TB'

>>> for zeros in range(0, 7):
...     print("│ {0:16ld}╎{0:9d} │".format(Q(10**zeros)))
│     1 byte      ╎     1 B  │
│    10 bytes     ╎    10 B  │
│   100 bytes     ╎   100 B  │
│     1 kilobyte  ╎     1 kB │
│    10 kilobytes ╎    10 kB │
│   100 kilobytes ╎   100 kB │
│     1 megabyte  ╎     1 MB │

>>> fmt(1000 * 1024**7 - 1)
'999.9 ZiB'

>>> fmt(1000 * 1024**7)
'1000 ZiB'

>>> fmt(1000 * 1024**7 + 1)
'0.976 YiB'

>>> bytesize.formatter(cutoff=1024)(1000 * 1024**7 + 1)
'1000. ZiB'

Installation
============

>>> pip install bytesize  # doctest: +SKIP

More information
================

.. toctree::
   :maxdepth: 1

   formatting
   reference

*bytesize* is released under terms of `Apache 2.0 License <http://opensource.org/licenses/Apache-2.0>`_.

..
   * :ref:`genindex`
   * :ref:`modindex`
   * :ref:`search`

.. _`pint`: http://pint.readthedocs.org/
