"""
RadioManager - Web应用主入口
"""

import os
import sys

# 检查环境
if __name__ == "__main__":
    # 检查Python版本
    if sys.version_info < (3, 11):
        print("错误: Python 3.11+ 需要")
        sys.exit(1)
    
    # 运行应用
    print("RadioManager 启动中...")
    print("访问: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    
    from app.main import app
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
