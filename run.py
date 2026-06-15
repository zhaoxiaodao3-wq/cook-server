"""启动脚本 — 本地开发或宝塔生产均可使用"""
import os

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "").lower() in ("1", "true", "yes")
    print("菜品小程序服务端启动中...")
    print(f"API 文档: http://localhost:{port}/docs")
    print("按 Ctrl+C 停止服务")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
    )
