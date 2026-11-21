FROM python:3.12-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖（利用缓存层）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/logs /app/uploads

# 创建非 root 用户
RUN useradd -m -r appuser && chown -R appuser:appuser /app

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import json, urllib.request; r=urllib.request.urlopen('http://localhost:8000/health'); assert r.status == 200 and json.load(r)['status'] == 'ok'" || exit 1

# 切换到非 root 用户
USER appuser

# 启动
CMD ["sh", "-c", "python -m app.scripts.init_db && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
