# { "Depends": "py-genlayer:test" }

import genlayer as gl
from genlayer.types import *


class Other(gl.contract.Contract):
    data: str

    def __init__(self, data: str):
        self.data = data

    @gl.public.view
    def test(self) -> str:
        return self.data
