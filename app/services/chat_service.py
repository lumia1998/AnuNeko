# -*- coding: utf-8 -*-
"""
聊天服务
处理聊天完成相关的逻辑
"""

import json
import time
import uuid
import asyncio
from typing import Dict, Any, Generator

from flask import Response, stream_with_context

from app.services.anuneko_service import AnuNekoAPI
from app.services.session_service import session_service


class ChatService:
    """聊天服务类"""
    
    def __init__(self):
        self._anuneko_api: AnuNekoAPI = None
    
    def get_anuneko_api(self) -> AnuNekoAPI:
        """获取 AnuNeko API 实例"""
        if self._anuneko_api is None:
            self._anuneko_api = AnuNekoAPI()
        return self._anuneko_api
    
    def format_openai_response(self, model: str, content: str, session_id: str = None) -> Dict[str, Any]:
        """格式化 OpenAI API 响应"""
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 0,  # AnuNeko 不提供 token 计数
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "session_id": session_id
        }
    
    def format_openai_chunk(self, model: str, content: str, session_id: str = None) -> str:
        """格式化 OpenAI API 流式响应块"""
        chunk = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "content": content
                    },
                    "finish_reason": None
                }
            ]
        }
        
        if session_id:
            chunk["session_id"] = session_id
        
        return f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
    
    def process_chat_request(self, request_data: Dict[str, Any], api_key: str = None):
        """处理聊天请求（支持智能会话管理）"""
        if not request_data:
            return {"error": {"message": "请求体不能为空", "type": "invalid_request_error"}}, 400
        
        messages = request_data.get("messages", [])
        if not messages:
            return {"error": {"message": "messages 不能为空", "type": "invalid_request_error"}}, 400
        
        # 获取最后一条用户消息
        user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        if not user_message:
            return {"error": {"message": "未找到用户消息", "type": "invalid_request_error"}}, 400
        
        model = request_data.get("model", "gpt-3.5-turbo")
        stream = request_data.get("stream", False)
        
        # 获取或创建会话（传递 API Key 用于智能管理）
        session_id = session_service.get_session_for_request(request_data, api_key)
        session = session_service.get_session(session_id)
        
        if stream:
            # 流式响应
            def generate():
                api = self.get_anuneko_api()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    async def stream_generator():
                        async for chunk in api.stream_reply_generator(
                            session["anuneko_chat_id"], user_message
                        ):
                            yield self.format_openai_chunk(model, chunk, session_id)
                        
                        # 发送结束块
                        end_chunk = {
                            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {},
                                    "finish_reason": "stop"
                                }
                            ]
                        }
                        yield f"data: {json.dumps(end_chunk, ensure_ascii=False)}\n\n"
                        yield "data: [DONE]\n\n"
                    
                    # 运行异步生成器
                    async_gen = stream_generator()
                    while True:
                        try:
                            chunk = loop.run_until_complete(async_gen.__anext__())
                            yield chunk
                        except StopAsyncIteration:
                            break
                finally:
                    loop.close()
            
            return Response(
                stream_with_context(generate()),
                mimetype="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream"
                }
            )
        else:
            # 非流式响应
            api = self.get_anuneko_api()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                response = loop.run_until_complete(
                    api.stream_reply(session["anuneko_chat_id"], user_message)
                )
                return self.format_openai_response(model, response, session_id)
            finally:
                loop.close()


# 全局聊天服务实例
chat_service = ChatService()