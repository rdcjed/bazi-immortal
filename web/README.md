# Web Demo

此目录包含基于 Flask 的 Web 示例，用于交互式八字推算与运势报告展示。

## 启动方式

1. 安装运行依赖：

```bash
pip install flask zhdate requests
```

2. 启动服务：

```bash
python web/app.py
```

3. 打开浏览器访问：

```bash
http://localhost:5000
```

## LLM 模式

如果你希望启用 LLM 增强分析：

1. 复制 `.env.example` 到项目根目录：

```bash
copy .env.example .env
```

2. 编辑 `.env`：

```ini
SENSENOVA_API_KEY=your_api_key_here
LLM_QUALITY_CHECK=true
```

3. 启动增强模式：

```bash
start_llm.bat
```

> 注意：请不要将 `.env` 提交到版本控制。
