import random

from myhdl import block, Signal, always, intbv, StopSimulation

from kea.hdl.axi import AxiStreamInterface
from kea.testing.test_utils import axi_stream_types_generator

from kea.testing.test_utils.base_test import (
    KeaTestCase, KeaVivadoVHDLTestCase, KeaVivadoVerilogTestCase)

from ._axis_ramp_driver import axis_ramp_driver

from kea.hdl.axi.axi_stream_utils import (
    check_axi_stream_interface_attributes)
from kea.utils.interface_checks import (
    check_bool_signal,
    get_dut_function_call_arguments,
    verify_dut_called_function)

def dut_args_setup(data_bytewidth):
    ''' Generate the arguments and argument types for the DUT.
    '''

    axis_interface_args = {
        'bus_width': data_bytewidth,
        'TID_width': None,
        'TDEST_width': None,
        'TUSER_width': None,
        'TVALID_init': False,
        'TREADY_init': False,
        'use_TLAST': True,
        'use_TSTRB': False,
        'use_TKEEP': False
    }

    dut_args = {
        'clock': Signal(False),
        'enable': Signal(False),
        'axis_ramp': AxiStreamInterface(**axis_interface_args),
    }

    axis_sink_types = (
        axi_stream_types_generator(
            sink=True,
            TID_width=axis_interface_args['TID_width'],
            TDEST_width=axis_interface_args['TDEST_width'],
            TUSER_width=axis_interface_args['TUSER_width'],
            use_TLAST=axis_interface_args['use_TLAST'],
            use_TSTRB=axis_interface_args['use_TSTRB'],
            use_TKEEP=axis_interface_args['use_TKEEP']))

    dut_arg_types = {
        'clock': 'clock',
        'enable': 'custom',
        'axis_ramp': axis_sink_types,
    }

    return dut_args, dut_arg_types

class TestAxisRampDriverInterface(KeaTestCase):
    ''' The `axis_ramp_driver` block should reject incompatible interfaces
    and arguments.
    '''

    def setUp(self):

        data_bytewidth = 4
        self.dut_args, _dut_arg_types = dut_args_setup(data_bytewidth)

    def test_bool_ports_checked(self):
        '''The `clock` and `enable` ports should be boolean signals.

        Anything else should raise an error.
        '''
        dut = axis_ramp_driver
        bool_port_names = ['clock', 'enable']

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

    def test_axis_attributes_checked(self):
        '''The `axis_ramp` `AxiStreamInterface` should not have a `TID`,
        `TDEST`, `TUSER`, `TSTRB` or `TKEEP`. It should have a `TLAST`. The
        `TVALID` and `TREADY` signals should initialise low.

        Anything else should raise an error.
        '''
        dut = axis_ramp_driver
        axis_interface_expected_attributes = {
            'axis_ramp': {
                'TID_width': None,
                'TDEST_width': None,
                'TUSER_width': None,
                'TVALID_init': False,
                'TREADY_init': False,
                'use_TLAST': True,
                'use_TSTRB': False,
                'use_TKEEP': False,
            },
        }

        # Get all calls to check_axi_stream_interface_attributes made by the
        # DUT
        dut_function_call_arguments_list = (
            get_dut_function_call_arguments(
                check_axi_stream_interface_attributes, dut, self.dut_args))

        for port_name in axis_interface_expected_attributes:
            # Assemble the args that should have been passed to
            # check_axi_stream_interface_attributes
            expected_args_dict = {
                'expected_attributes': (
                    axis_interface_expected_attributes[port_name]),
                'axis_interface': self.dut_args[port_name]
            }

            # Check that the specified port was checked
            verify_dut_called_function(
                check_axi_stream_interface_attributes,
                dut_function_call_arguments_list,
                expected_args_dict, 'axis_interface', port_name)

class TestAxisRampDriver(KeaTestCase):

    def setUp(self):

        self.test_count = 0
        self.tests_complete = False

    @block
    def monitor_tests(self, n_tests, **dut_args):

        clock = dut_args['clock']

        return_objects = []

        @always(clock.posedge)
        def monitor():

            if self.test_count >= n_tests:
                # Check that all the tests are run
                self.tests_complete = True

                raise StopSimulation

        return_objects.append(monitor)

        return return_objects

    @block
    def dut_stim(
        self, enable_high_probability, enable_low_probability,
        tready_probability, **dut_args):

        clock = dut_args['clock']
        enable = dut_args['enable']
        axis_ramp = dut_args['axis_ramp']

        return_objects = []

        @always(clock.posedge)
        def stim():

            ##########
            # Enable #
            ##########

            if enable:
                if random.random() < enable_low_probability:
                    enable.next = False

            else:
                if random.random() < enable_high_probability:
                    enable.next = True

            ##########
            # TREADY #
            ##########

            if random.random() < tready_probability:
                axis_ramp.TREADY.next = True

            else:
                axis_ramp.TREADY.next = False

        return_objects.append(stim)

        return return_objects


    @block
    def dut_check(self, **dut_args):

        clock = dut_args['clock']
        enable = dut_args['enable']
        axis_ramp = dut_args['axis_ramp']

        return_objects = []

        ramp_wrap_val = 2**len(axis_ramp.TDATA) - 1

        expected_axis_ramp_tvalid = Signal(False)
        expected_axis_ramp_tdata = Signal(intbv(0)[len(axis_ramp.TDATA):])

        @always(clock.posedge)
        def check():

            assert(axis_ramp.TVALID == expected_axis_ramp_tvalid)
            assert(axis_ramp.TDATA == expected_axis_ramp_tdata)
            self.assertFalse(axis_ramp.TLAST)

            expected_axis_ramp_tvalid.next = enable

            if enable:
                self.test_count += 1

                if axis_ramp.TVALID and axis_ramp.TREADY:
                    if axis_ramp.TDATA == ramp_wrap_val:
                        # The axis_ramp.TDATA should wrap
                        expected_axis_ramp_tdata.next = 0

                    else:
                        expected_axis_ramp_tdata.next = (
                            expected_axis_ramp_tdata + 1)

            else:
                expected_axis_ramp_tdata.next = 0

        return_objects.append(check)

        return return_objects

    def base_test(
        self, data_bytewidth=4, enable_high_probability=0.01,
        enable_low_probability=0.01, tready_probability=1):

        dut_args, dut_arg_types = dut_args_setup(data_bytewidth)

        if not self.testing_using_vivado:
            cycles = 100000
            n_tests = 6000
        else:
            cycles = 35000
            n_tests = 2000

        @block
        def stimulate_check(**dut_args):

            return_objects = []

            return_objects.append(self.monitor_tests(n_tests, **dut_args))
            return_objects.append(
                self.dut_stim(
                    enable_high_probability, enable_low_probability,
                    tready_probability, **dut_args))
            return_objects.append(self.dut_check(**dut_args))

            return return_objects

        dut_outputs, ref_outputs = self.cosimulate(
            cycles, axis_ramp_driver, axis_ramp_driver, dut_args,
            dut_arg_types, custom_sources=[(stimulate_check, (), dut_args)])

        self.assertTrue(self.tests_complete)
        self.assertEqual(dut_outputs, ref_outputs)

    def test_ramp_drive(self):
        ''' When `enable` is set high the `axis_ramp_driver` should output
        ramp data on the `axis_ramp` interface.
        '''
        self.base_test()

    def test_constant_enable(self):
        ''' The `axis_ramp_driver` should function correctly when `enable` is
        held high.
        '''
        self.base_test(enable_high_probability=1, enable_low_probability=0)

    def test_varying_enable(self):
        ''' The `axis_ramp_driver` should function correctly when `enable` is
        varying rapidly.
        '''
        self.base_test(
            enable_high_probability=0.5, enable_low_probability=0.5)

    def test_varying_tready(self):
        ''' The `axis_ramp_driver` should function correctly when
        `axis_ramp.TREADY` is varying.
        '''
        self.base_test(tready_probability=0.5)

    def test_ramp_wrapping(self):
        ''' The `axis_ramp_driver` should wrap around to 0 when it reaches the
        maximum value that `axis_ramp.TDATA` can carry.
        '''
        self.base_test(
            enable_high_probability=1,
            enable_low_probability=0,
            data_bytewidth=1)

class TestAxisRampDriverVivadoVhdl(
    KeaVivadoVHDLTestCase, TestAxisRampDriver):
    pass

class TestAxisRampDriverVivadoVerilog(
    KeaVivadoVerilogTestCase, TestAxisRampDriver):
    pass
