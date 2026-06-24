"""
RadioManager Desktop Launcher v2.5.0
启动后端服务 + 打开原生桌面窗口（pywebview + Edge WebView2）
"""
import os
import sys
import time
import socket
import subprocess
import threading
import traceback

VERSION = '2.5.0'
PORT = 8000

_backend_error = None


def fix_console():
    """pythonw.exe 没有控制台，重定向 stdout/stderr"""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w', encoding='utf-8')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w', encoding='utf-8')


def show_error(title, msg):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, msg, title, 0x10)
    except Exception:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(title, msg)
        except Exception:
            pass


def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def wait_for_port(port, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def main():
    fix_console()

    try:
        base = get_base_dir()
        backend_dir = os.path.join(base, 'backend')
        user_data_dir = os.path.join(base, 'data')
        python_dir = os.path.join(base, 'python')

        if not os.path.isdir(backend_dir):
            base = os.path.dirname(base)
            backend_dir = os.path.join(base, 'backend')
            user_data_dir = os.path.join(base, 'data')
            python_dir = os.path.join(base, 'python')

        if not os.path.isdir(backend_dir):
            show_error(f'RadioManager v{VERSION}', f'找不到 backend 目录:\n{backend_dir}')
            sys.exit(1)

        os.makedirs(user_data_dir, exist_ok=True)

        python_exe = os.path.join(python_dir, 'python.exe')
        release_server = os.path.join(backend_dir, 'release_server.py')

        if not os.path.isfile(python_exe):
            show_error(f'RadioManager v{VERSION}', f'找不到 Python:\n{python_exe}')
            sys.exit(1)

        if not os.path.isfile(release_server):
            show_error(f'RadioManager v{VERSION}', f'找不到 release_server.py:\n{release_server}')
            sys.exit(1)

        # 设置环境变量（与 web 版 start.bat 一致）
        env = os.environ.copy()
        env['PYTHONPATH'] = backend_dir
        env['DATABASE_MODE'] = 'sqlite'
        env['SQLITE_URL'] = 'sqlite:///./radiomanager.db'

        # 用 subprocess 启动 release_server.py（包含前端 SPA 挂载 + 管理员创建）
        proc = subprocess.Popen(
            [python_exe, release_server],
            cwd=base,  # 包根目录，与 web 版一致
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )

        # 等待后端就绪
        if not wait_for_port(PORT):
            show_error(
                f'RadioManager v{VERSION} - 启动失败',
                f'后端未响应 (端口 {PORT})\n\n'
                f'可能原因:\n'
                f'1. 端口被占用\n'
                f'2. 缺少 VC++ 运行库\n'
                f'   下载: https://aka.ms/vs/17/release/vc_redist.x64.exe\n\n'
                f'Python: {python_exe}\n'
                f'后端: {release_server}'
            )
            proc.kill()
            sys.exit(1)

        # 打开原生桌面窗口
        import webview
        window = webview.create_window(
            title=f'RadioManager v{VERSION}',
            url=f'http://127.0.0.1:{PORT}',
            width=1280,
            height=800,
            min_size=(900, 600),
            text_select=True,
        )
        webview.start(gui='edgechromium', debug=False)

        # 窗口关闭后终止后端
        proc.terminate()

    except Exception as e:
        show_error(
            f'RadioManager v{VERSION} - 启动异常',
            f'{type(e).__name__}: {e}\n\n{traceback.format_exc()}'
        )
        sys.exit(1)


if __name__ == '__main__':
    main()
