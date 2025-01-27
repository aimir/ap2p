"""
This file contains type aliases and exceptions used in the project.
"""

from asyncio import StreamWriter
from collections.abc import Awaitable, Callable
from typing import Any

# Type aliases for message handlers
MessageHandler = Callable[[bytes, StreamWriter], Awaitable[Any]]
HandlerDict = dict[bytes, MessageHandler]


class PeerDisconnectedException(Exception):
    """
    An exception raised when a peer disconnects unexpectedly.
    """

    pass
