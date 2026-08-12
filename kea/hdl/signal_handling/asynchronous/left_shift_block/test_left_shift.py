import random

from myhdl import Signal, intbv, block, always

from kea.testing.test_utils.base_test import (
    KeaTestCase, KeaVivadoVHDLTestCase, KeaVivadoVerilogTestCase)
from kea.utils.interface_checks import (
    check_bool_or_intbv_signal,
    check_bool_signal,
    check_intbv_signal,
    get_dut_function_call_arguments,
    verify_dut_called_function)

from ._left_shift import left_shift

def dut_args_setup(
    input_bitwidth, output_bitwidth, signed_input, signed_output, l_shift):
    ''' Generate the arguments and argument types for the DUT.
    '''

    if input_bitwidth == 1:
        assert(not signed_input)
        signal_in = Signal(intbv(0)[input_bitwidth:])

    else:
        assert(isinstance(input_bitwidth, int))
        assert(input_bitwidth > 0)

        if signed_input:
            sig_in_upper_bound = 2**(input_bitwidth-1)
            sig_in_lower_bound = -sig_in_upper_bound
            signal_in = (
                Signal(intbv(0, sig_in_lower_bound, sig_in_upper_bound)))

        else:
            signal_in = Signal(intbv(0)[input_bitwidth:])

    if output_bitwidth == 1:
        assert(not signed_output)
        signal_out = Signal(intbv(0)[output_bitwidth:])

    else:
        assert(isinstance(output_bitwidth, int))
        assert(output_bitwidth > 0)

        if signed_output:
            sig_out_upper_bound = 2**(output_bitwidth-1)
            sig_out_lower_bound = -sig_out_upper_bound
            signal_out = (
                Signal(intbv(0, sig_out_lower_bound, sig_out_upper_bound)))

        else:
            signal_out = Signal(intbv(0)[output_bitwidth:])

    args = {
        'signal_in': signal_in,
        'signal_out': signal_out,
        'l_shift': l_shift,
    }

    arg_types = {
        'signal_in': 'custom',
        'signal_out': 'output',
        'l_shift': 'non-signal',
    }

    return args, arg_types


def dut_wrapper_args_setup(
    input_bitwidth, output_bitwidth, signed_input, signed_output, l_shift):
    ''' Generate the arguments and argument types for the DUT.
    '''

    args, arg_types = (
        dut_args_setup(
            input_bitwidth, output_bitwidth, signed_input, signed_output,
            l_shift))

    args['clock'] = Signal(False)
    arg_types['clock'] = 'clock'

    return args, arg_types

@block
def left_shift_wrapper(clock, signal_in, signal_out, l_shift):
    return left_shift(signal_in, signal_out, l_shift)

class TestLeftShiftInterface(KeaTestCase):

    def setUp(self):

        self.dut_args, _dut_arg_types = (
            dut_args_setup(
                input_bitwidth=8, output_bitwidth=8, signed_input=False,
                signed_output=False, l_shift=0))

    def test_intbv_ports_checked_unsigned_signal_in(self):
        '''The `signal_in` port should be an intbv signal.

        If the `signal_in` port is unsigned then the `signal_out` port should
        be an unsigned intbv signal.

        Anything else should raise an error.
        '''

        dut = left_shift
        intbv_port_requirements = {
            'signal_in': {},
            'signal_out': {
                'signed': False,
            },
        }

        # Get all calls to check_intbv_signal made by the DUT
        dut_function_call_arguments_list = (
            get_dut_function_call_arguments(
                check_intbv_signal, dut, self.dut_args))

        for port_name in intbv_port_requirements:
            # Assemble the args that should have been passed to
            # check_intbv_signal
            expected_args_dict = intbv_port_requirements[port_name]
            expected_args_dict['test_signal'] = self.dut_args[port_name]
            expected_args_dict['name'] =  port_name

            # Check that the specified port was checked
            verify_dut_called_function(
                check_intbv_signal, dut_function_call_arguments_list,
                expected_args_dict, 'test_signal', port_name)

    def test_intbv_ports_checked_signed_signal_in(self):
        '''The `signal_in` port should be an intbv signal.

        If the `signal_in` port is signed then the `signal_out` port should be
        a signed intbv signal.

        Anything else should raise an error.
        '''

        self.dut_args, _dut_arg_types = (
            dut_args_setup(
                input_bitwidth=8, output_bitwidth=8, signed_input=True,
                signed_output=True, l_shift=0))

        dut = left_shift
        intbv_port_requirements = {
            'signal_in': {},
            'signal_out': {
                'signed': True,
            },
        }

        # Get all calls to check_intbv_signal made by the DUT
        dut_function_call_arguments_list = (
            get_dut_function_call_arguments(
                check_intbv_signal, dut, self.dut_args))

        for port_name in intbv_port_requirements:
            # Assemble the args that should have been passed to
            # check_intbv_signal
            expected_args_dict = intbv_port_requirements[port_name]
            expected_args_dict['test_signal'] = self.dut_args[port_name]
            expected_args_dict['name'] =  port_name

            # Check that the specified port was checked
            verify_dut_called_function(
                check_intbv_signal, dut_function_call_arguments_list,
                expected_args_dict, 'test_signal', port_name)

    def test_non_int_l_shift(self):
        '''The `left_shift` block should raise an error if `l_shift` is not
        an integer.
        '''
        self.dut_args['l_shift'] = 'This is not an int'

        # Check that the system errors
        self.assertRaisesRegex(
            TypeError,
            ('left_shift: l_shift should be an integer.'),
            left_shift,
            **self.dut_args
        )

    def test_negative_l_shift(self):
        '''The `left_shift` block should raise an error if `l_shift` is
        less than 0.
        '''
        self.dut_args['l_shift'] = -1

        # Check that the system errors
        self.assertRaisesRegex(
            ValueError,
            ('left_shift: l_shift should be greater than 0.'),
            left_shift,
            **self.dut_args
        )

        self.dut_args['l_shift'] = random.randrange(-10, -1)

        # Check that the system errors
        self.assertRaisesRegex(
            ValueError,
            ('left_shift: l_shift should be greater than 0.'),
            left_shift,
            **self.dut_args
        )

    def test_invalid_signal_out_bitwidth(self):
        '''The `left_shift` block should raise an error if the bitwidth of
        `signal_out` is less than the bitwidth of `signal_in` plus
        `l_shift`.
        '''
        signal_in_bitwidth = random.randrange(2, 17)
        l_shift = random.randrange(1, 9)
        invalid_sig_out_upper_bound = signal_in_bitwidth + l_shift
        signal_out_bitwidth = random.randrange(1, invalid_sig_out_upper_bound)

        self.dut_args['signal_in'] = Signal(intbv(0)[signal_in_bitwidth:])
        self.dut_args['signal_out'] = Signal(intbv(0)[signal_out_bitwidth:])
        self.dut_args['l_shift'] = l_shift

        # Check that the system errors
        self.assertRaisesRegex(
            TypeError,
            ('left_shift: the bitwidth of signal_out should be '
             'greater than or equal to to signal_in plus l_shift.'),
            left_shift,
            **self.dut_args
        )

class TestLeftShift(KeaTestCase):

    def setUp(self):
        pass

    @block
    def dut_stim_check(self, **dut_wrapper_args):

        clock = dut_wrapper_args['clock']
        signal_in = dut_wrapper_args['signal_in']
        signal_out = dut_wrapper_args['signal_out']
        l_shift = dut_wrapper_args['l_shift']

        return_objects = []

        if isinstance(signal_in.val, bool):
            bool_signal_in = True

        else:
            bool_signal_in = False

        @always(clock.posedge)
        def stim_check():

            ##################
            # Signal in stim #
            ##################

            if bool_signal_in:
                signal_in.next = bool(random.randrange(2))

            else:
                # Randomly drive signal_in
                signal_in.next = (
                    random.randrange(signal_in.min, signal_in.max))

            ####################
            # Signal out check #
            ####################

            assert(signal_out == signal_in << l_shift)

        return_objects.append(stim_check)

        return return_objects

    def base_test(
        self, input_bitwidth=8, output_bitwidth=8, signed_input=False,
        signed_output=False, l_shift=0):

        dut_wrapper_args, dut_wrapper_arg_types = (
            dut_wrapper_args_setup(
                input_bitwidth, output_bitwidth, signed_input, signed_output,
                l_shift))

        if not self.testing_using_vivado:
            cycles = 4000
        else:
            cycles = 500

        @block
        def stimulate_check(**dut_wrapper_args):

            return_objects = []

            return_objects.append(self.dut_stim_check(**dut_wrapper_args))

            return return_objects

        dut_outputs, ref_outputs = self.cosimulate(
            cycles, left_shift_wrapper, left_shift_wrapper,
            dut_wrapper_args, dut_wrapper_arg_types,
            custom_sources=[(stimulate_check, (), dut_wrapper_args)])

        self.assertEqual(dut_outputs, ref_outputs)

    def test_assignment(self):
        '''The `left_shift` should asynchronously assign `signal_in` shifted
        left by `l_shift` to `signal_out`.
        '''
        self.base_test()

    def test_one_bit_intbv_in_out(self):
        '''The `left_shift` should function correctly when `signal_in` is a
        one bit `intbv` and signal out is a one bit `intbv`.
        '''
        self.base_test(input_bitwidth=1, output_bitwidth=1)

    def test_one_bit_intbv_to_two_bit_intbv(self):
        '''The `left_shift` should function correctly when `signal_in` is a
        one bit `intbv` and signal out is a two bit `intbv`.
        '''
        l_shifts_to_test = [0, 1]

        for l_shift in l_shifts_to_test:
            self.base_test(
                input_bitwidth=1, output_bitwidth=2, l_shift=l_shift)

    def test_one_bit_intbv_to_wider_intbv(self):
        '''The `left_shift` should function correctly when `signal_in` is a
        one bit `intbv` and signal out is an n bit wide `intbv`.
        '''
        input_bitwidth = 1
        output_bitwidth = random.randrange(4, 17)

        max_l_shift = output_bitwidth - input_bitwidth

        l_shifts_to_test = [
            0, 1, random.randrange(2, max_l_shift), max_l_shift]

        for l_shift in l_shifts_to_test:
            self.base_test(
                input_bitwidth=input_bitwidth,
                output_bitwidth=output_bitwidth,
                l_shift=l_shift)

    def test_unsigned_two_bit_intbv_to_unsigned_two_bit_intbv(self):
        '''The `left_shift` should function correctly when `signal_in` is an
        unsigned, two bit `intbv` and signal out is an unsigned, two bit wide
        `intbv`.
        '''
        self.base_test(input_bitwidth=2, output_bitwidth=2)

    def test_unsigned_intbv_to_unsigned_intbv(self):
        '''The `left_shift` should function correctly when `signal_in` is an
        unsigned, n bit `intbv` and signal out is an unsigned, n bit `intbv`.
        '''
        bitwidth = random.randrange(2, 9)
        self.base_test(input_bitwidth=bitwidth, output_bitwidth=bitwidth)

    def test_unsigned_intbv_to_wider_unsigned_intbv(self):
        '''The `left_shift` should function correctly when `signal_in` is an
        unsigned, n bit `intbv` and signal out is an unsigned `intbv` with a
        bitwdith that is greater than n.
        '''
        input_bitwidth = random.randrange(2, 9)
        output_bitwidth = random.randrange(input_bitwidth+3, 17)

        max_l_shift = output_bitwidth - input_bitwidth

        l_shifts_to_test = [
            0, 1, random.randrange(2, max_l_shift), max_l_shift]

        for l_shift in l_shifts_to_test:
            self.base_test(
                input_bitwidth=input_bitwidth,
                output_bitwidth=output_bitwidth,
                l_shift=l_shift)

    def test_signed_two_bit_intbv_to_signed_two_bit_intbv(self):
        '''The `left_shift` should function correctly when `signal_in` is a
        signed, two bit `intbv` and signal out is a signed, two bit wide
        `intbv`.
        '''
        self.base_test(
            input_bitwidth=2, output_bitwidth=2, signed_input=True,
            signed_output=True)

    def test_signed_intbv_to_signed_intbv(self):
        '''The `left_shift` should function correctly when `signal_in` is a
        signed, n bit `intbv` and signal out is a signed, n bit `intbv`.
        '''
        bitwidth = random.randrange(2, 9)
        self.base_test(
            input_bitwidth=bitwidth, output_bitwidth=bitwidth,
            signed_input=True, signed_output=True)

    def test_signed_intbv_to_wider_signed_intbv(self):
        '''The `left_shift` should function correctly when `signal_in` is a
        signed, n bit `intbv` and signal out is a signed `intbv` with a
        bitwdith that is greater than n.
        '''
        input_bitwidth = random.randrange(2, 9)
        output_bitwidth = random.randrange(input_bitwidth+3, 17)

        max_l_shift = output_bitwidth - input_bitwidth

        l_shifts_to_test = [
            0, 1, random.randrange(2, max_l_shift), max_l_shift]

        for l_shift in l_shifts_to_test:
            self.base_test(
                input_bitwidth=input_bitwidth,
                output_bitwidth=output_bitwidth,
                signed_input=True,
                signed_output=True,
                l_shift=l_shift)

class TestLeftShiftVivadoVhdl(
    KeaVivadoVHDLTestCase, TestLeftShift):
    pass

class TestLeftShiftVivadoVerilog(
    KeaVivadoVerilogTestCase, TestLeftShift):
    pass
