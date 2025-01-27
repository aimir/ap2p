"""
This module contains constants and utility functions for the tests.
"""

from asyncio import create_task, sleep
from ipaddress import ip_address
from random import randrange

from ap2p.address import Address
from ap2p.node import Node
from ap2p.peer_discovery import PeerDiscoveryNode

LOCALHOST_STR = "127.0.0.1"
LOCALHOST = ip_address(LOCALHOST_STR)
# long enough to ensure that all peers have time to discover each other
# setting this too low can cause tests to fail, but setting it too high
# can make the tests take a long time to run.
EPS_SLEEP_SECONDS = 0.02


def random_port(exclude_ports: set[int] = {}):
    """
    A random port number between 32768 and 61000, likely to be free on most systems.
    Optionally exclude a set of ports, which is useful for tests that require multiple
    different ports to be used simultaneously.
    """
    port = randrange(32768, 61000)
    while port in exclude_ports:
        port = randrange(32768, 61000)
    return port


def localhost_address(port: int):
    """
    Create an address for localhost with the given port.
    """
    return Address(LOCALHOST, port)


async def generate_node(peers, use_known_peers, use_discovery, address=None):
    """
    Generate a node with the given parameters and peers list.
    If use_discovery is True, the node will be only be told about the first peer
    and will discover the rest through peer discovery, otherwise it will be told
    about all the peers.
    If use_known_peers is True, the node will be told about said peers when it
    starts, otherwise it will happen outside this function.
    If an address is not provided, a localhost address with a random port that
    is not in use by any of the peers will be generated.
    The resulting node is added to the peers list, and a task is created to
    start it. The task is returned for later cancellation during cleanup.
    """
    addresses = [peer.address for peer in peers]

    NodeType = PeerDiscoveryNode if use_discovery else Node
    if address is None:
        port = random_port(exclude_ports={address.port for address in addresses})
        address = localhost_address(port)
    node = NodeType(address)
    known_peers = set()
    if use_known_peers:
        if use_discovery:
            # Only tell the node about the last known peer
            known_peers = [addresses[-1]] if addresses else []
        else:
            # tell the node about all the other nodes
            known_peers = addresses
    task = create_task(node.start(known_peers))
    if use_discovery and use_known_peers:
        # wait for the node to discover the other nodes before continuing
        await sleep(EPS_SLEEP_SECONDS)
    peers.append(node)
    return task


async def connect_to_peers_explicitly(nodes, index, use_discovery):
    """
    Connect the node at the given index in the node list to every other node.
    If use_discovery is True, each node will only be told about the previous
    node (if such a node exists) and will discover the rest through peer
    discovery, otherwise they will be told about all the other nodes.
    """
    if use_discovery:
        # Only tell the node about the last known peer
        if index > 0:
            await nodes[index].connect_to_peer(nodes[index - 1].address)
            # wait for the peer discovery:
            await sleep(EPS_SLEEP_SECONDS)
    else:
        # tell the node about all the other nodes
        for i, node in enumerate(nodes):
            if i != index:
                await nodes[index].connect_to_peer(node.address)
