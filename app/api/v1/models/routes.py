from flask import Blueprint
from app.api.v1.models import models

models_bp = Blueprint("models", __name__)

@models_bp.route("", methods=["GET"])
def models_show_all():
    """全部模型列表端点"""
    return models.show()

@models_bp.route("/<model_name>", methods=["GET"])
def models_show(model_name: str):
    """单个模型列表端点"""
    return models.show(model_name)