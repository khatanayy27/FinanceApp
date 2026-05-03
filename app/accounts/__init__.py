from flask import Blueprint

accounts = Blueprint('accounts', __name__)

from app.accounts import routes