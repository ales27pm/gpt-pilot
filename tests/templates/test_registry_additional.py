import importlib
import sys
import types
from contextlib import contextmanager
import pytest

# Test framework note: Using pytest.
# The registry module under test is expected to perform relative imports:
#   from .django_postgres import DjangoPostgresProjectTemplate
#   ...
# To insulate tests from actual implementations and ensure import succeeds even if files don't exist,
# we inject stub modules/classes into sys.modules under the package path before import.

REQUIRED_TEMPLATES = [
    ("django_postgres", "DjangoPostgresProjectTemplate"),
    ("fastapi_sqlite", "FastapiSqliteProjectTemplate"),
    ("flask_sqlite", "FlaskSqliteProjectTemplate"),
    ("node_express_mongoose", "NodeExpressMongooseProjectTemplate"),
    ("react_express", "ReactExpressProjectTemplate"),
    ("typer_cli", "TyperCliProjectTemplate"),
    ("vite_react", "ViteReactProjectTemplate"),
]

@contextmanager
def ensure_package(path_parts, as_package=True):
    """
    Ensure a package hierarchy exists in sys.modules for a list of parts, e.g., ['templates'].
    Yields the full dotted name.
    """
    created = []
    try:
        parent_name = None
        for i in range(len(path_parts)):
            name = ".".join(path_parts[:i+1])
            if name not in sys.modules:
                mod = types.ModuleType(name)
                if as_package:
                    # Mark as package by giving __path__
                    mod.__path__ = []  # type: ignore[attr-defined]
                sys.modules[name] = mod
                created.append(name)
            parent_name = name
        yield ".".join(path_parts)
    finally:
        # Clean up only those we created (not to disturb test runner modules)
        for name in reversed(created):
            sys.modules.pop(name, None)

def build_template_stub(name_value: str):
    """
    Create a stub class having a .name class attribute and simple identity semantics.
    """
    class _Stub:
        name = name_value
    _Stub.__name__ = f"Stub<{name_value}>"
    return _Stub

def inject_sibling_modules(pkg_name: str, override_missing_name: bool = False):
    """
    Inject sibling modules under pkg_name (e.g., 'templates') with expected classes.
    If override_missing_name is True, one of the classes will be created without 'name' to simulate failure.
    """
    injected = []
    for idx, (mod_base, cls_name) in enumerate(REQUIRED_TEMPLATES):
        full_mod = f"{pkg_name}.{mod_base}"
        m = types.ModuleType(full_mod)
        # Determine a stable .name value for each stub
        # e.g., NodeExpressMongooseProjectTemplate -> "node_express_mongoose"
        default_name_value = mod_base
        StubClass = type(cls_name, (), {})  # dynamic class with desired name
        # Optionally omit 'name' attribute for the first module to simulate error
        if override_missing_name and idx == 0:
            pass
        else:
            setattr(StubClass, "name", default_name_value)
        setattr(m, cls_name, StubClass)
        sys.modules[full_mod] = m
        injected.append(full_mod)
    return injected

def remove_modules(mod_names):
    for n in mod_names:
        sys.modules.pop(n, None)

def import_registry(preferred_pkg="templates"):
    """
    Attempt to import the registry module from preferred package (templates.registry).
    Fall back to tests.templates.test_registry if needed.
    Returns the imported module object.
    """
    # Try preferred: templates.registry
    try:
        return importlib.import_module(f"{preferred_pkg}.registry")
    except ModuleNotFoundError:
        # Fallback: tests.templates.test_registry (path provided in diff)
        return importlib.import_module("tests.templates.test_registry")

class TestRegistryEnumAndMapping:
    def test_enum_members_and_types(self):
        with ensure_package(["templates"]) as pkg:
            injected = inject_sibling_modules(pkg)
            try:
                mod = import_registry("templates")
                # Collect enum members dynamically
                enum_cls = getattr(mod, "ProjectTemplateEnum")
                members = {e.name: e.value for e in enum_cls}  # type: ignore[call-arg]
                # Expected keys based on REQUIRED_TEMPLATES order
                expected_values = {
                    "NODE_EXPRESS_MONGOOSE": "node_express_mongoose",
                    "REACT_EXPRESS": "react_express",
                    "VITE_REACT": "vite_react",
                    "FLASK_SQLITE": "flask_sqlite",
                    "FASTAPI_SQLITE": "fastapi_sqlite",
                    "DJANGO_POSTGRES": "django_postgres",
                    "TYPER_CLI": "typer_cli",
                }
                # All expected enum names present
                assert set(members.keys()) == set(expected_values.keys())
                # Values must be exact string names
                assert members == expected_values
                # Each value is str (redundant but explicit)
                assert all(isinstance(v, str) for v in members.values())
            finally:
                remove_modules(injected)

    def test_project_templates_dict_integrity(self):
        with ensure_package(["templates"]) as pkg:
            injected = inject_sibling_modules(pkg)
            try:
                mod = import_registry("templates")
                enum_cls = getattr(mod, "ProjectTemplateEnum")
                registry = getattr(mod, "PROJECT_TEMPLATES")
                # 1) Keys equal enum values
                enum_values = {e.value for e in enum_cls}
                assert set(registry.keys()) == enum_values
                # 2) Values are classes; each has a 'name' attribute equal to the key
                for k, cls in registry.items():
                    assert isinstance(cls, type), f"Registry value for {k} should be a class"
                    assert getattr(cls, "name", None) == k
            finally:
                remove_modules(injected)

    def test_registry_and_enum_stay_in_sync_when_new_template_added(self):
        # Simulate adding a new template to siblings but not updating registry to ensure test catches drift.
        with ensure_package(["templates"]) as pkg:
            injected = inject_sibling_modules(pkg)
            try:
                # Dynamically add a new sibling module
                extra_mod = types.ModuleType(f"{pkg}.sanic_sqlite")
                ExtraClass = type("SanicSqliteProjectTemplate", (), {"name": "sanic_sqlite"})
                setattr(extra_mod, "SanicSqliteProjectTemplate", ExtraClass)
                sys.modules[f"{pkg}.sanic_sqlite"] = extra_mod
                # Import registry
                mod = import_registry("templates")
                enum_cls = getattr(mod, "ProjectTemplateEnum")
                registry = getattr(mod, "PROJECT_TEMPLATES")
                # Sanity: new sibling is NOT in enum/registry; assert they don't include unknowns
                enum_values = {e.value for e in enum_cls}
                assert "sanic_sqlite" not in enum_values
                assert "sanic_sqlite" not in registry
            finally:
                remove_modules(injected + [f"{pkg}.sanic_sqlite"])

    def test_import_fails_if_template_class_missing_name_attribute(self):
        # Simulate a missing 'name' attribute to ensure module still imports but registry consistency can be validated.
        with ensure_package(["templates"]) as pkg:
            injected = inject_sibling_modules(pkg, override_missing_name=True)
            try:
                mod = import_registry("templates")
                # The module under test uses the .name attribute at definition-time of Enum and dict.
                # If missing, Python will raise AttributeError during import. We assert that happens.
                # However, since we already imported successfully to get here in some environments,
                # we explicitly re-import with reload to surface errors.
                # Expecting AttributeError or similar during reload.
                with pytest.raises(Exception):
                    importlib.reload(mod)
            finally:
                remove_modules(injected)

class TestLoggingPresence:
    def test_logger_is_defined(self):
        with ensure_package(["templates"]) as pkg:
            injected = inject_sibling_modules(pkg)
            try:
                mod = import_registry("templates")
                # The module calls get_logger(__name__) and assigns to 'log'
                assert hasattr(mod, "log")
            finally:
                remove_modules(injected)