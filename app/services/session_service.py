# -*- coding: utf-8 -*-
"""
会话管理服务
处理会话创建、管理和模型映射
"""

import os
import uuid
import asyncio
import time
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
        # API Key -> session_id 映射（用于持久会话）
        self.api_key_sessions: Dict[str, str] = {}
        # 会话最后使用时间
        self.session_last_used: Dict[str, float] = {}
        # 会话配置
        self.SESSION_TTL = int(os.environ.get("SESSION_TTL", 7200))  # 默认2小时
        self.NEW_CONVERSATION_THRESHOLD = int(os.environ.get("NEW_CONVERSATION_THRESHOLD", 1))  # 消息数量阈值
    
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
    
    def should_create_new_session(
        self, 
        messages: List[Dict[str, str]], 
        current_session_id: Optional[str] = None
    ) -> bool:
        """智能判断是否应该创建新会话
        
        根据以下规则判断：
        1. 如果没有当前会话，创建新会话
        2. 如果会话已过期（超过 TTL），创建新会话
        3. 如果消息数量很少（可能是清空上下文后的新对话），创建新会话
        
        Args:
            messages: 消息列表
            current_session_id: 当前会话ID
            
        Returns:
            True 表示应该创建新会话，False 表示应该复用现有会话
        """
        # 1. 没有当前会话，必须创建
        if not current_session_id or current_session_id not in self.sessions:
            return True
        
        # 2. 检查会话是否过期
        last_used = self.session_last_used.get(current_session_id, 0)
        if time.time() - last_used > self.SESSION_TTL:
            print(f"会话 {current_session_id} 已过期 (TTL={self.SESSION_TTL}s)，创建新会话")
            return True
        
        # 3. 检查消息数量（智能检测是否为新对话）
        # 过滤掉 system 角色的消息，只统计用户和助手的对话
        conversation_messages = [
            msg for msg in messages 
            if msg.get("role") in ["user", "assistant"]
        ]
        
        # 如果对话消息数量小于阈值，认为是新对话
        if len(conversation_messages) <= self.NEW_CONVERSATION_THRESHOLD:
            print(f"检测到新对话（消息数={len(conversation_messages)}），创建新会话")
            return True
        
        # 4. 其他情况，复用现有会话
        return False
    
    def get_session_for_request(
        self, 
        request_data: Dict[str, Any], 
        api_key: Optional[str] = None
    ) -> str:
        """根据请求获取或创建会话（智能管理版本）
        
        Args:
            request_data: 请求数据
            api_key: 客户端的 API Key（用于会话绑定）
            
        Returns:
            会话 ID
        """
        model = request_data.get("model", "mihoyo-orange_cat")
        messages = request_data.get("messages", [])
        
        # 确保模型映射是最新的
        if not self.MODEL_MAPPING:
            self.update_model_mapping()
        
        # 从动态映射表中获取AnuNeko模型名
        anuneko_model = self.MODEL_MAPPING.get(model)
        
        if not anuneko_model:
            # 如果映射中没有，默认使用Orange Cat
            print("未找到模型映射，使用默认模型：Orange Cat")
            anuneko_model = "Orange Cat"
        
        # 获取当前 API Key 对应的会话ID（如果有的话）
        current_session_id = None
        if api_key and api_key in self.api_key_sessions:
            current_session_id = self.api_key_sessions[api_key]
        
        # 智能判断是否需要创建新会话
        should_create_new = self.should_create_new_session(messages, current_session_id)
        
        if not should_create_new and current_session_id:
            # 复用现有会话
            session = self.sessions[current_session_id]
            
            # 更新最后使用时间
            self.session_last_used[current_session_id] = time.time()
            
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
                        print(f"切换会话 {current_session_id} 的模型为 {anuneko_model}")
                finally:
                    loop.close()
            
            print(f"复用现有会话: {current_session_id}")
            return current_session_id
        
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
                
                # 更新 API Key 映射和最后使用时间
                if api_key:
                    self.api_key_sessions[api_key] = new_session_id
                self.session_last_used[new_session_id] = time.time()
                
                print(f"创建新会话: {new_session_id} (模型: {anuneko_model})")
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