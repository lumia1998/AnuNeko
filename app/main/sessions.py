from flask import jsonify
from typing import Dict, Any

# 全局变量存储会话信息
sessions_msg: Dict[str, Dict[str, Any]] = {}
def show():
    """列出会话"""
    session_list = []
    for session_id, session_data in sessions_msg.items():
        session_list.append({
            "id": session_data["id"],
            "model": session_data["openai_model"],
            "created_at": session_data["created_at"],
            "has_anuneko_chat": session_data["has_anuneko_chat"]
        })
    
    return jsonify({
        "sessions": session_list,
        "total": len(session_list)
    })

def delete(session_id: str):
    """删除会话"""
    if session_id in sessions_msg:
        del sessions_msg[session_id]
        return jsonify({"status": "success", "message": "会话已删除"})
    else:
        return jsonify({"status": "error", "message": "会话不存在"}), 404
