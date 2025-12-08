from flask import Blueprint, request, jsonify
from app.services.chat_service import chat_service

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/completions", methods=["POST"])
def chat_completions():
    """聊天完成端点"""
    try:
        request_data = request.get_json()
        result = chat_service.process_chat_request(request_data)
        
        # 如果结果是元组，说明包含状态码
        if isinstance(result, tuple) and len(result) == 2:
            return jsonify(result[0]), result[1]
        
        # 如果结果是字典，说明是正常响应
        if isinstance(result, dict):
            return jsonify(result)
        
        # 如果是Response对象，直接返回（流式响应）
        return result
        
    except Exception as e:
        return jsonify({
            "error": {
                "message": f"服务器内部错误: {str(e)}",
                "type": "server_error"
            }
        }), 500