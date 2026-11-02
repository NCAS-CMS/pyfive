import struct
from pyfive.dataobjects import DataObjects


def test_attr_info_message_flags_zero_no_overrun():
    """Test that _get_attributes_from_attr_info correctly parses an
    ATTR_INFO_MESSAGE with flags=0 (18 bytes) without attempting to
    unpack optional creation order fields past the end of the message
    buffer.

    """
    UNDEFINED_ADDRESS = 0xFFFFFFFFFFFFFFFF

    # Version 0, Flags 0: 1B version + 1B flags + 8B heap address + 8B
    # name btree address. Total length = 18 bytes
    msg = struct.pack("<BBQQ", 0, 0, UNDEFINED_ADDRESS, UNDEFINED_ADDRESS)

    obj = DataObjects.__new__(DataObjects)
    obj.msg_data = msg

    result = obj._get_attributes_from_attr_info({}, [{"offset_to_message": 0}])
    assert result == {}
