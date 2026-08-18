from myhdl import block, Signal, intbv, enum, always

from kea.hdl.axi.axi_stream_utils import (
    check_axi_stream_interface_attributes)
from kea.hdl.logic.asynchronous import reducing_and
from kea.hdl.signal_handling import sig_assigner
from kea.utils.interface_checks import check_bool_signal

@block
def axis_ramp_driver(clock, enable, axis_ramp):

    check_bool_signal(clock, 'clock')
    check_bool_signal(enable, 'enable')

    expected_axis_attributes = {
        'TID_width': None,
        'TDEST_width': None,
        'TUSER_width': None,
        'TVALID_init': False,
        'TREADY_init': False,
        'use_TLAST': True,
        'use_TSTRB': False,
        'use_TKEEP': False
    }

    check_axi_stream_interface_attributes(
        expected_axis_attributes, axis_ramp)

    return_objects = []

    internal_axis_ramp_tvalid = Signal(False)
    return_objects.append(
        sig_assigner(internal_axis_ramp_tvalid, axis_ramp.TVALID))

    internal_axis_ramp_tdata = Signal(intbv(0)[len(axis_ramp.TDATA):])
    return_objects.append(
        sig_assigner(internal_axis_ramp_tdata, axis_ramp.TDATA))

    wrap = Signal(False)
    return_objects.append(reducing_and(wrap, internal_axis_ramp_tdata))

    t_state = enum('IDLE', 'RAMPING')
    state = Signal(t_state.IDLE)

    @always(clock.posedge)
    def ramper():

        axis_ramp.TLAST.next = False

        if state == t_state.IDLE:
            if enable:
                # Enabled so start ramping the output
                internal_axis_ramp_tvalid.next = True
                state.next = t_state.RAMPING

        elif state == t_state.RAMPING:
            if internal_axis_ramp_tvalid and axis_ramp.TREADY:
                if wrap:
                    # The data value should wrap
                    internal_axis_ramp_tdata.next = 0

                else:
                    # Increment the data value
                    internal_axis_ramp_tdata.next = (
                        internal_axis_ramp_tdata + 1)

        if not enable:
            # The ramp has been disabled
            internal_axis_ramp_tvalid.next = False
            internal_axis_ramp_tdata.next = 0
            state.next = t_state.IDLE

    return_objects.append(ramper)

    return return_objects
