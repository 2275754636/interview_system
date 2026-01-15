
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

import interview_system.common.logger as logger
from interview_system.common.config import ensure_dirs
from interview_system.integrations.api_helpers import (
    initialize_api,
    is_api_available,
    get_api_client,
    get_available_providers,
)
from interview_system.services.session_manager import get_session_manager
from interview_system.core.interview_engine import create_interview
from interview_system.ui.web_ui import start_web_server, check_gradio_available

# 尝试导入管理后台（可选）
try:
    from interview_system.ui.admin_ui import start_admin_server
    ADMIN_AVAILABLE = True
except ImportError:
    ADMIN_AVAILABLE = False


def setup_api_interactive():
    """
    交互式配置API - 支持多种大模型API
    """
    print("\n===== 智能追问 API 配置 =====")
    
    client = get_api_client()
    providers = get_available_providers()
    
    # 检查是否有已保存的配置
    if client.current_provider and client.api_key:
        print(f"已检测到本地保存的配置：{client.current_provider.name}")
        print(f"模型：{client.model}")
        use_saved = input("\n是否使用已保存的配置？(Y/n): ").strip().lower()
        
        if use_saved != 'n':
            # 尝试用已保存的配置初始化
            success = client.initialize(
                client.current_provider.provider_id,
                client.api_key,
                client.secret_key,
                client.model
            )
            if success:
                print(f"✅ {client.current_provider.name} 智能追问功能已启用")
                return
            else:
                print("⚠️ 已保存的配置无效，请重新配置")
    
    # 显示可用的 API 提供商
    print("\n支持的 API 提供商：")
    print("-" * 50)
    provider_list = list(providers.keys())
    for i, (pid, provider) in enumerate(providers.items(), 1):
        print(f"  {i}. {provider.name}")
        print(f"     官网：{provider.website}")
    print(f"  0. 跳过配置（使用预设追问）")
    print("-" * 50)
    
    # 选择提供商
    while True:
        choice = input(f"\n请选择 API 提供商 [0-{len(provider_list)}]: ").strip()
        
        if choice == '0' or choice == '':
            print("ℹ️ 跳过API配置，将使用预设追问")
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(provider_list):
                selected_id = provider_list[idx]
                break
            else:
                print("无效选择，请重新输入")
        except ValueError:
            # 也支持直接输入提供商ID
            if choice in providers:
                selected_id = choice
                break
            print("无效输入，请输入数字")
    
    provider = providers[selected_id]
    print(f"\n已选择：{provider.name}")
    print(f"获取 API Key：{provider.website}")
    
    # 特别提示：不要使用推理模型
    if selected_id == "deepseek":
        print("\n⚠️ 注意：请使用 deepseek-chat 模型")
        print("   不要使用 deepseek-reasoner (R1)，推理模型不适合对话场景")
    
    print("-" * 50)
    
    # 输入 API Key
    api_key = input(f"请输入 {provider.api_key_name}: ").strip()
    if not api_key:
        print("ℹ️ 未输入 API Key，将使用预设追问")
        return
    
    # 百度千帆需要额外的 Secret Key
    secret_key = None
    if provider.need_secret_key:
        secret_key = input("请输入 Secret Key: ").strip()
        if not secret_key:
            print("ℹ️ 未输入 Secret Key，将使用预设追问")
            return
    
    # 选择模型（可选）
    model = None
    if provider.models and len(provider.models) > 1:
        print(f"\n可用模型：")
        for i, m in enumerate(provider.models, 1):
            default_mark = " (默认)" if m == provider.default_model else ""
            print(f"  {i}. {m}{default_mark}")
        
        model_choice = input(f"选择模型 [直接回车使用默认]: ").strip()
        if model_choice:
            try:
                model_idx = int(model_choice) - 1
                if 0 <= model_idx < len(provider.models):
                    model = provider.models[model_idx]
            except ValueError:
                pass
    
    # 初始化API
    print("\n正在验证 API 配置...")
    success = initialize_api(selected_id, api_key, secret_key, model)
    
    if success:
        # 保存配置
        client.save_config()
        print(f"✅ {provider.name} 智能追问功能已启用")
        print(f"   模型：{client.model}")
    else:
        print("❌ API 配置验证失败，请检查密钥是否正确")
        print("ℹ️ 将使用预设追问")


def run_cli_mode():
    """
    运行命令行交互模式
    """
    print("\n" + "─" * 50)
    print("📋 操作提示")
    print("─" * 50)
    print("  · 输入 '跳过' - 跳过当前问题")
    print("  · 输入 '导出' - 保存访谈记录")
    print("  · 输入 '结束' - 结束本次访谈")
    print("─" * 50)
    
    # 获取用户名
    user_name = input("\n请输入你的称呼（直接回车跳过）：").strip() or None
    
    # 创建访谈
    session, engine = create_interview(user_name)
    
    print("\n" + "═" * 50)
    print("👋 你好，欢迎参加本次访谈！")
    print("═" * 50)
    print("\n接下来我会向你提出 6 个问题，")
    print("话题涉及你在学校、家庭和社区中的经历与感受。")
    print("\n💬 请放松心情，用自己的话分享真实想法。")
    print("\n准备好了吗？让我们开始吧！\n")
    
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
            print(f"\n⏭️ 好的，已跳过第 {idx + 1} 题")
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
            prefix = "💡 " if result.is_ai_generated else "📝 "
            print(f"\n{prefix}{result.followup_question}")
            
            # 等待追问回答
            followup_answer = input("\n你的补充回答：").strip()
            if followup_answer and followup_answer.lower() not in ("跳过", "/跳过"):
                result = engine.process_answer(followup_answer)
        
        if result.is_finished:
            pass  # 结束统计会在循环外处理
        elif result.next_question:
            print(f"\n{result.next_question}")
    
    # 访谈结束统计
    print("\n" + "═" * 50)
    print("🎉 访谈结束！感谢你的参与！")
    print("═" * 50)
    
    summary = engine.get_summary()
    stats = summary.get("statistics", {})
    
    print("\n📊 本次访谈统计：")
    print("─" * 30)
    print(f"  📝 回答记录：{stats.get('total_logs', 0)} 条")
    
    scene_dist = stats.get('scene_distribution', {})
    if scene_dist:
        scenes = '、'.join([f"{k}({v})" for k, v in scene_dist.items()])
        print(f"  🏠 场景覆盖：{scenes}")
    
    edu_dist = stats.get('edu_distribution', {})
    if edu_dist:
        edus = '、'.join([f"{k}({v})" for k, v in edu_dist.items()])
        print(f"  📚 五育覆盖：{edus}")
    
    print("─" * 30)
    
    # 自动导出日志
    path = get_session_manager().export_session(session.session_id)
    if path:
        print(f"\n💾 访谈记录已自动保存至：")
        print(f"   {path}")
    
    print("\n" + "═" * 50)
    print("✨ 感谢参与访谈，祝你学习进步！")
    print("═" * 50 + "\n")


def run_web_mode():
    """
    运行Web模式
    """
    if not check_gradio_available():
        print("❌ 无法启动 Web 版：缺少 gradio 库")
        print("请先运行 pip install gradio qrcode[pil]")
        return
    
    start_web_server()


def run_admin_mode():
    """
    运行管理后台模式
    """
    if not ADMIN_AVAILABLE:
        print("❌ 无法启动管理后台：缺少必要模块")
        print("请确保已安装: pip install gradio plotly")
        return

    start_admin_server()


def main():
    """
    主入口函数
    """
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "🎓 大学生五育并举访谈智能体".center(48) + "║")
    print("║" + " " * 58 + "║")
    print("║" + "探索德·智·体·美·劳，记录你的成长故事".center(42) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")

    # 确保目录存在
    ensure_dirs()

    # 配置API
    setup_api_interactive()

    # 选择模式
    print("\n" + "─" * 50)
    print("请选择启动模式：")
    print("  1. 💻 命令行模式   - 在终端中进行访谈")
    print("  2. 🌐 Web访谈模式  - 生成网页链接，支持手机访问")
    print("  3. 🔧 管理后台模式 - 查看数据、统计分析")
    print("─" * 50)
    mode = input("请输入选项 [默认2]: ").strip()

    if mode == "1":
        run_cli_mode()
    elif mode == "3":
        run_admin_mode()
    else:
        run_web_mode()


if __name__ == "__main__":
    main()
