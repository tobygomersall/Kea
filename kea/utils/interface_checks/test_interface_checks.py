import random

from unittest import TestCase

from myhdl import Signal, intbv

from .interface_checks import check_bool_signal, check_intbv_signal

class TestCheckBoolSignal(TestCase):

    def setUp(self):

        self.dut_args = {
            'test_signal': Signal(False),
            'name': 'test_name',
        }

    def test_non_signal(self):
        '''The `check_bool_signal` function should raise an error if
        `test_signal` is not an instance of `myhdl._Signal._Signal`.
        '''

        self.dut_args['test_signal'] = 'this is not a signal'

        self.assertRaisesRegex(
            TypeError,
            ('Port %s should be a Signal.' % (self.dut_args['name'],)),
            check_bool_signal,
            **self.dut_args
        )

    def test_invalid_signal(self):
        '''The `check_bool_signal` function should raise an error if
        `test_signal` is not a bool signal or an intbv signal.
        '''

        self.dut_args['test_signal'] = Signal(0)

        self.assertRaisesRegex(
            TypeError,
            ('Port %s signal should be a boolean or a single bit intbv '
             'signal.' % (self.dut_args['name'],)),
            check_bool_signal,
            **self.dut_args
        )

    def test_intbv_bitwidth_not_one(self):
        '''The `check_bool_signal` function should raise an error if
        `test_signal` is an intbv signal and the bitwidth is not 1.
        '''

        bitwidth = 2
        self.dut_args['test_signal'] = Signal(intbv(0)[bitwidth:])

        self.assertRaisesRegex(
            TypeError,
            ('Port %s signal: intbv signals should be a single bit.'
             % (self.dut_args['name'],)),
            check_bool_signal,
            **self.dut_args
        )

        bitwidth = random.randrange(3, 9)
        self.dut_args['test_signal'] = Signal(intbv(0)[bitwidth:])

        self.assertRaisesRegex(
            TypeError,
            ('Port %s signal: intbv signals should be a single bit.'
             % (self.dut_args['name'],)),
            check_bool_signal,
            **self.dut_args
        )

class TestCheckIntbvSignal(TestCase):

    def setUp(self):

        self.dut_args = {
            'test_signal': Signal(intbv(0, 0, 16)),
            'name': 'test_name',
        }

    def test_non_signal(self):
        '''The `check_intbv_signal` function should raise an error if
        `test_signal` is not an instance of `myhdl._Signal._Signal`.
        '''

        self.dut_args['test_signal'] = 'this is not a signal'

        self.assertRaisesRegex(
            TypeError,
            ('Port %s should be a Signal.' % (self.dut_args['name'],)),
            check_intbv_signal,
            **self.dut_args
        )

    def test_non_intbv_signal(self):
        '''The `check_intbv_signal` function should raise an error if
        `test_signal` is not an intbv signal.
        '''

        self.dut_args['test_signal'] = Signal(0)

        self.assertRaisesRegex(
            TypeError,
            ('Port %s should be an intbv signal.' %
             (self.dut_args['name'],)),
            check_intbv_signal,
            **self.dut_args
        )

    def test_incorrect_bitwidth(self):
        '''If `bitwidth` is specified, the `check_intbv_signal`
        function should raise an error if the bit width of `test_signal` is
        not equal to `bitwidth`.
        '''

        mismatched_bitwidths = random.sample(range(1, 17), 2)
        self.dut_args['test_signal'] = (
            Signal(intbv(0)[mismatched_bitwidths[0]:]))
        self.dut_args['bitwidth'] = mismatched_bitwidths[1]

        self.assertRaisesRegex(
            TypeError,
            ('Port %s should be %d bits wide.' %
             (self.dut_args['name'], self.dut_args['bitwidth'])),
            check_intbv_signal,
            **self.dut_args,
        )

    def test_signed_invalid_min(self):
        '''If `signed` is `True`, the `check_intbv_signal` function should
        raise an error if `test_signal.min` is greater than or equal to 0.
        '''
        lower_bound = random.randrange(1, 10)
        upper_bound = random.randrange(lower_bound+1, lower_bound+10)

        self.dut_args['test_signal'] = (
            Signal(intbv(lower_bound, lower_bound, upper_bound)))
        self.dut_args['signed'] = True

        self.assertRaisesRegex(
            ValueError,
            ('Port %s should be signed.' % (self.dut_args['name'],)),
            check_intbv_signal,
            **self.dut_args
        )

    def test_unsigned_invalid_min(self):
        '''If `signed` is `False`, the `check_intbv_signal` function should
        raise an error if `test_signal.min` is less than 0.
        '''
        lower_bound = random.randrange(-10, 0)
        upper_bound = random.randrange(lower_bound+1, lower_bound+10)

        self.dut_args['test_signal'] = (
            Signal(intbv(lower_bound, lower_bound, upper_bound)))
        self.dut_args['signed'] = False

        self.assertRaisesRegex(
            ValueError,
            ('Port %s should be unsigned.' % (self.dut_args['name'],)),
            check_intbv_signal,
            **self.dut_args
        )

    def test_inside_val_range(self):
        '''If `val_range` is specified and `range_test` is `'inside'`, the
        `check_intbv_signal` function should raise an error if
        `test_signal.min` is less than `val_range[0]` or `test_signal.max` is
        greater than `val_range[1]`.
        '''
        self.dut_args['range_test'] = 'inside'

        self.dut_args['val_range'] = (
            self.dut_args['test_signal'].min + 1,
            self.dut_args['test_signal'].max)

        self.assertRaisesRegex(
            ValueError,
            ('Port %s.min should be >= %d and port %s.max should be '
             '<= %d.' % (
                 self.dut_args['name'], self.dut_args['val_range'][0],
                 self.dut_args['name'], self.dut_args['val_range'][1])),
            check_intbv_signal,
            **self.dut_args
        )

        self.dut_args['val_range'] = (
            self.dut_args['test_signal'].min,
            self.dut_args['test_signal'].max - 1)

        self.assertRaisesRegex(
            ValueError,
            ('Port %s.min should be >= %d and port %s.max should be '
             '<= %d.' % (
                 self.dut_args['name'], self.dut_args['val_range'][0],
                 self.dut_args['name'], self.dut_args['val_range'][1])),
            check_intbv_signal,
            **self.dut_args
        )

    def test_outside_val_range(self):
        '''If `val_range` is specified and `range_test` is `'outside'`, the
        `check_intbv_signal` function should raise an error if
        `test_signal.min` is greater than `val_range[0]` or `test_signal.max`
        is less than `val_range[1]`.
        '''
        self.dut_args['range_test'] = 'outside'

        self.dut_args['val_range'] = (
            self.dut_args['test_signal'].min - 1,
            self.dut_args['test_signal'].max)

        self.assertRaisesRegex(
            ValueError,
            ('Port %s.min should be <= %d and port %s.max should be '
             '>= %d.' % (
                 self.dut_args['name'], self.dut_args['val_range'][0],
                 self.dut_args['name'], self.dut_args['val_range'][1])),
            check_intbv_signal,
            **self.dut_args
        )

        self.dut_args['val_range'] = (
            self.dut_args['test_signal'].min,
            self.dut_args['test_signal'].max + 1)

        self.assertRaisesRegex(
            ValueError,
            ('Port %s.min should be <= %d and port %s.max should be '
             '>= %d.' % (
                 self.dut_args['name'], self.dut_args['val_range'][0],
                 self.dut_args['name'], self.dut_args['val_range'][1])),
            check_intbv_signal,
            **self.dut_args
        )

    def test_exact_val_range(self):
        '''If `val_range` is specified and `range_test` is `'exact'`, the
        `check_intbv_signal` function should raise an error if
        `test_signal.min` is not equal to `val_range[0]` or `test_signal.max`
        is not equal to `val_range[1]`.
        '''
        self.dut_args['range_test'] = 'exact'

        self.dut_args['val_range'] = (
            self.dut_args['test_signal'].min + 1,
            self.dut_args['test_signal'].max)

        self.assertRaisesRegex(
            ValueError,
            ('Port %s.min should be == %d and port %s.max should be '
             '== %d.' % (
                 self.dut_args['name'], self.dut_args['val_range'][0],
                 self.dut_args['name'], self.dut_args['val_range'][1])),
            check_intbv_signal,
            **self.dut_args
        )

        self.dut_args['val_range'] = (
            self.dut_args['test_signal'].min,
            self.dut_args['test_signal'].max - 1)

        self.assertRaisesRegex(
            ValueError,
            ('Port %s.min should be == %d and port %s.max should be '
             '== %d.' % (
                 self.dut_args['name'], self.dut_args['val_range'][0],
                 self.dut_args['name'], self.dut_args['val_range'][1])),
            check_intbv_signal,
            **self.dut_args
        )

    def test_invalid_range_test(self):
        '''If `range_test` is anything other than `'inside'`, `'outside'` or
        `'exact'`, the `check_intbv_signal` function should raise an error.
        '''

        self.dut_args['val_range'] = (
            self.dut_args['test_signal'].min,
            self.dut_args['test_signal'].max)
        self.dut_args['range_test'] = 'invalid string'

        self.assertRaisesRegex(
            ValueError,
            ('`range_test` should be one of \'inside\', \'outside\' or '
             '\'exact\''),
            check_intbv_signal,
            **self.dut_args
        )

    def test_invalid_range(self):
        '''For a given length of `test_signal` the full range that the signal
        can take is given by `2**bitwidth`. Let's call this the full possible
        range.

        If `test_signal.min` is less than zero, the `check_intbv_signal`
        function should raise an error if `test_signal.min` is not equal to
        minus half the full possible range or `test_signal.max` is not equal
        to half the full possible range.

        If `test_signal.min` is not less than zero, the `check_intbv_signal`
        function should raise an error if `test_signal.min` is not equal to
        zero or `test_signal.max` is not equal to the full possible range.
        '''
        bitwidth = random.randrange(3, 9)

        # Signed: invalid test_signal.min #

        lower_bound = -2**(bitwidth-2)
        upper_bound = 2**(bitwidth-1)

        self.dut_args['test_signal'] = (
            Signal(intbv(0, lower_bound, upper_bound)))

        self.assertRaisesRegex(
            ValueError,
            ('Port %s should use the full range available given the bitwidth.'
             % (self.dut_args['name'],)),
            check_intbv_signal,
            **self.dut_args
        )

        # Signed: invalid test_signal.max #

        lower_bound = -2**(bitwidth-1)
        upper_bound = 2**(bitwidth-2)

        self.dut_args['test_signal'] = (
            Signal(intbv(0, lower_bound, upper_bound)))

        self.assertRaisesRegex(
            ValueError,
            ('Port %s should use the full range available given the bitwidth.'
             % (self.dut_args['name'],)),
            check_intbv_signal,
            **self.dut_args
        )

        # Unsigned: invalid test_signal.min #

        upper_bound = 2**bitwidth
        lower_bound = random.randrange(1, upper_bound)

        self.dut_args['test_signal'] = (
            Signal(intbv(lower_bound, lower_bound, upper_bound)))

        self.assertRaisesRegex(
            ValueError,
            ('Port %s should use the full range available given the bitwidth.'
             % (self.dut_args['name'],)),
            check_intbv_signal,
            **self.dut_args
        )

        # Unsigned: invalid test_signal.max #

        lower_bound = 0
        upper_bound = random.randrange(2**(bitwidth-1) + 1, 2**bitwidth)

        self.dut_args['test_signal'] = (
            Signal(intbv(0, lower_bound, upper_bound)))

        self.assertRaisesRegex(
            ValueError,
            ('Port %s should use the full range available given the bitwidth.'
             % (self.dut_args['name'],)),
            check_intbv_signal,
            **self.dut_args
        )
