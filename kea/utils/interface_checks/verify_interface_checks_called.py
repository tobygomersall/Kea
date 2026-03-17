import inspect

from unittest.mock import patch, call

from .interface_checks import check_bool_signal, check_intbv_signal

def _normalise_function_call_args(func, args, kwargs):
    ''' Normalise the call so we can compare calls to the `func`.

    This converts the call arguments to a consistent form irrespective of
    argument order, positional arguments, keyword arguments and defaults.
    '''

    sig = inspect.signature(func)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()

    return bound.arguments

def get_dut_function_call_arguments(func, dut, dut_args):
    ''' Get the arguments used when the `dut` called `func`.
    '''

    # Set up the location to patch in the mock function
    patch_location = dut.__module__ + '.' + func.__name__

    with patch(patch_location) as (mock_check_function):
        # Make the call
        dut(**dut_args)

        # Normalise all calls to func
        normalised_arguments_list = [
            _normalise_function_call_args(func, args, kwargs)
            for args, kwargs in mock_check_function.call_args_list]

    return normalised_arguments_list

def verify_dut_called_function(
    func, dut_function_call_arguments_list, expected_args_dict,
    port_under_test_arg_name, port_under_test_name):
    '''Verify that `dut_function_call_arguments_list` contains a call to
    `func` with the args specified by `expected_args_dict`.

    `dut_function_call_arguments_list` should be the list returned by
    `get_dut_function_call_arguments`.

    `expected_args_dict` should be a dict of the expected arguments in which
    the key is the argument name. If you don't care what value is passed to
    func for any of the arguments then do not include it in
    `expected_args_dict`.

    `port_under_test_arg_name` should be the name of the argument under which
    the port is passed to `func`. Note: `expected_args_dict` should also
    contain this key. For example if we were calling
    `.interface_checks.check_bool_signal` which has arguments `'test_signal'`
    and `'name'` then the `port_under_test_arg_name` would be `'test_signal'`.

    `port_under_test_name` should be a string. This is used to clarify any
    errors raised.
    '''
    dut_arguments_list = dut_function_call_arguments_list

    # Normalise the expected call to the func
    expected_arguments = (
        _normalise_function_call_args(func, [], expected_args_dict))

    # Check that the normalised expected arguments are in the
    # dut_arguments_list
    if expected_arguments not in dut_arguments_list:
        raise AssertionError(
            'The ' + port_under_test_name + ' port check cannot be found. '
            'Either this port has not been checked or the arguments used to '
            'perform the check did not match the expected arguments '
            'provided.')

    # Get a list of indices for all calls to func which were made with the
    # expected_arguments
    matching_call_indices = [
        i for i, call_args in enumerate(dut_arguments_list)
        if call_args == expected_arguments]

    # Check that the expected call was only made once
    if len(matching_call_indices) != 1:
        raise AssertionError(
            'The ' + port_under_test_name + ' port has been checked multiple '
            'times.')

    # Extract the argumnets used in the matching call
    matching_call_args = (
        dut_function_call_arguments_list[matching_call_indices[0]])

    # Extract the port used in the matching call
    matching_call_port = matching_call_args[port_under_test_arg_name]

    # Extract the port which the DUT should have checked
    expected_port = expected_args_dict[port_under_test_arg_name]

    # Check that the func was called with the correct signal.
    if matching_call_port is not expected_port:
        raise AssertionError(
            'The ' + port_under_test_name + ' port was not the object passed '
            'to the specified check function.')
