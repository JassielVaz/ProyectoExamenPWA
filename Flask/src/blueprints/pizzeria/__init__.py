from flask import Blueprint

pizzeria_bp = Blueprint(
    'pizzeria',
    __name__,
    url_prefix='/api/pizzeria'
)

from . import routes