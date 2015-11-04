==================================
Format specification mini-language
==================================

.. module:: bytesize

Format specifiers for :class:`Quantity` are similar to those for
:ref:`Python's built-in numeric types <python:formatspec>`.

.. productionlist::
   format_spec: [[`fill`]`align`][`width`][.`precision`][`type`]
   fill: <any character>
   align: "<" | ">" | "=" | "^"
   width: `integer`
   precision: `integer`
   type: "i" | "d" | "a" | "l"

*width* is a whole number defining the minimum field width. If not specified,
then the field width will be determined by the content. To avoid overflow,
*width* should be at least *precision* plus the length of the longest unit
name plus one (for the space), for example, at least 9 for abbreviated binary
units.

*precision* is a whole number specifying the maximum length of the numeric
portion of the representation, including any decimal point. The default
is 5. If *precision* is specified and less than 5, the default is used. For a
shorter alternative, see :func:`short_formatter`.

*type* determines how the unit symbols should be presented:

   +---------+----------------------------------------------------------+
   | Type    | Meaning                                                  |
   +=========+==========================================================+
   | ``'i'`` | Use binary IEC unit prefixes. This is the default.       |
   +---------+----------------------------------------------------------+
   | ``'d'`` | Use decimal SI unit prefixes.                            |
   +---------+----------------------------------------------------------+
   | ``'a'`` | Automatic: use binary units unless the quantity is       |
   |         | a whole number of some decimal unit, then use decimal    |
   |         | units.                                                   |
   +---------+----------------------------------------------------------+
   | ``'l'`` | Use long unit names. If absent, use abbreviations.       |
   +---------+----------------------------------------------------------+

Unit symbols are presented according to
`Wikipedia:Binary prefix <https://en.wikipedia.org/wiki/Binary_prefix>`_.

If a valid *align* value is specified, it can be preceded by a *fill*
character that can be any character and defaults to a space if omitted. The
alignment options are as follows:

   +---------+----------------------------------------------------------+
   | Option  | Meaning                                                  |
   +=========+==========================================================+
   | ``'='`` | The digits are right-aligned against the unit symbols,   |
   |         | and the units are left-aligned and padded on the right   |
   |         | to the length of the longest unit symbol. This entire    |
   |         | field is right-aligned within the available space. This  |
   |         | has the effect of aligning the least significant digits  |
   |         | and first letters in the unit symbols when               |
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

Note that, unlike built-in numerics, there is no ``','`` for specifying a
thousands separator, no signs, and no ``'#'`` for specifying "alternate form".

