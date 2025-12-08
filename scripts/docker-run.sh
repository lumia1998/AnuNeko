#!/bin/bash

# Docker运行脚本
# 用于运行AnuNeko OpenAI API兼容服务器的Docker容器

# 设置镜像名称和标签
IMAGE_NAME="anuneko-openai"
IMAGE_TAG="latest"
CONTAINER_NAME="anuneko-api"

# 检查环境变量
if [ -z "$ANUNEKO_TOKEN" ]; then
    echo "⚠️ 警告: 未设置ANUNEKO_TOKEN环境变量"
    echo "请设置AnuNeko Token或使用以下命令运行:"
    echo "ANUNEKO_TOKEN=your_token_here $0"
    echo ""
    read -p "是否继续运行容器? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 停止并删除已存在的容器
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "停止并删除已存在的容器: $CONTAINER_NAME"
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
fi

# 创建日志目录
mkdir -p logs

# 运行Docker容器
echo "启动Docker容器: $CONTAINER_NAME"
docker run -d \
    --name $CONTAINER_NAME \
    -p 8000:8000 \
    -e ANUNEKO_TOKEN=$ANUNEKO_TOKEN \
    -e ANUNEKO_COOKIE=$ANUNEKO_COOKIE \
    -e FLASK_HOST=0.0.0.0 \
    -e FLASK_PORT=8000 \
    -e FLASK_DEBUG=False \
    -v $(pwd)/logs:/app/logs \
    --restart unless-stopped \
    $IMAGE_NAME:$IMAGE_TAG

if [ $? -eq 0 ]; then
    echo "✅ 容器启动成功!"
    echo ""
    echo "API服务地址: http://localhost:8000"
    echo "健康检查地址: http://localhost:8000/health"
    echo ""
    echo "查看日志: docker logs -f $CONTAINER_NAME"
    echo "停止容器: docker stop $CONTAINER_NAME"
else
    echo "❌ 容器启动失败"
    exit 1
fi