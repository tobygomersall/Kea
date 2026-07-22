from myhdl import Signal

class EthernetStatusInterface(object):
    '''An interface that carries the ethernet status.
    '''

    def __init__(self):

        self.mac_clock_locked = Signal(False)
        self.sfp_rx_loss_of_signal = Signal(False)
        self.sfp_module_absent = Signal(False)
        self.sfp_tx_fault = Signal(False)
