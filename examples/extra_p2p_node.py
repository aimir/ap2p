from asyncio import run
from ipaddress import ip_address

from ap2p import Address, PeerDiscoveryNode

LOCALHOST = ip_address("127.0.0.1")

EXTRA_NODE = Address(LOCALHOST, 8003)
PEER = Address(LOCALHOST, 8002)

if __name__ == "__main__":
    node = PeerDiscoveryNode(EXTRA_NODE)
    run(node.start([PEER]))
