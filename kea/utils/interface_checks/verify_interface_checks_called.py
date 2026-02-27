import inspect

from unittest.mock import patch, call

from .interface_checks import check_bool_signal, check_intbv_signal

def _normalise_call(func, args, kwargs):
    ''' Normalise the call so we can compare calls to the `func`.

    This converts the call arguments to a consistent form irrespective of
    argument order, positional arguments, keyword arguments and defaults.
    '''

    sig = inspect.signature(func)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()

    return bound.arguments

def _get_dut_function_call_arguments(func, dut, dut_args):
    ''' Get the arguments used when the `dut` called `func`.
    '''

    # Set up the location to patch in the mock function
    patch_location = dut.__module__ + '.' + func.__name__

    with patch(patch_location) as (mock_check_function):
        # Make the call
        dut(**dut_args)

        # Normalise all calls to func
        normalised_arguments_list = [
            _normalise_call(func, args, kwargs)
            for args, kwargs in mock_check_function.call_args_list]

    return normalised_arguments_list

def get_dut_check_bool_signal_call_arguments(dut, dut_args):
    ''' Get the arguments used when the `dut` called `check_bool_signal`.
    '''
    dut_check_bool_signal_call_arguments_list = (
        _get_dut_function_call_arguments(check_bool_signal, dut, dut_args))

    return dut_check_bool_signal_call_arguments_list

def get_dut_check_intbv_signal_call_arguments(dut, dut_args):
    ''' Get the arguments used when the `dut` called `check_intbv_signal`.
    '''
    dut_check_intbv_signal_call_arguments_list = (
        _get_dut_function_call_arguments(check_intbv_signal, dut, dut_args))

    return dut_check_intbv_signal_call_arguments_list

def verify_dut_called_check_bool_signal(
    dut_check_bool_signal_call_arguments_list, port, port_name):
    '''Verify that `dut_check_bool_signal_call_arguments_list` contains a call
    to `check_bool_signal` with the correct `port` and `port_name`.

    `dut_check_bool_signal_call_arguments_list` should be the list returned by
    `get_dut_check_bool_signal_call_arguments`.
    '''
    dut_arguments_list = dut_check_bool_signal_call_arguments_list

    # Set up the expected args and kwargs that the DUT should use when calling
    # check_bool_signal.
    expected_args = [port, port_name]
    expected_kwargs = {}

    # Normalise the expected call to check_bool_signal
    expected_arguments = (
        _normalise_call(check_bool_signal, expected_args, expected_kwargs))

    # Check that the normalised expected arguments were actually called
    if expected_arguments not in dut_arguments_list:
        raise AssertionError(
            'The ' + port_name + ' signal has not been checked or the DUT '
            'passed different arguments to check_bool_signal.')

    # Get the index of the expected call
    expected_call_index = dut_arguments_list.index(expected_arguments)

    # Check that the check_bool_signal was called with the correct signal.
    if dut_arguments_list[expected_call_index]['test_signal'] is not port:
        raise AssertionError(
            'The ' + port_name + ' signal was not the signal in the call to '
            'check_bool_signal.')

def verify_dut_called_check_intbv_signal(
    dut_check_intbv_signal_call_arguments_list, port, port_name,
    bitwidth=None, signed=None, val_range=None, range_test=None):
    '''Verify that `dut_check_intbv_signal_call_arguments_list` contains a
    call to `check_intbv_signal` with the correct `port` and `port_name`.

    `dut_check_intbv_signal_call_arguments_list` should be the list returned by
    `get_dut_check_intbv_signal_call_arguments`.
    '''
    dut_arguments_list = dut_check_intbv_signal_call_arguments_list

    # Set up the expected args and kwargs that the DUT should use when calling
    # check_intbv_signal.
    expected_args = [port, port_name]

    potential_expected_args = {
        'bitwidth': bitwidth,
        'signed': signed,
        'val_range': val_range,
        'range_test': range_test,
    }

    expected_kwargs = {
        k: v for k, v in potential_expected_args.items() if v is not None}

    # Normalise the expected call to check_intbv_signal
    expected_arguments = (
        _normalise_call(check_intbv_signal, expected_args, expected_kwargs))

    # Check that the normalised expected arguments were actually called
    if expected_arguments not in dut_arguments_list:
        raise AssertionError(
            'The ' + port_name + ' signal has not been checked or the DUT '
            'passed different arguments to check_bool_signal.')

    # Get the index of the expected call
    expected_call_index = dut_arguments_list.index(expected_arguments)

    # Check that the check_intbv_signal was called with the correct signal.
    if dut_arguments_list[expected_call_index]['test_signal'] is not port:
        raise AssertionError(
            'The ' + port_name + ' signal was not the signal in the call to '
            'check_intbv_signal.')
