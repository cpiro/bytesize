.. bytesize documentation master file, created by
   sphinx-quickstart on Fri Oct 23 18:52:05 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to bytesize's documentation!
====================================

Contents:

.. toctree::
   :maxdepth: 2

Format Specification Mini-Language
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Format specifiers for :class:`bytesize.Quantity` are similar to Python's
built-in numerics, and control how values are presented.

.. productionlist::
   format_spec: [[`fill`]`align`][`width`][.`precision`][`type`]
   fill: <any character>
   align: "<" | ">" | "=" | "^"
   width: `integer`
   precision: `integer`
   type: "i" | "d" | "a" | "l"

*width* is a whole number defining the minimum field width. If not specified,
then the field width will be determined by the content.

*precision* is a whole number specifying the maximum length of the numeric
portion of the representation, including any decimal point. The default
is 5. If *precision* is specified and less than 5, the default is used. For a
shorter alternative, see :func:`bytesize.short_formatter`.

*type* determines how the unit labels should be presented:

   +---------+----------------------------------------------------------+
   | Type    | Meaning                                                  |
   +=========+==========================================================+
   | ``'i'`` | Use binary IEC units. This is the default.               |
   +---------+----------------------------------------------------------+
   | ``'d'`` | Use decimal SI units.                                    |
   +---------+----------------------------------------------------------+
   | ``'a'`` | Automatic: use binary units unless the quantity is       |
   |         | a whole number of some decimal unit, then use decimal    |
   |         | units.                                                   |
   +---------+----------------------------------------------------------+
   | ``'l'`` | Use long unit names. If absent, use abbreviated units.   |
   +---------+----------------------------------------------------------+

If a valid *align* value is specified, it can be preceded by a *fill*
character that can be any character and defaults to a space if omitted. The
alignment options are as follows:

   +---------+----------------------------------------------------------+
   | Option  | Meaning                                                  |
   +=========+==========================================================+
   | ``'='`` | The digits are right-aligned against the unit labels,    |
   |         | and the units are left-aligned and padded on the right   |
   |         | to the length of the longest unit label. This entire     |
   |         | field is right-aligned within the available space. This  |
   |         | has the effect of aligning the least significant digits  |
   |         | and first letters in the unit labels when                |
   |         | several are printed in a column.                         |
   |         | This is the default if a width is specified.             |
   +---------+----------------------------------------------------------+
   | ``'<'`` | Forces the field to be left-aligned within the available |
   |         | space.                                                   |
   +---------+----------------------------------------------------------+
   | ``'>'`` | Forces the field to be right-aligned within the          |
   |         | available space.                                         |
   +---------+----------------------------------------------------------+
   | ``'^'`` | Forces the field to be centered within the available     |
   |         | space.                                                   |
   +---------+----------------------------------------------------------+

https://en.wikipedia.org/wiki/Binary_prefix

Unlike built-in numerics, there is no ``','`` for specifying a thousands
separator, no signs, and no ``'#'`` for specifying "alternate form".


.. automodule:: bytesize
   :members:


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

