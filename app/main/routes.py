from flask import Blueprint
# 导入处理函数
from app.main import health,sessions

# 创建蓝图
health_bp = Blueprint("health", __name__)
sessions_dp = Blueprint("sessions", __name__)


# 定义路由
@health_bp.route("", methods=["GET"])
@health_bp.route("/", methods=["GET"])
def health_check():
    return health.check()


@sessions_dp.route("", methods=["GET"])
@sessions_dp.route("/", methods=["GET"])
def list_sessions_route():
    """列出会话"""
    return sessions.show()

@sessions_dp.route("/<session_id>", methods=["DELETE"])
def delete_session_route(session_id: str):
    """删除会话"""
    return sessions.delete(session_id)
