from myhdl import block, Signal, intbv, always

from kea.utils.interface_checks import (
    check_bool_or_intbv_signal,
    check_bool_signal,
    check_intbv_signal)

@block
def stage(clock, reset, enable, source_data, sink_data):
    ''' A single stage in the `register_pipeline`.
    '''
    if isinstance(sink_data.val, intbv):
        # sink_data is an intbv

        # Check that source_data is also an intbv
        assert(isinstance(source_data.val, intbv))

        # Check that sink_data can carry any value on source_data
        assert(sink_data.max >= source_data.max)
        assert(sink_data.min <= source_data.min)

        # Check that we can assign 0 on reset
        assert(sink_data.max > 0)
        assert(sink_data.min <= 0)

    return_objects = []

    @always(clock.posedge)
    def assigner():

        if enable:
            sink_data.next = source_data

        if reset:
            sink_data.next = 0

    return_objects.append(assigner)

    return return_objects

@block
def register_pipeline(
    clock, reset, enable, source_data, sink_data, n_stages):
    ''' A simple register pipeline of `n_stages`.

    When `reset` is set high all registers in the pipeline will be reset to 0.

    When `enable` is set high, data will shift through the registers in the
    pipeline.
    '''

    if n_stages <= 0:
        raise ValueError(
            'register_pipeline: n_stages should be greater than 0.')

    # Check that source_data is a bool or intbv signal
    check_bool_or_intbv_signal(source_data, 'source_data')

    if isinstance(source_data.val, intbv):
        # source_data is an intbv signal so check that the sink_data can carry
        # any value on source_data
        sink_required_val_range = (source_data.min, source_data.max)
        check_intbv_signal(
            sink_data, 'sink_data', val_range=sink_required_val_range,
            range_test='exact')

        register_sink_datas = [
            Signal(intbv(0, min=source_data.min, max=source_data.max))
            for n in range(n_stages)]

    else:
        # source_data is a boolean signal so check that sink_data is also a
        # boolean signal
        check_bool_signal(sink_data, 'sink_data')

        register_sink_datas = [Signal(False) for n in range(n_stages)]


    return_objects = []

    data_bitwidth = len(source_data)

    for n in range(n_stages):
        if n == 0:
            register_source_data = source_data

        else:
            register_source_data = register_sink_datas[n-1]

        if n == n_stages-1:
            register_sink_data = sink_data

        else:
            register_sink_data = register_sink_datas[n]

        return_objects.append(
            stage(
                clock, reset, enable, register_source_data,
                register_sink_data))

    return return_objects
