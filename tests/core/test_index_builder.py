import json
import tempfile
import shutil
from pathlib import Path

import pytest

from pathfinder.core.storage import init_project, save_component
from pathfinder.core.index_builder import build_index, load_index


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    init_project(d, "Test")
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_builds_empty_index(test_dir):
    index = build_index(test_dir)
    assert index["version"] == 1
    assert len(index["components"]) == 0
    assert len(index["flows"]) == 0


def test_indexes_parent_child_relationships(test_dir):
    save_component(test_dir, {"id": "system", "name": "System", "type": "system", "status": "active"})
    save_component(test_dir, {"id": "payment", "name": "Payment", "type": "module", "status": "active", "parent": "system"})
    save_component(test_dir, {"id": "payment.gateway", "name": "Gateway", "type": "service", "status": "active", "parent": "payment"})
    index = build_index(test_dir)
    assert len(index["components"]) == 3
    assert "payment" in index["components"]["system"]["children"]
    assert "payment.gateway" in index["components"]["payment"]["children"]
    assert len(index["components"]["payment.gateway"]["children"]) == 0


def test_collects_all_data_flows(test_dir):
    save_component(test_dir, {
        "id": "order", "name": "Order", "type": "service", "status": "active",
        "dataFlows": [{"to": "payment", "data": "PaymentRequest", "protocol": "REST"}],
    })
    save_component(test_dir, {
        "id": "payment", "name": "Payment", "type": "service", "status": "active",
        "dataFlows": [{"to": "ledger", "data": "Transaction", "protocol": "async/event"}],
    })
    index = build_index(test_dir)
    assert len(index["flows"]) == 2


def test_resolves_implicit_from(test_dir):
    save_component(test_dir, {
        "id": "order", "name": "Order", "type": "service", "status": "active",
        "dataFlows": [{"to": "payment", "data": "PaymentRequest"}],
    })
    index = build_index(test_dir)
    flow = index["flows"][0]
    assert flow["from"] == "order"
    assert flow["to"] == "payment"


def test_writes_and_loads_index(test_dir):
    save_component(test_dir, {"id": "system", "name": "System", "type": "system", "status": "active"})
    build_index(test_dir)
    index_path = test_dir / ".pathfinder" / "index.json"
    assert index_path.exists()
    loaded = load_index(test_dir)
    assert loaded["components"]["system"]["name"] == "System"


def test_preserves_code_mappings_and_tags(test_dir):
    save_component(test_dir, {
        "id": "payment", "name": "Payment", "type": "service", "status": "active",
        "codeMappings": [{"repo": "backend", "glob": "src/payment/**"}],
        "tags": ["pci-scope"],
    })
    index = build_index(test_dir)
    assert len(index["components"]["payment"]["codeMappings"]) == 1
    assert "pci-scope" in index["components"]["payment"]["tags"]
