from asyncio import StreamReader, StreamWriter

import pytest

from ap2p.address import Address
from tests.test_utils import LOCALHOST, LOCALHOST_STR, localhost_address, random_port

EXAMPLE_PORT = 54321
# bytes representation of LOCALHOST:EXAMPLE_PORT
ADDR_BYTES = b"fwAAAdQx"


def test_address_from_bytes():
    """
    Test that an address can be created from bytes.
    """
    address = Address.from_bytes(ADDR_BYTES)
    assert address.host == LOCALHOST
    assert address.port == EXAMPLE_PORT


def test_address_to_bytes():
    """
    Test that an address can be converted to bytes.
    """
    address = localhost_address(EXAMPLE_PORT)
    addr_bytes = bytes(address)
    assert addr_bytes == ADDR_BYTES


@pytest.mark.asyncio(loop_scope="session")
async def test_offline_address_connect():
    """
    Test that an address cannot connect to a non-existent server.
    """
    address = localhost_address(random_port())
    with pytest.raises(ConnectionRefusedError):
        await address.connect()


@pytest.mark.asyncio(loop_scope="session")
async def test_online_address_connect():
    """
    Test that an address can connect to a server.
    """

    async def handle_client(reader, writer):
        data = await reader.read(100)
        writer.write(data)
        await writer.drain()
        writer.close()

    port = random_port()
    address = localhost_address(port)
    await address.serve(handle_client)
    reader, writer = await address.connect()
    assert isinstance(reader, StreamReader)
    assert isinstance(writer, StreamWriter)
    writer.close()
    await writer.wait_closed()


@pytest.mark.asyncio(loop_scope="session")
async def test_address_serve():
    """
    Test that an address can serve a client.
    """

    async def handle_client(reader, writer):
        data = await reader.read(100)
        writer.write(data)
        await writer.drain()
        writer.close()

    port = random_port()
    address = localhost_address(port)
    server = await address.serve(handle_client)
    assert server.sockets[0].getsockname() == (LOCALHOST_STR, port)
    server.close()
    await server.wait_closed()
