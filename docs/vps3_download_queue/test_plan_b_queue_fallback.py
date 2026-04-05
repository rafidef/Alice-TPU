#!/usr/bin/env python3
"""Unit tests for Plan B queue fallback behavior."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[2]
MINER_DIR = REPO_ROOT / "miner"
if str(MINER_DIR) not in sys.path:
    sys.path.insert(0, str(MINER_DIR))

import plan_b


class PlanBQueueFallbackTests(unittest.TestCase):
    def _make_trainer(self) -> plan_b.LocalTrainer:
        trainer = plan_b.LocalTrainer.__new__(plan_b.LocalTrainer)
        trainer.model_queue_base_url = "https://dl.aliceprotocol.org"
        trainer.miner_address = "alice-wallet"
        trainer.miner_instance_id = "miner-1"
        trainer.token = "auth-token"
        trainer.ps_url = "https://ps.aliceprotocol.org"
        return trainer

    def test_repeated_queue_poll_failures_fall_back_to_direct_model_download(self) -> None:
        trainer = self._make_trainer()
        queue_join = mock.Mock(return_value={"queue_id": "queue-1", "position": 2, "wait_seconds": 60})
        complete = mock.Mock()
        download_direct = mock.Mock()

        trainer._queue_join = queue_join
        trainer._complete_download_queue = complete
        trainer._download_full_model_direct = download_direct

        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "full_model_v123.pt"
            with mock.patch.object(plan_b.time, "sleep", return_value=None), mock.patch.object(
                plan_b.requests,
                "get",
                return_value=mock.Mock(status_code=500),
            ):
                trainer._download_full_model_queued(123, model_path)

        self.assertEqual(queue_join.call_count, 1)
        complete.assert_called_once_with(
            "https://dl.aliceprotocol.org/models/queue",
            "queue-1",
            "",
        )
        download_direct.assert_called_once_with(123, mock.ANY)


if __name__ == "__main__":
    unittest.main()
