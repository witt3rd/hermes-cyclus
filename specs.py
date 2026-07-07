from __future__ import annotations
from pathlib import Path
from typing import ClassVar, Literal
import yaml
from pydantic import BaseModel, Field


class TerminalConditions(BaseModel):
    max_iterations: int = 100
    plateau_count: int = 10
    target_score: float | None = None


class LoopSpec(BaseModel):
    kind: str
    name: str
    level: Literal['L1', 'L2', 'L3'] = 'L1'
    terminal: TerminalConditions = Field(default_factory=TerminalConditions)


class MetricOptimizationSpec(LoopSpec):
    kind: Literal['MetricOptimizationKind'] = 'MetricOptimizationKind'
    metric: str
    direction: Literal['higher_is_better', 'lower_is_better']
    baseline: float | None = None
    evaluate: str | None = None
    target_files: list[str] = Field(default_factory=list)


class TaskExecutionSpec(LoopSpec):
    kind: Literal['TaskExecutionKind'] = 'TaskExecutionKind'
    target_files: list[str] = Field(default_factory=list)


class ConsensusSpec(LoopSpec):
    kind: Literal['ConsensusKind'] = 'ConsensusKind'


class InformationSeekingSpec(LoopSpec):
    kind: Literal['InformationSeekingKind'] = 'InformationSeekingKind'


class ClarificationSpec(LoopSpec):
    kind: Literal['ClarificationKind'] = 'ClarificationKind'
    HUMAN_GATED: ClassVar[bool] = True


_KIND_MAP = {
    'MetricOptimizationKind': MetricOptimizationSpec,
    'TaskExecutionKind': TaskExecutionSpec,
    'ConsensusKind': ConsensusSpec,
    'InformationSeekingKind': InformationSeekingSpec,
    'ClarificationKind': ClarificationSpec,
}


def load_spec(path: str | Path) -> LoopSpec:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Spec not found: {path}")
    data = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f"Spec must be a YAML mapping, got {type(data).__name__}")
    kind = data.get('kind')
    if kind not in _KIND_MAP:
        raise ValueError(f"Unknown loop kind: {kind!r}. Valid: {list(_KIND_MAP)}")
    return _KIND_MAP[kind].model_validate(data)
