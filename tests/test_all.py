# python test.py make_hardcases

from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *

import sys
from nose.tools import raises

import bytesize as bs
if __name__ != '__main__':
    from test_cases import *

if bs.ureg:
    @raises(bs.DifferentRegistryError)
    def test_different_registry():
        other_ureg = bs.pint.UnitRegistry()
        pp = bs.formatter()
        pp(other_ureg('10 bytes'))

def test_hands():
    pp = bs.formatter()
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
        if bs.ureg:
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
    for fill in (None, ' ', '0')
    for align in (None, '>', '<', '=', '^')
    for width in (None, 6, 10, 15)
    for precision in (None, 5, 6, 7, 8, 9, 10, 11)
    for type_ in ('', 't', 'm') #, ' ', '=', '.', '0', '>')
    if not (fill is not None and align is None)
]

def test_simple():
    q = bs.Quantity(1400605)
    assert int(q) == 1400605
    assert str(q) == '1.335 MiB'
    assert repr(q) == '<Quantity 1400605>'
    # gently exercise 0-padding special case in parse_spec
    assert '{:<0}'.format(q) == '1.335 MiB'
    assert '{:0}'.format(q) == '1.335 MiB'

@raises(ValueError)
def test_format_specifier_missing_precision():
    '{:.}'.format(bs.Quantity(1400605))

@raises(bs.UnitNoExistError)
def test_way_too_big():
    print(bs.Quantity(100000000000000000000000000000))
    
def mk_formatter(**kwargs):
    _catch = kwargs['_catch']; del kwargs['_catch']
    _short = kwargs['_short']; del kwargs['_short']

    if _catch:
        maybe_catch = catch
    else:
        maybe_catch = lambda f: f

    if _short:
        return maybe_catch(bs.short_formatter(**kwargs))
    else:
        return maybe_catch(bs.formatter(**kwargs))

def test_hardcases():
    def check_formatter(b, result, fmt):
        assert fmt(b) == result

    def check_long_guts(b, result, kwargs):
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

    def check_reverse(b, result, kwargs):
        """parse `result` back through pint, check that it's <= to the original,
        within truncation error
        """
        if kwargs['_short']:
            result += 'B'
            lower_bound = 1.0 - kwargs['tolerance']
        else:
            lower_bound = 0.999

        pint_bytes = bs.ureg(result).to('bytes').magnitude
        if isinstance(pint_bytes, float):
            assert lower_bound <= (pint_bytes / b) <= 1, "ureg(`result`) should be <= `b`, but not by too much"
        else:
            assert pint_bytes == b

    for b, results in hardcases:
        for result, kwargs in zip(results, kwargses):
            fmt = mk_formatter(_catch=False, **kwargs)
            if not isinstance(result, Exception):
                yield check_formatter, b, result, fmt
                if not kwargs['_short']:
                    yield check_long_guts, b, result, kwargs
                if bs.ureg:
                    yield check_reverse, b, result, kwargs
            else:
                yield raises(type(result))(fmt), b

def catch(f):
    """Wrap `f` such that exceptions are returned, rather than raised"""
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except BaseException as exn:
            return exn
    return wrapper

def make_hardcases():
    import pprint

    kwargses = [
        {'_short': False, 'base': base, 'cutoff': cutoff, 'abbrev': abbrev}
        for abbrev in (True, False)
        for base, cutoff in ((1024, 1000), (1024, 1024), (1000, 1000))
    ] + [
        {'_short': True, 'try_metric': try_metric, 'tolerance': tolerance}
        for try_metric in (True, False)
        for tolerance in (0.01,)
    ]

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

    print("""__test__ = False
from bytesize import UnitNoExistError
__all__ = ['kwargses', 'hardcases']
""")

    print("kwargses = {}".format(pprint.pformat(kwargses)))
    print("hardcases = [")

    for case in cases:
        results = tuple(mk_formatter(**kwargs)(case) for kwargs in kwargses)
        if any(results):
            print("    ({}, {!r}),".format(case, results))

    print("]")


if __name__ == '__main__':
    if sys.argv[1:] == ['make_hardcases']:
        make_hardcases()
