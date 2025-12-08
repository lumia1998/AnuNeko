from flask import jsonify
from app.services.session_service import session_service

def show():
    """列出会话"""
    session_list = session_service.list_sessions()
    
    return jsonify({
        "sessions": session_list,
        "total": len(session_list)
    })

def delete(session_id: str):
    """删除会话"""
    if session_service.delete_session(session_id):
        return jsonify({"status": "success", "message": "会话已删除"})
    else:
        return jsonify({"status": "error", "message": "会话不存在"}), 404
