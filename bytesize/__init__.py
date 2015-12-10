from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *
from future.utils import PY2

import os
import sys
from fractions import Fraction
import decimal
import string

__all__ = ['Quantity', 'formatter', 'short_formatter']

if PY2:
    def is_string(ss):
        import __builtin__
        return (isinstance(ss, str) or            # `unicode` or `future.builtin.str`
                isinstance(ss, __builtin__.str))  # a real Python 2 `str`, from old code
else:
    def is_string(ss):
        return isinstance(ss, str)


class UnitNoExistError(RuntimeError):
    pass


class NeedPintForParsingError(RuntimeError):
    def __init__(self, value):
        msg = "Cannot parse {} {!r} as Quantity without Pint installed".format(type(value).__name__, value)
        super(NeedPintForParsingError, self).__init__(msg)


UNITS_TABLE = {
    1000: [  # decimal SI prefixes
        ('', ''),
        ('k', 'kilo'),
        ('M', 'mega'),
        ('G', 'giga'),
        ('T', 'tera'),
        ('P', 'peta'),
        ('E', 'exa'),
        ('Z', 'zetta'),
        ('Y', 'yotta'),
    ],
    1024: [  # binary IEC prefixes
        ('', ''),
        ('Ki', 'kibi'),
        ('Mi', 'mebi'),
        ('Gi', 'gibi'),
        ('Ti', 'tebi'),
        ('Pi', 'pebi'),
        ('Ei', 'exbi'),
        ('Zi', 'zebi'),
        ('Yi', 'yobi'),
    ],
}


class Quantity(int):
    """Represents a quantity of bytes, suitable for formatting.

    :param value: a non-negative, integral number of bytes. If pint_ is
                  available, `value` may also be specified as a
                  :class:`pint.Quantity` or a `str` to pass to
                  :class:`pint.Quantity`'s constructor.
    :type value: Integral or :class:`pint.Quantity` or str
    :raises TypeError: if `value` is not integral or is negative
    :raises NeedPintForParsingError: if `value` is a `str` and
                                     pint_ is not installed
    """

    def __new__(cls, value):
        orig_value = value

        if _ureg and is_string(value):
            value = _ureg(value)
        elif isinstance(value, float):
            if value.is_integer():
                value = int(value)
            else:
                raise TypeError("Value {} must be integral".format(orig_value))
        elif isinstance(value, Quantity):
            value = int(value)

        if _ureg and isinstance(value, pint.quantity._Quantity):
            assert value.magnitude >= 0
            bytes_f = value.to('byte').magnitude
            assert isinstance(bytes_f, int) or bytes_f.is_integer()
            value = int(bytes_f)
        elif isinstance(value, int):
            if value < 0:
                raise TypeError("Value {} must be non-negative".format(orig_value))
        elif is_string(value):
            raise NeedPintForParsingError(value)
        else:
            raise TypeError("Cannot parse {} {!r} as Quantity".format(type(orig_value).__name__, orig_value))

        return super(Quantity, cls).__new__(cls, value)

    def __int__(self):
        return int.__int__(self)

    def __add__(self, other):
        return Quantity(int(self) + other)

    def __radd__(self, other):
        return Quantity(other + int(self))

    def __sub__(self, other):
        return Quantity(int(self) - other)

    def __rsub__(self, other):
        return Quantity(other - int(self))

    def __mul__(self, other):
        return Quantity(int(self) * other)

    def __rmul__(self, other):
        return Quantity(other * int(self))

    # regular division is not overloaded

    def __floordiv__(self, other):
        return Quantity(int(self) // other)

    def __rfloordiv__(self, other):
        return Quantity(other // int(self))

    def __eq__(self, other):
        return int(self) == other

    def __lt__(self, other):
        if type(other) != Quantity:
            raise TypeError("unorderable types: {}() < {}()".format(type(self).__name__, type(other).__name__))
        return int(self) < int(other)

    def __le__(self, other):
        if type(other) != Quantity:
            raise TypeError("unorderable types: {}() <= {}()".format(type(self).__name__, type(other).__name__))
        return int(self) <= int(other)

    def __gt__(self, other):
        if type(other) != Quantity:
            raise TypeError("unorderable types: {}() > {}()".format(type(self).__name__, type(other).__name__))
        return int(self) > int(other)

    def __ge__(self, other):
        if type(other) != Quantity:
            raise TypeError("unorderable types: {}() >= {}()".format(type(self).__name__, type(other).__name__))
        return int(self) >= int(other)

    def __str__(self):
        return self.__format__('')

    def __repr__(self):
        return '<Quantity {}>'.format(int(self))

    def __format__(self, spec):
        fill, align, string_width, precision, type_ = Quantity.parse_spec(spec)
        base, short, long_opts = self.format_options(fill, align, string_width, precision, type_)

        if short:
            units_width = 1 if base == 1000 else 2
            number, units = self.short_humanize(base=base, tolerance=0.01)
        else:
            cutoff, digits_width, units_width, abbrev = long_opts
            number, units = self.humanize(base=base, cutoff=cutoff, digits=digits_width, abbrev=abbrev)

        return Quantity.string_format(number, units, fill, align, string_width, units_width, short)

    def humanize(self, base=1024, cutoff=1000, digits=5, abbrev=True):
        assert base >= cutoff
        assert digits >= 5

        qq, exp = _Quotient.division(int(self), base=base, cutoff=cutoff)

        def units():
            plural = qq != 1
            try:
                prefix = UNITS_TABLE[base][exp][0 if abbrev else 1]
                base_unit = 'B' if abbrev else ('bytes' if plural else 'byte')
                return prefix + base_unit
            except IndexError:
                pass
            raise UnitNoExistError()

        if qq.exact:
            return str(qq.numerator), units()
        else:
            return qq.decimalize(digits), units()

    def short_humanize(self, base=None, tolerance=0.01):
        if base is None:
            base = self.guess_base(tolerance=tolerance)
            base_was_guessed = True
        else:
            base_was_guessed = False

        qq, exp = _Quotient.division(int(self), base=base, cutoff=1000)

        def units():
            try:
                return UNITS_TABLE[base][exp][0] or 'B'
            except IndexError:
                pass
            raise UnitNoExistError()

        if qq.exact or (base == 1000 and base_was_guessed):
            return str(qq.whole_part), units()
        elif qq < 100:
            return qq.decimalize(4), units()
        else:
            return str(qq.whole_part), units()

    def guess_base(self, tolerance=0):
        # guess base 1000 vs. 1024. if 1000 is exact or slightly above exact
        # (like HDD capacities), round down and call it 'exact'. otherwise use
        # base 1024

        qq, exp = _Quotient.division(int(self), base=1000, cutoff=1000)

        return 1000 if qq.fractional_part <= tolerance else 1024

    def format_options(self, fill, align, string_width, precision, type_):
        type_pref = None
        abbrev = True
        short = False
        for code in type_:
            if (code == 'd' or  # decimal
                code == 'i' or  # binary
                code == 'a'):   # automatic
                if type_pref:
                    raise ValueError("Format code must be at most one of 'a', 'd', or 'i'")
                type_pref = code
            elif code == 's':
                short = True

            elif code == 'l':
                abbrev = False
            else:
                raise ValueError("Unknown format code '{}' for object of type 'bytesize.Quantity'".format(code))

        if short and not abbrev:
            raise ValueError("Format code must contain at most one of 's' or 'l'")

        if type_pref is None:
            type_pref = 'a' if short else 'i'

        if type_pref == 'i':
            base = 1024
        elif type_pref == 'd':
            base = 1000
        elif type_pref == 'a':
            base = None

        if short:
            return base, short, None

        else:
            if base is None:
                base = self.guess_base()

            binary = base == 1024

            # "precision" from spec is the width of the number itself (including the dot)
            digits_width = precision if precision is not None and precision > 5 else 5

            if abbrev:
                units_width = len('YiB') if binary else len('YB')
            else:
                units_width = len('yobibytes') if binary else len('yottabytes')

            cutoff = 1024 if binary and digits_width > 5 else 1000

            return base, short, (cutoff, digits_width, units_width, abbrev)

    @staticmethod
    def string_format(number, units, fill=None, align=None, string_width=None, units_width=None, short=None):
        if string_width is not None and align is None:
            align = '='

        if align == '=':
            # right pad so units will line up
            units += (fill if fill is not None else ' ') * (units_width - len(units))

        def fa_spec():
            if align is None:
                assert fill is None
                return ''
            elif align == '=':
                # '=' align here means align on the units,
                # which we've accounted for above
                return (fill if fill is not None else '') + '>'
            else:
                return (fill if fill is not None else '') + align

        width_spec = str(string_width) if string_width is not None else ''
        return "{:{fa_spec}{width_spec}}".format(
            number + ('' if short else ' ') + units,
            fa_spec=fa_spec(),
            width_spec=width_spec)

    @staticmethod
    def parse_spec(spec):
        # see formatting.rst

        # static int
        # parse_internal_render_format_spec(PyObject *format_spec,
        #                                   Py_ssize_t start, Py_ssize_t end,
        #                                   InternalFormatSpec *format,
        #                                   char default_type,
        #                                   char default_align)
        # { ...

        def is_alignment_token(t):
            return t in '<>=^'

        pos, end = 0, len(spec)

        fill_char = ' '                        # format->fill_char = ' ';
        fill_char_specified = False            # format->align = default_align;
        align = '>'  # default                 # format->alternate = 0;
        align_specified = False                # format->sign = '\0';
        # alternate = 0                        # format->width = -1;
        # sign = ''                            # format->thousands_separators = 0;
        width = -1                             # format->precision = -1;
        # thousands_separators = 0             # format->type = default_type;
        precision = -1
        type_ = ''

        ## If the second char is an alignment token, then parse the fill char
        if (end-pos >= 2 and                   # if (end-pos >= 2 &&
            is_alignment_token(spec[pos+1])):  #     is_alignment_token(READ_spec(pos+1))) {
            align = spec[pos+1]                #     format->align = READ_spec(pos+1);
            fill_char = spec[pos]              #     format->fill_char = READ_spec(pos);
            fill_char_specified = True         #     fill_char_specified = 1;
            align_specified = True             #     align_specified = 1;
            pos += 2                           #     pos += 2;
                                               # }
        elif (end-pos >= 1 and                 # else if (end-pos >= 1 &&
              is_alignment_token(spec[pos])):  #          is_alignment_token(READ_spec(pos))) {
            align = spec[pos]                  #     format->align = READ_spec(pos);
            align_specified = True             #     align_specified = 1;
            pos += 1                           #     ++pos;
                                               # }
        ## Parse the various sign options
        ## (not implemented)
        #                                      # if (end-pos >= 1 && is_sign_element(READ_spec(pos))) {
        #                                      #     format->sign = READ_spec(pos);
        #                                      #     ++pos;
        #                                      # }

        ## If the next character is '#', we're in alternate mode. This only
        ## applies to integers.
        ## (not implemented)
        #                                      # if (end-pos >= 1 && READ_spec(pos) == '#') {
        #                                      #     format->alternate = 1;
        #                                      #     ++pos;
        #                                      # }

        ## The special case for 0-padding (backwards compat)
        if (not fill_char_specified and        # if (!fill_char_specified &&
            end-pos >= 1 and                   #       end-pos >= 1 &&
            spec[pos] == '0'):                 #       READ_spec(pos) == '0') {
            fill_char = '0'                    #     format->fill_char = '0';
            if not align_specified:            #     if (!align_specified) {
                align = '='                    #         format->align = '=';
                pos += 1                       #     }
                                               #     ++pos;
                                               # }
        consumed = 0                           # consumed = get_integer(...);
        while (end-pos > 0 and                 # if (consumed == -1)
               spec[pos] in string.digits):    #     /* Overflow error. Exception already set. */
            consumed += 1                      #     return 0;
            pos += 1                           # /* If consumed is 0, we didn't consume any characters for the
                                               #    width. In that case, reset the width to -1, because
        if consumed == 0:                      #    get_integer() will have set it to zero. -1 is how we record
            width = -1                         #    that the width wasn't specified. */
        else:                                  # if (consumed == 0)
            width = int(spec[pos-consumed:pos])#     format->width = -1;

        ## Comma signifies add thousands separators
        ## (not implemented)
        #if end-pos != 0 and spec[pos] == ',':  # if (end-pos && READ_spec(pos) == ',') {
        #    thousands_separators = 1           #     format->thousands_separators = 1;
        #    pos += 1                           #     ++pos;
        #                                       # }

        ## Parse field precision
        if end-pos != 0 and spec[pos] == '.':            # if (end-pos && READ_spec(pos) == '.') {
            pos += 1                                     #     ++pos;
            consumed = 0                                 #     consumed = get_integer(...);
            while (end-pos > 0 and                       #     if (consumed == -1)
                   spec[pos] in string.digits):          #         /* Overflow error. Exception already set. */
                consumed += 1                            #         return 0;
                pos += 1                                 #     /* Not having a precision after a dot is an error. */
                                                         #     if (consumed == 0) {
            if consumed == 0:                            #         PyErr_Format(PyExc_ValueError, ...);
                raise ValueError("Format specifier missing precision")
            else:                                        #         return 0;
                precision = int(spec[pos-consumed:pos])  #     }
                                                         # }
        ## Finally, parse the type field.
        ## (This limits to at most one type. Let's allow more)
        # if end-pos > 1:                                  # if (end-pos > 1) {
        #     # more than one char remains                 #     PyErr_Format(PyExc_ValueError, ...);
        #     raise ValueError("Invalid format specifier") #     return 0;
        #                                                  # }
        # if end-pos == 1:                                 # if (end-pos == 1) {
        #     type_ = spec[pos]                            #     format->type = READ_spec(pos);
        #     pos +=1                                      #     ++pos;
        #                                                  # }
        type_ = spec[pos:]

        ## Do as much validating as we can, just by looking at the format
        ## specifier.  Do not take into account what type of formatting
        ## we're doing (int, float, string).
        ## (not implemented)
        # if thousands_separators:                      # if (format->thousands_separators) {
        #     if type_ is None or type_ in 'defgEG%F':  #     switch (format->type) {
        #         pass  # ok                            #     case 'd': case 'e': case 'f': case 'g': case 'E':
        #     else:                                     #     case 'G': case '%': case 'F': case '\0':
        #         pass  # invalid comma type            #         /* These are allowed. See PEP 378.*/
        #                                               #         break;
        #                                               #     default:
        #                                               #         invalid_comma_type(format->type);
        #                                               #         return 0;
        #                                               #     }
        #                                               # }

        return (fill_char if fill_char_specified else None,
                align if align_specified else None,
                width if width != -1 else None,
                precision if precision != -1 else None,
                type_)

    @staticmethod
    def unparse_spec(fill, align, width, precision, type_):
        return ((fill if fill is not None else '') +
                (align if align is not None else '') +
                (str(width) if width is not None else '') +
                ('.' + str(precision) if precision is not None else '') +
                type_)


def formatter(base=1024, cutoff=1000, digits=5, abbrev=True):
    """Return a function that formats quantities of bytes.

    xxx principles

    >>> fmt = formatter()
    >>> fmt(1400605)
    '1.335 MiB'

    .. _formatter:

    :param base: 1000 to use decimal SI units, or 1024 to use binary IEC units
    :param cutoff: the highest allowable formatted number. Must be either
                   1000 or 1024, and less than or equal to `base`
    :return: a function from values to strings

    """
    if not base in (1000, 1024):
        raise ValueError("base must be 1000 or 1024 if specified")
    if not cutoff in (1000, 1024):
        raise ValueError("cutoff must be 1000 or 1024 if specified")
    if not base >= cutoff:
        raise ValueError("base must be greater than or equal to cutoff")
    if not (digits >= 5 and isinstance(digits, int)):
        raise ValueError("digits must be integral at least 5")
    if not abbrev in (True, False):
        raise ValueError("abbrev must be boolean")

    def inner(value):
        number, units = Quantity(value).humanize(
            base=base, cutoff=cutoff, digits=digits, abbrev=abbrev)
        result = Quantity.string_format(number, units)
        return result
    return inner


def short_formatter(tolerance=None, base=None):
    """Return a function that formats quantities of bytes.

    xxx principles, drag text out of param text

    >>> fmt = short_formatter()
    >>> fmt(1400605)
    '1.33Mi'
    >>> fmt(2000398934016)
    '2T'
    >>> short_formatter(base=1024)(2000398934016)
    '1.81Ti'

    :param tolerance float: If `base` is not specified and `value` is less
                            than `tolerance` times more than a whole number of
                            decimal units, round down to that number and use
                            decimal units, otherwise, use binary units. If
                            `tolerance` is zero, only use decimal units when
                            exact. If specified must be between 0 and 1, and
                            defaults to 0.01.
    :param base int: If 1024, use binary units. If 1000, use decimal units.

    :return: a function from values to strings

    """
    if not (tolerance is None or (0.0 <= tolerance and tolerance <= 1.0)):
        raise ValueError("tolerance must be between 0.0 and 1.0 if specified")
    if not (tolerance is None or base is None):
        raise ValueError("At most one of 'tolerance' and 'base' can be specified")
    if not base in (None, 1000, 1024):
        raise ValueError("base must be 1000 or 1024 if specified")

    if tolerance is None:
       tolerance = 0.01

    def inner(value):
        number, units = Quantity(value).short_humanize(base=base, tolerance=tolerance)
        return str(number) + units
    return inner


class _Quotient(Fraction):
    @staticmethod
    def division(value, base=1024, cutoff=1000):
        assert base in (1000, 1024)
        assert cutoff in (1000, 1024)

        qq = Fraction(numerator=value)
        exp = 0
        while qq >= cutoff:
            exp += 1
            qq /= base
            if base > cutoff and qq == cutoff:
                break

        return _Quotient(qq), exp

    @property
    def exact(self):
        return self.denominator == 1

    @property
    def whole_part(self):
        return self // 1

    @property
    def fractional_part(self):
        return self - self // 1

    def decimalize(self, length):
        D = decimal.Decimal
        with decimal.localcontext() as ctx:
            ctx.prec = length + 2
            ctx.rounding = decimal.ROUND_DOWN
            n = D(self.numerator) / D(self.denominator)
            return str(n)[0:length]


_ureg = None
"""This module's unique unit registry.

When pint_ is available, `bytesize` defines a unit registry containing only
the units ``bit = b`` and ``byte = B``. It can parse human-readable `str`s
into :class:`pint.Quantity` values. See the pint_ documentation for more
information.

For your convenience, :class:`bytesize.Quantity` will use `_ureg` implicitly
to parse `str` values when pint_ is installed, so you probably don't need to
use this directly.

>>> _ureg('10000 B')
<pint.Quantity(10000, 'byte')>
>>> _ureg('200 MiB') + _ureg('600 MiB')
<Quantity(800, 'mebibyte')>
>>> '{:ld}'.format(Quantity('500000 bytes'))
'500 kilobytes'
"""

def _add_pint_definitions(ureg):
    ureg.define("bit = [data] = b")
    ureg.define("byte = 8 bit = B")
    for base, subtable in UNITS_TABLE.items():
        for exp, (abbrev, prefix) in enumerate(subtable):
            if exp != 0:
                ureg.define('{}- = {}**{} = {}-'.format(prefix, base, exp, abbrev))


try:
    import pint
    _ureg = pint.UnitRegistry('/dev/null')
    _add_pint_definitions(_ureg)
except ImportError:
    pass
