from genlayer_py.types import CalldataAddress, CalldataEncodable
from collections.abc import Buffer
from typing import Any
from . import consts
from genlayer_py.exceptions import GenLayerError


def decode(mem0: Buffer) -> CalldataEncodable:
    mem: memoryview = memoryview(mem0)

    def read_uleb128() -> int:
        nonlocal mem
        ret = 0
        off = 0
        while True:
            m = mem[0]
            ret = ret | ((m & 0x7F) << off)
            off += 7
            mem = mem[1:]
            if (m & 0x80) == 0:
                break
        return ret

    def impl() -> CalldataEncodable:
        nonlocal mem
        code = read_uleb128()
        typ = code & 0x7
        if typ == consts.TYPE_SPECIAL:
            if code == consts.SPECIAL_NULL:
                return None
            if code == consts.SPECIAL_FALSE:
                return False
            if code == consts.SPECIAL_TRUE:
                return True
            if code == consts.SPECIAL_ADDR:
                ret_addr = mem[: CalldataAddress.SIZE]
                mem = mem[CalldataAddress.SIZE :]
                return CalldataAddress(ret_addr)
            raise GenLayerError(f"Unknown special {bin(code)} {hex(code)}")
        code = code >> 3
        if typ == consts.TYPE_PINT:
            return code
        elif typ == consts.TYPE_NINT:
            return -code - 1
        elif typ == consts.TYPE_BYTES:
            ret_bytes = mem[:code]
            mem = mem[code:]
            return bytes(ret_bytes)
        elif typ == consts.TYPE_STR:
            ret_str = mem[:code]
            mem = mem[code:]
            return str(ret_str, encoding="utf-8")
        elif typ == consts.TYPE_ARR:
            ret_arr = []
            for _i in range(code):
                ret_arr.append(impl())
            return ret_arr
        elif typ == consts.TYPE_MAP:
            ret_dict: dict[str, CalldataEncodable] = {}
            prev = None
            for _i in range(code):
                le = read_uleb128()
                key = str(mem[:le], encoding="utf-8")
                mem = mem[le:]
                if prev is not None:
                    assert prev < key
                prev = key
                assert key not in ret_dict
                ret_dict[key] = impl()
            return ret_dict
        raise GenLayerError(f"invalid type {typ}")

    res = impl()
    if len(mem) != 0:
        raise GenLayerError(f"unparsed end {bytes(mem[:5])!r}... (decoded {res})")
    return res
