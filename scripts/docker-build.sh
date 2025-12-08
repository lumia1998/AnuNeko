#!/bin/bash

# Docker构建脚本
# 用于构建AnuNeko OpenAI API兼容服务器的Docker镜像

echo "开始构建Docker镜像..."

# 设置镜像名称和标签
IMAGE_NAME="anuneko-openai"
IMAGE_TAG="latest"

# 构建Docker镜像
docker build -f ./docker/Dockerfile -t ${IMAGE_NAME}:${IMAGE_TAG} .

if [ $? -eq 0 ]; then
    echo "✅ Docker镜像构建成功: ${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    echo "使用以下命令运行容器:"
    echo "docker run -d -p 8000:8000 --name anuneko-api -e ANUNEKO_TOKEN=your_token_here ${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    echo "或使用docker-compose运行:"
    echo "docker-compose up -d"
else
    echo "❌ Docker镜像构建失败"
    exit 1
fi