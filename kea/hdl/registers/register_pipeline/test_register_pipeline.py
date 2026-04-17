import copy
import random

from collections import deque
from myhdl import Signal, intbv, block, always

from kea.testing.test_utils import (
    KeaTestCase, KeaVivadoVHDLTestCase, KeaVivadoVerilogTestCase,
    generate_value)
from kea.utils.interface_checks import (
    check_bool_or_intbv_signal,
    check_bool_signal,
    check_intbv_signal,
    get_dut_function_call_arguments,
    verify_dut_called_function)

from ._register_pipeline import register_pipeline

def dut_args_setup(signal_factory, n_stages):
    ''' Generate the arguments and argument types for the DUT.
    '''

    assert(n_stages > 0)

    source_data = signal_factory()
    sink_data = signal_factory()

    dut_args = {
        'clock': Signal(False),
        'reset': Signal(False),
        'enable': Signal(False),
        'source_data': source_data,
        'sink_data': sink_data,
        'n_stages': n_stages,
    }

    dut_arg_types = {
        'clock': 'clock',
        'reset': 'custom',
        'enable': 'custom',
        'source_data': 'custom',
        'sink_data': 'output',
        'n_stages': 'non-signal',
    }

    return dut_args, dut_arg_types

class TestRegisterPipelineInterface(KeaTestCase):

    def setUp(self):
        signal_factory = lambda: Signal(intbv(0)[8:])
        n_stages = 4

        self.dut_args, _dut_arg_types = (
            dut_args_setup(signal_factory, n_stages))

    def test_zero_n_stages(self):
        ''' The `register_pipeline` should raise an error if `n_stages` is
        0.
        '''
        self.dut_args['n_stages'] = 0

        self.assertRaisesRegex(
            ValueError,
            ('register_pipeline: n_stages should be greater than 0.'),
            register_pipeline,
            **self.dut_args,
        )

    def test_negative_n_stages(self):
        ''' The `register_pipeline` should raise an error if `n_stages` is
        less than 0.
        '''
        self.dut_args['n_stages'] = random.randrange(-100, 0)

        self.assertRaisesRegex(
            ValueError,
            ('register_pipeline: n_stages should be greater than 0.'),
            register_pipeline,
            **self.dut_args,
        )

    def test_bool_or_intbv_ports_checked(self):
        '''The `source_data` port should be a boolean or intbv signal.

        Anything else should raise an error.
        '''
        dut = register_pipeline
        port_names = ['source_data']

        # Get all calls to check_bool_signal made by the DUT
        dut_function_call_arguments_list = (
            get_dut_function_call_arguments(
                check_bool_or_intbv_signal, dut, self.dut_args))

        for port_name in port_names:
            expected_args_dict = {
                'test_signal': self.dut_args[port_name],
                'name': port_name,
            }

            # Check that the specified port was checked
            verify_dut_called_function(
                check_bool_or_intbv_signal, dut_function_call_arguments_list,
                expected_args_dict, 'test_signal', port_name)

    def test_intbv_ports_checked(self):
        '''If the `source_data` port is an `intbv` signal then the
        `sink_data` should be an `intbv` with a matching data range.

        Anything else should raise an error.
        '''
        upper_bound = 2**random.randrange(1, 17)
        lower_bound = -upper_bound

        signal_factory = lambda: Signal(intbv(0, lower_bound, upper_bound))
        n_stages = 4

        self.dut_args, _dut_arg_types = (
            dut_args_setup(signal_factory, n_stages))

        dut = register_pipeline
        intbv_port_requirements = {
            'sink_data': {
                'val_range': (lower_bound, upper_bound),
                'range_test': 'exact',
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

    def test_bool_ports_checked(self):
        '''If the `source_data` port is a boolean signal then the `sink_data`
        port should be a boolean signal.

        Anything else should raise an error.
        '''

        signal_factory = lambda: Signal(False)
        n_stages = 4

        self.dut_args, _dut_arg_types = (
            dut_args_setup(signal_factory, n_stages))

        dut = register_pipeline
        bool_port_names = ['sink_data']

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

class TestRegisterPipeline(KeaTestCase):

    @block
    def dut_stim(self, **dut_args):
        ''' A block to stim the inputs to the DUT.
        '''
        clock = dut_args['clock']
        reset = dut_args['reset']
        enable = dut_args['enable']
        source_data = dut_args['source_data']

        return_objects = []

        if isinstance(source_data.val, intbv):
            data_lower_bound = source_data.min
            data_upper_bound = source_data.max

            intbv_signal = True

        else:
            intbv_signal = False

        @always(clock.posedge)
        def stim():

            if reset:
                if random.random() < 0.3:
                    reset.next = False

            else:
                if random.random() < 0.01:
                    reset.next = True

            if enable:
                if random.random() < 0.02:
                    enable.next = False

            else:
                if random.random() < 0.08:
                    enable.next = True

            if intbv_signal:
                source_data.next = (
                    generate_value(
                        data_lower_bound, data_upper_bound, 0.1, 0.1))

            else:
                source_data.next = bool(random.randrange(2))

        return_objects.append(stim)

        return return_objects

    @block
    def dut_check(self, **dut_args):
        ''' Check the outputs of the DUT.
        '''

        clock = dut_args['clock']
        reset = dut_args['reset']
        enable = dut_args['enable']
        source_data = dut_args['source_data']
        sink_data = dut_args['sink_data']
        n_stages = dut_args['n_stages']

        return_objects = []

        if isinstance(source_data.val, intbv):
            expected_sink_data = (
                Signal(intbv(0, source_data.min, source_data.max)))

        else:
            expected_sink_data = Signal(False)

        if n_stages > 1:
            pipeline_len = n_stages-1
            pipeline = deque([0]*pipeline_len, maxlen=pipeline_len)

        @always(clock.posedge)
        def check():

            assert(sink_data == expected_sink_data)

            if enable:

                if n_stages > 1:
                    # Get the next value out of the pipeline then add the new
                    # value. Because pipeline has a maxlen, this will remove
                    # the oldest value in the pipeline.
                    expected_sink_data.next = pipeline[0]
                    pipeline.append(copy.copy(source_data.val))

                else:
                    expected_sink_data.next = source_data

            if reset:
                expected_sink_data.next = 0

                if n_stages > 1:
                    for n in range(n_stages):
                        # Reset all values in the pipeline to 0
                        pipeline.append(0)

        return_objects.append(check)

        return return_objects

    def base_test(self, signal_factory, n_stages):

        dut_args, dut_arg_types = dut_args_setup(signal_factory, n_stages)

        if not self.testing_using_vivado:
            cycles = 5000

        else:
            cycles = 1000

        @block
        def stimulate_check(**dut_args):

            return_objects = []

            return_objects.append(self.dut_stim(**dut_args))
            return_objects.append(self.dut_check(**dut_args))

            return return_objects

        dut_outputs, ref_outputs = self.cosimulate(
            cycles, register_pipeline, register_pipeline, dut_args,
            dut_arg_types, custom_sources=[(stimulate_check, (), dut_args)])

        self.assertEqual(dut_outputs, ref_outputs)

    def test_bool_data(self):
        ''' The `register_pipeline` should instantiate a pipeline of
        `n_stages`.

        When `reset` is set high all registers in the pipeline should be reset
        to 0.

        When `enable` is set high, data should shift through the registers in
        the pipeline.

        Note: `n_stages` can also be considered the number of cycles between
        `source_data` being clocked in to the `register_pipeline` and it being
        assigned to `sink_data`

        The `register_pipeline` should function correctly when the
        `source_data` and `sink_data` are boolean signals.
        '''
        self.base_test(
            signal_factory=lambda: Signal(False),
            n_stages=4)

    def test_one_bit_data(self):
        ''' The `register_pipeline` should function correctly when the
        `source_data` and `sink_data` are 1 bit wide `intbv` signals.
        '''
        self.base_test(
            signal_factory=lambda: Signal(intbv(0)[1:]),
            n_stages=4)

    def test_random_bitwidth_data(self):
        ''' The `register_pipeline` should function correctly for any bitwidth
        of `source_data` and `sink_data`.
        '''
        data_bitwidth = random.randrange(2, 17)
        self.base_test(
            signal_factory=lambda: Signal(intbv(0)[data_bitwidth:]),
            n_stages=4)

    def test_one_bit_unsigned_data(self):
        ''' The `register_pipeline` should function correctly when the
        `source_data` and `sink_data` are 1 bit wide unsigned `intbv` signals.
        '''
        self.base_test(
            signal_factory=lambda: Signal(intbv(0, 0, 2)),
            n_stages=4)

    def test_random_bitwidth_unsigned_data(self):
        ''' The `register_pipeline` should function correctly when the
        `source_data` and `sink_data` are n bit wide unsigned `intbv` signals.
        '''
        data_bitwidth = random.randrange(2, 17)
        data_upper_bound = 2**(data_bitwidth-1)
        data_lower_bound = 0

        self.base_test(
            signal_factory=(
                lambda: Signal(intbv(0, data_lower_bound, data_upper_bound))),
            n_stages=4)

    def test_one_bit_signed_data(self):
        ''' The `register_pipeline` should function correctly when the
        `source_data` and `sink_data` are 1 bit wide signed `intbv` signals.
        '''
        self.base_test(
            signal_factory=lambda: Signal(intbv(0, -1, 1)),
            n_stages=4)

    def test_random_bitwidth_signed_data(self):
        ''' The `register_pipeline` should function correctly when the
        `source_data` and `sink_data` are n bit wide signed `intbv` signals.
        '''
        data_bitwidth = random.randrange(2, 17)
        data_upper_bound = 2**(data_bitwidth-1)
        data_lower_bound = -data_upper_bound

        self.base_test(
            signal_factory=(
                lambda: Signal(intbv(0, data_lower_bound, data_upper_bound))),
            n_stages=4)

    def test_one_stage(self):
        ''' The `register_pipeline` should function correctly when the
        `n_stages` is set to 1.

        When `n_stages` is set to 1 the `register_pipeline` should assign
        `source_data` to `sink_data` on the next rising edge of `clock`.
        '''
        self.base_test(
            signal_factory=lambda: Signal(intbv(0)[4:]),
            n_stages=1)

    def test_two_stages(self):
        ''' The `register_pipeline` should function correctly when the
        `n_stages` is set to 2.
        '''
        self.base_test(
            signal_factory=lambda: Signal(intbv(0)[4:]),
            n_stages=2)

    def test_random_n_stages(self):
        ''' The `register_pipeline` should function correctly for any value of
        `n_stages`.
        '''
        n_stages = random.randrange(3, 9)
        self.base_test(
            signal_factory=lambda: Signal(intbv(0)[4:]),
            n_stages=n_stages)

class TestRegisterPipelineVivadoVHDL(
    KeaVivadoVHDLTestCase, TestRegisterPipeline):
    pass

class TestRegisterPipelineVivadoVerilog(
    KeaVivadoVerilogTestCase, TestRegisterPipeline):
    pass
