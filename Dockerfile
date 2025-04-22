FROM python:3.12-slim as builder
ENV REASONING_API_KEY=sk-***
ENV REASONING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
ENV REASONING_MODEL=deepseek-r1
ENV BASIC_API_KEY=sk-***
ENV BASIC_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
ENV BASIC_MODEL=qwen-max-latest
ENV CODE_API_KEY=sk-***
ENV CODE_BASE_URL=https://api.deepseek.com/v1
ENV CODE_MODEL=deepseek-chat
ENV Generate_avatar_API_KEY=sk-***
ENV Generate_avatar_BASE_URL=https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis
ENV Generate_avatar_MODEL=wanx2.0-t2i-turbo
ENV VL_API_KEY=sk-***
ENV VL_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
ENV VL_MODEL=qwen2.5-vl-72b-instruct
ENV APP_ENV=development
ENV TAVILY_API_KEY=tvly-dev-***
ENV ANONYMIZED_TELEMETRY=false
ENV SLACK_USER_TOKEN=***
# -------------- 内网环境配置 --------------
# 设置固定时区（内网常用）
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone


# -------------- 构建阶段 --------------

# 安装内网定制的uv工具（指定版本+内网源）
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple uv

# -------------- 项目准备 --------------
WORKDIR /app

COPY pyproject.toml .
COPY . /app
COPY .env /app/.env

ENV http_proxy=http://10.16.6.112:7890
ENV https_proxy=http://10.16.6.112:7890
ENV NO_PROXY=localhost,127.0.0.1,10.0.0.0/8
# -------------- 虚拟环境构建 --------------
# 创建虚拟环境（指定内网Python 3.12）
RUN uv python install 3.12
RUN uv venv --python 3.12
ENV UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
# 激活环境并安装依赖（内网镜像源）
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN uv sync

EXPOSE 9000
# 启动命令（内网监听配置）
CMD ["uv", "run", "src/service/app.py","--port", "9000"]
