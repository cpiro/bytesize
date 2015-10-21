# python test.py make_fudges

from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *

import sys
from nose.tools import *

import bytesize as bs

def pp(*args, **kwargs):
    return bs.formatter(**kwargs)(*args)

if bs.ureg:
    def undefine_ureg():
        bs._saved_ureg = bs.ureg
        bs.ureg = None
    def redefine_ureg():
        bs.ureg = bs._saved_ureg
        bs._saved_ureg = None

    @with_setup(undefine_ureg, redefine_ureg)
    def test_no_ureg():
        assert bs.ureg is None
        assert pp(0) == '0 B'

    def test_has_ureg():
        assert bs.ureg

    @raises(bs.DifferentRegistryError)
    def test_different_registry():
        other_ureg = bs.pint.UnitRegistry()
        pp(other_ureg('10 bytes'))

    def test_hands():
        assert pp(0) == '0 B'
        assert pp(-0) == '0 B'
        assert pp('-0 B') == '0 B'

        data = [
            ('10230 B', '9.990 KiB'),
            ('11366 B', '11.09 KiB'),
            ('102391 B', '99.99 KiB'),
            ('999 KiB', '999 KiB'),
            ('1000 KiB', '1000 KiB'),
            ('1001 KiB', '0.977 MiB'),
            ('1023 KiB', '0.999 MiB'),
            ('1024 KiB', '1 MiB'),
            ('1025 KiB', '1.000 MiB'),
            ('1099511000000 B', '0.999 TiB'),
            ('1 TiB', '1 TiB'),
            ('24008 B', '23.44 KiB'),
        ]
        def check_direct(b, result):
            assert pp(b) == result
            assert pp(bs.ureg(b)) == result

        for b, result in data:
            yield check_direct, b, result

@raises(ValueError)
def test_format_mt_mutex():
    '{:mt}'.format(bs.Quantity(10000))

def test_parse_spec():
    def reversible(spec_tuple):
        spec = bs.Quantity.unparse_spec(*spec_tuple)
        assert spec_tuple == bs.Quantity.parse_spec(spec)

    def basic(spec_tuple, values):
        spec = bs.Quantity.unparse_spec(*spec_tuple)
        fill, align, width, precision, type_ = spec_tuple
        format_str = '{:' + spec + '}'

        flo = ''  # format_str.format(100.123)
        print("\n{:13} {}".format(format_str, flo))

        for value in values:
            byt = format_str.format(value)

            if align is not None and width is not None:
                if precision is None and width >= 9:
                    assert len(byt) == width
                else:
                    assert len(byt) >= width

            print("{:13} {!r}".format('', byt))

    values = [bs.Quantity(k) for k in (1, 999, 1023, 102526)]

    for spec_tuple in parse_spec_cases:
        yield reversible, spec_tuple
        yield basic, spec_tuple, values

parse_spec_cases = [
    (fill, align, width, precision, type_)
    for fill in (None, ' ')
    for align in (None, '>', '<', '=', '^')
    for width in (None, 6, 10, 15)
    for precision in (None, 5, 6, 7, 8, 9, 10, 11)
    for type_ in ('', 't', 'm') #, ' ', '=', '.', '0', '>')
    if not (fill is not None and align is None)
]

def test_fudges():
    def check_formatter(b, result, fmt):
        assert fmt(b) == result

    def check_guts(b, result, kwargs):
        base, cutoff = kwargs['base'], kwargs['cutoff']
        sig, exp, rem = bs.Quantity(b).factor(base=base, cutoff=cutoff)
        assert b == sig * base**exp + rem
        assert sig < cutoff or (sig == cutoff and base > cutoff)

        # decimal_part
        width = 5
        whole = "{:d}.".format(sig)
        places = width - len(whole)
        digits = bs.Quantity.decimal_part(places, rem, base, exp)
        assert isinstance(digits, str)  # sure

        # should be the same as the floating division
        digits_int = int(digits if digits != '' else 0)
        frac_lowerbound = float(digits_int) / float(10**places)
        frac_upperbound = float(digits_int + 1) / float(10**places)
        frac_quot = rem / base**exp

        assert frac_lowerbound <= frac_quot
        assert frac_quot <= frac_upperbound
        # ^^^ strictly less than unless frac_quot doesn't have precision enough to represent
        assert len(digits) == places
        assert ('.' in result) == (rem != 0), "there's a decimal dot iff the value is not exact"

    def check_reverse(b, result):
        """parse `result` back through pint, check that it's <= to the original,
        within truncation error
        """
        if bs.ureg:
            pint_bytes = bs.ureg(result).to('bytes').magnitude
            if isinstance(pint_bytes, float):
                assert 0.999 <= (pint_bytes / b) <= 1, "ureg(`result`) should be <= `b`, but not by too much"
            else:
                assert pint_bytes == b

    for b, results in fudge_cases:
        for result, kwargs in zip(results, kwargses):
            fmt = bs.formatter(**kwargs)
            if result is not None:
                yield check_formatter, b, result, fmt
                yield check_guts, b, result, kwargs
                yield check_reverse, b, result

def make_fudges():
    import pprint
    def safe_formatter(*args, **kwargs):
        fmt = bs.formatter(*args, **kwargs)
        def inner(value):
            try:
                return fmt(value)
            except bs.UnitNoExistError:
                return None
        return inner

    kwargses = [{'base': base, 'cutoff': cutoff, 'abbrev': abbrev}
                for abbrev in (True, False)
                for base, cutoff in ((1024, 1000), (1024, 1024), (1000, 1000))]

    cases = [
        10**dec *
        1024**exp +
        fudge
        for exp in range(0, 10)
        for dec in range(0, 4)
        for fudge in (-1, 0, 1)
    ] + [
        10**dec *
        1000**exp +
        fudge
        for exp in range(0, 10)
        for dec in range(0, 3)
        for fudge in (-1, 0, 1)
    ]

    print("kwargses = {}".format(pprint.pformat(kwargses)))
    print("fudge_cases = [")

    for case in cases:
        results = tuple(safe_formatter(**kwargs)(case) for kwargs in kwargses)
        if any(results):
            print("    ({}, {!r}),".format(case, results))

    print("]")


if __name__ == '__main__':
    if sys.argv[1:] == ['make_fudges']:
        make_fudges()

# data

kwargses = [{'abbrev': True, 'base': 1024, 'cutoff': 1000},
 {'abbrev': True, 'base': 1024, 'cutoff': 1024},
 {'abbrev': True, 'base': 1000, 'cutoff': 1000},
 {'abbrev': False, 'base': 1024, 'cutoff': 1000},
 {'abbrev': False, 'base': 1024, 'cutoff': 1024},
 {'abbrev': False, 'base': 1000, 'cutoff': 1000}]
fudge_cases = [
    (0, ('0 B', '0 B', '0 B', '0 bytes', '0 bytes', '0 bytes')),
    (1, ('1 B', '1 B', '1 B', '1 byte', '1 byte', '1 byte')),
    (2, ('2 B', '2 B', '2 B', '2 bytes', '2 bytes', '2 bytes')),
    (9, ('9 B', '9 B', '9 B', '9 bytes', '9 bytes', '9 bytes')),
    (10, ('10 B', '10 B', '10 B', '10 bytes', '10 bytes', '10 bytes')),
    (11, ('11 B', '11 B', '11 B', '11 bytes', '11 bytes', '11 bytes')),
    (99, ('99 B', '99 B', '99 B', '99 bytes', '99 bytes', '99 bytes')),
    (100, ('100 B', '100 B', '100 B', '100 bytes', '100 bytes', '100 bytes')),
    (101, ('101 B', '101 B', '101 B', '101 bytes', '101 bytes', '101 bytes')),
    (999, ('999 B', '999 B', '999 B', '999 bytes', '999 bytes', '999 bytes')),
    (1000, ('0.976 KiB', '1000 B', '1 kB', '0.976 kibibytes', '1000 bytes', '1 kilobyte')),
    (1001, ('0.977 KiB', '1001 B', '1.001 kB', '0.977 kibibytes', '1001 bytes', '1.001 kilobytes')),
    (1023, ('0.999 KiB', '1023 B', '1.023 kB', '0.999 kibibytes', '1023 bytes', '1.023 kilobytes')),
    (1024, ('1 KiB', '1 KiB', '1.024 kB', '1 kibibyte', '1 kibibyte', '1.024 kilobytes')),
    (1025, ('1.000 KiB', '1.000 KiB', '1.025 kB', '1.000 kibibytes', '1.000 kibibytes', '1.025 kilobytes')),
    (10239, ('9.999 KiB', '9.999 KiB', '10.23 kB', '9.999 kibibytes', '9.999 kibibytes', '10.23 kilobytes')),
    (10240, ('10 KiB', '10 KiB', '10.24 kB', '10 kibibytes', '10 kibibytes', '10.24 kilobytes')),
    (10241, ('10.00 KiB', '10.00 KiB', '10.24 kB', '10.00 kibibytes', '10.00 kibibytes', '10.24 kilobytes')),
    (102399, ('99.99 KiB', '99.99 KiB', '102.3 kB', '99.99 kibibytes', '99.99 kibibytes', '102.3 kilobytes')),
    (102400, ('100 KiB', '100 KiB', '102.4 kB', '100 kibibytes', '100 kibibytes', '102.4 kilobytes')),
    (102401, ('100.0 KiB', '100.0 KiB', '102.4 kB', '100.0 kibibytes', '100.0 kibibytes', '102.4 kilobytes')),
    (1023999, ('999.9 KiB', '999.9 KiB', '1.023 MB', '999.9 kibibytes', '999.9 kibibytes', '1.023 megabytes')),
    (1024000, ('1000 KiB', '1000 KiB', '1.024 MB', '1000 kibibytes', '1000 kibibytes', '1.024 megabytes')),
    (1024001, ('0.976 MiB', '1000. KiB', '1.024 MB', '0.976 mebibytes', '1000. kibibytes', '1.024 megabytes')),
    (1048575, ('0.999 MiB', '1023. KiB', '1.048 MB', '0.999 mebibytes', '1023. kibibytes', '1.048 megabytes')),
    (1048576, ('1 MiB', '1 MiB', '1.048 MB', '1 mebibyte', '1 mebibyte', '1.048 megabytes')),
    (1048577, ('1.000 MiB', '1.000 MiB', '1.048 MB', '1.000 mebibytes', '1.000 mebibytes', '1.048 megabytes')),
    (10485759, ('9.999 MiB', '9.999 MiB', '10.48 MB', '9.999 mebibytes', '9.999 mebibytes', '10.48 megabytes')),
    (10485760, ('10 MiB', '10 MiB', '10.48 MB', '10 mebibytes', '10 mebibytes', '10.48 megabytes')),
    (10485761, ('10.00 MiB', '10.00 MiB', '10.48 MB', '10.00 mebibytes', '10.00 mebibytes', '10.48 megabytes')),
    (104857599, ('99.99 MiB', '99.99 MiB', '104.8 MB', '99.99 mebibytes', '99.99 mebibytes', '104.8 megabytes')),
    (104857600, ('100 MiB', '100 MiB', '104.8 MB', '100 mebibytes', '100 mebibytes', '104.8 megabytes')),
    (104857601, ('100.0 MiB', '100.0 MiB', '104.8 MB', '100.0 mebibytes', '100.0 mebibytes', '104.8 megabytes')),
    (1048575999, ('999.9 MiB', '999.9 MiB', '1.048 GB', '999.9 mebibytes', '999.9 mebibytes', '1.048 gigabytes')),
    (1048576000, ('1000 MiB', '1000 MiB', '1.048 GB', '1000 mebibytes', '1000 mebibytes', '1.048 gigabytes')),
    (1048576001, ('0.976 GiB', '1000. MiB', '1.048 GB', '0.976 gibibytes', '1000. mebibytes', '1.048 gigabytes')),
    (1073741823, ('0.999 GiB', '1023. MiB', '1.073 GB', '0.999 gibibytes', '1023. mebibytes', '1.073 gigabytes')),
    (1073741824, ('1 GiB', '1 GiB', '1.073 GB', '1 gibibyte', '1 gibibyte', '1.073 gigabytes')),
    (1073741825, ('1.000 GiB', '1.000 GiB', '1.073 GB', '1.000 gibibytes', '1.000 gibibytes', '1.073 gigabytes')),
    (10737418239, ('9.999 GiB', '9.999 GiB', '10.73 GB', '9.999 gibibytes', '9.999 gibibytes', '10.73 gigabytes')),
    (10737418240, ('10 GiB', '10 GiB', '10.73 GB', '10 gibibytes', '10 gibibytes', '10.73 gigabytes')),
    (10737418241, ('10.00 GiB', '10.00 GiB', '10.73 GB', '10.00 gibibytes', '10.00 gibibytes', '10.73 gigabytes')),
    (107374182399, ('99.99 GiB', '99.99 GiB', '107.3 GB', '99.99 gibibytes', '99.99 gibibytes', '107.3 gigabytes')),
    (107374182400, ('100 GiB', '100 GiB', '107.3 GB', '100 gibibytes', '100 gibibytes', '107.3 gigabytes')),
    (107374182401, ('100.0 GiB', '100.0 GiB', '107.3 GB', '100.0 gibibytes', '100.0 gibibytes', '107.3 gigabytes')),
    (1073741823999, ('999.9 GiB', '999.9 GiB', '1.073 TB', '999.9 gibibytes', '999.9 gibibytes', '1.073 terabytes')),
    (1073741824000, ('1000 GiB', '1000 GiB', '1.073 TB', '1000 gibibytes', '1000 gibibytes', '1.073 terabytes')),
    (1073741824001, ('0.976 TiB', '1000. GiB', '1.073 TB', '0.976 tebibytes', '1000. gibibytes', '1.073 terabytes')),
    (1099511627775, ('0.999 TiB', '1023. GiB', '1.099 TB', '0.999 tebibytes', '1023. gibibytes', '1.099 terabytes')),
    (1099511627776, ('1 TiB', '1 TiB', '1.099 TB', '1 tebibyte', '1 tebibyte', '1.099 terabytes')),
    (1099511627777, ('1.000 TiB', '1.000 TiB', '1.099 TB', '1.000 tebibytes', '1.000 tebibytes', '1.099 terabytes')),
    (10995116277759, ('9.999 TiB', '9.999 TiB', '10.99 TB', '9.999 tebibytes', '9.999 tebibytes', '10.99 terabytes')),
    (10995116277760, ('10 TiB', '10 TiB', '10.99 TB', '10 tebibytes', '10 tebibytes', '10.99 terabytes')),
    (10995116277761, ('10.00 TiB', '10.00 TiB', '10.99 TB', '10.00 tebibytes', '10.00 tebibytes', '10.99 terabytes')),
    (109951162777599, ('99.99 TiB', '99.99 TiB', '109.9 TB', '99.99 tebibytes', '99.99 tebibytes', '109.9 terabytes')),
    (109951162777600, ('100 TiB', '100 TiB', '109.9 TB', '100 tebibytes', '100 tebibytes', '109.9 terabytes')),
    (109951162777601, ('100.0 TiB', '100.0 TiB', '109.9 TB', '100.0 tebibytes', '100.0 tebibytes', '109.9 terabytes')),
    (1099511627775999, ('999.9 TiB', '999.9 TiB', '1.099 PB', '999.9 tebibytes', '999.9 tebibytes', '1.099 petabytes')),
    (1099511627776000, ('1000 TiB', '1000 TiB', '1.099 PB', '1000 tebibytes', '1000 tebibytes', '1.099 petabytes')),
    (1099511627776001, ('0.976 PiB', '1000. TiB', '1.099 PB', '0.976 pebibytes', '1000. tebibytes', '1.099 petabytes')),
    (1125899906842623, ('0.999 PiB', '1023. TiB', '1.125 PB', '0.999 pebibytes', '1023. tebibytes', '1.125 petabytes')),
    (1125899906842624, ('1 PiB', '1 PiB', '1.125 PB', '1 pebibyte', '1 pebibyte', '1.125 petabytes')),
    (1125899906842625, ('1.000 PiB', '1.000 PiB', '1.125 PB', '1.000 pebibytes', '1.000 pebibytes', '1.125 petabytes')),
    (11258999068426239, ('9.999 PiB', '9.999 PiB', '11.25 PB', '9.999 pebibytes', '9.999 pebibytes', '11.25 petabytes')),
    (11258999068426240, ('10 PiB', '10 PiB', '11.25 PB', '10 pebibytes', '10 pebibytes', '11.25 petabytes')),
    (11258999068426241, ('10.00 PiB', '10.00 PiB', '11.25 PB', '10.00 pebibytes', '10.00 pebibytes', '11.25 petabytes')),
    (112589990684262399, ('99.99 PiB', '99.99 PiB', '112.5 PB', '99.99 pebibytes', '99.99 pebibytes', '112.5 petabytes')),
    (112589990684262400, ('100 PiB', '100 PiB', '112.5 PB', '100 pebibytes', '100 pebibytes', '112.5 petabytes')),
    (112589990684262401, ('100.0 PiB', '100.0 PiB', '112.5 PB', '100.0 pebibytes', '100.0 pebibytes', '112.5 petabytes')),
    (1125899906842623999, ('999.9 PiB', '999.9 PiB', '1.125 EB', '999.9 pebibytes', '999.9 pebibytes', '1.125 exabytes')),
    (1125899906842624000, ('1000 PiB', '1000 PiB', '1.125 EB', '1000 pebibytes', '1000 pebibytes', '1.125 exabytes')),
    (1125899906842624001, ('0.976 EiB', '1000. PiB', '1.125 EB', '0.976 exbibytes', '1000. pebibytes', '1.125 exabytes')),
    (1152921504606846975, ('0.999 EiB', '1023. PiB', '1.152 EB', '0.999 exbibytes', '1023. pebibytes', '1.152 exabytes')),
    (1152921504606846976, ('1 EiB', '1 EiB', '1.152 EB', '1 exbibyte', '1 exbibyte', '1.152 exabytes')),
    (1152921504606846977, ('1.000 EiB', '1.000 EiB', '1.152 EB', '1.000 exbibytes', '1.000 exbibytes', '1.152 exabytes')),
    (11529215046068469759, ('9.999 EiB', '9.999 EiB', '11.52 EB', '9.999 exbibytes', '9.999 exbibytes', '11.52 exabytes')),
    (11529215046068469760, ('10 EiB', '10 EiB', '11.52 EB', '10 exbibytes', '10 exbibytes', '11.52 exabytes')),
    (11529215046068469761, ('10.00 EiB', '10.00 EiB', '11.52 EB', '10.00 exbibytes', '10.00 exbibytes', '11.52 exabytes')),
    (115292150460684697599, ('99.99 EiB', '99.99 EiB', '115.2 EB', '99.99 exbibytes', '99.99 exbibytes', '115.2 exabytes')),
    (115292150460684697600, ('100 EiB', '100 EiB', '115.2 EB', '100 exbibytes', '100 exbibytes', '115.2 exabytes')),
    (115292150460684697601, ('100.0 EiB', '100.0 EiB', '115.2 EB', '100.0 exbibytes', '100.0 exbibytes', '115.2 exabytes')),
    (1152921504606846975999, ('999.9 EiB', '999.9 EiB', '1.152 ZB', '999.9 exbibytes', '999.9 exbibytes', '1.152 zettabytes')),
    (1152921504606846976000, ('1000 EiB', '1000 EiB', '1.152 ZB', '1000 exbibytes', '1000 exbibytes', '1.152 zettabytes')),
    (1152921504606846976001, ('0.976 ZiB', '1000. EiB', '1.152 ZB', '0.976 zebibytes', '1000. exbibytes', '1.152 zettabytes')),
    (1180591620717411303423, ('0.999 ZiB', '1023. EiB', '1.180 ZB', '0.999 zebibytes', '1023. exbibytes', '1.180 zettabytes')),
    (1180591620717411303424, ('1 ZiB', '1 ZiB', '1.180 ZB', '1 zebibyte', '1 zebibyte', '1.180 zettabytes')),
    (1180591620717411303425, ('1.000 ZiB', '1.000 ZiB', '1.180 ZB', '1.000 zebibytes', '1.000 zebibytes', '1.180 zettabytes')),
    (11805916207174113034239, ('9.999 ZiB', '9.999 ZiB', '11.80 ZB', '9.999 zebibytes', '9.999 zebibytes', '11.80 zettabytes')),
    (11805916207174113034240, ('10 ZiB', '10 ZiB', '11.80 ZB', '10 zebibytes', '10 zebibytes', '11.80 zettabytes')),
    (11805916207174113034241, ('10.00 ZiB', '10.00 ZiB', '11.80 ZB', '10.00 zebibytes', '10.00 zebibytes', '11.80 zettabytes')),
    (118059162071741130342399, ('99.99 ZiB', '99.99 ZiB', '118.0 ZB', '99.99 zebibytes', '99.99 zebibytes', '118.0 zettabytes')),
    (118059162071741130342400, ('100 ZiB', '100 ZiB', '118.0 ZB', '100 zebibytes', '100 zebibytes', '118.0 zettabytes')),
    (118059162071741130342401, ('100.0 ZiB', '100.0 ZiB', '118.0 ZB', '100.0 zebibytes', '100.0 zebibytes', '118.0 zettabytes')),
    (1180591620717411303423999, ('999.9 ZiB', '999.9 ZiB', '1.180 YB', '999.9 zebibytes', '999.9 zebibytes', '1.180 yottabytes')),
    (1180591620717411303424000, ('1000 ZiB', '1000 ZiB', '1.180 YB', '1000 zebibytes', '1000 zebibytes', '1.180 yottabytes')),
    (1180591620717411303424001, ('0.976 YiB', '1000. ZiB', '1.180 YB', '0.976 yobibytes', '1000. zebibytes', '1.180 yottabytes')),
    (1208925819614629174706175, ('0.999 YiB', '1023. ZiB', '1.208 YB', '0.999 yobibytes', '1023. zebibytes', '1.208 yottabytes')),
    (1208925819614629174706176, ('1 YiB', '1 YiB', '1.208 YB', '1 yobibyte', '1 yobibyte', '1.208 yottabytes')),
    (1208925819614629174706177, ('1.000 YiB', '1.000 YiB', '1.208 YB', '1.000 yobibytes', '1.000 yobibytes', '1.208 yottabytes')),
    (12089258196146291747061759, ('9.999 YiB', '9.999 YiB', '12.08 YB', '9.999 yobibytes', '9.999 yobibytes', '12.08 yottabytes')),
    (12089258196146291747061760, ('10 YiB', '10 YiB', '12.08 YB', '10 yobibytes', '10 yobibytes', '12.08 yottabytes')),
    (12089258196146291747061761, ('10.00 YiB', '10.00 YiB', '12.08 YB', '10.00 yobibytes', '10.00 yobibytes', '12.08 yottabytes')),
    (120892581961462917470617599, ('99.99 YiB', '99.99 YiB', '120.8 YB', '99.99 yobibytes', '99.99 yobibytes', '120.8 yottabytes')),
    (120892581961462917470617600, ('100 YiB', '100 YiB', '120.8 YB', '100 yobibytes', '100 yobibytes', '120.8 yottabytes')),
    (120892581961462917470617601, ('100.0 YiB', '100.0 YiB', '120.8 YB', '100.0 yobibytes', '100.0 yobibytes', '120.8 yottabytes')),
    (1208925819614629174706175999, ('999.9 YiB', '999.9 YiB', None, '999.9 yobibytes', '999.9 yobibytes', None)),
    (1208925819614629174706176000, ('1000 YiB', '1000 YiB', None, '1000 yobibytes', '1000 yobibytes', None)),
    (1208925819614629174706176001, (None, '1000. YiB', None, None, '1000. yobibytes', None)),
    (1237940039285380274899124223, (None, '1023. YiB', None, None, '1023. yobibytes', None)),
    (0, ('0 B', '0 B', '0 B', '0 bytes', '0 bytes', '0 bytes')),
    (1, ('1 B', '1 B', '1 B', '1 byte', '1 byte', '1 byte')),
    (2, ('2 B', '2 B', '2 B', '2 bytes', '2 bytes', '2 bytes')),
    (9, ('9 B', '9 B', '9 B', '9 bytes', '9 bytes', '9 bytes')),
    (10, ('10 B', '10 B', '10 B', '10 bytes', '10 bytes', '10 bytes')),
    (11, ('11 B', '11 B', '11 B', '11 bytes', '11 bytes', '11 bytes')),
    (99, ('99 B', '99 B', '99 B', '99 bytes', '99 bytes', '99 bytes')),
    (100, ('100 B', '100 B', '100 B', '100 bytes', '100 bytes', '100 bytes')),
    (101, ('101 B', '101 B', '101 B', '101 bytes', '101 bytes', '101 bytes')),
    (999, ('999 B', '999 B', '999 B', '999 bytes', '999 bytes', '999 bytes')),
    (1000, ('0.976 KiB', '1000 B', '1 kB', '0.976 kibibytes', '1000 bytes', '1 kilobyte')),
    (1001, ('0.977 KiB', '1001 B', '1.001 kB', '0.977 kibibytes', '1001 bytes', '1.001 kilobytes')),
    (9999, ('9.764 KiB', '9.764 KiB', '9.999 kB', '9.764 kibibytes', '9.764 kibibytes', '9.999 kilobytes')),
    (10000, ('9.765 KiB', '9.765 KiB', '10 kB', '9.765 kibibytes', '9.765 kibibytes', '10 kilobytes')),
    (10001, ('9.766 KiB', '9.766 KiB', '10.00 kB', '9.766 kibibytes', '9.766 kibibytes', '10.00 kilobytes')),
    (99999, ('97.65 KiB', '97.65 KiB', '99.99 kB', '97.65 kibibytes', '97.65 kibibytes', '99.99 kilobytes')),
    (100000, ('97.65 KiB', '97.65 KiB', '100 kB', '97.65 kibibytes', '97.65 kibibytes', '100 kilobytes')),
    (100001, ('97.65 KiB', '97.65 KiB', '100.0 kB', '97.65 kibibytes', '97.65 kibibytes', '100.0 kilobytes')),
    (999999, ('976.5 KiB', '976.5 KiB', '999.9 kB', '976.5 kibibytes', '976.5 kibibytes', '999.9 kilobytes')),
    (1000000, ('976.5 KiB', '976.5 KiB', '1 MB', '976.5 kibibytes', '976.5 kibibytes', '1 megabyte')),
    (1000001, ('976.5 KiB', '976.5 KiB', '1.000 MB', '976.5 kibibytes', '976.5 kibibytes', '1.000 megabytes')),
    (9999999, ('9.536 MiB', '9.536 MiB', '9.999 MB', '9.536 mebibytes', '9.536 mebibytes', '9.999 megabytes')),
    (10000000, ('9.536 MiB', '9.536 MiB', '10 MB', '9.536 mebibytes', '9.536 mebibytes', '10 megabytes')),
    (10000001, ('9.536 MiB', '9.536 MiB', '10.00 MB', '9.536 mebibytes', '9.536 mebibytes', '10.00 megabytes')),
    (99999999, ('95.36 MiB', '95.36 MiB', '99.99 MB', '95.36 mebibytes', '95.36 mebibytes', '99.99 megabytes')),
    (100000000, ('95.36 MiB', '95.36 MiB', '100 MB', '95.36 mebibytes', '95.36 mebibytes', '100 megabytes')),
    (100000001, ('95.36 MiB', '95.36 MiB', '100.0 MB', '95.36 mebibytes', '95.36 mebibytes', '100.0 megabytes')),
    (999999999, ('953.6 MiB', '953.6 MiB', '999.9 MB', '953.6 mebibytes', '953.6 mebibytes', '999.9 megabytes')),
    (1000000000, ('953.6 MiB', '953.6 MiB', '1 GB', '953.6 mebibytes', '953.6 mebibytes', '1 gigabyte')),
    (1000000001, ('953.6 MiB', '953.6 MiB', '1.000 GB', '953.6 mebibytes', '953.6 mebibytes', '1.000 gigabytes')),
    (9999999999, ('9.313 GiB', '9.313 GiB', '9.999 GB', '9.313 gibibytes', '9.313 gibibytes', '9.999 gigabytes')),
    (10000000000, ('9.313 GiB', '9.313 GiB', '10 GB', '9.313 gibibytes', '9.313 gibibytes', '10 gigabytes')),
    (10000000001, ('9.313 GiB', '9.313 GiB', '10.00 GB', '9.313 gibibytes', '9.313 gibibytes', '10.00 gigabytes')),
    (99999999999, ('93.13 GiB', '93.13 GiB', '99.99 GB', '93.13 gibibytes', '93.13 gibibytes', '99.99 gigabytes')),
    (100000000000, ('93.13 GiB', '93.13 GiB', '100 GB', '93.13 gibibytes', '93.13 gibibytes', '100 gigabytes')),
    (100000000001, ('93.13 GiB', '93.13 GiB', '100.0 GB', '93.13 gibibytes', '93.13 gibibytes', '100.0 gigabytes')),
    (999999999999, ('931.3 GiB', '931.3 GiB', '999.9 GB', '931.3 gibibytes', '931.3 gibibytes', '999.9 gigabytes')),
    (1000000000000, ('931.3 GiB', '931.3 GiB', '1 TB', '931.3 gibibytes', '931.3 gibibytes', '1 terabyte')),
    (1000000000001, ('931.3 GiB', '931.3 GiB', '1.000 TB', '931.3 gibibytes', '931.3 gibibytes', '1.000 terabytes')),
    (9999999999999, ('9.094 TiB', '9.094 TiB', '9.999 TB', '9.094 tebibytes', '9.094 tebibytes', '9.999 terabytes')),
    (10000000000000, ('9.094 TiB', '9.094 TiB', '10 TB', '9.094 tebibytes', '9.094 tebibytes', '10 terabytes')),
    (10000000000001, ('9.094 TiB', '9.094 TiB', '10.00 TB', '9.094 tebibytes', '9.094 tebibytes', '10.00 terabytes')),
    (99999999999999, ('90.94 TiB', '90.94 TiB', '99.99 TB', '90.94 tebibytes', '90.94 tebibytes', '99.99 terabytes')),
    (100000000000000, ('90.94 TiB', '90.94 TiB', '100 TB', '90.94 tebibytes', '90.94 tebibytes', '100 terabytes')),
    (100000000000001, ('90.94 TiB', '90.94 TiB', '100.0 TB', '90.94 tebibytes', '90.94 tebibytes', '100.0 terabytes')),
    (999999999999999, ('909.4 TiB', '909.4 TiB', '999.9 TB', '909.4 tebibytes', '909.4 tebibytes', '999.9 terabytes')),
    (1000000000000000, ('909.4 TiB', '909.4 TiB', '1 PB', '909.4 tebibytes', '909.4 tebibytes', '1 petabyte')),
    (1000000000000001, ('909.4 TiB', '909.4 TiB', '1.000 PB', '909.4 tebibytes', '909.4 tebibytes', '1.000 petabytes')),
    (9999999999999999, ('8.881 PiB', '8.881 PiB', '9.999 PB', '8.881 pebibytes', '8.881 pebibytes', '9.999 petabytes')),
    (10000000000000000, ('8.881 PiB', '8.881 PiB', '10 PB', '8.881 pebibytes', '8.881 pebibytes', '10 petabytes')),
    (10000000000000001, ('8.881 PiB', '8.881 PiB', '10.00 PB', '8.881 pebibytes', '8.881 pebibytes', '10.00 petabytes')),
    (99999999999999999, ('88.81 PiB', '88.81 PiB', '99.99 PB', '88.81 pebibytes', '88.81 pebibytes', '99.99 petabytes')),
    (100000000000000000, ('88.81 PiB', '88.81 PiB', '100 PB', '88.81 pebibytes', '88.81 pebibytes', '100 petabytes')),
    (100000000000000001, ('88.81 PiB', '88.81 PiB', '100.0 PB', '88.81 pebibytes', '88.81 pebibytes', '100.0 petabytes')),
    (999999999999999999, ('888.1 PiB', '888.1 PiB', '999.9 PB', '888.1 pebibytes', '888.1 pebibytes', '999.9 petabytes')),
    (1000000000000000000, ('888.1 PiB', '888.1 PiB', '1 EB', '888.1 pebibytes', '888.1 pebibytes', '1 exabyte')),
    (1000000000000000001, ('888.1 PiB', '888.1 PiB', '1.000 EB', '888.1 pebibytes', '888.1 pebibytes', '1.000 exabytes')),
    (9999999999999999999, ('8.673 EiB', '8.673 EiB', '9.999 EB', '8.673 exbibytes', '8.673 exbibytes', '9.999 exabytes')),
    (10000000000000000000, ('8.673 EiB', '8.673 EiB', '10 EB', '8.673 exbibytes', '8.673 exbibytes', '10 exabytes')),
    (10000000000000000001, ('8.673 EiB', '8.673 EiB', '10.00 EB', '8.673 exbibytes', '8.673 exbibytes', '10.00 exabytes')),
    (99999999999999999999, ('86.73 EiB', '86.73 EiB', '99.99 EB', '86.73 exbibytes', '86.73 exbibytes', '99.99 exabytes')),
    (100000000000000000000, ('86.73 EiB', '86.73 EiB', '100 EB', '86.73 exbibytes', '86.73 exbibytes', '100 exabytes')),
    (100000000000000000001, ('86.73 EiB', '86.73 EiB', '100.0 EB', '86.73 exbibytes', '86.73 exbibytes', '100.0 exabytes')),
    (999999999999999999999, ('867.3 EiB', '867.3 EiB', '999.9 EB', '867.3 exbibytes', '867.3 exbibytes', '999.9 exabytes')),
    (1000000000000000000000, ('867.3 EiB', '867.3 EiB', '1 ZB', '867.3 exbibytes', '867.3 exbibytes', '1 zettabyte')),
    (1000000000000000000001, ('867.3 EiB', '867.3 EiB', '1.000 ZB', '867.3 exbibytes', '867.3 exbibytes', '1.000 zettabytes')),
    (9999999999999999999999, ('8.470 ZiB', '8.470 ZiB', '9.999 ZB', '8.470 zebibytes', '8.470 zebibytes', '9.999 zettabytes')),
    (10000000000000000000000, ('8.470 ZiB', '8.470 ZiB', '10 ZB', '8.470 zebibytes', '8.470 zebibytes', '10 zettabytes')),
    (10000000000000000000001, ('8.470 ZiB', '8.470 ZiB', '10.00 ZB', '8.470 zebibytes', '8.470 zebibytes', '10.00 zettabytes')),
    (99999999999999999999999, ('84.70 ZiB', '84.70 ZiB', '99.99 ZB', '84.70 zebibytes', '84.70 zebibytes', '99.99 zettabytes')),
    (100000000000000000000000, ('84.70 ZiB', '84.70 ZiB', '100 ZB', '84.70 zebibytes', '84.70 zebibytes', '100 zettabytes')),
    (100000000000000000000001, ('84.70 ZiB', '84.70 ZiB', '100.0 ZB', '84.70 zebibytes', '84.70 zebibytes', '100.0 zettabytes')),
    (999999999999999999999999, ('847.0 ZiB', '847.0 ZiB', '999.9 ZB', '847.0 zebibytes', '847.0 zebibytes', '999.9 zettabytes')),
    (1000000000000000000000000, ('847.0 ZiB', '847.0 ZiB', '1 YB', '847.0 zebibytes', '847.0 zebibytes', '1 yottabyte')),
    (1000000000000000000000001, ('847.0 ZiB', '847.0 ZiB', '1.000 YB', '847.0 zebibytes', '847.0 zebibytes', '1.000 yottabytes')),
    (9999999999999999999999999, ('8.271 YiB', '8.271 YiB', '9.999 YB', '8.271 yobibytes', '8.271 yobibytes', '9.999 yottabytes')),
    (10000000000000000000000000, ('8.271 YiB', '8.271 YiB', '10 YB', '8.271 yobibytes', '8.271 yobibytes', '10 yottabytes')),
    (10000000000000000000000001, ('8.271 YiB', '8.271 YiB', '10.00 YB', '8.271 yobibytes', '8.271 yobibytes', '10.00 yottabytes')),
    (99999999999999999999999999, ('82.71 YiB', '82.71 YiB', '99.99 YB', '82.71 yobibytes', '82.71 yobibytes', '99.99 yottabytes')),
    (100000000000000000000000000, ('82.71 YiB', '82.71 YiB', '100 YB', '82.71 yobibytes', '82.71 yobibytes', '100 yottabytes')),
    (100000000000000000000000001, ('82.71 YiB', '82.71 YiB', '100.0 YB', '82.71 yobibytes', '82.71 yobibytes', '100.0 yottabytes')),
    (999999999999999999999999999, ('827.1 YiB', '827.1 YiB', '999.9 YB', '827.1 yobibytes', '827.1 yobibytes', '999.9 yottabytes')),
    (1000000000000000000000000000, ('827.1 YiB', '827.1 YiB', None, '827.1 yobibytes', '827.1 yobibytes', None)),
    (1000000000000000000000000001, ('827.1 YiB', '827.1 YiB', None, '827.1 yobibytes', '827.1 yobibytes', None)),
]
