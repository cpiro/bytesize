.. bytesize documentation master file, created by
   sphinx-quickstart on Fri Oct 23 18:52:05 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. testsetup::

    import bytesize

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

.. xxx example of switching to a particular unit. we don't support that; just use pint

Features
========

Installation
============

>>> pip install bytesize  # doctest: +SKIP

Contribute
==========

- Source code: https://github.com/cpiro/bytesize
- Issues: https://github.com/cpiro/bytesize/issues

Contents
========

.. toctree::
   :maxdepth: 2

   formatting
   reference


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _`pint`: http://pint.readthedocs.org/
