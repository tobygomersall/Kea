from myhdl import block, always_comb

from kea.utils.interface_checks import (
    check_bool_signal, check_intbv_signal)

@block
def left_shift(signal_in, signal_out, l_shift):
    ''' Assigns the `signal_in` to the uppermost bits of `signal_out`.

    Note `signal_in` and `signal_out` must both be signed or both be unsigned.
    '''

    check_intbv_signal(signal_in, 'signal_in')

    if signal_in.min < 0:
        # If signal_in is signed, check that signal_out is also a signed intbv
        check_intbv_signal(signal_out, 'signal_out', signed=True)

    else:
        # If signal_in is unsigned, check that signal_out is also an unsigned
        # intbv
        check_intbv_signal(signal_out, 'signal_out', signed=False)

    if not isinstance(l_shift, int):
        raise TypeError('left_shift: l_shift should be an integer.')

    if l_shift < 0:
        raise ValueError(
            'left_shift: l_shift should be greater than 0.')

    if len(signal_out) < (len(signal_in) + l_shift):
        raise TypeError(
            'left_shift: the bitwidth of signal_out should be '
            'greater than or equal to to signal_in plus l_shift.')

    return_objects = []

    @always_comb
    def assigner():

        # Always set signal_out to 0. This ensures all bits not driven by
        # signal_in are set to 0.
        signal_out.next = 0

        # Update the uppermost bits of signal_out with signal_in
        signal_out.next[:l_shift] = signal_in

    return_objects.append(assigner)

    return return_objects
