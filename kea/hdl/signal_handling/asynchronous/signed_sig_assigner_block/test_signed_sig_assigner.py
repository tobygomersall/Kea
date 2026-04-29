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

from ._signed_sig_assigner import signed_sig_assigner

def signed_interpretation(value, bitwidth):
    '''Interprets the `value` as signed based on the bitwidth.
    '''

    threshold = 2**(bitwidth-1)

    if value >= threshold:
        signed_val = value - 2**bitwidth

    else:
        signed_val = value

    return signed_val

def dut_args_setup(input_bitwidth, output_bitwidth, signed_input):
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

    sig_out_upper_bound = 2**(output_bitwidth-1)
    sig_out_lower_bound = -sig_out_upper_bound
    signal_out = Signal(intbv(0, sig_out_lower_bound, sig_out_upper_bound))

    args = {
        'signal_in': signal_in,
        'signal_out': signal_out,
    }

    arg_types = {
        'signal_in': 'custom',
        'signal_out': 'output',
    }

    return args, arg_types

def dut_wrapper_args_setup(
    input_bitwidth, output_bitwidth, signed_input):
    ''' Generate the arguments and argument types for the DUT.
    '''

    args, arg_types = (
        dut_args_setup(
            input_bitwidth, output_bitwidth, signed_input))

    args['clock'] = Signal(False)
    arg_types['clock'] = 'clock'

    return args, arg_types

@block
def signed_sig_assigner_wrapper(clock, signal_in, signal_out):
    return signed_sig_assigner(signal_in, signal_out)

class TestSignedSigAssignerInterface(KeaTestCase):
    ''' The signed_sig_assigner should reject incompatible interfaces and
    arguments.
    '''

    def setUp(self):

        self.dut_args, _dut_arg_types = (
            dut_args_setup(
                input_bitwidth=8, output_bitwidth=8, signed_input=False))

    def test_intbv_ports_checked(self):
        '''The `signal_in` port should be an intbv.

        The `signal_out` port should be an intbv and the range of values
        that `signal_out` can take should include all possible values of
        `signal_in` when interpreted as signed.

        Anything else should raise an error.
        '''

        signal_out_upper_bound = 2**(len(self.dut_args['signal_in'])-1)
        signal_out_lower_bound = -signal_out_upper_bound

        signal_out_required_val_range = (
            signal_out_lower_bound,
            signal_out_upper_bound)

        dut = signed_sig_assigner
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

class TestSignedSigAssigner(KeaTestCase):

    def setUp(self):
        pass

    @block
    def dut_stim_check(self, **dut_wrapper_args):

        clock = dut_wrapper_args['clock']
        signal_in = dut_wrapper_args['signal_in']
        signal_out = dut_wrapper_args['signal_out']

        return_objects = []

        if isinstance(signal_in.val, bool):
            bool_signal_in = True

        else:
            bool_signal_in = False

        expected_signal_out = Signal(intbv(0, signal_out.min, signal_out.max))

        @always(clock.posedge)
        def stim_check():

            if bool_signal_in:
                stim_val = bool(random.randrange(2))

            else:
                stim_val = random.randrange(signal_in.min, signal_in.max)

            signal_in.next = stim_val
            expected_signal_out.next = (
                signed_interpretation(stim_val, len(signal_in)))

            # Check that signal_out is correct
            assert(signal_out == expected_signal_out)

        return_objects.append(stim_check)

        return return_objects

    def base_test(
        self, input_bitwidth=8, output_bitwidth=8, signed_input=False):

        dut_wrapper_args, dut_wrapper_arg_types = (
            dut_wrapper_args_setup(
                input_bitwidth, output_bitwidth, signed_input))

        if not self.testing_using_vivado:
            cycles = 8000
        else:
            cycles = 750

        @block
        def stimulate_check(**dut_wrapper_args):

            return_objects = []

            return_objects.append(self.dut_stim_check(**dut_wrapper_args))

            return return_objects

        dut_outputs, ref_outputs = self.cosimulate(
            cycles, signed_sig_assigner_wrapper, signed_sig_assigner_wrapper,
            dut_wrapper_args, dut_wrapper_arg_types,
            custom_sources=[(stimulate_check, (), dut_wrapper_args)])

        self.assertEqual(dut_outputs, ref_outputs)

    def test_signal_assignment(self):
        '''The `signed_sig_assigner` should asynchronously interpret
        `signal_in` as signed and assign to `signal_out`.
        '''
        self.base_test()

    def test_one_bit_intbv_to_one_bit_intbv(self):
        '''The `signed_sig_assigner` should function correctly when
        `signal_in` is a one bit `intbv` and signal out is a one bit `intbv`.
        '''
        self.base_test(input_bitwidth=1, output_bitwidth=1)

    def test_one_bit_intbv_to_wider_signed_intbv(self):
        '''The `signed_sig_assigner` should function correctly when
        `signal_in` is a one bit `intbv` and signal out is a signed, n bit
        wide `intbv`.
        '''
        self.base_test(input_bitwidth=1, output_bitwidth=2)

    def test_unsigned_two_bit_intbv_to_signed_two_bit_intbv(self):
        '''The `signed_sig_assigner` should function correctly when
        `signal_in` is an unsigned, two bit `intbv` and signal out is a
        signed, two bit wide `intbv`.
        '''
        self.base_test(input_bitwidth=2, output_bitwidth=2)

    def test_unsigned_intbv_to_signed_intbv(self):
        '''The `signed_sig_assigner` should function correctly when
        `signal_in` is an unsigned, n bit `intbv` and signal out is a signed,
        n bit `intbv`.
        '''
        bitwidth = random.randrange(2, 9)
        self.base_test(input_bitwidth=bitwidth, output_bitwidth=bitwidth)

    def test_unsigned_intbv_to_wider_signed_intbv(self):
        '''The `signed_sig_assigner` should function correctly when
        `signal_in` is an unsigned, n bit `intbv` and signal out is a signed
        `intbv` with a bitwdith that is greater than n.
        '''
        input_bitwidth = random.randrange(2, 9)
        output_bitwidth = random.randrange(input_bitwidth+1, 17)
        self.base_test(
            input_bitwidth=input_bitwidth, output_bitwidth=output_bitwidth)

    def test_signed_two_bit_intbv_to_signed_two_bit_intbv(self):
        '''The `signed_sig_assigner` should function correctly when
        `signal_in` is a signed, two bit `intbv` and signal out is a signed,
        two bit wide `intbv`.
        '''
        self.base_test(
            input_bitwidth=2, output_bitwidth=2, signed_input=True)

    def test_signed_intbv_to_signed_intbv(self):
        '''The `signed_sig_assigner` should function correctly when
        `signal_in` is a signed, n bit `intbv` and signal out is a signed, n
        bit `intbv`.
        '''
        bitwidth = random.randrange(2, 9)
        self.base_test(
            input_bitwidth=bitwidth, output_bitwidth=bitwidth,
            signed_input=True)

    def test_signed_intbv_to_wider_signed_intbv(self):
        '''The `signed_sig_assigner` should function correctly when
        `signal_in` is a signed, n bit `intbv` and signal out is a signed
        `intbv` with a bitwdith that is greater than n.
        '''
        input_bitwidth = random.randrange(2, 9)
        output_bitwidth = random.randrange(input_bitwidth+1, 17)
        self.base_test(
            input_bitwidth=input_bitwidth, output_bitwidth=output_bitwidth,
            signed_input=True)

class TestSignedSigAssignerVivadoVhdl(
    KeaVivadoVHDLTestCase, TestSignedSigAssigner):
    pass

class TestSignedSigAssignerVivadoVerilog(
    KeaVivadoVerilogTestCase, TestSignedSigAssigner):
    pass
