from myhdl import block, Signal, intbv, always, always_comb, enum

from kea.hdl.axi.axi_stream_utils import check_axi_stream_interface_attributes
from kea.hdl.logic.asynchronous import and_gate
from kea.hdl.signal_handling.asynchronous import sig_assigner
from kea.utils.interface_checks import check_bool_signal, check_intbv_signal

@block
def axis_chunker(clock, reset, n_words_per_chunk, axis_source, axis_sink):
    ''' This block will chunk an AXI stream packet into smaller packets based
    on `n_words_per_chunk`.
    '''

    check_bool_signal(clock, 'clock')
    check_bool_signal(reset, 'reset')

    check_intbv_signal(n_words_per_chunk, 'n_words_per_chunk', signed=False)

    expected_axis_attributes = {
        'TID_width': None,
        'TDEST_width': None,
        'TUSER_width': None,
        'TVALID_init': False,
        'TREADY_init': False,
        'use_TLAST': True,
        'use_TSTRB': False,
        'use_TKEEP': False,
    }

    check_axi_stream_interface_attributes(
        expected_axis_attributes, axis_source)

    # Check the axis_sink has the same bus width as the axis_source
    expected_axis_attributes['bus_width'] = axis_source.bus_width

    check_axi_stream_interface_attributes(
        expected_axis_attributes, axis_sink)

    return_objects = []

    # Create an internal_source_tready and connect it to the
    # axis_source.TREADY
    internal_source_tready = Signal(False)
    return_objects.append(
        sig_assigner(internal_source_tready, axis_source.TREADY))

    # Create a valid_transaction signal
    valid_transaction = Signal(False)
    return_objects.append(
        and_gate(
            axis_source.TVALID, internal_source_tready, valid_transaction))

    en_axis_connection = Signal(False)

    # Create a signal to record the number of words in each chunk for this
    # packet
    current_n_words_per_chunk = Signal(intbv(0)[len(n_words_per_chunk):])

    # Create a signal so we can count the number of words per chunk
    word_count = Signal(intbv(0)[len(n_words_per_chunk):])

    chunk_tlast = Signal(False)

    t_state = enum('IDLE', 'PACKET_IN_PROGRESS', 'LAST_WORD_OF_CHUNK')
    state = Signal(t_state.IDLE)

    @always(clock.posedge)
    def control():

        if state == t_state.IDLE:

            if valid_transaction:

                # There has been a valid_transaction so data is flowing
                word_count.next = 1

                if not axis_source.TLAST:
                    # It is not a one word packet.

                    if current_n_words_per_chunk <= 2:
                        # We should produce one or two word chunks. Either way
                        # the next word will be the last of the chunk.
                        chunk_tlast.next = True
                        state.next = t_state.LAST_WORD_OF_CHUNK

                    else:
                        # The chunk is not yet complete
                        chunk_tlast.next = False
                        state.next = t_state.PACKET_IN_PROGRESS

        elif state == t_state.PACKET_IN_PROGRESS:

            if valid_transaction:

                # Count the words
                word_count.next = word_count + 1

                if not axis_source.TLAST:
                    # The packet has not finished so carry on chunking the
                    # data

                    if word_count >= current_n_words_per_chunk-2:
                        # The next word will be the last of the chunk.
                        chunk_tlast.next = True
                        state.next = t_state.LAST_WORD_OF_CHUNK

                    else:
                        # We have not yet forwarded a chunks worth of data
                        chunk_tlast.next = False
                        state.next = t_state.PACKET_IN_PROGRESS

                else:
                    # The last word of the source packet has been received
                    state.next = t_state.IDLE

        elif state == t_state.LAST_WORD_OF_CHUNK:

            if valid_transaction:

                # Reset the word_count for the next chunk
                word_count.next = 0

                if not axis_source.TLAST:
                    # This is not the last word of the packet so carry on
                    # chunking the data

                    if current_n_words_per_chunk <= 1:
                        # The chunks should be one word so all words are the
                        # last word of the chunk
                        chunk_tlast.next = True
                        state.next = t_state.LAST_WORD_OF_CHUNK

                    else:
                        # There should be more than one word in the chunk
                        chunk_tlast.next = False
                        state.next = t_state.PACKET_IN_PROGRESS

                else:
                    # The last word of the source packet has been received
                    state.next = t_state.IDLE


        if ((state==t_state.IDLE and not valid_transaction) or
            (valid_transaction and axis_source.TLAST)):

            # Either we are in the idle state and there hasn't been a valid
            # transaction or there has been a valid transaction but it was the
            # last word of the source packet.
            #
            # When in the idle state we need to keep updating the
            # current_n_words_per_chunk until a valid transaction occurs. Once
            # a valid transaction has occured, a word has been accepted based
            # on the n_words_per_chunk at the time of the previous clock edge.
            # So we should make use of that n_words_per_chunk for the entire
            # packet.
            #
            # When we see the last word of a source packet we need to update
            # current_n_words_per_chunk ready for the next packet. This is
            # true if we are in idle (and it is a one word packet) or not.
            current_n_words_per_chunk.next = n_words_per_chunk

            if n_words_per_chunk == 0:
                # n_words_per_chunk is set to 0 so block the stream
                en_axis_connection.next = False
                chunk_tlast.next = False

            elif n_words_per_chunk == 1:
                # n_words_per_chunk is set to 1 so enable the stream and
                # hold TLAST high for every word.
                en_axis_connection.next = True
                chunk_tlast.next = True

            else:
                # n_words_per_chunk is greater than 1 so enable the stream
                # and set TLAST low.
                en_axis_connection.next = True
                chunk_tlast.next = False

        if reset:
            en_axis_connection.next = False
            state.next = t_state.IDLE

    return_objects.append(control)

    @always_comb
    def axis_connector():

        if en_axis_connection:
            # The axis interface should be connected.

            # Pass the sink TREADY though to the source.
            internal_source_tready.next = axis_sink.TREADY

            # Pass the source TVALID and TDATA through to the sink.
            axis_sink.TVALID.next = axis_source.TVALID
            axis_sink.TDATA.next = axis_source.TDATA

            # Pass the source TLAST though to the sink and or the chunk
            # TLAST signals into it.
            axis_sink.TLAST.next = axis_source.TLAST or chunk_tlast

        else:

            # en_axis_connection is low so the source TREADY and the sink
            # TVALID should be held low.
            internal_source_tready.next = False
            axis_sink.TVALID.next = False

        if reset:
            # Reset the source TREADY and the sink TVALID.
            internal_source_tready.next = False
            axis_sink.TVALID.next = False

    return_objects.append(axis_connector)

    return return_objects
