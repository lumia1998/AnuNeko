# Docker 部署指南

本文档介绍如何使用Docker部署AnuNeko OpenAI API兼容服务器。

## 目录结构

```
.
├── docker/
│   ├── Dockerfile          # Docker镜像构建文件
│   ├── .dockerignore       # Docker忽略文件
│   └── docker-compose.yml # Docker Compose配置
├── scripts/
│   ├── docker-build.sh     # Docker构建脚本
│   └── docker-run.sh       # Docker运行脚本
└── .github/
    └── workflows/
        └── docker-build.yml # GitHub Actions自动化构建
```

## 本地构建和运行

### 方法1: 使用脚本

1. 构建镜像：
```bash
./scripts/docker-build.sh
```

2. 运行容器：
```bash
ANUNEKO_TOKEN=your_token_here ./scripts/docker-run.sh
```

### 方法2: 使用Docker命令

1. 构建镜像：
```bash
docker build -f ./docker/Dockerfile -t anuneko-openai:latest .
```

2. 运行容器：
```bash
docker run -d \
  --name anuneko-api \
  -p 8000:8000 \
  -e ANUNEKO_TOKEN=your_token_here \
  -e ANUNEKO_COOKIE=your_cookie_here \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  anuneko-openai:latest
```

### 方法3: 使用Docker Compose

1. 复制环境变量文件：
```bash
cp .env.example .env
# 编辑.env文件，填入你的ANUNEKO_TOKEN
```

2. 启动服务：
```bash
docker-compose -f docker/docker-compose.yml up -d
```

## 环境变量

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `ANUNEKO_TOKEN` | 是 | - | AnuNeko API Token |
| `ANUNEKO_COOKIE` | 否 | - | AnuNeko Cookie (可选) |
| `FLASK_HOST` | 否 | 0.0.0.0 | Flask服务器主机地址 |
| `FLASK_PORT` | 否 | 8000 | Flask服务器端口 |
| `FLASK_DEBUG` | 否 | False | 是否启用调试模式 |
| `LOG_LEVEL` | 否 | info | 日志级别 |
| `LOG_PATH` | 否 | logs | 日志目录 |
| `LOG_NAME` | 否 | anuneko-openai | 日志文件名 |

## 自动化构建

### GitHub Actions

项目配置了GitHub Actions自动化构建，当以下情况发生时会自动构建Docker镜像：

1. 推送到`main`或`master`分支
2. 创建标签（如`v1.0.0`）
3. 创建Pull Request

构建的镜像会推送到GitHub Container Registry (ghcr.io)。

镜像标签规则：
- 分支推送：`branch-name`
- 标签推送：`v1.0.0`, `v1.0`, `v1`
- 默认分支：`latest`

### GitLab CI/CD

项目也配置了GitLab CI/CD流水线，包含以下阶段：

1. `build`: 构建Docker镜像并推送到GitLab Container Registry
2. `test`: 运行容器测试
3. `deploy`: 部署到生产环境（手动触发）

## 健康检查

容器启动后，可以通过以下端点进行健康检查：

- API服务: http://localhost:8000
- 健康检查: http://localhost:8000/health

## 日志查看

查看容器日志：
```bash
docker logs -f anuneko-api
```

查看应用日志文件：
```bash
tail -f logs/anuneko-openai.log
```

## 故障排除

### 常见问题

1. **容器启动失败**
   - 检查环境变量是否正确设置
   - 查看容器日志：`docker logs anuneko-api`

2. **API调用失败**
   - 确认ANUNEKO_TOKEN是否有效
   - 检查网络连接

3. **权限问题**
   - 确保logs目录有写权限
   - 检查Docker用户权限

### 调试模式

启用调试模式：
```bash
docker run -d \
  --name anuneko-api \
  -p 8000:8000 \
  -e ANUNEKO_TOKEN=your_token_here \
  -e FLASK_DEBUG=True \
  anuneko-openai:latest
```

## 生产环境部署建议

1. 使用HTTPS反向代理（如Nginx）
2. 设置适当的资源限制
3. 配置日志轮转
4. 使用健康检查
5. 设置重启策略
6. 定期更新基础镜像

## 安全注意事项

1. 不要在镜像中包含敏感信息
2. 使用环境变量传递敏感配置
3. 定期更新依赖包
4. 限制容器权限
5. 使用非root用户运行容器（可选）