import tempfile
import shutil
from pathlib import Path

import pytest

from pathfinder.core.storage import (
    init_project,
    load_config,
    save_config,
    load_component,
    save_component,
    delete_component,
    load_standards,
    save_standards,
    find_all_component_files,
    get_component_dir,
    get_pathfinder_dir,
    resolve_component_id,
)
from pathfinder.types import ProjectConfig, Standards


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


class TestInitProject:
    def test_creates_pathfinder_directory(self, test_dir):
        init_project(test_dir, "Test Project")
        pf_dir = test_dir / ".pathfinder"
        assert pf_dir.exists()
        assert (pf_dir / "config.yaml").exists()
        assert (pf_dir / "components").exists()

    def test_writes_config_with_project_name(self, test_dir):
        init_project(test_dir, "My App")
        config = load_config(test_dir)
        assert config["name"] == "My App"

    def test_throws_if_already_initialized(self, test_dir):
        init_project(test_dir, "Test")
        with pytest.raises(Exception, match="already initialized"):
            init_project(test_dir, "Test")


class TestConfig:
    def test_saves_and_loads_config(self, test_dir):
        init_project(test_dir, "Test")
        save_config(test_dir, {
            "name": "Updated",
            "repos": {"backend": {"path": "../backend"}},
        })
        config = load_config(test_dir)
        assert config["name"] == "Updated"
        assert config["repos"]["backend"]["path"] == "../backend"

    def test_throws_if_not_initialized(self, test_dir):
        with pytest.raises(Exception, match="not initialized"):
            load_config(test_dir)


class TestComponents:
    @pytest.fixture(autouse=True)
    def setup(self, test_dir):
        init_project(test_dir, "Test")

    def test_saves_and_loads_root_component(self, test_dir):
        save_component(test_dir, {
            "id": "system",
            "name": "My System",
            "type": "system",
            "status": "active",
        })
        comp = load_component(test_dir, "system")
        assert comp["id"] == "system"
        assert comp["name"] == "My System"

    def test_saves_and_loads_nested_component(self, test_dir):
        save_component(test_dir, {
            "id": "payment",
            "name": "Payment Module",
            "type": "module",
            "status": "active",
            "parent": "system",
        })
        save_component(test_dir, {
            "id": "payment.gateway",
            "name": "Payment Gateway",
            "type": "service",
            "status": "active",
            "parent": "payment",
        })
        comp = load_component(test_dir, "payment.gateway")
        assert comp["name"] == "Payment Gateway"
        assert comp["parent"] == "payment"

    def test_creates_directory_hierarchy(self, test_dir):
        save_component(test_dir, {
            "id": "payment",
            "name": "Payment",
            "type": "module",
            "status": "active",
        })
        save_component(test_dir, {
            "id": "payment.gateway",
            "name": "Gateway",
            "type": "service",
            "status": "active",
            "parent": "payment",
        })
        gateway_dir = get_component_dir(test_dir, "payment.gateway")
        assert (gateway_dir / "_component.yaml").exists()
        assert "payment" in str(gateway_dir) and "gateway" in str(gateway_dir)

    def test_deletes_component(self, test_dir):
        save_component(test_dir, {
            "id": "payment",
            "name": "Payment",
            "type": "module",
            "status": "active",
        })
        delete_component(test_dir, "payment")
        with pytest.raises(Exception):
            load_component(test_dir, "payment")

    def test_finds_all_component_files(self, test_dir):
        save_component(test_dir, {
            "id": "system",
            "name": "System",
            "type": "system",
            "status": "active",
        })
        save_component(test_dir, {
            "id": "payment",
            "name": "Payment",
            "type": "module",
            "status": "active",
            "parent": "system",
        })
        files = find_all_component_files(test_dir)
        assert len(files) == 2


class TestResolveComponentId:
    @pytest.fixture(autouse=True)
    def setup(self, test_dir):
        init_project(test_dir, "Test")
        save_component(test_dir, {
            "id": "api-layer",
            "name": "API Layer",
            "type": "module",
            "status": "active",
        })
        save_component(test_dir, {
            "id": "api-layer.client",
            "name": "Client",
            "type": "component",
            "status": "active",
            "parent": "api-layer",
        })

    def test_resolves_dot_notation_as_is(self, test_dir):
        resolved = resolve_component_id(test_dir, "api-layer.client")
        assert resolved == "api-layer.client"

    def test_resolves_slash_to_dot_notation(self, test_dir):
        resolved = resolve_component_id(test_dir, "api-layer/client")
        assert resolved == "api-layer.client"

    def test_resolves_root_component_dot_notation(self, test_dir):
        resolved = resolve_component_id(test_dir, "api-layer")
        assert resolved == "api-layer"

    def test_raises_for_nonexistent_dot_id(self, test_dir):
        with pytest.raises(FileNotFoundError, match="not found"):
            resolve_component_id(test_dir, "does.not.exist")

    def test_raises_for_nonexistent_slash_id(self, test_dir):
        with pytest.raises(FileNotFoundError, match="not found"):
            resolve_component_id(test_dir, "does/not/exist")

    def test_helpful_message_includes_tried_dot_id(self, test_dir):
        with pytest.raises(FileNotFoundError, match="does.not.exist"):
            resolve_component_id(test_dir, "does/not/exist")


class TestStandards:
    @pytest.fixture(autouse=True)
    def setup(self, test_dir):
        init_project(test_dir, "Test")

    def test_saves_and_loads_standards(self, test_dir):
        save_standards(test_dir, {"spec": "Use Python\nUse pytest"})
        standards = load_standards(test_dir)
        assert "Python" in standards["spec"]

    def test_returns_none_when_no_standards(self, test_dir):
        standards = load_standards(test_dir)
        assert standards is None
