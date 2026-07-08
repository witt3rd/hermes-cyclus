"""
Tests for loop spec models and load_spec() — via loop_spec library.

cyclus.specs re-exports from loop_spec (https://github.com/witt3rd/loop-spec).
Imports go through cyclus.specs for backward compatibility.

Covers: load_spec() roundtrip, default terminal conditions, error paths
(missing kind, unknown kind, FileNotFoundError, malformed YAML), and
model-level validation (required fields, ClarificationSpec.HUMAN_GATED).
No network or external deps; tmp_path fixture isolates all file I/O.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from cyclus.specs import (
    ClarificationSpec,
    ConsensusSpec,
    LoopSpec,
    MetricOptimizationSpec,
    TaskExecutionSpec,
    load_spec,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, filename: str, content: str) -> Path:
    p = tmp_path / filename
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Test 1 — Valid MetricOptimizationSpec: correct type + level='L1'
# ---------------------------------------------------------------------------

def test_load_metric_optimization_spec(tmp_path):
    spec_file = _write(tmp_path, "metric.yaml", """\
kind: MetricOptimizationKind
name: test-metric-loop
level: L1
metric: test_coverage
direction: higher_is_better
""")
    spec = load_spec(spec_file)
    assert isinstance(spec, MetricOptimizationSpec)
    assert spec.level == "L1"


# ---------------------------------------------------------------------------
# Test 2 — Valid TaskExecutionSpec: correct type returned
# ---------------------------------------------------------------------------

def test_load_task_execution_spec(tmp_path):
    spec_file = _write(tmp_path, "task.yaml", """\
kind: TaskExecutionKind
name: test-task-loop
""")
    spec = load_spec(spec_file)
    assert isinstance(spec, TaskExecutionSpec)


# ---------------------------------------------------------------------------
# Test 3 — Missing `kind` field raises (ValueError: unknown kind None)
# ---------------------------------------------------------------------------

def test_missing_kind_field_raises(tmp_path):
    spec_file = _write(tmp_path, "no_kind.yaml", "name: no-kind-spec\n")
    # load_spec checks kind against _KIND_MAP before pydantic; None → ValueError
    with pytest.raises(ValueError):
        load_spec(spec_file)


# ---------------------------------------------------------------------------
# Test 4 — Default terminal conditions: max_iterations == 100
# ---------------------------------------------------------------------------

def test_default_terminal_conditions(tmp_path):
    spec_file = _write(tmp_path, "task_defaults.yaml", """\
kind: TaskExecutionKind
name: test-default-terminal
""")
    spec = load_spec(spec_file)
    assert spec.terminal.max_iterations == 100


# ---------------------------------------------------------------------------
# Test 5 — Unknown kind string → ValueError
# ---------------------------------------------------------------------------

def test_unknown_kind_raises(tmp_path):
    spec_file = _write(tmp_path, "unknown.yaml", """\
kind: BogusKind
name: test-unknown
""")
    with pytest.raises(ValueError):
        load_spec(spec_file)


# ---------------------------------------------------------------------------
# Test 6 — load_spec on nonexistent path → FileNotFoundError
# ---------------------------------------------------------------------------

def test_nonexistent_path_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_spec(tmp_path / "does_not_exist.yaml")


# ---------------------------------------------------------------------------
# Test 7 — Malformed YAML raises an exception (not silent)
# ---------------------------------------------------------------------------

def test_malformed_yaml_raises(tmp_path):
    spec_file = _write(tmp_path, "malformed.yaml", "key: [unclosed")
    with pytest.raises(Exception):
        load_spec(spec_file)


# ---------------------------------------------------------------------------
# Test 8 — ClarificationSpec.HUMAN_GATED is True
# ---------------------------------------------------------------------------

def test_clarification_human_gated():
    assert ClarificationSpec.HUMAN_GATED is True


# ---------------------------------------------------------------------------
# Test 9 — MetricOptimizationSpec missing required `metric` → ValidationError
# ---------------------------------------------------------------------------

def test_metric_optimization_missing_metric():
    with pytest.raises(ValidationError):
        MetricOptimizationSpec(
            name="test",
            direction="higher_is_better",
        )


# ---------------------------------------------------------------------------
# Test 10 — MetricOptimizationSpec missing required `direction` → ValidationError
# ---------------------------------------------------------------------------

def test_metric_optimization_missing_direction():
    with pytest.raises(ValidationError):
        MetricOptimizationSpec(
            name="test",
            metric="test_coverage",
        )
