import random

from unittest.mock import patch, sentinel

from kea.hdl.axi import AxiStreamInterface
from kea.testing.test_utils.base_test import KeaTestCase

from ._ethernet_framer import ethernet_framer
from .test_utils import dut_args_setup

class TestEthernetFramerInterface(KeaTestCase):
    ''' The DUT should reject incompatible interfaces and arguments.
    '''

    def test_invalid_axis_sink_interface(self):
        ''' The `ethernet_framer` should raise an error if the `axis_sink`
        is not an instance of `AxiStreamInterface`.
        '''

        dut_args, _dut_arg_types = dut_args_setup(axis_data_bytewidth=4)

        dut_args['axis_sink'] = random.randrange(0, 100)

        # Check that the system errors
        self.assertRaisesRegex(
            TypeError,
            ('ethernet_framer: axis_sink should be an instance of '
            'AxiStreamInterface'),
            ethernet_framer,
            **dut_args,
        )

class TestEthernetFramer(KeaTestCase):

    def setUp(self):

        self.multi_beat_import_path = patch_location = (
            ethernet_framer.__module__ + '.' + 'multi_beat_framer')
        self.single_beat_import_path = (
            ethernet_framer.__module__ + '.' + 'single_beat_framer')

    def test_multi_beat(self):
        ''' When the bitwdith of `axis_sink.TDATA` is less than
        `ETHERNET_HEADER_N_BITS` the `ethernet_framer` should instantiate
        a `multi_beat_framer`.
        '''

        with patch(self.multi_beat_import_path) as mock_mbf, \
             patch(self.single_beat_import_path) as mock_sbf:

            # Set up the return value for the mock_mbf so we can check that
            # the ethernet_framer actually returns it
            mock_mbf.return_value = sentinel.framer

            # Set up the axis_sink so the ethernet_framer should call the
            # multi_beat_framer
            axis_sink = AxiStreamInterface(bus_width=4)

            # Call the ethernet_framer and keep the result. We have to use
            # `.func` here otherwise myhdl checks that the returned object is
            # a block (which it isn't, it's a mock).
            result = (
                ethernet_framer.func(
                    sentinel.clock,
                    sentinel.reset,
                    sentinel.ethernet_header_values_interface,
                    sentinel.axis_source,
                    axis_sink,
                )
            )

            # Check the mock_mbf was called with the expected arguments
            mock_mbf.assert_called_once_with(
                sentinel.clock,
                sentinel.reset,
                sentinel.ethernet_header_values_interface,
                sentinel.axis_source,
                axis_sink,
            )

            # Check that mock_sbf wasn't called
            mock_sbf.assert_not_called()

            # Check that the ethernet_framer returned the correct thing
            assert result == [sentinel.framer]

    def test_single_beat(self):
        ''' When the bitwdith of `axis_sink.TDATA` is greater than or equal to
        `ETHERNET_HEADER_N_BITS` the `ethernet_framer` should instantiate
        a `single_beat_framer`.
        '''

        with patch(self.multi_beat_import_path) as mock_mbf, \
             patch(self.single_beat_import_path) as mock_sbf:

            # Set up the return value for the mock_sbf so we can check that
            # the ethernet_framer actually returns it
            mock_sbf.return_value = sentinel.framer

            # Set up the axis_sink so the ethernet_framer should call the
            # multi_beat_framer
            axis_sink = AxiStreamInterface(bus_width=16)

            # Call the ethernet_framer and keep the result. We have to use
            # `.func` here otherwise myhdl checks that the returned object is
            # a block (which it isn't, it's a mock).
            result = (
                ethernet_framer.func(
                    sentinel.clock,
                    sentinel.reset,
                    sentinel.ethernet_header_values_interface,
                    sentinel.axis_source,
                    axis_sink,
                )
            )

            # Check the mock_sbf was called with the expected arguments
            mock_sbf.assert_called_once_with(
                sentinel.clock,
                sentinel.reset,
                sentinel.ethernet_header_values_interface,
                sentinel.axis_source,
                axis_sink,
            )

            # Check that mock_mbf wasn't called
            mock_mbf.assert_not_called()

            # Check that the ethernet_framer returned the correct thing
            assert result == [sentinel.framer]
