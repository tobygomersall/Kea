import random

from myhdl import *

from kea.testing.test_utils.base_test import (
    KeaTestCase, KeaVivadoVHDLTestCase, KeaVivadoVerilogTestCase)

from ._synchronous_signal_slicer import synchronous_signal_slicer

def test_args_setup():
    ''' Generate the arguments and argument types for the DUT.
    '''

    clock = Signal(False)

    # Choose a random signal in width
    signal_in_bitwidth = random.randrange(1, 32)
    signal_in = Signal(intbv(0)[signal_in_bitwidth: 0])

    # Choose random slice offset and bitwidth
    slice_offset = random.randrange(0, signal_in_bitwidth)

    # Create a valid signal_out
    signal_out_bitwidth = (
        random.randrange(1, signal_in_bitwidth-slice_offset+1))
    signal_out = Signal(intbv(0)[signal_out_bitwidth: 0])

    # Define the default arguments for the DUT
    args = {
        'clock': clock,
        'signal_in': signal_in,
        'slice_offset': slice_offset,
        'signal_out': signal_out,
    }

    arg_types = {
        'clock': 'clock',
        'signal_in': 'custom',
        'slice_offset': 'non-signal',
        'signal_out': 'output',
    }

    return args, arg_types

class TestSignalSlicerInterface(KeaTestCase):
    ''' The synchronous_signal_slicer should reject incompatible interfaces
    and arguments.
    '''

    def setUp(self):

        self.args, _arg_types = test_args_setup()

    def test_negative_slice_offset(self):
        ''' The `synchronous_signal_slicer` should raise an error if the
        `slice_offset` is less than 0.
        '''

        # Generate a negative slice offset
        self.args['slice_offset'] = random.randrange(-100, 0)

        # Check that the system errors
        self.assertRaisesRegex(
            ValueError,
            ('synchronous_signal_slicer: slice_offset must not be negative'),
            synchronous_signal_slicer,
            **self.args,)

    def test_invalid_slice_offset(self):
        ''' The `synchronous_signal_slicer` should raise an error if the
        `slice_offset` is greater than the `signal_in` bit width.
        '''

        # Generate an invalid slice offset
        signal_in_bitwidth = len(self.args['signal_in'])
        self.args['slice_offset'] = (
            random.randrange(signal_in_bitwidth, 2*(signal_in_bitwidth+1)))

        # Check that the system errors
        self.assertRaisesRegex(
            ValueError,
            ('synchronous_signal_slicer: slice_offset must be less than the '
            'signal_in width'),
            synchronous_signal_slicer,
            **self.args,)

    def test_invalid_bitfield(self):
        ''' The `synchronous_signal_slicer` should raise an error if the
        combination of `slice_offset` and `signal_out` bitwidth result in any
        bits of the slice exceeding the bit width of the `signal_in`.
        '''

        # Generate an invalid bitwidth
        min_invalid_bitwidth = (
            len(self.args['signal_in']) - self.args['slice_offset'] + 1)

        signal_out_bitwidth = (
            random.randrange(min_invalid_bitwidth, min_invalid_bitwidth+10))
        self.args['signal_out'] = Signal(intbv(0)[signal_out_bitwidth:])

        # Check that the system errors
        self.assertRaisesRegex(
            ValueError,
            ('synchronous_signal_slicer: Slice bitfield must fit within '
             'signal_in'),
            synchronous_signal_slicer,
            **self.args,)

class TestSignalSlicer(KeaTestCase):

    def setUp(self):

        self.args, self.arg_types = test_args_setup()

    @block
    def check_synchronous_signal_slicer(self, **kwargs):

        clock = kwargs['clock']
        signal_in = kwargs['signal_in']
        slice_offset = kwargs['slice_offset']
        signal_out = kwargs['signal_out']

        expected_output_val = Signal(intbv(0)[len(signal_out):0])

        signal_in_upper_bound = 2**len(signal_in)

        slice_bitwidth = len(signal_out)
        slice_mask = 2**slice_bitwidth - 1

        @always(clock.posedge)
        def stim_check():

            # Randomly drive signal_in
            signal_in.next = random.randrange(0, signal_in_upper_bound)

            # Shift and mask the input value to get the expected output
            # value
            expected_output_val.next = (
                (signal_in >> slice_offset) & slice_mask)

            # Check that signal out always equals the expected output
            assert(signal_out == expected_output_val)

        return stim_check

    def test_random_bitfields(self):
        ''' The `synchronous_signal_slicer` should use `slice_offset` and
        the `signal_out` bitwidth to extract a slice out of `signal_in`. This
        slice should be synchronously assigned to `signal_out`.
        '''

        cycles = 2000

        @block
        def stimulate_check(**kwargs):

            return self.check_synchronous_signal_slicer(**kwargs)

        dut_outputs, ref_outputs = self.cosimulate(
            cycles, synchronous_signal_slicer, synchronous_signal_slicer,
            self.args, self.arg_types,
            custom_sources=[(stimulate_check, (), self.args)])

        self.assertEqual(dut_outputs, ref_outputs)

    def test_max_offset(self):
        ''' The `synchronous_signal_slicer` should work correctly with a
        `slice_offset` which is equal to the highest bit index in `signal_in`.
        '''

        signal_out_bitwidth = 1

        # Modify the arguments to test the required behaviour
        self.args['slice_offset'] = len(self.args['signal_in']) - 1
        self.args['signal_out'] = Signal(intbv(0)[signal_out_bitwidth: 0])

        cycles = 2000

        @block
        def stimulate_check(**kwargs):

            return self.check_synchronous_signal_slicer(**kwargs)

        dut_outputs, ref_outputs = self.cosimulate(
            cycles, synchronous_signal_slicer, synchronous_signal_slicer,
            self.args, self.arg_types,
            custom_sources=[(stimulate_check, (), self.args)])

        self.assertEqual(dut_outputs, ref_outputs)

    def test_max_bitwidth(self):
        ''' The `synchronous_signal_slicer` should work correctly with a
        `slice_offset` of 0 and a `signal_out` bitwidth which is equal to the
        bitwidth of `signal_in`.
        '''

        signal_out_bitwidth = len(self.args['signal_in'])

        # Modify the arguments to test the required behaviour
        self.args['slice_offset'] = 0
        self.args['signal_out'] = Signal(intbv(0)[signal_out_bitwidth: 0])

        cycles = 2000

        @block
        def stimulate_check(**kwargs):

            return self.check_synchronous_signal_slicer(**kwargs)

        dut_outputs, ref_outputs = self.cosimulate(
            cycles, synchronous_signal_slicer, synchronous_signal_slicer,
            self.args, self.arg_types,
            custom_sources=[(stimulate_check, (), self.args)])

        self.assertEqual(dut_outputs, ref_outputs)

    def test_bool_output(self):
        ''' The `synchronous_signal_slicer` should work correctly with a
        boolean `signal_out`.
        '''

        # Modify the arguments to test the required behaviour
        self.args['slice_offset'] = (
            random.randrange(len(self.args['signal_in'])))
        self.args['signal_out'] = Signal(False)

        cycles = 2000

        @block
        def stimulate_check(**kwargs):

            return self.check_synchronous_signal_slicer(**kwargs)

        dut_outputs, ref_outputs = self.cosimulate(
            cycles, synchronous_signal_slicer, synchronous_signal_slicer,
            self.args, self.arg_types,
            custom_sources=[(stimulate_check, (), self.args)])

        self.assertEqual(dut_outputs, ref_outputs)

class TestSignalSlicerVivadoVhdl(KeaVivadoVHDLTestCase, TestSignalSlicer):
    pass

class TestSignalSlicerVivadoVerilog(
    KeaVivadoVerilogTestCase, TestSignalSlicer):
    pass
