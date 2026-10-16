import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def imported_modules(path):
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            yield node.module or ""


def test_services_and_domain_do_not_depend_on_frameworks_or_concrete_adapters():
    forbidden = {"django", "rest_framework", "redis", "volleyball_ticketing"}
    for app in ("accounts", "booking"):
        for layer in ("services", "domain"):
            for path in (ROOT / app / layer).rglob("*.py"):
                for module in imported_modules(path):
                    assert module.split(".")[0] not in forbidden, (path, module)
                    assert not {"models", "repositories", "infrastructure", "api"}.intersection(
                        module.split(".")
                    ), (path, module)


def test_api_does_not_import_models_or_repositories():
    for app in ("accounts", "booking"):
        for path in (ROOT / app / "api").rglob("*.py"):
            for module in imported_modules(path):
                assert not {"models", "repositories", "infrastructure"}.intersection(
                    module.split(".")
                ), (path, module)
