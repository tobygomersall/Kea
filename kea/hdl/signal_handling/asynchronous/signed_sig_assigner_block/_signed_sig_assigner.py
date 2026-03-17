from myhdl import block, always_comb

from kea.utils.interface_checks import (check_bool_signal, check_intbv_signal)

@block
def signed_sig_assigner(signal_in, signal_out):
    ''' Interprets `signal_in` as signed and assigns it to `signal_out`.
    '''

    # Check that signal_in is an intbv signals (bool signals don't have the
    # signed property so we can't allow a bool signal_in).
    check_intbv_signal(signal_in, 'signal_in')

    out_upper_bound = 2**(len(signal_in)-1)
    out_lower_bound = -out_upper_bound

    # Check that signal_out is an intbv signals and that it can take any
    # value on signal_in interpreted as signed.
    check_intbv_signal(
        signal_out,
        'signal_out',
        val_range=(out_lower_bound, out_upper_bound),
        range_test='outside')

    return_objects = []

    @always_comb
    def assigner():

        signal_out.next = signal_in.signed()

    return_objects.append(assigner)

    return return_objects
