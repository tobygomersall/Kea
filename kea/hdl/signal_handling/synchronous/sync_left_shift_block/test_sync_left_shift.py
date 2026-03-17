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

from ._sync_left_shift import sync_left_shift

def dut_args_setup(
    input_bitwidth, output_bitwidth, signed_input, signed_output, left_shift):
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
        'clock': Signal(False),
        'signal_in': signal_in,
        'signal_out': signal_out,
        'left_shift': left_shift,
    }

    arg_types = {
        'clock': 'clock',
        'signal_in': 'custom',
        'signal_out': 'output',
        'left_shift': 'non-signal',
    }

    return args, arg_types

class TestSyncLeftShiftInterface(KeaTestCase):

    def setUp(self):

        self.dut_args, _dut_arg_types = (
            dut_args_setup(
                input_bitwidth=8, output_bitwidth=8, signed_input=False,
                signed_output=False, left_shift=0))

    def test_bool_ports_checked(self):
        '''The `clock` port should be a boolean signal.

        Anything else should raise an error.
        '''
        dut = sync_left_shift
        bool_port_names = ['clock']

        # Get all calls to check_bool_signal made by the DUT
        dut_function_call_arguments_list = (
            get_dut_function_call_arguments(
                check_bool_signal, dut, self.dut_args))

        for port_name in bool_port_names:
            expected_args_dict = {
                'test_signal': self.dut_args[port_name],
                'name': port_name,
            }

            # Check that the specified port was checked
            verify_dut_called_function(
                check_bool_signal, dut_function_call_arguments_list,
                expected_args_dict, 'test_signal', port_name)

    def test_intbv_ports_checked_unsigned_signal_in(self):
        '''The `signal_in` port should be an intbv signal.

        If the `signal_in` port is unsigned then the `signal_out` port should
        be an unsigned intbv signal.

        Anything else should raise an error.
        '''

        dut = sync_left_shift
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
                signed_output=True, left_shift=0))

        dut = sync_left_shift
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

    def test_non_int_left_shift(self):
        '''The `sync_left_shift` block should raise an error if `left_shift`
        is not an integer.
        '''
        self.dut_args['left_shift'] = 'This is not an int'

        # Check that the system errors
        self.assertRaisesRegex(
            TypeError,
            ('sync_left_shift: left_shift should be an integer.'),
            sync_left_shift,
            **self.dut_args
        )

    def test_negative_left_shift(self):
        '''The `sync_left_shift` block should raise an error if `left_shift`
        is less than 0.
        '''
        self.dut_args['left_shift'] = -1

        # Check that the system errors
        self.assertRaisesRegex(
            ValueError,
            ('sync_left_shift: left_shift should be greater than 0.'),
            sync_left_shift,
            **self.dut_args
        )

        self.dut_args['left_shift'] = random.randrange(-10, -1)

        # Check that the system errors
        self.assertRaisesRegex(
            ValueError,
            ('sync_left_shift: left_shift should be greater than 0.'),
            sync_left_shift,
            **self.dut_args
        )

    def test_invalid_signal_out_bitwidth(self):
        '''The `sync_left_shift` block should raise an error if the
        bitwidth of `signal_out` is less than the bitwidth of `signal_in` plus
        `left_shift`.
        '''

        signal_in_bitwidth = random.randrange(2, 17)
        left_shift = random.randrange(1, 9)
        invalid_sig_out_upper_bound = signal_in_bitwidth + left_shift
        signal_out_bitwidth = random.randrange(1, invalid_sig_out_upper_bound)

        self.dut_args['signal_in'] = Signal(intbv(0)[signal_in_bitwidth:])
        self.dut_args['signal_out'] = Signal(intbv(0)[signal_out_bitwidth:])
        self.dut_args['left_shift'] = left_shift

        # Check that the system errors
        self.assertRaisesRegex(
            TypeError,
            ('sync_left_shift: the bitwidth of signal_out should be '
             'greater than or equal to to signal_in plus left_shift.'),
            sync_left_shift,
            **self.dut_args
        )

class TestSyncLeftShift(KeaTestCase):

    def setUp(self):
        pass

    @block
    def dut_stim_check(self, **dut_args):

        clock = dut_args['clock']
        signal_in = dut_args['signal_in']
        signal_out = dut_args['signal_out']
        left_shift = dut_args['left_shift']

        return_objects = []

        if isinstance(signal_in.val, bool):
            bool_signal_in = True
            signal_in_d0 = Signal(False)

        else:
            bool_signal_in = False
            signal_in_d0 = Signal(intbv(0, signal_in.min, signal_in.max))

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

            # Keep a record of signal_in so we can check signal_out
            signal_in_d0.next = signal_in

            assert(signal_out == signal_in_d0 << left_shift)

        return_objects.append(stim_check)

        return return_objects

    def base_test(
        self, input_bitwidth=8, output_bitwidth=8, signed_input=False,
        signed_output=False, left_shift=0):

        dut_args, dut_arg_types = (
            dut_args_setup(
                input_bitwidth, output_bitwidth, signed_input, signed_output,
                left_shift))

        if not self.testing_using_vivado:
            cycles = 4000
        else:
            cycles = 500

        @block
        def stimulate_check(**dut_args):

            return_objects = []

            return_objects.append(self.dut_stim_check(**dut_args))

            return return_objects

        dut_outputs, ref_outputs = self.cosimulate(
            cycles, sync_left_shift, sync_left_shift,
            dut_args, dut_arg_types,
            custom_sources=[(stimulate_check, (), dut_args)])

        self.assertEqual(dut_outputs, ref_outputs)

    def test_assignment(self):
        '''The `sync_left_shift` should synchronously assign `signal_in`
        shifted left by `left_shift` to `signal_out`.
        '''
        self.base_test()

    def test_one_bit_intbv_in_out(self):
        '''The `sync_left_shift` should function correctly when
        `signal_in` is a one bit `intbv` and signal out is a one bit `intbv`.
        '''
        self.base_test(input_bitwidth=1, output_bitwidth=1)

    def test_one_bit_intbv_to_two_bit_intbv(self):
        '''The `sync_left_shift` should function correctly when
        `signal_in` is a one bit `intbv` and signal out is a two bit `intbv`.
        '''
        left_shifts_to_test = [0, 1]

        for left_shift in left_shifts_to_test:
            self.base_test(
                input_bitwidth=1, output_bitwidth=2, left_shift=left_shift)

    def test_one_bit_intbv_to_wider_intbv(self):
        '''The `sync_left_shift` should function correctly when
        `signal_in` is a one bit `intbv` and signal out is an n bit wide
        `intbv`.
        '''
        input_bitwidth = 1
        output_bitwidth = random.randrange(4, 17)

        max_left_shift = output_bitwidth - input_bitwidth

        left_shifts_to_test = [
            0, 1, random.randrange(2, max_left_shift), max_left_shift]

        for left_shift in left_shifts_to_test:
            self.base_test(
                input_bitwidth=input_bitwidth,
                output_bitwidth=output_bitwidth,
                left_shift=left_shift)

    def test_unsigned_two_bit_intbv_to_unsigned_two_bit_intbv(self):
        '''The `sync_left_shift` should function correctly when
        `signal_in` is an unsigned, two bit `intbv` and signal out is an
        unsigned, two bit wide `intbv`.
        '''
        self.base_test(input_bitwidth=2, output_bitwidth=2)

    def test_unsigned_intbv_to_unsigned_intbv(self):
        '''The `sync_left_shift` should function correctly when
        `signal_in` is an unsigned, n bit `intbv` and signal out is an
        unsigned, n bit `intbv`.
        '''
        bitwidth = random.randrange(2, 9)
        self.base_test(input_bitwidth=bitwidth, output_bitwidth=bitwidth)

    def test_unsigned_intbv_to_wider_unsigned_intbv(self):
        '''The `sync_left_shift` should function correctly when
        `signal_in` is an unsigned, n bit `intbv` and signal out is an
        unsigned `intbv` with a bitwdith that is greater than n.
        '''
        input_bitwidth = random.randrange(2, 9)
        output_bitwidth = random.randrange(input_bitwidth+3, 17)

        max_left_shift = output_bitwidth - input_bitwidth

        left_shifts_to_test = [
            0, 1, random.randrange(2, max_left_shift), max_left_shift]

        for left_shift in left_shifts_to_test:
            self.base_test(
                input_bitwidth=input_bitwidth,
                output_bitwidth=output_bitwidth,
                left_shift=left_shift)

    def test_signed_two_bit_intbv_to_signed_two_bit_intbv(self):
        '''The `sync_left_shift` should function correctly when
        `signal_in` is a signed, two bit `intbv` and signal out is a signed,
        two bit wide `intbv`.
        '''
        self.base_test(
            input_bitwidth=2, output_bitwidth=2, signed_input=True,
            signed_output=True)

    def test_signed_intbv_to_signed_intbv(self):
        '''The `sync_left_shift` should function correctly when
        `signal_in` is a signed, n bit `intbv` and signal out is a signed, n
        bit `intbv`.
        '''
        bitwidth = random.randrange(2, 9)
        self.base_test(
            input_bitwidth=bitwidth, output_bitwidth=bitwidth,
            signed_input=True, signed_output=True)

    def test_signed_intbv_to_wider_signed_intbv(self):
        '''The `sync_left_shift` should function correctly when
        `signal_in` is a signed, n bit `intbv` and signal out is a signed
        `intbv` with a bitwdith that is greater than n.
        '''
        input_bitwidth = random.randrange(2, 9)
        output_bitwidth = random.randrange(input_bitwidth+3, 17)

        max_left_shift = output_bitwidth - input_bitwidth

        left_shifts_to_test = [
            0, 1, random.randrange(2, max_left_shift), max_left_shift]

        for left_shift in left_shifts_to_test:
            self.base_test(
                input_bitwidth=input_bitwidth,
                output_bitwidth=output_bitwidth,
                signed_input=True,
                signed_output=True,
                left_shift=left_shift)

class TestSyncLeftShiftVivadoVhdl(
    KeaVivadoVHDLTestCase, TestSyncLeftShift):
    pass

class TestSyncLeftShiftVivadoVerilog(
    KeaVivadoVerilogTestCase, TestSyncLeftShift):
    pass
