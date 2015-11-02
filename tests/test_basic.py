# Don't import future. Real Python 2 users won't

import operator

from nose.tools import raises, assert_raises
from future.utils import PY2

import bytesize as bs
from bytesize import Quantity as Q


def test_simple():
    def for_quantity(q):
        assert int(q) == 1400605
        assert str(q) == '1.335 MiB'
        assert repr(q) == '<Quantity 1400605>'

        # gently exercise 0-padding special case in parse_spec
        assert '{:<0}'.format(q) == '1.335 MiB'
        assert '{:0}'.format(q) == '1.335 MiB'

        pp = bs.formatter()
        assert pp(0) == '0 B'
        assert pp(-0) == '0 B'

    yield for_quantity, bs.Quantity(1400605)
    if PY2:
        yield for_quantity, bs.Quantity(eval('1400605L'))


def test_arithmetic():
    assert type(1 + 1) == int
    assert type(Q(1) + 1) == Q
    assert type(1 + Q(1)) == Q
    assert type(Q(1) + Q(1)) == Q

    assert type(1 - 1) == int
    assert type(Q(1) - 1) == Q
    assert type(1 - Q(1)) == Q
    assert type(Q(1) - Q(1)) == Q

    assert type(1 * 1) == int
    assert type(Q(1) * 1) == Q
    assert type(1 * Q(1)) == Q
    assert type(Q(1) * Q(1)) == Q

    assert type(1 / 1) == float
    assert type(Q(1) / 1) == Q
    assert type(1 / Q(1)) == Q
    assert type(Q(1) / Q(1)) == Q


def test_relations():
    assert Q(10) > Q(1)
    assert Q(10) >= Q(1)
    assert Q(10) >= Q(10)
    assert Q(10) == Q(10)
    assert Q(10) != Q(1)
    assert Q(1) <= Q(10)
    assert Q(10) <= Q(10)
    assert Q(1) < Q(10)

    assert not (Q(10) < Q(1))
    assert not (Q(10) <= Q(1))
    assert not (Q(10) < Q(10))
    assert not (Q(10) != Q(10))
    assert not (Q(10) == Q(1))
    assert not (Q(1) >= Q(10))
    assert not (Q(10) > Q(10))
    assert not (Q(1) >= Q(10))


def test_neg_and_frac():
    @raises(TypeError)
    def check(value):
        Q(value)

    for value in (-1, -1.0, 0.1, 10123123.1):
        yield check, value


def test_incomparable():
    ops = (operator.lt, operator.le,
           operator.gt, operator.ge)

    @raises(TypeError)
    def check(lhs, op, rhs):
        op(lhs, rhs)

    for lhs, op, rhs in (
            [(Q(1), op, 1) for op in ops] +
            [(1, op, Q(1)) for op in ops]):
        yield check, lhs, op, rhs


def test_integral_float():
    assert Q(1.0) == Q(1)
    assert Q(123456789.0) == Q(123456789)


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
        (u'1400605 B', '1.335 MiB'),
    ]

    if bs._ureg:
        def check_direct(b, result):
            assert pp(b) == result
            assert pp(bs._ureg(b)) == result
    else:
        @raises(bs.NeedPintForParsingError)
        def check_direct(b, result):
            pp(b)

    for b, result in data:
        yield check_direct, b, result

def test_format_type():
    data = [
        ('', 1, '1 B'),
        ('', 999, '999 B'),
        ('', 1000, '0.976 KiB'),
        ('', 1001, '0.977 KiB'),
        ('', 1000000, '976.5 KiB'),
        ('', 1000001, '976.5 KiB'),
        ('', 1048576, '1 MiB'),
        ('', 1048577, '1.000 MiB'),
        ('a', 1, '1 B'),
        ('a', 999, '999 B'),
        ('a', 1000, '1 kB'),
        ('a', 1001, '0.977 KiB'),
        ('a', 1000000, '1 MB'),
        ('a', 1000001, '976.5 KiB'),
        ('a', 1048576, '1 MiB'),
        ('a', 1048577, '1.000 MiB'),
        ('d', 1, '1 B'),
        ('d', 999, '999 B'),
        ('d', 1000, '1 kB'),
        ('d', 1001, '1.001 kB'),
        ('d', 1000000, '1 MB'),
        ('d', 1000001, '1.000 MB'),
        ('d', 1048576, '1.048 MB'),
        ('d', 1048577, '1.048 MB'),
        ('i', 1, '1 B'),
        ('i', 999, '999 B'),
        ('i', 1000, '0.976 KiB'),
        ('i', 1001, '0.977 KiB'),
        ('i', 1000000, '976.5 KiB'),
        ('i', 1000001, '976.5 KiB'),
        ('i', 1048576, '1 MiB'),
        ('i', 1048577, '1.000 MiB'),
        ('l', 1, '1 byte'),
        ('l', 999, '999 bytes'),
        ('l', 1000, '0.976 kibibytes'),
        ('l', 1001, '0.977 kibibytes'),
        ('l', 1000000, '976.5 kibibytes'),
        ('l', 1000001, '976.5 kibibytes'),
        ('l', 1048576, '1 mebibyte'),
        ('l', 1048577, '1.000 mebibytes'),
        ('la', 1, '1 byte'),
        ('la', 999, '999 bytes'),
        ('la', 1000, '1 kilobyte'),
        ('la', 1001, '0.977 kibibytes'),
        ('la', 1000000, '1 megabyte'),
        ('la', 1000001, '976.5 kibibytes'),
        ('la', 1048576, '1 mebibyte'),
        ('la', 1048577, '1.000 mebibytes'),
        ('ld', 1, '1 byte'),
        ('ld', 999, '999 bytes'),
        ('ld', 1000, '1 kilobyte'),
        ('ld', 1001, '1.001 kilobytes'),
        ('ld', 1000000, '1 megabyte'),
        ('ld', 1000001, '1.000 megabytes'),
        ('ld', 1048576, '1.048 megabytes'),
        ('ld', 1048577, '1.048 megabytes'),
        ('li', 1, '1 byte'),
        ('li', 999, '999 bytes'),
        ('li', 1000, '0.976 kibibytes'),
        ('li', 1001, '0.977 kibibytes'),
        ('li', 1000000, '976.5 kibibytes'),
        ('li', 1000001, '976.5 kibibytes'),
        ('li', 1048576, '1 mebibyte'),
        ('li', 1048577, '1.000 mebibytes'),
    ]
    def check(spec, value, result):
        fmt_str = '{{:{}}}'.format(spec)
        assert fmt_str.format(bs.Quantity(value)) == result

    for spec, value, result in data:
        yield check, spec, value, result

def test_short_tolerance():
    data = [
        (0, 1999999999999, '1.81Ti'),
        (0, 2000000000000, '2T'),
        (0, 2000000000001, '1.81Ti'),
        (0, 2999999999999, '2.72Ti'),
        (0.0, 1999999999999, '1.81Ti'),
        (0.0, 2000000000000, '2T'),
        (0.0, 2000000000001, '1.81Ti'),
        (0.0, 2999999999999, '2.72Ti'),
        (0.01, 1999999999999, '1.81Ti'),
        (0.01, 2000000000000, '2T'),
        (0.01, 2000000000001, '2T'),
        (0.01, 2999999999999, '2.72Ti'),
        (1, 1999999999999, '1T'),
        (1, 2000000000000, '2T'),
        (1, 2000000000001, '2T'),
        (1, 2999999999999, '2T'),
        (1.0, 1999999999999, '1T'),
        (1.0, 2000000000000, '2T'),
        (1.0, 2000000000001, '2T'),
        (1.0, 2999999999999, '2T'),
        (None, 1999999999999, '1.81Ti'),
        (None, 2000000000000, '1.81Ti'),
        (None, 2000000000001, '1.81Ti'),
        (None, 2999999999999, '2.72Ti'),
    ]
    def check(tolerance, value, result):
        assert bs.short_formatter(tolerance=tolerance)(value) == result

    for tolerance, value, result in data:
        yield check, tolerance, value, result


@raises(AssertionError)
def test_short_tolerance_error():
    bs.short_formatter(tolerance=9000)
    bs.short_formatter(tolerance=1.1)
    bs.short_formatter(tolerance=-0.1)
    bs.short_formatter(tolerance=-9000)


if bs._ureg:
    def test_other_registry():
        other_ureg = bs.pint.UnitRegistry()
        q = other_ureg('800 kilobits/sec') * other_ureg('5 days')
        assert bs.formatter()(q) == '40.23 GiB'

    @raises(bs.pint.unit.DimensionalityError)
    def test_dimensionality_error():
        other_ureg = bs.pint.UnitRegistry()
        q = other_ureg("20080313 seconds per square gram")
        bs.formatter()(q)


@raises(ValueError)
def test_format_unknown_code():
    '{:z}'.format(bs.Quantity(10000))


@raises(ValueError)
def test_format_mutex_code():
    '{:di}'.format(bs.Quantity(10000))


@raises(ValueError)
def test_format_specifier_missing_precision():
    '{:.}'.format(bs.Quantity(1400605))


@raises(bs.UnitNoExistError)
def test_way_too_big():
    print(bs.Quantity(100000000000000000000000000000))


PARSE_SPEC_CASES = [
    (fill, align, width, precision, type_)
    for fill in (None, ' ', '0')
    for align in (None, '>', '<', '=', '^')
    for width in (None, 6, 10, 15)
    for precision in (None, 5, 6, 7, 8, 9, 10, 11)
    for type_ in ('', 'i', 'd', 'a')
    if not (fill is not None and align is None)
]


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

    for spec_tuple in PARSE_SPEC_CASES:
        yield reversible, spec_tuple
        yield basic, spec_tuple, values
