#!/usr/bin/env python3
"""Unit tests for the VPS3 download queue core."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from queue_core import DownloadQueueManager


class FakeClock:
    def __init__(self) -> None:
        self.value = 1_700_000_000.0

    def now(self) -> float:
        return self.value

    def advance(self, seconds: int) -> None:
        self.value += float(seconds)


class DownloadQueueManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()
        self.queue = DownloadQueueManager(
            max_concurrent=1,
            download_timeout=120,
            slot_estimate_sec=60,
            time_fn=self.clock.now,
        )

    def test_join_promote_complete_fifo(self) -> None:
        first = self.queue.join("alice-1", "miner-a", "10.0.0.1")
        second = self.queue.join("alice-2", "miner-b", "10.0.0.2")

        self.assertEqual(first["position"], 0)
        self.assertEqual(second["position"], 1)

        payload, status = self.queue.complete(
            download_token=str(first["download_token"]),
            client_ip="10.0.0.1",
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")

        promoted, status = self.queue.status(str(second["queue_id"]))
        self.assertEqual(status, 200)
        self.assertEqual(promoted["position"], 0)
        self.assertIn("download_token", promoted)

    def test_verify_token_enforces_ip_and_full_model_path(self) -> None:
        active = self.queue.join("alice-1", "miner-a", "10.0.0.1")
        token = str(active["download_token"])

        self.assertTrue(self.queue.verify_token(token, "10.0.0.1", "/models/v123_full.pt"))
        self.assertFalse(self.queue.verify_token(token, "10.0.0.2", "/models/v123_full.pt"))
        self.assertFalse(self.queue.verify_token(token, "10.0.0.1", "/models/v123_layers_0-31.pt"))

    def test_not_found_after_restart_like_state_reset(self) -> None:
        waiting = self.queue.join("alice-2", "miner-b", "10.0.0.2")
        queue_id = str(waiting["queue_id"])

        # Simulate a service restart by constructing a fresh manager.
        fresh_queue = DownloadQueueManager(
            max_concurrent=1,
            download_timeout=120,
            slot_estimate_sec=60,
            time_fn=self.clock.now,
        )
        payload, status = fresh_queue.status(queue_id)
        self.assertEqual(status, 404)
        self.assertEqual(payload["status"], "not_found")

    def test_heartbeat_extends_slot_expiry(self) -> None:
        active = self.queue.join("alice-1", "miner-a", "10.0.0.1")
        token = str(active["download_token"])

        self.clock.advance(100)
        payload, status = self.queue.heartbeat(token, "10.0.0.1")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(int(payload["expires_in"]), 119)

    def test_expired_slot_promotes_next_waiter(self) -> None:
        active = self.queue.join("alice-1", "miner-a", "10.0.0.1")
        waiting = self.queue.join("alice-2", "miner-b", "10.0.0.2")

        self.clock.advance(121)
        payload, status = self.queue.status(str(waiting["queue_id"]))
        self.assertEqual(status, 200)
        self.assertEqual(payload["position"], 0)
        self.assertNotEqual(payload["queue_id"], active["queue_id"])


if __name__ == "__main__":
    unittest.main()
