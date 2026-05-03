from flask import Blueprint

goals = Blueprint('goals', __name__)

from app.goals import routes