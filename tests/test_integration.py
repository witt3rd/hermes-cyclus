"""
v18 plugin registration smoke tests.
Replaces the v2 integration tests which tested omh_state, pre_llm_call, on_session_end
— all removed in Phase 3.
"""
import importlib
import sys
import pytest


def test_queue_tool_importable():
    """cyclus_queue tool handler must be importable."""
    from cyclus.tools.queue_tool import cyclus_queue_handler
    assert callable(cyclus_queue_handler)


def test_omh_state_gone():
    """omh_state must not be importable (deleted in Phase 3)."""
    with pytest.raises(ImportError):
        from cyclus.omh_state import state_write  # noqa: F401


def test_omh_delegate_gone():
    """omh_delegate must not be importable (deleted in Phase 3)."""
    with pytest.raises(ImportError):
        from cyclus.omh_delegate import omh_delegate_prepare  # noqa: F401


def test_hooks_gone():
    """Pre-llm_call and tool hooks must not be importable (deleted in Phase 3)."""
    with pytest.raises(ImportError):
        from cyclus.hooks.llm_hooks import pre_llm_call  # noqa: F401
    with pytest.raises(ImportError):
        from cyclus.hooks.tool_hooks import pre_tool_call  # noqa: F401


def test_plugin_yaml_version():
    """plugin.yaml must be version 18.0.0 and list only v18 tools."""
    import yaml
    from pathlib import Path
    yaml_path = Path(__file__).parent.parent / "plugin.yaml"
    data = yaml.safe_load(yaml_path.read_text())
    assert data["version"] == "18.0.0", f"Expected 18.0.0, got {data['version']}"
    tools = data.get("provides_tools", [])
    assert "cyclus_queue" in tools, "cyclus_queue must be in provides_tools"
    assert "omh_state" not in tools, "omh_state must not be in provides_tools (deleted)"
    hooks = data.get("provides_hooks", [])
    assert len(hooks) == 0, f"No hooks expected in v18, got: {hooks}"


def test_queue_six_operations_importable():
    """All six queue operations plus status must be importable."""
    from cyclus.queue import (
        post, claim, release, write_state, cancel, complete, status
    )
    for fn in (post, claim, release, write_state, cancel, complete, status):
        assert callable(fn)
