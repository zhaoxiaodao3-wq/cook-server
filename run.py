"""开发服务器启动脚本 — 双击 start.bat 或在终端运行 python run.py"""
import uvicorn

if __name__ == "__main__":
    print("菜品小程序服务端启动中...")
    print("API 文档: http://localhost:8000/docs")
    print("按 Ctrl+C 停止服务")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
