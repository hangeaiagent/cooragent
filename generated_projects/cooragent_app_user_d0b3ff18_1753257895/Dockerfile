FROM python:3.12-slim

WORKDIR /app


# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt


# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p store/agents store/prompts store/workflows logs

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# 启动命令
CMD ["python", "main.py"]
