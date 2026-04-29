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

from ._sync_sig_assigner import sync_sig_assigner

def dut_args_setup(
    input_bitwidth, output_bitwidth, signed_input, signed_output):
    ''' Generate the arguments and argument types for the DUT.
    '''

    if input_bitwidth == 'bool':
        assert(not signed_input)
        signal_in = Signal(False)

    elif input_bitwidth == 1:
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

    if output_bitwidth == 'bool':
        assert(not signed_output)
        signal_out = Signal(False)

    elif output_bitwidth == 1:
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
    }

    arg_types = {
        'clock': 'clock',
        'signal_in': 'custom',
        'signal_out': 'output',
    }

    return args, arg_types

class TestSyncSigAssignerInterface(KeaTestCase):
    ''' The sync_sig_assigner should reject incompatible interfaces and
    arguments.
    '''

    def setUp(self):

        self.dut_args, _dut_arg_types = (
            dut_args_setup(
                input_bitwidth=8, output_bitwidth=8, signed_input=False,
                signed_output=False))

    def test_bool_ports_checked(self):
        '''The `clock` port should be a boolean signal.

        Anything else should raise an error.
        '''
        dut = sync_sig_assigner
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

    def test_bool_or_intbv_ports_checked(self):
        '''The `signal_in` and `signal_out` ports should be boolean or `intbv`
        signals.

        Anything else should raise an error.
        '''
        dut = sync_sig_assigner
        bool_or_intbv_port_names = ['signal_in', 'signal_out']

        # Get all calls to check_bool_or_intbv_signal made by the DUT
        dut_function_call_arguments_list = (
            get_dut_function_call_arguments(
                check_bool_or_intbv_signal, dut, self.dut_args))

        for port_name in bool_or_intbv_port_names:
            expected_args_dict = {
                'test_signal': self.dut_args[port_name],
                'name': port_name,
            }

            # Check that the specified port was checked
            verify_dut_called_function(
                check_bool_or_intbv_signal, dut_function_call_arguments_list,
                expected_args_dict, 'test_signal', port_name)

    def test_intbv_ports_checked(self):
        '''If the bitwidth of `signal_in` is greater than 1 then the following
        checks should be made:

            - `signal_in` should be an intbv.
            - `signal_out` should be an intbv and the range of values that
            `signal_out` can take should include all possible values on
            `signal_in`.

        Anything else should raise an error.
        '''

        signal_out_required_val_range = (
            self.dut_args['signal_in'].min, self.dut_args['signal_in'].max)

        dut = sync_sig_assigner
        intbv_port_requirements = {
            'signal_in': {},
            'signal_out': {
                'val_range': signal_out_required_val_range,
                'range_test': 'outside',
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

class TestSyncSigAssigner(KeaTestCase):

    def setUp(self):
        pass

    @block
    def dut_stim_check(self, **dut_args):

        clock = dut_args['clock']
        signal_in = dut_args['signal_in']
        signal_out = dut_args['signal_out']

        return_objects = []

        if isinstance(signal_in.val, bool):
            bool_signal_in = True
            signal_in_d0 = Signal(False)

        else:
            bool_signal_in = False
            signal_in_d0 = Signal(intbv(0, signal_in.min, signal_in.max))

        @always(clock.posedge)
        def stim_check():

            if bool_signal_in:
                signal_in.next = bool(random.randrange(2))

            else:
                # Randomly drive signal_in
                signal_in.next = (
                    random.randrange(signal_in.min, signal_in.max))

            # Keep a record of signal_in so we can check signal_out
            signal_in_d0.next = signal_in

            assert(signal_out == signal_in_d0)

        return_objects.append(stim_check)

        return return_objects

    def base_test(
        self, input_bitwidth=8, output_bitwidth=8, signed_input=False,
        signed_output=False):

        dut_args, dut_arg_types = (
            dut_args_setup(
                input_bitwidth, output_bitwidth, signed_input, signed_output))

        if not self.testing_using_vivado:
            cycles = 8000
        else:
            cycles = 2000

        @block
        def stimulate_check(**dut_args):

            return_objects = []

            return_objects.append(self.dut_stim_check(**dut_args))

            return return_objects

        dut_outputs, ref_outputs = self.cosimulate(
            cycles, sync_sig_assigner, sync_sig_assigner, dut_args,
            dut_arg_types, custom_sources=[(stimulate_check, (), dut_args)])

        self.assertEqual(dut_outputs, ref_outputs)

    def test_signal_assignment(self):
        '''The `sync_sig_assigner` should synchronously assign `signal_in` to
        `signal_out`.
        '''
        self.base_test()

    def test_bool_to_bool(self):
        '''The `sync_sig_assigner` should function correctly when `signal_in`
        is a bool and signal out is a bool.
        '''
        self.base_test(input_bitwidth='bool', output_bitwidth='bool')

    def test_bool_to_one_bit_intbv(self):
        '''The `sync_sig_assigner` should function correctly when `signal_in`
        is a bool and signal out is a one bit `intbv`.
        '''
        self.base_test(input_bitwidth='bool', output_bitwidth=1)

    def test_one_bit_intbv_to_bool(self):
        '''The `sync_sig_assigner` should function correctly when `signal_in`
        is a one bit `intbv` and signal out is a bool.
        '''
        self.base_test(input_bitwidth=1, output_bitwidth='bool')

    def test_bool_to_wider_intbv(self):
        '''The `sync_sig_assigner` should function correctly when `signal_in`
        is a bool and signal out is an n bit wide `intbv`.
        '''
        self.base_test(input_bitwidth='bool', output_bitwidth=2)

    def test_one_bit_intbv_to_wider_intbv(self):
        '''The `sync_sig_assigner` should function correctly when `signal_in`
        is a one bit `intbv` and signal out is an n bit wide `intbv`.
        '''
        self.base_test(input_bitwidth=1, output_bitwidth=2)

    def test_unsigned_two_bit_intbv_to_unsigned_two_bit_intbv(self):
        '''The `sync_sig_assigner` should function correctly when `signal_in`
        is an unsigned, two bit `intbv` and signal out is an unsigned, two bit
        wide `intbv`.
        '''
        self.base_test(input_bitwidth=2, output_bitwidth=2)

    def test_unsigned_intbv_to_unsigned_intbv(self):
        '''The `sync_sig_assigner` should function correctly when `signal_in`
        is an unsigned, n bit `intbv` and signal out is an unsigned, n bit
        `intbv`.
        '''
        bitwidth = random.randrange(2, 9)
        self.base_test(input_bitwidth=bitwidth, output_bitwidth=bitwidth)

    def test_unsigned_intbv_to_wider_unsigned_intbv(self):
        '''The `sync_sig_assigner` should function correctly when `signal_in`
        is an unsigned, n bit `intbv` and signal out is an unsigned `intbv`
        with a bitwdith that is greater than n.
        '''
        input_bitwidth = random.randrange(2, 9)
        output_bitwidth = random.randrange(input_bitwidth+1, 17)
        self.base_test(
            input_bitwidth=input_bitwidth, output_bitwidth=output_bitwidth)

    def test_signed_two_bit_intbv_to_signed_two_bit_intbv(self):
        '''The `sync_sig_assigner` should function correctly when `signal_in`
        is a signed, two bit `intbv` and signal out is a signed, two bit wide
        `intbv`.
        '''
        self.base_test(
            input_bitwidth=2, output_bitwidth=2, signed_input=True,
            signed_output=True)

    def test_signed_intbv_to_signed_intbv(self):
        '''The `sync_sig_assigner` should function correctly when `signal_in`
        is a signed, n bit `intbv` and signal out is a signed, n bit `intbv`.
        '''
        bitwidth = random.randrange(2, 9)
        self.base_test(
            input_bitwidth=bitwidth, output_bitwidth=bitwidth,
            signed_input=True, signed_output=True)

    def test_signed_intbv_to_wider_signed_intbv(self):
        '''The `sync_sig_assigner` should function correctly when `signal_in`
        is a signed, n bit `intbv` and signal out is a signed `intbv` with a
        bitwdith that is greater than n.
        '''
        input_bitwidth = random.randrange(2, 9)
        output_bitwidth = random.randrange(input_bitwidth+1, 17)
        self.base_test(
            input_bitwidth=input_bitwidth, output_bitwidth=output_bitwidth,
            signed_input=True, signed_output=True)

    def test_unsigned_intbv_to_signed_intbv(self):
        '''The `sync_sig_assigner` should function correctly when `signal_in`
        is an unsigned `intbv` and signal out is a signed `intbv`. Note
        the positive range of `signal_out` needs to be able to accomodate the
        full range of `signal_in`.
        '''
        input_bitwidth = random.randrange(2, 9)
        output_bitwidth = input_bitwidth + 1
        self.base_test(
            input_bitwidth=input_bitwidth, output_bitwidth=output_bitwidth,
            signed_input=False, signed_output=True)

class TestSyncSigAssignerVivadoVhdl(
    KeaVivadoVHDLTestCase, TestSyncSigAssigner):
    pass

class TestSyncSigAssignerVivadoVerilog(
    KeaVivadoVerilogTestCase, TestSyncSigAssigner):
    pass
