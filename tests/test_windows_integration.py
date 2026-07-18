from __future__ import annotations

import uuid

from window_swapper import acquire_instance_mutex, release_instance_mutex


def test_instance_mutex_rejects_a_second_instance() -> None:
    name = rf"Local\JCOMLabs.WindowSwap.Tests.{uuid.uuid4()}"
    first = acquire_instance_mutex(name)
    assert first is not None
    try:
        assert acquire_instance_mutex(name) is None
    finally:
        release_instance_mutex(first)

    replacement = acquire_instance_mutex(name)
    assert replacement is not None
    release_instance_mutex(replacement)
