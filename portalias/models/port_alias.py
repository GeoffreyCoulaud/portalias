from typing import TypedDict


class PortAlias(TypedDict):
    ip_address: str
    port: int
    aliases: list[int]
    protocols: list[str]
