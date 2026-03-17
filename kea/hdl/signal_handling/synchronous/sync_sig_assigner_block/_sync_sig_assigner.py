from myhdl import block, always

from kea.utils.interface_checks import (
    check_bool_signal, check_bool_or_intbv_signal, check_intbv_signal)

@block
def sync_sig_assigner(clock, signal_in, signal_out):
    ''' Assigns the `signal_in` to the `signal_out`.
    '''

    check_bool_signal(clock, 'clock')

    # Check that signal_in and signal_out are bool or intbv signals
    check_bool_or_intbv_signal(signal_in, 'signal_in')
    check_bool_or_intbv_signal(signal_out, 'signal_out')

    if len(signal_in) > 1:
        # Check that signal_in is an intbv signal
        check_intbv_signal(signal_in, 'signal_in')

        # Check that signal_out is an intbv signals and that it can take any
        # value on signal_in.
        check_intbv_signal(
            signal_out,
            'signal_out',
            val_range=(signal_in.min, signal_in.max),
            range_test='outside')

    return_objects = []

    @always(clock.posedge)
    def assigner():

        signal_out.next = signal_in

    return_objects.append(assigner)

    return return_objects
