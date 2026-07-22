from .ethernet_constants import (
    DEST_MAC_N_OCTETS,
    SRC_MAC_N_OCTETS,
    ETHERTYPE_N_OCTETS,
    ETHERNET_HEADER_N_OCTETS,
    DEST_MAC_BITWIDTH,
    SRC_MAC_BITWIDTH,
    ETHERTYPE_BITWIDTH,
    ETHERNET_HEADER_N_BITS,
)
from ._ethernet_framer import ethernet_framer
from .interfaces import EthernetHeaderValuesInterface
from .test_utils import extract_packet_fields
