@echo off
cd /d E:\AI相关\hermes\program\bazi-immortal
set SENSENOVA_API_KEY=sk-YQXF3e87xb8zHZxcjwKOgYf2IaLJRmih
set LLM_QUALITY_CHECK=true
start "bazi-immortal" pythonw web\app.py
echo 道士预测已启动！
echo 访问地址: http://localhost:5000
pause
