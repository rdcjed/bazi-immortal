# 使用 Python 3.12 作为基础镜像
FROM python:3.12-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY bazi_immortal/ bazi_immortal/
COPY web/ web/
COPY knowledge_base/ knowledge_base/
COPY pyproject.toml .

# 安装本包
RUN pip install --no-cache-dir -e .

EXPOSE 5000

CMD ["python", "web/app.py"]