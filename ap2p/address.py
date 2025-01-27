"""
A module containing the Address class, which represents a network address.
"""

from asyncio import open_connection, start_server
from dataclasses import dataclass
from ipaddress import ip_address


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

    def __repr__(self):
        """
        Returns a string representation of the Address instance.

        Returns:
            str: The string representation of the Address instance.
        """
        return f"{self.host}:{self.port}"
