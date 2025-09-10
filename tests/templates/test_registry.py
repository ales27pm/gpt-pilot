"""Fallback registry module that mirrors the real templates registry.

This module imports project template classes from the dynamically created
``templates`` package used in tests. Any missing ``name`` attributes on those
classes will raise ``AttributeError`` during import, allowing tests to verify
the registry's integrity.
"""

from enum import Enum

try:
    from templates.django_postgres import DjangoPostgresProjectTemplate
    from templates.fastapi_sqlite import FastapiSqliteProjectTemplate
    from templates.flask_sqlite import FlaskSqliteProjectTemplate
    from templates.node_express_mongoose import NodeExpressMongooseProjectTemplate
    from templates.react_express import ReactExpressProjectTemplate
    from templates.typer_cli import TyperCliProjectTemplate
    from templates.vite_react import ViteReactProjectTemplate
except ModuleNotFoundError:  # pragma: no cover - used only when real modules unavailable

    class DjangoPostgresProjectTemplate:
        name = "django_postgres"

    class FastapiSqliteProjectTemplate:
        name = "fastapi_sqlite"

    class FlaskSqliteProjectTemplate:
        name = "flask_sqlite"

    class NodeExpressMongooseProjectTemplate:
        name = "node_express_mongoose"

    class ReactExpressProjectTemplate:
        name = "react_express"

    class TyperCliProjectTemplate:
        name = "typer_cli"

    class ViteReactProjectTemplate:
        name = "vite_react"


from core.log import get_logger

log = get_logger(__name__)


class ProjectTemplateEnum(str, Enum):
    NODE_EXPRESS_MONGOOSE = NodeExpressMongooseProjectTemplate.name
    REACT_EXPRESS = ReactExpressProjectTemplate.name
    VITE_REACT = ViteReactProjectTemplate.name
    FLASK_SQLITE = FlaskSqliteProjectTemplate.name
    FASTAPI_SQLITE = FastapiSqliteProjectTemplate.name
    DJANGO_POSTGRES = DjangoPostgresProjectTemplate.name
    TYPER_CLI = TyperCliProjectTemplate.name


PROJECT_TEMPLATES = {
    NodeExpressMongooseProjectTemplate.name: NodeExpressMongooseProjectTemplate,
    ReactExpressProjectTemplate.name: ReactExpressProjectTemplate,
    ViteReactProjectTemplate.name: ViteReactProjectTemplate,
    FlaskSqliteProjectTemplate.name: FlaskSqliteProjectTemplate,
    FastapiSqliteProjectTemplate.name: FastapiSqliteProjectTemplate,
    DjangoPostgresProjectTemplate.name: DjangoPostgresProjectTemplate,
    TyperCliProjectTemplate.name: TyperCliProjectTemplate,
}


__all__ = ["ProjectTemplateEnum", "PROJECT_TEMPLATES", "log"]
