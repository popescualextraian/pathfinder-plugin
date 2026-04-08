"""Shared types for Pathfinder."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


ComponentStatus = Literal["proposed", "active", "deprecated"]


@dataclass
class Contract:
    name: str
    format: str
    source: str | None = None
    target: str | None = None


@dataclass
class Contracts:
    inputs: list[Contract] = field(default_factory=list)
    outputs: list[Contract] = field(default_factory=list)


@dataclass
class DataFlow:
    data: str
    from_id: str | None = None
    to: str | None = None
    protocol: str | None = None


@dataclass
class CodeMapping:
    glob: str
    repo: str | None = None


@dataclass
class Component:
    id: str
    name: str
    type: str
    status: ComponentStatus
    parent: str | None = None
    spec: str | None = None
    contracts: Contracts | None = None
    data_flows: list[DataFlow] = field(default_factory=list)
    code_mappings: list[CodeMapping] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    external: bool = False


@dataclass
class RepoConfig:
    path: str


@dataclass
class ProjectConfig:
    name: str
    repos: dict[str, RepoConfig] = field(default_factory=dict)
    integrations: dict[str, dict] = field(default_factory=dict)


@dataclass
class Standards:
    spec: str


@dataclass
class IndexEntry:
    id: str
    name: str
    type: str
    status: ComponentStatus
    parent: str | None
    children: list[str]
    tags: list[str]
    data_flows: list[DataFlow]
    code_mappings: list[CodeMapping]
    file_path: str
    depends_on: list[str] = field(default_factory=list)
    external: bool = False


@dataclass
class ComponentIndex:
    version: int
    generated_at: str
    components: dict[str, IndexEntry]
    flows: list[DataFlow]


@dataclass
class ValidationIssue:
    component_id: str
    issue: str
    severity: Literal["error", "warning"]
