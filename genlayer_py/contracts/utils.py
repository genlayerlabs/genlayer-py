from typing import Optional, List, Dict
from genlayer_py.types import CalldataEncodable


def make_calldata_object(
    method: Optional[str] = None,
    args: Optional[List[CalldataEncodable]] = None,
    kwargs: Optional[Dict[str, CalldataEncodable]] = None,
) -> CalldataEncodable:
    ret: Dict[str, CalldataEncodable] = {}
    if method is not None:
        ret["method"] = method
    if args is not None and len(args) > 0:
        ret["args"] = args
    if kwargs is not None and isinstance(kwargs, dict) and kwargs:
        ret["kwargs"] = kwargs
    return ret
