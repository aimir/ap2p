"""
A module containing the Address class, which represents a network address.
"""

from asyncio import open_connection, start_server
from base64 import b64decode, b64encode
from dataclasses import dataclass
from ipaddress import ip_address
from struct import pack, unpack


@dataclass(frozen=True)
class Address:
    """
    A class representing a network address, consisting of an IP address and port number.
    """

    host: ip_address
    port: int

    async def connect(self):
        """
        Establish a connection to the address specified by this Address instance.

        Returns:
            A tuple containing a StreamReader and StreamWriter for the connection.
        """
        return await open_connection(str(self.host), self.port)

    async def serve(self, callback):
        """
        Start a server at the address specified by this Address instance.

        Args:
            callback (Callable): A callback function to handle incoming connections.

        Returns:
            asyncio.base_events.Server: The server object.
        """
        return await start_server(callback, host=str(self.host), port=self.port)

    @staticmethod
    def from_bytes(addr_bytes: bytes):
        """
        Convert a 6-byte sequence into an Address instance.

        Args:
            addr_bytes (bytes): A 6-byte sequence representing the IP address
                and port number, encoded in base64.

        Returns:
            Address: An Address instance created from the given bytes.
        """
        unwrapped = b64decode(addr_bytes)
        if len(unwrapped) != 6:
            raise ValueError("Address bytes must be exactly 6 bytes long")
        host = ip_address(unwrapped[0:4])
        port = unpack("!H", unwrapped[4:6])[0]
        return Address(host=host, port=port)

    def __bytes__(self):
        """
        Convert the Address instance to bytes for easy transmission over the network.

        The returned bytes are in the following format:
        - The first 4 bytes represent the packed IP address.
        - The next 2 bytes represent the port number in network byte order.

        Returns:
            bytes: The byte representation of the Address instance.
        """
        return b64encode(self.host.packed + pack("!H", self.port))

    def __repr__(self):
        """
        Returns a string representation of the Address instance.

        Returns:
            str: The string representation of the Address instance.
        """
        return f"{self.host}:{self.port}"
