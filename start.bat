@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ================================
echo  命运道士 · 八字命理推算系统
echo ================================
echo.
echo 请选择模式：
echo  1. 普通模式（规则引擎）
echo  2. LLM 增强模式（需配置 API Key）
echo.
set /p mode=请输入 (1 或 2):

if "%mode%"=="2" (
    if not exist .env (
        echo.
        echo ❌ 未找到 .env 文件
        echo 请创建 .env 文件并写入：
        echo SENSENOVA_API_KEY=你的API密钥
        pause
        exit /b
    )
    for /f "tokens=*" %%a in (.env) do set "%%a"
    set LLM_QUALITY_CHECK=true
    echo ✅ LLM 增强模式已开启
) else (
    echo ℹ️ 普通模式（规则引擎）
)

python web\app.py
pause