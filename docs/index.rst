.. bytesize documentation master file, created by
   sphinx-quickstart on Fri Oct 23 18:52:05 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. xxx nice docs http://nose.readthedocs.org/en/latest/index.html
   http://pytest.org/latest/

.. module:: bytesize

Overview
========
Generate human-readable strings for quantities of bytes!

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
- **Binary and decimal units**: Choose between `binary IEC
  <https://en.wikipedia.org/wiki/Binary_prefix>`_ and decimal SI unit
  prefixes, or allow `bytesize` to guess *xxx ref*. The units are chosen
  automatically to keep the magnitude between 0 and 1,000 (or optionally 1,024
  for binary units). Units are your choice of abbreviated symbols or full
  names.
- **Pedantic**: The `long formatter <:func:`formatter`>`_ will omit a decimal
  point if and only if the quantity is exact. Approximations will never be
  greater than the actual value -- we use only integer math *xxx ref* to avoid
  floating point rounding errors.
- **Pint integration**: If installed, use pint_ to parse string representations,
  and allow formatting of any :class:`pint.Quantity` that converts to a whole
  number of ``'bytes'``.
- **Python 2/3**: supported and tested on Python 2.7+ and 3.4+.

>>> fmt(1000 * 1024**7 - 1)
'999.9 ZiB'
>>> fmt(1000 * 1024**7)
'1000 ZiB'
>>> fmt(1000 * 1024**7 + 1)
'0.976 YiB'

Installation
============

>>> pip install bytesize  # doctest: +SKIP

More information
================

.. toctree::
   :maxdepth: 1

   formatting
   reference

..
   * :ref:`genindex`
   * :ref:`modindex`
   * :ref:`search`

.. _`pint`: http://pint.readthedocs.org/
