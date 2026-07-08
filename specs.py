"""
cyclus.specs — re-exports from loop_spec.

The canonical loop spec models and load_spec() now live in the
standalone loop-spec library (https://github.com/witt3rd/loop-spec).
This module re-exports everything for backward compatibility.

Import from loop_spec directly for new code:
    from loop_spec import load_spec, MetricOptimizationSpec
"""

from loop_spec import (  # noqa: F401
    ClarificationSpec,
    ConsensusSpec,
    InformationSeekingSpec,
    LoopSpec,
    MetricOptimizationSpec,
    SelectionSpec,
    TaskExecutionSpec,
    TerminalConditions,
    load_spec,
)

__all__ = [
    "LoopSpec",
    "TerminalConditions",
    "MetricOptimizationSpec",
    "TaskExecutionSpec",
    "ConsensusSpec",
    "InformationSeekingSpec",
    "ClarificationSpec",
    "SelectionSpec",
    "load_spec",
]
