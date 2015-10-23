from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *

from nose.tools import raises

import bytesize as bs

def test_simple():
    q = bs.Quantity(1400605)
    assert int(q) == 1400605
    assert str(q) == '1.335 MiB'
    assert repr(q) == '<Quantity 1400605>'

    # gently exercise 0-padding special case in parse_spec
    assert '{:<0}'.format(q) == '1.335 MiB'
    assert '{:0}'.format(q) == '1.335 MiB'

    pp = bs.formatter()
    assert pp(0) == '0 B'
    assert pp(-0) == '0 B'

def test_parsing():
    pp = bs.formatter()
    data = [
        ('-0 B', '0 B'),
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

    if bs.ureg:
        def check_direct(b, result):
            assert pp(b) == result
            assert pp(bs.ureg(b)) == result
    else:
        @raises(bs.NeedPintForParsingError)
        def check_direct(b, result):
            pp(b)

    for b, result in data:
        yield check_direct, b, result

if bs.ureg:
    @raises(bs.DifferentRegistryError)
    def test_different_registry():
        other_ureg = bs.pint.UnitRegistry()
        pp = bs.formatter()
        pp(other_ureg('10 bytes'))

@raises(ValueError)
def test_format_mt_mutex():
    '{:mt}'.format(bs.Quantity(10000))

@raises(ValueError)
def test_format_specifier_missing_precision():
    '{:.}'.format(bs.Quantity(1400605))

@raises(bs.UnitNoExistError)
def test_way_too_big():
    print(bs.Quantity(100000000000000000000000000000))

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

