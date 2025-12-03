#!/usr/bin/env python3
# coding: utf-8
"""
大学生五育并举访谈智能体（重构版）

主入口文件 - 整合所有模块，提供统一的启动入口

特点：
- 模块化设计，代码结构清晰
- 配置与代码分离
- 统一日志输出
- API调用失败时自动重试
- 支持多人同时访谈
- 支持命令行和Web两种模式
"""

import sys
import os

# 确保模块路径正确
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logger
from config import ensure_dirs
from api_client import initialize_api, is_api_available, get_api_client
from session_manager import get_session_manager
from interview_engine import create_interview, InterviewEngine
from web_server import start_web_server, check_gradio_available


def setup_api_interactive():
    """
    交互式配置API密钥
    """
    print("\n===== 百度千帆智能追问配置 =====")
    
    client = get_api_client()
    
    if client.config.access_key and client.config.secret_key:
        print("1. 已检测到本地保存的密钥，直接回车使用现有密钥")
        print("2. 若需更新密钥，直接输入新的 Access Key 和 Secret Key")
    else:
        print("1. 访问百度千帆官网：https://qianfan.baidubce.com/")
        print("2. 注册/登录后，进入「控制台」→「API密钥管理」")
        print("3. 复制「Access Key」和「Secret Key」粘贴到下方")
        print("   （密钥将自动保存到本地，下次启动无需重复输入）")
    
    print("-" * 50)
    
    # 输入Access Key
    prompt_ak = "请输入百度千帆 Access Key（直接回车使用已保存）：" if client.config.access_key else "请输入百度千帆 Access Key："
    new_ak = input(prompt_ak).strip()
    
    # 输入Secret Key
    prompt_sk = "请输入百度千帆 Secret Key（直接回车使用已保存）：" if client.config.secret_key else "请输入百度千帆 Secret Key："
    new_sk = input(prompt_sk).strip()
    
    # 初始化API
    ak = new_ak or client.config.access_key
    sk = new_sk or client.config.secret_key
    
    if ak and sk:
        success = initialize_api(ak, sk)
        if success and (new_ak or new_sk):
            # 保存新密钥
            client.save_keys(ak, sk)
        
        if success:
            print("✅ 百度千帆智能追问功能已启用")
        else:
            print("ℹ️ 将使用预设追问")
    else:
        print("ℹ️ 未输入完整密钥，将使用预设追问")


def run_cli_mode():
    """
    运行命令行交互模式
    """
    print("\n核心规则：每次随机6题，覆盖学校/家庭/社区三场景 + 德/智/体/美/劳五育")
    print("支持指令：输入 '结束' 终止访谈，输入 '导出' 保存日志，输入 '跳过' 跳过当前题")
    
    # 获取用户名
    user_name = input("\n请简单自我介绍（或直接回车跳过）：").strip() or None
    
    # 创建访谈
    session, engine = create_interview(user_name)
    
    print("\n欢迎进入大学生五育并举主题访谈！")
    print("本次访谈将随机抽取6题，涵盖学校、家庭、社区三场景及德、智、体、美、劳五育。")
    print(f"\n已为你生成6个访谈问题，现在开始吧～\n")
    
    # 显示第一个问题
    print(engine.get_current_question())
    
    # 主循环
    while not session.is_finished:
        answer = input("\n你的回答：").strip()
        cmd = answer.lower()
        
        # 处理指令
        if cmd in ("结束", "exit", "quit", "结束访谈"):
            print("已手动结束访谈。")
            session.is_finished = True
            break
        
        if cmd == "导出":
            path = get_session_manager().export_session(session.session_id)
            if path:
                print(f"JSON 日志已导出至：{path}")
            print("你可以继续回答，或输入 '结束' 退出。")
            continue
        
        if cmd in ("跳过", "不想说", "不愿意", "/跳过"):
            idx = session.current_question_idx
            print(f"理解，跳过第{idx + 1}题，进入下一题～")
            result = engine.skip_question()
            
            if not result.is_finished:
                print(f"\n{result.next_question}")
            continue
        
        if not answer:
            print("请给出一个回答，或输入 '跳过' 跳过当前题、'结束' 结束访谈。")
            continue
        
        # 处理回答
        result = engine.process_answer(answer)
        
        if result.need_followup:
            prefix = "💡 百度千帆智能追问：" if result.is_ai_generated else "追问："
            print(f"\n{prefix}")
            print(result.followup_question)
            
            # 等待追问回答
            followup_answer = input("\n你的补充回答：").strip()
            if followup_answer and followup_answer.lower() not in ("跳过", "/跳过"):
                result = engine.process_answer(followup_answer)
        
        if result.is_finished:
            print("\n6个问题已全部问完，访谈结束！")
        elif result.next_question:
            print(f"\n{result.next_question}")
    
    # 访谈结束统计
    print("\n访谈结束！本次访谈统计：")
    summary = engine.get_summary()
    stats = summary.get("statistics", {})
    
    print(f"- 总题数：{stats.get('total_logs', 0)}（含核心问题+追问）")
    print(f"- 场景分布：{stats.get('scene_distribution', {})}")
    print(f"- 五育分布：{stats.get('edu_distribution', {})}")
    print(f"- 追问类型分布：{stats.get('followup_distribution', {})}")
    print(f"- 百度千帆功能启用状态：{'✅ 已启用' if is_api_available() else '❌ 未启用'}")
    
    # 导出选项
    while True:
        choice = input("\n是否导出完整访谈日志？输入 'JSON' 导出，输入 '结束' 退出：").strip().lower()
        if choice == "json":
            path = get_session_manager().export_session(session.session_id)
            if path:
                print(f"日志已导出至：{path}")
        elif choice in ("结束", "exit", "quit"):
            print("感谢参与访谈，祝你学习进步！再见～")
            break
        else:
            print("无效输入，请输入 'JSON' 或 '结束'。")


def run_web_mode():
    """
    运行Web模式
    """
    if not check_gradio_available():
        print("❌ 无法启动 Web 版：缺少 gradio 库")
        print("请先运行 pip install gradio qrcode[pil]")
        return
    
    start_web_server()


def main():
    """
    主入口函数
    """
    print("=" * 60)
    print("    大学生五育并举访谈智能体（百度千帆增强版）")
    print("=" * 60)
    
    # 确保目录存在
    ensure_dirs()
    
    # 配置API
    setup_api_interactive()
    
    # 选择模式
    print("\n" + "-" * 50)
    mode = input("请选择启动模式 (1: 命令行交互, 2: Web扫码版) [默认2]: ").strip()
    
    if mode == "1":
        run_cli_mode()
    else:
        run_web_mode()


if __name__ == "__main__":
    main()
