import myhdl

from myhdl import intbv

def check_bool_signal(test_signal, name):
    '''Check the `test_signal` is valid.
    '''

    assert(isinstance(name, str))

    if not isinstance(test_signal, myhdl._Signal._Signal):
        raise TypeError(
            'Port %s should be a Signal.' % (name,))

    if not isinstance(test_signal.val, (intbv, bool)):
        raise TypeError(
            'Port %s signal should be a boolean or a single bit intbv signal.'
            % (name,))

    if isinstance(test_signal.val, intbv) and len(test_signal) != 1:
        raise TypeError (
            'Port %s signal: intbv signals should be a single bit.' % (name,))

def check_intbv_signal(
    test_signal, name, bitwidth=None, signed=None, val_range=None,
    range_test=None):
    '''Check the `test_signal` is valid.

    If `bitwidth` is not None, this function checks that `test_signal`
    is the width specified by `bitwith`. If `bitwith` is
    None, this function will not check the bitwidth of `test_signal`.

    If `signed` is `True`, this function checks:

        - The `test_signal` is signed.
        - The `min` and `max` values fill the entire range available given
        the bit width.

    If `signed` is `False`, this function checks:

        - The `test_signal` is unsigned.
        - That `min` is zero.
        - That `max` fills the entire range available given the bit width.

    If `signed` is None, this function will not check the signedness of the
    `test_signal`.

    The three possible values for `range_test` are:

        - `'inside'`
        - `'outside'`
        - `'exact'`

    For `val_range = (n, p)`, each asserts the following is true:

        - `'inside'`: `test_signal.min >= n`, `test_signal.max <= p`
        - `'outside'`: `test_signal.min <= n`, `test_signal.max >= p`
        - `'exact'`: `test_signal.min == n`, `test_signal.max == p`

    If `val_range` is None, this function will not check the value range.
    '''

    if not isinstance(test_signal, myhdl._Signal._Signal):
        raise TypeError('Port %s should be a Signal.' % (name,))

    if not isinstance(test_signal.val, intbv):
        raise TypeError('Port %s should be an intbv signal.' % (name,))

    # An intbv can be created with min and max set to None. This function is
    # intended to check that the signals are convertible so we disallow the
    # case when min and max are set to None.
    assert(test_signal.min is not None)
    assert(test_signal.max is not None)

    if bitwidth is not None:

        if len(test_signal) != bitwidth:
            raise TypeError(
                'Port %s should be %d bits wide.' % (name, bitwidth))

    if signed is not None:
        assert(isinstance(signed, bool))

        if signed:
            if test_signal.min >= 0:
                raise ValueError('Port %s should be signed.' % (name,))

        else:
            if test_signal.min < 0:
                raise ValueError('Port %s should be unsigned.' % (name,))

    if val_range is not None:
        assert(len(val_range) == 2)
        assert(isinstance(val_range[0], int))
        assert(isinstance(val_range[1], int))

        if range_test == 'inside':
            if (test_signal.min < val_range[0] or
                test_signal.max > val_range[1]):
                raise ValueError(
                    'Port %s.min should be >= %d and port %s.max should be '
                    '<= %d.' % (name, val_range[0], name, val_range[1]))

        elif range_test == 'outside':
            if (test_signal.min > val_range[0] or
                test_signal.max < val_range[1]):
                raise ValueError(
                    'Port %s.min should be <= %d and port %s.max should be '
                    '>= %d.' % (name, val_range[0], name, val_range[1]))

        elif range_test == 'exact':
            if (test_signal.min != val_range[0] or
                test_signal.max != val_range[1]):
                raise ValueError(
                    'Port %s.min should be == %d and port %s.max should be '
                    '== %d.' % (name, val_range[0], name, val_range[1]))

        else:
            raise ValueError(
                '`range_test` should be one of \'inside\', \'outside\' or '
                '\'exact\'')

    if test_signal.min < 0:
        # test_signal is signed
        expected_upper_bound = 2**(len(test_signal) - 1)
        expected_lower_bound = -expected_upper_bound

    else:
        # test_signal is unsigned
        expected_upper_bound = 2**len(test_signal)
        expected_lower_bound = 0

    # The min and max values can limit the signal value in myhdl but they have
    # no effect after conversion. We ensure the signals are not relying on the
    # min and max values.
    if (test_signal.min != expected_lower_bound or
        test_signal.max != expected_upper_bound):
        raise ValueError(
            'Port %s should use the full range available given the bitwidth.'
            % (name,))
