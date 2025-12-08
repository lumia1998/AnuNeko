from app.services.anuneko_service import AnuNekoAPI
from app.services.session_service import session_service
import asyncio
import time
from flask import jsonify
from typing import Dict, Optional

def show(model_name: Optional[str] = None):
    """列出可用模型"""
    def get_anuneko_api() -> AnuNekoAPI:
        """获取 AnuNeko API 实例"""
        return session_service.get_anuneko_api()
    
    # 使用会话服务中的模型映射表
    MODEL_MAPPING = session_service.MODEL_MAPPING

    try:
        # 尝试从AnuNeko API获取真实模型列表
        api = get_anuneko_api()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            anuneko_models = loop.run_until_complete(api.model_view())
        finally:
            loop.close()
        
        models = []
        
        # 如果成功获取到AnuNeko模型，使用真实数据
        if anuneko_models and "models" in anuneko_models:
            # 更新模型映射表
            MODEL_MAPPING.clear()
            
            # 为每个AnuNeko模型创建对应的OpenAI模型条目
            for anuneko_model in anuneko_models["models"]:
                # 生成模型ID
                openai_model = f"mihoyo-{anuneko_model.lower().replace(' ', '_')}"
                MODEL_MAPPING[openai_model] = anuneko_model
                
                model_info = {
                    "id": openai_model,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "anuneko",
                    "permission": [],
                    "root": openai_model,
                    "parent": None,
                    "anuneko_model": anuneko_model,
                    "anuneko_model_id": anuneko_models["models"].index(anuneko_model)
                }
                
                # 如果请求特定模型，则只返回该模型
                if model_name is None or model_name == openai_model:
                    models.append(model_info)
            
            # 如果请求特定模型但未找到
            if model_name is not None and len(models) == 0:
                return jsonify({
                    "error": {
                        "message": f"Model {model_name} not found",
                        "type": "invalid_request_error",
                        "param": "model",
                        "code": "model_not_found"
                    }
                }), 404
            
            print(f"已更新模型映射表，共{len(MODEL_MAPPING)}个模型")
            # 同时更新会话服务中的模型映射
            session_service.MODEL_MAPPING = MODEL_MAPPING.copy()
        else:
            # 如果无法获取真实模型，使用默认映射
            MODEL_MAPPING.clear()
            MODEL_MAPPING["mihoyo-orange_cat"] = "Orange Cat"
            # 同时更新会话服务中的模型映射
            session_service.MODEL_MAPPING = MODEL_MAPPING.copy()
            
            default_model = {
                "id": "mihoyo-orange_cat",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "anuneko",
                "permission": [],
                "root": "mihoyo-orange_cat",
                "parent": None,
                "anuneko_model": "Orange Cat",
                "note": "default_model"
            }
            
            # 只有当请求所有模型或请求默认模型时才添加
            if model_name is None or model_name == "mihoyo-orange_cat":
                models.append(default_model)
            
        if model_name is not None and len(models) == 0:
            return jsonify({
                "error": {
                    "message": f"Model {model_name} not found",
                    "type": "invalid_request_error",
                    "param": "model",
                    "code": "model_not_found"
                }
            }), 404
        
        # 如果请求特定模型，只返回该模型的数据而不是列表
        if model_name is not None:
            return jsonify(models[0])
        else:
            return jsonify({
                "object": "list",
                "data": models,
                "anuneko_api_response": anuneko_models  # 调试信息，可选
            })
    
    except Exception as e:
        # 如果出错，设置默认映射作为后备
        MODEL_MAPPING.clear()
        MODEL_MAPPING["mihoyo-orange_cat"] = "Orange Cat"
        # 同时更新会话服务中的模型映射
        session_service.MODEL_MAPPING = MODEL_MAPPING.copy()
        
        models = [{
            "id": "mihoyo-orange_cat",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "anuneko",
            "permission": [],
            "root": "mihoyo-orange_cat",
            "parent": None,
            "anuneko_model": "Orange Cat",
            "note": "fallback_default_model"
        }]
        
        # 即使出错也要处理特定模型请求
        if model_name is not None and model_name != "mihoyo-orange_cat":
            return jsonify({
                "error": {
                    "message": f"Model {model_name} not found",
                    "type": "invalid_request_error",
                    "param": "model",
                    "code": "model_not_found"
                }
            }), 404
        elif model_name is not None:
            return jsonify(models[0])
        
        return jsonify({
            "object": "list",
            "data": models,
            "error": f"无法获取AnuNeko模型列表，使用默认模型: {str(e)}"
        })