from asyncio import create_task, gather, run
from ipaddress import ip_address

from ap2p import Address, PeerDiscoveryNode

LOCALHOST = ip_address("127.0.0.1")

PEERS = [
    Address(LOCALHOST, 8000),
    Address(LOCALHOST, 8001),
    Address(LOCALHOST, 8002),
]


async def main(peers=PEERS):
    tasks = []
    for peer in peers:
        node = PeerDiscoveryNode(address=peer)
        other_peers = [p for p in peers if p != peer]
        tasks.append(create_task(node.start(peers=other_peers)))

    await gather(*tasks)


if __name__ == "__main__":
    run(main())
