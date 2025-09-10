from enum import Enum

from core.log import get_logger

from .django_postgres import DjangoPostgresProjectTemplate
from .fastapi_sqlite import FastapiSqliteProjectTemplate
from .flask_sqlite import FlaskSqliteProjectTemplate
from .node_express_mongoose import NodeExpressMongooseProjectTemplate
from .react_express import ReactExpressProjectTemplate
from .typer_cli import TyperCliProjectTemplate
from .vite_react import ViteReactProjectTemplate

log = get_logger(__name__)


class ProjectTemplateEnum(str, Enum):
    """Choices of available project templates."""

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
