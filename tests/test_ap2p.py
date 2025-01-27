from asyncio import sleep

import pytest

from tests.test_utils import (
    EPS_SLEEP_SECONDS,
    connect_to_peers_explicitly,
    generate_node,
)


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize("node_count", [1, 2, 3, 4])
@pytest.mark.parametrize("use_known_peers", [False, True])
@pytest.mark.parametrize("use_discovery", [False, True])
async def test_nodes_connect(node_count, use_known_peers, use_discovery):
    """
    Test that nodes can connect to each other.
    """
    nodes = []
    tasks = []

    for _ in range(node_count):
        tasks.append(await generate_node(nodes, use_known_peers, use_discovery))

    # wait for the nodes to connect to each other
    await sleep(EPS_SLEEP_SECONDS)

    if not use_known_peers:
        # connect each node to every other node after they have started
        for i in range(node_count):
            await connect_to_peers_explicitly(nodes, i, use_discovery)

    # every node should have connected to every other node
    for node1 in nodes:
        for node2 in nodes:
            if node1.address != node2.address:
                assert node2.address in node1.peers
                assert node1.address in node2.peers

    # cleanup
    for node in nodes:
        await node.stop()
    for task in tasks:
        task.cancel()


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize("node_count", [1, 2, 3, 4])
@pytest.mark.parametrize("use_known_peers", [False, True])
@pytest.mark.parametrize("use_discovery", [False, True])
async def test_nodes_disconnect_and_reconnect(
    node_count, use_known_peers, use_discovery
):
    """
    Test that nodes can disconnect and reconnect to each other, and that they
    discover each other again after reconnecting.
    """
    nodes = []
    tasks = []

    # Generate one extra node, which will be used to test that the other nodes
    # disconnect from it and reconnect to it correctly.
    for _ in range(node_count + 1):
        tasks.append(await generate_node(nodes, use_known_peers, use_discovery))

    # wait for the nodes to connect to each other
    await sleep(EPS_SLEEP_SECONDS)

    if not use_known_peers:
        # connect each node to every other node after they have started
        for i in range(node_count + 1):
            await connect_to_peers_explicitly(nodes, i, use_discovery)

    # wait for the final node to connect to the other nodes
    await sleep(EPS_SLEEP_SECONDS)

    # # every node should have connected to the final node
    address = nodes[-1].address
    for node in nodes[:-1]:
        assert address in node.peers

    await nodes[-1].stop()
    tasks[-1].cancel()
    nodes = nodes[:-1]
    tasks = tasks[:-1]
    await sleep(EPS_SLEEP_SECONDS)

    # # every node should have disconnected from the final node
    for node in nodes:
        assert address not in node.peers

    # reconnect the final node
    tasks.append(await generate_node(nodes, use_known_peers, use_discovery, address))

    await sleep(EPS_SLEEP_SECONDS)

    if not use_known_peers:
        await connect_to_peers_explicitly(nodes, len(nodes) - 1, use_discovery)

    # wait for the final node to connect to the other nodes again
    await sleep(EPS_SLEEP_SECONDS)

    # # every node should have reconnected to the final node
    address = nodes[-1].address
    for node in nodes[:-1]:
        assert address in node.peers

    # cleanup
    for node in nodes:
        await node.stop()
    for task in tasks:
        task.cancel()
