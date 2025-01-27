import pytest
from test_utils import localhost_address, random_port

from ap2p.node import Node


@pytest.mark.asyncio(loop_scope="session")
async def test_node_discover_peers():
    """
    Test that a node can discover peers from a list of bytes.
    """
    port1 = random_port()
    address1 = localhost_address(port1)
    node = Node(address1)

    port2 = random_port(exclude_ports={port1})
    address2 = localhost_address(port2)
    address2_bytes = bytes(address2)

    peers = await node.discover_peers([address2_bytes])
    assert address2 in peers

    await node.stop()


@pytest.mark.asyncio(loop_scope="session")
async def test_node_send_back_connect():
    """
    Test that a node can send a back-connect message to a peer.
    """
    port = random_port()
    address = localhost_address(port)
    node = Node(address)

    async def handle_client(reader, writer):
        data = await reader.read(100)
        assert data.startswith(b"HELO")
        writer.close()

    server = await address.serve(handle_client)
    peer_address = localhost_address(port)
    _, writer = await peer_address.connect()
    await node.send_back_connect(writer)
    writer.close()
    await writer.wait_closed()
    server.close()
    await server.wait_closed()

    await node.stop()
