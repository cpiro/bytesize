# python $0 generate

from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *

import sys
import re
from nose.tools import raises

import bytesize as bs

if __name__ != '__main__':
    from data_for_hardcases import *


def catch(f):
    """Wrap `f` such that exceptions are returned, rather than raised"""
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except BaseException as exn:
            return exn
    return wrapper


def mk_formatter(**kwargs):
    _catch = kwargs['_catch']; del kwargs['_catch']
    _short = kwargs['_short']; del kwargs['_short']

    if _catch:
        maybe_catch = catch
    else:
        def maybe_catch(f):
            return f

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
        # ^^^ strictly less than, *unless* frac_quot doesn't have precision
        # enough to represent
        assert len(digits) == places
        assert ('.' in result) == (rem != 0), \
            "there's a decimal dot iff the value is not exact"

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
            assert lower_bound <= (pint_bytes / b) <= 1, \
                "ureg(`result`) should be <= `b`, but not by too much"
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


def generate():
    import pprint

    kwargses = tuple(
        {'_short': False, 'base': base, 'cutoff': cutoff, 'abbrev': abbrev}
        for abbrev in (True, False)
        for base, cutoff in ((1024, 1000), (1024, 1024), (1000, 1000))
    ) + tuple(
        {'_short': True, 'try_metric': try_metric, 'tolerance': tolerance}
        for try_metric in (True, False)
        for tolerance in (0.01,)
    )

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
        results = tuple(mk_formatter(_catch=True, **kwargs)(case) for kwargs in kwargses)
        cells = ', '.join('{:19}'.format(xx) for xx in re.split(',', repr(results)))
        print("    ({:31}, {}),".format(case, cells))

    print("]")

if __name__ == '__main__':
    if sys.argv[1:] == ['generate']:
        generate()
