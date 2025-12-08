# -*- coding: utf-8 -*-
"""
会话管理服务
处理会话创建、管理和模型映射
"""

import os
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

from app.services.anuneko_service import AnuNekoAPI


class SessionService:
    """会话管理服务类"""
    
    def __init__(self):
        # 全局变量存储会话信息
        self.sessions: Dict[str, Dict[str, Any]] = {}
        # 动态模型映射表
        self.MODEL_MAPPING: Dict[str, str] = {}
        # AnuNeko API 实例
        self._anuneko_api: Optional[AnuNekoAPI] = None
    
    def get_anuneko_api(self) -> AnuNekoAPI:
        """获取 AnuNeko API 实例"""
        if self._anuneko_api is None:
            self._anuneko_api = AnuNekoAPI()
        return self._anuneko_api
    
    def update_model_mapping(self):
        """动态更新模型映射表"""
        try:
            api = self.get_anuneko_api()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                anuneko_models = loop.run_until_complete(api.model_view())
            finally:
                loop.close()
            
            if anuneko_models and "models" in anuneko_models:
                # 清空现有映射
                self.MODEL_MAPPING.clear()
                
                # 为每个AnuNeko模型创建映射
                for anuneko_model in anuneko_models["models"]:
                    # 生成模型ID
                    openai_model = f"mihoyo-{anuneko_model.lower().replace(' ', '_')}"
                    self.MODEL_MAPPING[openai_model] = anuneko_model
                
                print(f"已更新模型映射表，共{len(self.MODEL_MAPPING)}个模型")
            else:
                # 如果无法获取，设置默认映射
                self.MODEL_MAPPING.clear()
                self.MODEL_MAPPING["mihoyo-orange_cat"] = "Orange Cat"
                print("无法获取AnuNeko模型，使用默认映射")
                
        except Exception as e:
            print(f"更新模型映射失败: {str(e)}")
            # 设置默认映射作为后备
            self.MODEL_MAPPING.clear()
            self.MODEL_MAPPING["mihoyo-orange_cat"] = "Orange Cat"
    
    def get_session_for_request(self, request_data: Dict[str, Any]) -> str:
        """根据请求获取或创建会话"""
        model = request_data.get("model", "mihoyo-orange_cat")
        
        # 确保模型映射是最新的
        if not self.MODEL_MAPPING:
            self.update_model_mapping()
        
        # 从动态映射表中获取AnuNeko模型名
        anuneko_model = self.MODEL_MAPPING.get(model)
        
        if not anuneko_model:
            # 如果映射中没有，默认使用Orange Cat
            print("未找到模型映射，使用默认模型：Orange Cat")
            anuneko_model = "Orange Cat"
        
        # 尝试从请求中获取会话ID（如果有的话）
        session_id = request_data.get("session_id")
        
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            # 检查模型是否匹配，如果不匹配则切换模型
            if session.get("model") != anuneko_model:
                api = self.get_anuneko_api()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    success = loop.run_until_complete(
                        api.switch_model(session["anuneko_chat_id"], anuneko_model)
                    )
                    if success:
                        session["model"] = anuneko_model
                finally:
                    loop.close()
            return session_id
        
        # 创建新会话
        api = self.get_anuneko_api()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            anuneko_chat_id = loop.run_until_complete(api.create_session(anuneko_model))
            if anuneko_chat_id:
                new_session_id = str(uuid.uuid4())
                self.sessions[new_session_id] = {
                    "id": new_session_id,
                    "anuneko_chat_id": anuneko_chat_id,
                    "model": anuneko_model,
                    "openai_model": model,
                    "created_at": datetime.now().isoformat(),
                    "has_anuneko_chat": True
                }
                return new_session_id
        finally:
            loop.close()
        
        raise Exception("无法创建会话")
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出会话"""
        session_list = []
        for session_id, session_data in self.sessions.items():
            session_list.append({
                "id": session_data["id"],
                "model": session_data["openai_model"],
                "created_at": session_data["created_at"],
                "has_anuneko_chat": session_data["has_anuneko_chat"]
            })
        return session_list
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        return self.sessions.get(session_id)


# 全局会话服务实例
session_service = SessionService()