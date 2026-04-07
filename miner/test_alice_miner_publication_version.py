#!/usr/bin/env python3
"""Regression tests for miner publication-version handling."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
MINER_DIR = REPO_ROOT / "miner"
if str(MINER_DIR) not in sys.path:
    sys.path.insert(0, str(MINER_DIR))

import alice_miner


class MinerPublicationVersionTests(unittest.TestCase):
    def test_select_static_publication_version_prefers_published_full(self) -> None:
        selected = alice_miner._select_static_publication_version(
            {
                "version": 156,
                "published_full_version": 155,
            },
            target_version=156,
        )
        self.assertEqual(selected, 155)

    def test_ensure_cached_model_keeps_downloaded_publication_version_when_delta_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            model_dir = Path(tmp)

            def fake_download(ps_url, target_version, assigned_layers, model_path, auth_token=None, max_attempts=3, retry_delay=10):
                model_path.write_bytes(b"published-v155")
                return True, len(b"published-v155"), 155

            with mock.patch.object(alice_miner, "download_partial_model_with_retry", side_effect=fake_download), \
                mock.patch.object(alice_miner, "request_delta_update", return_value=None), \
                mock.patch.object(alice_miner, "cleanup_old_versions"):
                model_path, changed = alice_miner.ensure_cached_model(
                    ps_url="http://ps",
                    ps_version=156,
                    assigned_layers=list(range(32)),
                    model_dir=model_dir,
                )

            self.assertTrue(changed)
            self.assertEqual(model_path.name, "alice-7b-v155.pt")
            self.assertEqual(alice_miner.read_local_version(model_dir), 155)
            self.assertTrue(model_path.exists())

    def test_ensure_cached_model_applies_delta_after_bootstrap_download(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            model_dir = Path(tmp)

            def fake_download(ps_url, target_version, assigned_layers, model_path, auth_token=None, max_attempts=3, retry_delay=10):
                model_path.write_bytes(b"published-v155")
                return True, len(b"published-v155"), 155

            def fake_apply_delta(old_path, new_path, delta_data, from_version, to_version):
                self.assertEqual(old_path.name, "alice-7b-v155.pt")
                self.assertEqual(new_path.name, "alice-7b-v156.pt")
                self.assertEqual(from_version, 155)
                self.assertEqual(to_version, 156)
                new_path.write_bytes(b"live-v156")
                return True

            with mock.patch.object(alice_miner, "download_partial_model_with_retry", side_effect=fake_download), \
                mock.patch.object(
                    alice_miner,
                    "request_delta_update",
                    return_value={"status": "ok", "delta": {"weight": [1]}, "to_version": 156},
                ), \
                mock.patch.object(alice_miner, "apply_delta_update", side_effect=fake_apply_delta), \
                mock.patch.object(alice_miner, "cleanup_old_versions"):
                model_path, changed = alice_miner.ensure_cached_model(
                    ps_url="http://ps",
                    ps_version=156,
                    assigned_layers=list(range(32)),
                    model_dir=model_dir,
                )

            self.assertTrue(changed)
            self.assertEqual(model_path.name, "alice-7b-v156.pt")
            self.assertEqual(alice_miner.read_local_version(model_dir), 156)
            self.assertTrue(model_path.exists())


if __name__ == "__main__":
    unittest.main()
