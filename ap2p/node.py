"""
Peer-to-peer network implementation using asyncio.

This module provides a simple implementation of a peer-to-peer network using
Python's asyncio library. It includes classes for representing network nodes
and handling peer connections and communications.
"""

from asyncio import Lock, StreamReader, StreamWriter, create_task
from collections.abc import Awaitable, Callable
from typing import Any, Iterable, Optional

from ap2p.address import Address

# Type aliases for message handlers
MessageHandler = Callable[[bytes, StreamWriter], Awaitable[Any]]
HandlerDict = dict[bytes, MessageHandler]


# Message type's byte sequences
BACK_CONNECT = b"HELO"
PEER_REQ = b"PREQ"
PEER_RES = b"PRES"


class PeerDisconnectedException(Exception):
    """
    An exception raised when a peer disconnects unexpectedly.
    """

    pass


class Node:
    """
    A class representing a network node in a peer-to-peer network. Each node
    has an address, can connect to other nodes, and can send and receive
    messages from other nodes.

    Attributes:
        address (Address): The address of the node.
        server (asyncio.base_events.Server): The server object for the node.
        peers (dict[Address, StreamWriter]): A dictionary of connected peers
            and their associated StreamWriter objects.
        active_handlers (HandlerDict): A dictionary of active message handlers.
        handlers (HandlerDict): A dictionary of message handlers for the node.
        peers_lock (asyncio.Lock): A lock for managing access to the peers
            dictionary.

    Methods:
        log: Log a message with the node's address.
        start: Start the server and attempt to connect to known peers.
        stop: Stop the server and close all peer connections.
        connect_to_peer: Connect to a peer as a client and send a back-connect
            message to the peer.
        send_message: Send a message with the specified message type and content
            to a peer.
        send_back_connect: Send a back-connect message to a peer.
        send_peers_request: Send a peer request message to a peer.
        send_peers_list: Send the list of known peers to a peer.
        discover_peers: Discover and connect to new peers from a list of peer
            strings.
        handle_back_connect: Handle a back-connect message from a peer.
        activate_handler: Activate a specific message handler.
        activate_all_handlers: Activate all message handlers.
        process_message: Process an incoming message and call the appropriate
            handler.
        handle_message: Handle an incoming message from a peer.
        _handle_incoming: The "server" side of the connection.
        _remove_peer: Remove a peer from the list of connected peers.
    """

    def __init__(self, address: Address):
        """
        Initialize a new Node instance with the specified address.
        """
        self.address = address
        self.server = None
        self.peers: dict[Address, StreamWriter] = {}
        self.active_handlers: HandlerDict = {}
        self.handlers: HandlerDict = {
            BACK_CONNECT: self.handle_back_connect,
        }
        self.peers_lock = Lock()

    def log(self, message: str):
        """
        Log a message with the node's address.
        """
        print(f"[{self.address}] {message}")

    async def start(self, peers: Iterable[Address] = {}):
        """
        Start the server and attempt to connect to known peers.
        """
        self.server = await self.address.serve(self._handle_incoming)
        self.log("Server started")

        # Attempt to connect to known peers
        for p in peers:
            await self.connect_to_peer(p)

        # Keep the server running
        await self.server.serve_forever()

    async def _remove_peer(self, peer: Address, writer: Optional[StreamWriter] = None):
        """
        Remove a peer from the list of connected peers, closing the writter
        associated with it. If a writer is provided, assert that it matches the
        writer associated with the peer.
        """
        async with self.peers_lock:
            if peer not in self.peers:
                return
            found_writer = self.peers.pop(peer)
            if writer is not None:
                assert found_writer == writer
            try:
                found_writer.close()
                await found_writer.wait_closed()
            except ConnectionResetError:
                # The peer may have already disconnected
                pass

    async def stop(self):
        """
        Stop the server and close all peer connections.
        """
        if self.server is None:
            return

        peers = list(self.peers)
        for peer in peers:
            await self._remove_peer(peer)
        assert not self.peers
        self.active_handlers.clear()

        self.server.close()
        await self.server.wait_closed()

    async def connect_to_peer(self, peer: Address):
        """
        Connect to a peer as a client, and send a back-connect message to
        the peer. Also send a peer request message if this is the first
        connection.
        """
        # this is a critical section - we should lock it, so that we don't
        # have two connections to the same peer symultaneously
        async with self.peers_lock:
            if peer == self.address or peer in self.peers:
                # Don't connect to self or to a peer we're already connected to
                return

            task = None
            try:
                # Connect to a peer as client
                reader, writer = await peer.connect()
                self.peers[peer] = writer

                self.log(f"Connected to peer {peer}")

                await self.send_back_connect(writer)

                task = create_task(self._client_keepalive(peer, reader, writer))

            except ConnectionRefusedError:
                self.log(f"Could not connect to peer {peer}")

            finally:
                if task is not None:
                    task.cancel()

    async def send_message(
        self, writer: StreamWriter, message_type: bytes, message: bytes = b""
    ):
        """
        Send a message with the specified message type and content to a peer.
        If the message argument isn't provided, only the message type is sent.
        """
        writer.write(message_type + message + b"\n")
        await writer.drain()

    async def send_back_connect(self, writer: StreamWriter):
        """
        Send a back-connect message to a peer.
        """
        await self.send_message(writer, BACK_CONNECT, bytes(self.address))

    async def send_peers_request(self, writer: StreamWriter):
        """
        Send a peer request message to a peer.
        """
        await self.send_message(writer, PEER_REQ)

    async def send_peers_list(self, writer: StreamWriter):
        """
        Send the list of known peers to a peer.
        """
        relevant_peers = set(self.peers.keys())
        message = b",".join(bytes(peer) for peer in relevant_peers)
        await self.send_message(writer, PEER_RES, message)

    async def discover_peers(self, new_peer_strings):
        """
        Discover and connect to new peers from a list of peer strings.
        """
        peers_received = []
        for p_str in new_peer_strings:
            try:
                peer = Address.from_bytes(p_str)
                peers_received.append(peer)
                await self.connect_to_peer(peer)
            except ValueError:
                # invalid peer string
                continue
        return peers_received

    async def handle_back_connect(self, message, _):
        """
        Handle a back-connect message from a peer.
        """
        peers_received = await self.discover_peers([message])
        assert len(peers_received) <= 1
        peer = peers_received[0] if peers_received else None
        return peer

    def activate_handler(self, message_type: bytes):
        """
        Activate a specific message handler.
        """
        self.active_handlers[message_type] = self.handlers[message_type]

    def activate_all_handlers(self):
        """
        Activate all message handlers.
        """
        for req_type in self.handlers:
            self.activate_handler(req_type)

    async def process_message(self, message: bytes, writer: StreamWriter):
        """
        Process an incoming message and call the appropriate handler.
        """
        if len(message) < 4 or message[:4] not in self.active_handlers:
            raise ValueError(f"Invalid message {message}")
        return message[:4], await self.active_handlers[message[:4]](message[4:], writer)

    async def handle_message(self, reader: StreamReader, writer: StreamWriter):
        """
        Handle an incoming message from a peer.
        """
        data = await reader.readline()
        if not data:
            raise PeerDisconnectedException()
        message = data.strip()
        return await self.process_message(message, writer)

    async def _handle_incoming(self, reader: StreamReader, writer: StreamWriter):
        """
        The "server" side of the connection. We accept peers,
        immediately send our known peers, then continuously read.
        """

        # Note that this is a server side connection, so we don't use the
        # writer to send messages - we only use it to keep the connection
        # alive. The client side will send messages to us, and we can reply
        # on the back-connect channel.
        peer = None
        try:
            # first get the back_connect - this is needed so we know the correct
            # writer:
            self.activate_handler(BACK_CONNECT)
            message_type, peer = await self.handle_message(reader, None)
            if message_type != BACK_CONNECT or peer is None or peer not in self.peers:
                # client did not back_connect - disconnect from it
                raise PeerDisconnectedException()
            # now we can handle all messages:
            self.activate_all_handlers()
            while True:
                await self.handle_message(reader, self.peers[peer])

        except (PeerDisconnectedException, ValueError):
            if peer is not None:
                self.log(f"Peer {peer} disconnected.")

        finally:
            writer.close()
            await writer.wait_closed()
            if peer is not None:
                await self._remove_peer(peer)

    async def _client_keepalive(
        self, peer: Address, reader: StreamReader, writer: StreamWriter
    ):
        """
        Keep the client connection alive and handle disconnection.
        """
        # We don't really need the client side anymore, but we do need the
        # writer to remain available as long as our peer is connected - and to
        # be closed and removed once it isn't

        # the following line hangs until peer disconnects:
        data = await reader.readline()
        # we should never actually receive data in this direction!
        assert not data
        self.log(f"Lost connection to peer {peer}")
        await self._remove_peer(peer, writer)
