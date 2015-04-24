#!/usr/bin/env python3

# xxx cli

# (hurry.filesize) A simple Python library for human readable file sizes (or anything sized in bytes).
# (hfilesize) Human Readable File Sizes

# module docstring, readme.md, readthedocs (https://github.com/mtik00/obfuscator)
# travis, coverall

# keywords: byte size file

# __version__ = "0.2a"
# __date__ = "2012-05-06"
# __author__ = "Steven D'Aprano"
# __author_email__ = "steve+python@pearwood.info"
#
# __all__ = ['format', 'ByteFormatter']

import os
import sys
import math
import string

class UnitNoExistError(RuntimeError):
    pass

class DifferentRegistryError(ValueError):
    def __init__(self, *args):
        if args is ():
            args = ("Cannot operate between quantities of different registries",)
        super().__init__(*args)

units_table = {
    1000: [
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
    1024: [
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
    def inner(value):
        # xxx width vs digits name, then **kwargs this
        kind, number, units = ByteQuantity(value).humanize(base=base, cutoff=cutoff, width=digits, abbrev=abbrev)
        result = ByteQuantity.string_format(kind, number, units)
        return result
    return inner

class ByteQuantity:
    def __init__(self, value):
        """Tries to interpret `value` as a number of bytes.
        Returns (int) number of bytes"""

        if ureg and isinstance(value, str):
            value = ureg(value)

        if ureg and isinstance(value, pint.quantity._Quantity):
            if value._REGISTRY is not ureg:
                raise DifferentRegistryError()
            assert value.magnitude >= 0
            bytes_f = value.to(ureg.byte).magnitude
            assert isinstance(bytes_f, int) or bytes_f.is_integer()
            self.value = int(bytes_f)
        else:
            assert isinstance(value, int)
            self.value = value

    def __int__(self):
        return self.value

    def __str__(self):
        return self.__format__('')

    def __repr__(self):
        return '<BytesQuantity {}>'.format(self.value)

    def __format__(self, spec):
        fill, align, string_width, precision, type_ = ByteQuantity.parse_spec(spec)
        base, cutoff, digits_width, units_width = ByteQuantity.format_options(fill, align, string_width, precision, type_)
        kind, number, units = self.humanize(base=base, cutoff=cutoff, width=digits_width)
        result = ByteQuantity.string_format(kind, number, units, fill, align, string_width, units_width)
        return result

    def humanize(self, base=1024, cutoff=1000, width=5, abbrev=True):
        """returns (kind, number, units)"""
        assert base in (1000, 1024)
        assert cutoff in (1000, 1024)
        assert base >= cutoff
        assert width >= 5

        sig, exp, rem = self.factor(base=base, cutoff=cutoff)

        def units(plural):
            try:
                prefix = units_table[base][exp][0 if abbrev else 1]
                base_unit = 'B' if abbrev else ('bytes' if plural else 'byte')
                return prefix + base_unit
            except IndexError:
                pass
            raise UnitNoExistError()

        if rem == 0:
            return 'exact', sig, units(sig != 1)  # "{:d} {}".format(sig, units)
        else:
            whole = "{:d}.".format(sig)
            digits = ByteQuantity.decimal_part(width - len(whole), rem, base, exp)
            number = whole + digits
            frac_quot = rem / base**exp
            assert len(number) == width

            return 'trunc', number, units(True)  # "{} {}".format(number, units)

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

        return "{:{fa_spec}{width_spec}}".format(
            "{} {}".format(number, units),
            fa_spec = fa_spec(),
            width_spec = str(string_width) if string_width is not None else '')

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
        align = '>' # default                  # format->alternate = 0;
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


def main():
    import pretty_capacity_tests
    pretty_capacity_tests.make_fudges()


### GLOBAL SCOPE


try:
    import pint
    ureg = pint.UnitRegistry('/dev/null')
    ureg.define("bit = [data] = b")
    ureg.define("byte = 8 bit = B")
    for base, subtable in units_table.items():
        for exp, (abbrev, prefix) in enumerate(subtable):
            if exp != 0:
                ureg.define('{}- = {}**{} = {}-'.format(prefix, base, exp, abbrev))

except ImportError:
    ureg = None

if __name__ == '__main__':
    main()
