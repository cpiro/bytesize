# python $0 generate

from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *

import sys
import re
from nose.tools import raises

import bytesize

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

    maybe_catch = catch if _catch else lambda f: f
    factory = bytesize.short_formatter if _short else bytesize.formatter
    return maybe_catch(factory(**kwargs))


def test_hardcases():
    def check_formatter(b, result, fmt):
        assert fmt(b) == result

    def check_long_guts(b, result, kwargs):
        base, cutoff = kwargs['base'], kwargs['cutoff']
        qq, exp = bytesize._Quotient.division(int(bytesize.Quantity(b)), base=base, cutoff=cutoff)

        assert b == qq * base**exp
        assert qq < cutoff or (qq == cutoff and base > cutoff)

        assert ('.' in result) == (not qq.exact), \
            "there's a decimal dot iff the value is not exact"

    def check_reverse(b, result, kwargs):
        """parse `result` back through pint, check that it's <= to the original,
        within truncation error
        """
        if kwargs['_short']:
            if not result.endswith('B'):
                result += 'B'
            lower_bound = 1.0 - (kwargs['tolerance'] or 0.01)
        else:
            lower_bound = 0.999

        pint_bytes = bytesize._ureg(result).to('bytes').magnitude
        if isinstance(pint_bytes, float):
            assert lower_bound <= (pint_bytes / b) <= 1, \
                "_ureg(`result`) should be <= `b`, but not by too much"
        else:
            assert pint_bytes == b

    for b, results in hardcases:
        for result, kwargs in zip(results, kwargses):
            fmt = mk_formatter(_catch=False, **kwargs)
            if not isinstance(result, Exception):
                yield check_formatter, b, result, fmt
                if not kwargs['_short']:
                    yield check_long_guts, b, result, kwargs
                if bytesize._ureg:
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
        {'_short': True, 'tolerance': tolerance, 'base': base}
        for (tolerance, base) in ((0.01, None), (None, 1024), (None, 1000))
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
        results = tuple(mk_formatter(_catch=True, **kwargs)(case)
                        for kwargs in kwargses)
        wide_results = ('{:19}'.format(rr)
                        for rr in re.split(',', repr(results)))
        print("    ({:31}, {}),".format(case, ', '.join(wide_results)))

    print("]")

if __name__ == '__main__':
    if sys.argv[1:] == ['generate']:
        generate()
