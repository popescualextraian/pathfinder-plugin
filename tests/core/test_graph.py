import tempfile
import shutil
from pathlib import Path
from collections import deque
import pytest
from pathfinder.core.storage import init_project, save_component
from pathfinder.core.index_builder import build_index
from pathfinder.core.graph import (
    get_dependencies, get_dependents, get_flows_for_component,
    trace_flow, get_components_by_tag, find_component_by_code_path,
    get_structural_deps,
)

@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    init_project(d, "Test")
    yield d
    shutil.rmtree(d, ignore_errors=True)

@pytest.fixture
def graph_index(test_dir):
    save_component(test_dir, {"id": "order", "name": "Order", "type": "service", "status": "active",
        "dataFlows": [{"to": "payment", "data": "PaymentRequest", "protocol": "REST"}],
        "codeMappings": [{"glob": "src/order/**"}]})
    save_component(test_dir, {"id": "payment", "name": "Payment", "type": "service", "status": "active",
        "dataFlows": [{"to": "ledger", "data": "Transaction", "protocol": "async/event"}],
        "codeMappings": [{"repo": "backend", "glob": "src/payment/**"}], "tags": ["pci-scope"]})
    save_component(test_dir, {"id": "ledger", "name": "Ledger", "type": "service", "status": "active",
        "codeMappings": [{"glob": "src/ledger/**"}], "tags": ["pci-scope"]})
    save_component(test_dir, {"id": "notification", "name": "Notification", "type": "service", "status": "active",
        "dataFlows": [{"from": "payment", "data": "PaymentEvent"}]})
    save_component(test_dir, {"id": "order", "name": "Order", "type": "service", "status": "active",
        "dataFlows": [{"to": "payment", "data": "PaymentRequest", "protocol": "REST"}],
        "codeMappings": [{"glob": "src/order/**"}],
        "dependsOn": ["notification"]})
    return build_index(test_dir)

class TestGetDependencies:
    def test_returns_outgoing_deps(self, graph_index):
        deps = get_dependencies(graph_index, "order")
        assert "payment" in deps
        assert "ledger" not in deps
    def test_returns_empty_for_leaf(self, graph_index):
        assert len(get_dependencies(graph_index, "ledger")) == 0

class TestGetDependents:
    def test_returns_incoming_deps(self, graph_index):
        assert "order" in get_dependents(graph_index, "payment")

class TestGetFlowsForComponent:
    def test_returns_all_flows(self, graph_index):
        assert len(get_flows_for_component(graph_index, "payment")) >= 2

class TestTraceFlow:
    def test_finds_path(self, graph_index):
        assert trace_flow(graph_index, "order", "ledger") == ["order", "payment", "ledger"]
    def test_returns_none_when_no_path(self, graph_index):
        assert trace_flow(graph_index, "ledger", "order") is None

class TestGetComponentsByTag:
    def test_finds_tagged(self, graph_index):
        tagged = get_components_by_tag(graph_index, "pci-scope")
        assert "payment" in tagged and "ledger" in tagged and "order" not in tagged

class TestFindComponentByCodePath:
    def test_finds_owner(self, graph_index):
        assert find_component_by_code_path(graph_index, "src/payment/gateway/handler.py") == "payment"
    def test_returns_none_for_unmapped(self, graph_index):
        assert find_component_by_code_path(graph_index, "src/unknown/file.py") is None

class TestDependsOn:
    def test_deps_includes_depends_on(self, graph_index):
        deps = get_dependencies(graph_index, "order")
        assert "payment" in deps
        assert "notification" in deps

    def test_dependents_includes_depends_on(self, graph_index):
        dependents = get_dependents(graph_index, "notification")
        assert "order" in dependents

    def test_structural_deps_only(self, graph_index):
        deps = get_structural_deps(graph_index, "order")
        assert "notification" in deps
        assert "payment" not in deps
