#!/usr/bin/env python3
"""
Interview System 统一启动脚本
双击或运行 python start.py 即可启动全部服务
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

# 配置
BACKEND_PORT = 8000
FRONTEND_PORT = 5173
ROOT_DIR = Path(__file__).parent
FRONTEND_DIR = ROOT_DIR / "frontend"

# 进程列表
processes = []


def log(step: int, total: int, msg: str, status: str = ""):
    """格式化输出"""
    prefix = f"[{step}/{total}]"
    if status == "ok":
        print(f"{prefix} {msg} ✓")
    elif status == "fail":
        print(f"{prefix} {msg} ✗")
    elif status == "wait":
        print(f"{prefix} {msg}...", end=" ", flush=True)
    else:
        print(f"{prefix} {msg}")


def check_python() -> bool:
    """检查 Python 版本"""
    log(1, 4, "检查 Python 环境", "wait")
    version = sys.version_info
    if version >= (3, 10):
        print(f"✓ Python {version.major}.{version.minor}")
        return True
    print(f"✗ 需要 Python 3.10+，当前 {version.major}.{version.minor}")
    return False


def check_node() -> bool:
    """检查 Node.js"""
    log(2, 4, "检查 Node.js 环境", "wait")
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode == 0:
            print(f"✓ Node {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    print("✗ 未安装 Node.js")
    return False


def install_backend_deps() -> bool:
    """安装后端依赖"""
    try:
        import fastapi
        import uvicorn
        return True
    except ImportError:
        print("    安装后端依赖...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", ".[api]", "-q"],
            cwd=ROOT_DIR
        )
        return result.returncode == 0


def install_frontend_deps() -> bool:
    """安装前端依赖"""
    node_modules = FRONTEND_DIR / "node_modules"
    if node_modules.exists():
        return True
    print("    安装前端依赖...")
    result = subprocess.run(
        ["npm", "install"],
        cwd=FRONTEND_DIR,
        shell=True
    )
    return result.returncode == 0


def start_backend() -> subprocess.Popen | None:
    """启动后端服务"""
    log(3, 4, "启动后端服务", "wait")
    try:
        env = os.environ.copy()
        src_dir = str(ROOT_DIR / "src")
        existing_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{src_dir}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else src_dir
        )

        proc = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn",
                "interview_system.api.main:app",
                "--app-dir", src_dir,
                "--host", "0.0.0.0",
                "--port", str(BACKEND_PORT),
                "--reload"
            ],
            cwd=ROOT_DIR,
            env=env,
        )
        time.sleep(2)
        if proc.poll() is None:
            print(f"✓ http://localhost:{BACKEND_PORT}")
            return proc
        print("✗ 启动失败")
        return None
    except Exception as e:
        print(f"✗ {e}")
        return None


def start_frontend() -> subprocess.Popen | None:
    """启动前端服务"""
    log(4, 4, "启动前端服务", "wait")
    try:
        proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=FRONTEND_DIR,
            shell=True,
        )
        time.sleep(3)
        if proc.poll() is None:
            print(f"✓ http://localhost:{FRONTEND_PORT}")
            return proc
        print("✗ 启动失败")
        return None
    except Exception as e:
        print(f"✗ {e}")
        return None


def cleanup(signum=None, frame=None):
    """清理所有进程"""
    print("\n\n正在停止服务...")
    for proc in processes:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    print("已停止所有服务")
    sys.exit(0)


def main():
    print("=" * 50)
    print("  Interview System 启动器")
    print("=" * 50)
    print()

    # 注册信号处理
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # 环境检查
    if not check_python():
        sys.exit(1)

    if not check_node():
        print("\n提示: 前端需要 Node.js，请从 https://nodejs.org 下载安装")
        sys.exit(1)

    # 安装依赖
    print()
    print("检查依赖...")
    if not install_backend_deps():
        print("后端依赖安装失败")
        sys.exit(1)

    if not install_frontend_deps():
        print("前端依赖安装失败")
        sys.exit(1)

    print("依赖检查完成 ✓")
    print()

    # 启动服务
    backend = start_backend()
    if not backend:
        sys.exit(1)
    processes.append(backend)

    frontend = start_frontend()
    if not frontend:
        cleanup()
        sys.exit(1)
    processes.append(frontend)

    # 完成
    print()
    print("=" * 50)
    print("  ✅ 启动完成!")
    print()
    print(f"  前端: http://localhost:{FRONTEND_PORT}")
    print(f"  后端: http://localhost:{BACKEND_PORT}")
    print(f"  API 文档: http://localhost:{BACKEND_PORT}/docs")
    print()
    print("  按 Ctrl+C 停止所有服务")
    print("=" * 50)

    # 保持运行
    try:
        while True:
            # 检查进程状态
            for proc in processes:
                if proc and proc.poll() is not None:
                    print("\n服务异常退出，正在停止...")
                    cleanup()
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
