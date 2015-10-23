from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *
from future.utils import PY2

import os
import sys
import math
import string

__all__ = ['formatter', 'short_formatter', 'Quantity']


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


class DifferentRegistryError(ValueError):
    def __init__(self, *args):
        if args is ():
            args = ("Cannot operate between quantities of different registries",)
        super(DifferentRegistryError, self).__init__(*args)


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


def formatter(base=1024, cutoff=1000, digits=5, abbrev=True):
    assert base in (1000, 1024)
    assert cutoff in (1000, 1024)
    assert base >= cutoff
    assert digits >= 5

    def inner(value):
        kind, number, units = Quantity(value).humanize(
            base=base, cutoff=cutoff, digits=digits, abbrev=abbrev)
        result = Quantity.string_format(kind, number, units)
        return result
    return inner


def short_formatter(try_metric=True, tolerance=0.01):
    def inner(value):
        kind, number, units = Quantity(value).short_humanize(
            try_metric=try_metric, tolerance=tolerance)
        return str(number) + units
    return inner


class Quantity(object):
    """Represents a quantity of bytes, suitable for formatting."""

    def __init__(self, value):
        """Interpret `value` as a number of bytes.

        If `value` is an `int`, this object represents that number of
        bytes.

        If `pint` is available, `value` may also be specified as a `pint`
        quantity or a `str` parsable by `pint` to a number of bytes.

        """
        if ureg and is_string(value):
            value = ureg(value)

        if ureg and isinstance(value, pint.quantity._Quantity):
            if value._REGISTRY is not ureg:
                raise DifferentRegistryError()
            assert value.magnitude >= 0
            bytes_f = value.to(ureg.byte).magnitude
            assert isinstance(bytes_f, int) or bytes_f.is_integer()
            self.value = int(bytes_f)
        elif isinstance(value, int):
            self.value = value
        else:
            raise NeedPintForParsingError(value)

    def __int__(self):
        return self.value

    def __str__(self):
        return self.__format__('')

    def __repr__(self):
        return '<Quantity {}>'.format(self.value)

    def __format__(self, spec):
        fill, align, string_width, precision, type_ = Quantity.parse_spec(spec)
        base, cutoff, digits_width, units_width = Quantity.format_options(fill, align, string_width, precision, type_)
        kind, number, units = self.humanize(base=base, cutoff=cutoff, digits=digits_width)
        result = Quantity.string_format(kind, number, units, fill, align, string_width, units_width)
        return result

    def humanize(self, base=1024, cutoff=1000, digits=5, abbrev=True):
        """returns (kind, number, units)"""
        assert base in (1000, 1024)
        assert cutoff in (1000, 1024)
        assert base >= cutoff
        assert digits >= 5

        sig, exp, rem = self.factor(base=base, cutoff=cutoff)

        def units(plural):
            try:
                prefix = UNITS_TABLE[base][exp][0 if abbrev else 1]
                base_unit = 'B' if abbrev else ('bytes' if plural else 'byte')
                return prefix + base_unit
            except IndexError:
                pass
            raise UnitNoExistError()

        if rem == 0:
            return 'exact', sig, units(sig != 1)  # "{:d} {}".format(sig, units)
        else:
            whole_str = "{:d}.".format(sig)
            digits_str = Quantity.decimal_part(digits - len(whole_str), rem, base, exp)
            number_str = whole_str + digits_str
            frac_quot = rem / base**exp
            assert len(number_str) == digits

            return 'trunc', number_str, units(True)  # "{} {}".format(number, units)

    def short_humanize(self, try_metric=True, tolerance=0.01):
        cutoff = 1000

        # guess base 1000 vs. 1024. if 1000 is exact or slightly above exact
        # (like HDD capacities), round down and call it 'exact'. otherwise use
        # base 1024
        base = None
        if try_metric:
            sig10, exp10, rem10 = self.factor(base=1000, cutoff=cutoff)
            if rem10 < tolerance * (1000**exp10):
                base = 1000
                sig, exp, rem = sig10, exp10, 0

        if base is None:
            base = 1024
            sig, exp, rem = self.factor(base=1024, cutoff=cutoff)

        def units(plural):
            try:
                return UNITS_TABLE[base][exp][0]
            except IndexError:
                pass
            raise UnitNoExistError()

        if rem == 0:
            return 'exact', sig, units(True)
        elif sig < 100:
            whole = "{}.".format(sig)
            digits = Quantity.decimal_part(4-len(whole), rem, base, exp)
            number = whole + digits
            frac_quot = rem / base**exp
            return 'trunc', number, units(True)
        else:
            return 'trunc', sig, units(True)

    def factor(self, base, cutoff):
        """Solves for (sig, exp, rem) where:
              sig * base**exp + rem == self.value
              sig < cutoff
        """
        sig, exp, rem = self.value, 0, 0
        while sig >= cutoff:
            exp += 1
            sig, new_rem = divmod(sig, base)
            rem += new_rem * (base**(exp-1))
            if rem == 0 and sig == cutoff and base > cutoff:
                break  # is exactly the cutoff amount (when base > cutoff)
        return sig, exp, rem

    @staticmethod
    def decimal_part(places, rem, base, exp):
        digits = ''
        while len(digits) < places:
            digit, rem = divmod(10 * rem, base**exp)
            digits += '%0d' % (digit,)
        return digits

    @staticmethod
    def format_options(fill, align, string_width, precision, type_):
        metric = 'm' in type_
        traditional = 't' in type_
        if metric and traditional:
            raise ValueError("at most one of 'm' and 't'")

        # "precision" from spec is the width of the number itself (including the dot)
        digits_width = precision if precision is not None and precision > 5 else 5
        units_width = 2 if metric else 3
        base = 1000 if metric else 1024
        cutoff = 1000 if metric or digits_width <= 5 else 1024

        return base, cutoff, digits_width, units_width

    @staticmethod
    def string_format(kind, number, units, fill=None, align=None, string_width=None, units_width=None):
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
            "{} {}".format(number, units),
            fa_spec=fa_spec(),
            width_spec=width_spec)

    @staticmethod
    def parse_spec(spec):
        # minimum precision is 5
        # width should be at least 9 (for precision of 5) to avoid overflowing

        # format_spec ::=  [[fill]align][width][.precision][type+]
        # fill        ::=  <any character>
        # align       ::=  "<" | ">" | "=" | "^"
        # width       ::=  integer
        # precision   ::=  integer
        # type        ::=  xxx

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


try:
    import pint
    ureg = pint.UnitRegistry('/dev/null')
    ureg.define("bit = [data] = b")
    ureg.define("byte = 8 bit = B")
    for base, subtable in UNITS_TABLE.items():
        for exp, (abbrev, prefix) in enumerate(subtable):
            if exp != 0:
                ureg.define('{}- = {}**{} = {}-'.format(prefix, base, exp, abbrev))
except ImportError:
    ureg = None
