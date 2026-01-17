#!/usr/bin/env python3
"""
Interview System 统一启动脚本
双击或运行 python start.py 即可启动全部服务
"""

import subprocess
import sys
import os
import json
import time
import signal
import re
import argparse
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


PUBLIC_URL_STATE_FILE = ROOT_DIR / ".public_url_state.json"


def write_public_url_state(url: str | None, is_public: bool) -> None:
    """写入前端公网 URL 状态文件（后端从该文件读取）。"""
    try:
        PUBLIC_URL_STATE_FILE.write_text(
            json.dumps({"url": url, "is_public": is_public}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:
        import traceback
        print(f"警告: 写入公网 URL 状态失败: {e}")
        traceback.print_exc()


def print_ascii_qrcode(url: str) -> None:
    """在终端输出 ASCII 二维码（依赖 qrcode）。"""
    try:
        import qrcode

        qr = qrcode.QRCode(border=2)
        qr.add_data(url)
        qr.make(fit=True)
        matrix = qr.get_matrix()

        print()
        print("  扫码打开前端公网地址:")
        for row in matrix:
            print("  " + "".join("██" if cell else "  " for cell in row))
        print(f"\n  {url}\n")
    except Exception as e:
        import traceback
        print(f"警告: 终端二维码输出失败: {e}")
        traceback.print_exc()


def check_python() -> bool:
    """检查 Python 版本"""
    log(1, 4, "检查 Python 环境", "wait")
    version = sys.version_info
    if version >= (3, 11):
        print(f"✓ Python {version.major}.{version.minor}")
        return True
    print(f"✗ 需要 Python 3.11+，当前 {version.major}.{version.minor}")
    return False


def check_node() -> bool:
    """检查 Node.js"""
    log(2, 4, "检查 Node.js 环境", "wait")
    try:
        result = subprocess.run(
            ["node", "--version"], capture_output=True, text=True, shell=True
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
    import importlib.util

    if importlib.util.find_spec("fastapi") and importlib.util.find_spec("uvicorn"):
        return True

    print("    安装后端依赖...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", ".[api]", "-q"],
        cwd=ROOT_DIR,
    )
    return result.returncode == 0


def install_frontend_deps() -> bool:
    """安装前端依赖"""
    node_modules = FRONTEND_DIR / "node_modules"
    if node_modules.exists():
        return True
    print("    安装前端依赖...")
    result = subprocess.run(["npm", "install"], cwd=FRONTEND_DIR, shell=True)
    return result.returncode == 0


def start_backend(*, enable_public: bool) -> subprocess.Popen | None:
    """启动后端服务"""
    log(3, 4, "启动后端服务", "wait")
    try:
        env = os.environ.copy()
        src_dir = str(ROOT_DIR / "src")
        existing_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{src_dir}{os.pathsep}{existing_pythonpath}"
            if existing_pythonpath
            else src_dir
        )
        env["PUBLIC_URL_STATE_PATH"] = str(PUBLIC_URL_STATE_FILE)
        if enable_public:
            env.setdefault(
                "CORS_ALLOWED_HOST_SUFFIXES",
                ".trycloudflare.com,.ngrok-free.app,.ngrok.io",
            )

        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "interview_system.api.main:app",
                "--app-dir",
                src_dir,
                "--host",
                "0.0.0.0",
                "--port",
                str(BACKEND_PORT),
                "--reload",
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


def start_frontend(*, enable_public: bool) -> subprocess.Popen | None:
    """启动前端服务"""
    log(4, 4, "启动前端服务", "wait")
    try:
        env = os.environ.copy()
        if enable_public:
            env.setdefault(
                "VITE_ALLOWED_HOSTS",
                ".trycloudflare.com,.ngrok-free.app,.ngrok.io",
            )
        proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=FRONTEND_DIR,
            shell=True,
            env=env,
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


def check_tunnel_binary() -> str | None:
    """检测隧道工具，优先 cloudflared"""
    for binary in ["cloudflared", "ngrok"]:
        try:
            result = subprocess.run(
                [binary, "--version"], capture_output=True, shell=True, timeout=3
            )
            if result.returncode == 0:
                return binary
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def install_cloudflared() -> bool:
    """自动安装 cloudflared（优先使用系统包管理器；不再提供直接下载二进制的 fallback）。"""
    import platform

    system = platform.system()

    print("    正在安装 cloudflared...")

    if system == "Windows":
        # 尝试 winget
        result = subprocess.run(
            [
                "winget",
                "install",
                "--id",
                "Cloudflare.cloudflared",
                "-e",
                "--accept-source-agreements",
                "--accept-package-agreements",
            ],
            capture_output=True,
            shell=True,
        )
        if result.returncode == 0:
            print("    cloudflared 安装成功 ✓")
            return True

        print("    winget 安装失败，请手动安装 cloudflared 后重试。")
        print(
            "    参考: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
        )
        return False

    elif system == "Darwin":  # macOS
        result = subprocess.run(["brew", "install", "cloudflared"], capture_output=True)
        if result.returncode == 0:
            print("    cloudflared 安装成功 ✓")
            return True
        print("    brew 安装失败，请手动安装: brew install cloudflared")
        return False

    else:  # Linux
        print("    Linux 请通过发行版包管理器或官方安装文档安装 cloudflared 后重试。")
        print(
            "    参考: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
        )
        return False

    return False


def ensure_tunnel_tool() -> str | None:
    """确保隧道工具可用，必要时自动安装"""
    binary = check_tunnel_binary()
    if binary:
        return binary

    print("\n未检测到隧道工具，尝试自动安装 cloudflared...")
    if install_cloudflared():
        # 重新检测
        return check_tunnel_binary()

    print("\n自动安装失败，请手动安装:")
    print("  Windows: winget install cloudflare.cloudflared")
    print("  macOS: brew install cloudflared")
    print(
        "  Linux: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
    )
    return None


def start_tunnel(port: int, service_name: str) -> str | None:
    """启动隧道并返回公网 URL"""
    binary = ensure_tunnel_tool()
    if not binary:
        return None

    try:
        if binary == "cloudflared":
            proc = subprocess.Popen(
                ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
            )
            processes.append(proc)

            # 等待 URL 输出
            for _ in range(30):
                if proc.stderr:
                    line = proc.stderr.readline()
                    match = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
                    if match:
                        url = match.group(0)
                        print(f"  {service_name} 公网: {url}")
                        return url
                time.sleep(0.5)

        elif binary == "ngrok":
            proc = subprocess.Popen(
                ["ngrok", "http", str(port), "--log", "stdout"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
            )
            processes.append(proc)

            # 等待 URL 输出
            for _ in range(30):
                if proc.stdout:
                    line = proc.stdout.readline()
                    match = re.search(
                        r"https://[a-z0-9-]+\.(ngrok-free\.app|ngrok\.io)", line
                    )
                    if match:
                        url = match.group(0)
                        print(f"  {service_name} 公网: {url}")
                        return url
                time.sleep(0.5)

    except Exception as e:
        print(f"隧道启动失败: {e}")

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


def ensure_env_files():
    """确保 .env 文件存在"""
    # 后端 .env
    backend_env = ROOT_DIR / ".env"
    backend_example = ROOT_DIR / ".env.example"
    if not backend_env.exists() and backend_example.exists():
        import shutil

        shutil.copy2(backend_example, backend_env)
        print("    已创建后端 .env 文件 (从 .env.example 复制)")

    # 前端 .env.local（避免污染/误提交 .env）
    frontend_env = FRONTEND_DIR / ".env.local"
    if not frontend_env.exists():
        frontend_env.write_text(f"VITE_API_URL=http://localhost:{BACKEND_PORT}/api\n")
        print("    已创建前端 .env.local 文件")


def update_frontend_api_url(backend_url: str):
    """更新前端 API URL 配置"""
    frontend_env = FRONTEND_DIR / ".env.local"
    api_url = f"{backend_url}/api"

    # 读取现有内容
    content = ""
    if frontend_env.exists():
        content = frontend_env.read_text()

    # 更新或添加 VITE_API_URL
    lines = content.strip().split("\n") if content.strip() else []
    updated = False
    for i, line in enumerate(lines):
        if line.startswith("VITE_API_URL="):
            lines[i] = f"VITE_API_URL={api_url}"
            updated = True
            break

    if not updated:
        lines.append(f"VITE_API_URL={api_url}")

    frontend_env.write_text("\n".join(lines) + "\n")
    print(f"    前端 API URL 已更新: {api_url}")


def main():
    parser = argparse.ArgumentParser(description="Interview System 启动器")
    parser.add_argument(
        "--public", action="store_true", help="启用公网访问 (cloudflared/ngrok)"
    )
    args = parser.parse_args()

    print("=" * 50)
    print("  Interview System 启动器")
    print("=" * 50)
    print()

    # 防止上次公网 URL 残留（即使未启用 --public 也会写入 false 状态）
    write_public_url_state(url=None, is_public=False)

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

    # 确保环境配置
    print()
    print("检查环境配置...")
    ensure_env_files()
    print("环境配置完成 ✓")
    print()

    # 启动服务
    backend = start_backend(enable_public=args.public)
    if not backend:
        sys.exit(1)
    processes.append(backend)

    # 公网模式: 先启动后端隧道，获取 URL 后配置前端
    backend_url = f"http://localhost:{BACKEND_PORT}"
    frontend_url = f"http://localhost:{FRONTEND_PORT}"

    if args.public:
        print()
        print("启动公网隧道...")
        public_backend = start_tunnel(BACKEND_PORT, "后端")
        if public_backend:
            backend_url = public_backend
            # 更新前端 API URL 配置
            update_frontend_api_url(public_backend)
            print("    注意: 前端将使用公网后端 API")

    # 启动前端
    frontend = start_frontend(enable_public=args.public)
    if not frontend:
        cleanup()
        sys.exit(1)
    processes.append(frontend)

    # 公网模式: 启动前端隧道
    if args.public:
        public_frontend = start_tunnel(FRONTEND_PORT, "前端")
        if public_frontend:
            frontend_url = public_frontend

    # 公网模式: 写入前端公网 URL 状态（供前端弹窗/后端端点读取）
    if args.public and frontend_url.startswith("https://"):
        write_public_url_state(url=frontend_url, is_public=True)

    # 完成
    print()
    print("=" * 50)
    print("  ✅ 启动完成!")
    print()
    print(f"  前端: {frontend_url}")
    print(f"  后端: {backend_url}")
    print(f"  API 文档: {backend_url}/docs")
    print()
    print("  按 Ctrl+C 停止所有服务")
    print("=" * 50)

    # 公网模式: 在最终输出块后输出 ASCII 二维码（终端可扫码）
    if args.public and frontend_url.startswith("https://"):
        print_ascii_qrcode(frontend_url)

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
