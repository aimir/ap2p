# ap2p

## Overview
`ap2p` is a package designed to facilitate peer-to-peer communication and data exchange. It provides a robust and efficient framework for building decentralized applications.

## Features
- No-nonsense API for peer-to-peer communication
- Asynchronicity with modern python3 async / await syntax
- Threading based on asyncio
- Ease of use with clear documentation and examples
- Easily extensible to accommodate various use cases

## Installation
To install the package, use the following command:
```bash
pip install ap2p
```

## Usage
Here's a basic example of how to use `ap2p` to start three interconnected nodes on localhost:
```python
from asyncio import create_task, gather, run
from ipaddress import ip_address

from ap2p import Address, Node


LOCALHOST = ip_address("127.0.0.1")

PEERS = [
    Address(LOCALHOST, 8000),
    Address(LOCALHOST, 8001),
    Address(LOCALHOST, 8002),
]


for peer in peers:
    node = Node(address=peer)
    create_task(node.start(peers=peers))
```
