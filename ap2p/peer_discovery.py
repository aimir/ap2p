"""
This module contains the PeerDiscoveryNode class, which extends the Node
class to add support for peer discovery. The PeerDiscoveryNode class can
send and receive peer request and response messages to discover and connect
to other nodes on the network.

This also provides an example of how to use extended the Node class to add new
functionality to a network node.
"""

from ap2p.node import Address, Node

# Message types' byte sequences
PEER_REQ = b"PREQ"
PEER_RES = b"PRES"


class PeerDiscoveryNode(Node):
    """
    A class representing a network node that uses peer discovery to find and
    connect to other nodes. This class extends the Node class and adds support
    for sending and receiving peer request and response messages.

    Methods:
        handle_peer_request: Handle a peer request message from a peer.
        handle_peer_response: Handle a peer response message from a peer.
        connect_to_peer: Connect to a peer and send a peer request message.
    """

    def __init__(self, address: Address):
        super().__init__(address)
        self.handlers[PEER_REQ] = self.handle_peer_request
        self.handlers[PEER_RES] = self.handle_peer_response

    async def handle_peer_request(self, _, writer):
        """
        Handle a peer request message from a peer.
        """
        await self.send_peers_list(writer)

    async def handle_peer_response(self, message, _):
        """
        Handle a peer response message from a peer.
        """
        return await self.discover_peers(message.split(b","))

    async def connect_to_peer(self, peer: Address):
        first_connection = not self.peers
        await super().connect_to_peer(peer)
        if first_connection:
            # If this is the first connection, send a peer request so we
            # can get the peer list from the other side
            await self.send_peers_request(self.peers[peer])
