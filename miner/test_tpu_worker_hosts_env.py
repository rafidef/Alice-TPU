#!/usr/bin/env python3
"""Tests for TPU worker hostname env sanitization."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
MINER_DIR = REPO_ROOT / "miner"
if str(MINER_DIR) not in sys.path:
    sys.path.insert(0, str(MINER_DIR))

import alice_miner


class TpuWorkerHostEnvSanitizationTests(unittest.TestCase):
    def test_sanitize_tpu_worker_host_env_unsets_malformed_warning_value(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "TPU_WORKER_HOSTNAMES": (
                    "WARNING: could not determine TPU worker hostnames or IP addresses,"
                    " please set env var `TPU_WORKER_HOSTNAMES` manually"
                )
            },
            clear=False,
        ):
            hosts = alice_miner._sanitize_tpu_worker_host_env()
            self.assertEqual(hosts, [])
            self.assertNotIn("TPU_WORKER_HOSTNAMES", os.environ)
            self.assertNotIn("ALICE_TPU_WORKERS", os.environ)

    def test_sanitize_tpu_worker_host_env_keeps_valid_hostnames(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"TPU_WORKER_HOSTNAMES": "worker-0,worker-1"},
            clear=False,
        ):
            hosts = alice_miner._sanitize_tpu_worker_host_env()
            self.assertEqual(hosts, ["worker-0", "worker-1"])
            self.assertEqual(os.environ.get("TPU_WORKER_HOSTNAMES"), "worker-0,worker-1")
            self.assertEqual(os.environ.get("ALICE_TPU_WORKERS"), "worker-0,worker-1")

    def test_sanitize_tpu_worker_host_env_keeps_valid_ip_addresses(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"ALICE_TPU_WORKERS": "10.0.0.1,10.0.0.2"},
            clear=False,
        ):
            hosts = alice_miner._sanitize_tpu_worker_host_env()
            self.assertEqual(hosts, ["10.0.0.1", "10.0.0.2"])
            self.assertEqual(os.environ.get("TPU_WORKER_HOSTNAMES"), "10.0.0.1,10.0.0.2")
            self.assertEqual(os.environ.get("ALICE_TPU_WORKERS"), "10.0.0.1,10.0.0.2")


if __name__ == "__main__":
    unittest.main()
