from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .blockchain import Blockchain


class RegisterNodesRequest(BaseModel):
    nodes: List[str]


class MineRequest(BaseModel):
    data: Any


class ReceiveBlockRequest(BaseModel):
    data: Any


@dataclass
class Node:
    complexity: int = 3
    peers: Set[str] = field(default_factory=set)
    blockchain: Blockchain = field(init=False)

    def __post_init__(self) -> None:
        self.blockchain = Blockchain(self.complexity)

    def add_peers(self, nodes: List[str]) -> List[str]:
        added = []
        for n in nodes:
            normalized = self._normalize_node_url(n)
            if normalized and normalized not in self.peers:
                self.peers.add(normalized)
                added.append(normalized)
        return added

    def _normalize_node_url(self, n: str) -> Optional[str]:
        n = n.strip()
        if not n:
            return None
        if "://" not in n:
            n = "http://" + n
        u = urlparse(n)
        if not u.scheme or not u.netloc:
            return None
        return f"{u.scheme}://{u.netloc}"

    def resolve_conflicts(self) -> bool:
        max_len = len(self.blockchain.blocks)
        best_chain = None

        for peer in list(self.peers):
            try:
                r = requests.get(f"{peer}/chain", timeout=3)
                r.raise_for_status()
                payload = r.json()
            except Exception:
                continue

            chain = payload.get("chain")
            if not isinstance(chain, list):
                continue

            candidate = Blockchain(self.complexity)
            candidate.blocks = []  
            try:
                from .block import Block 

                for b in chain:
                    blk = Block(
                        b["previous_hash"],
                        b.get("data"),
                        b.get("complexity", self.complexity),
                        time=b.get("time"),  
                    )
                    blk.proof = b.get("proof", blk.proof)
                    blk.hash = b.get("hash", blk.hash)
                    candidate.blocks.append(blk)
            except Exception:
                continue

            if len(candidate.blocks) > max_len and candidate.validate():
                max_len = len(candidate.blocks)
                best_chain = candidate.blocks

        if best_chain is not None:
            self.blockchain.blocks = best_chain
            return True
        return False


def create_app(node: Node) -> FastAPI:
    app = FastAPI(title="Blockchain Node")

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/chain")
    def get_chain():
        out = []
        for b in node.blockchain.blocks:
            out.append(
                {
                    "previous_hash": b.previous_hash,
                    "data": b.data,
                    "time": b.time.isoformat() if hasattr(b.time, "isoformat") else b.time,
                    "proof": b.proof,
                    "complexity": b.complexity,
                    "hash": b.hash,
                }
            )
        return {"length": len(out), "chain": out, "peers": sorted(node.peers)}

    @app.post("/nodes/register")
    def register_nodes(req: RegisterNodesRequest):
        added = node.add_peers(req.nodes)
        return {"added": added, "total_peers": sorted(node.peers)}

    @app.post("/resolve")
    def resolve():
        replaced = node.resolve_conflicts()
        return {"replaced": replaced, "length": len(node.blockchain.blocks)}

    @app.post("/mine")
    def mine(req: MineRequest):
        node.resolve_conflicts()

        node.blockchain.add(req.data)

        for peer in list(node.peers):
            try:
                requests.post(f"{peer}/resolve", timeout=2)
            except Exception:
                pass

        return {
            "message": "mined",
            "length": len(node.blockchain.blocks),
            "last_hash": node.blockchain.blocks[-1].hash,
        }

    return app
