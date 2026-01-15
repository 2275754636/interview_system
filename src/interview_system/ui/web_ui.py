#!/usr/bin/env python3
# coding: utf-8
"""
Web Interface Module
Gradio-based web interface for interviews
"""

from typing import Tuple, List

import interview_system.common.logger as logger
from interview_system.common.config import WEB_CONFIG
from interview_system.ui.web_handler import InterviewHandler
from interview_system.ui.web_utils import get_local_ip
from interview_system.ui.web_styles import WECHAT_CSS

# Check Gradio availability
GRADIO_AVAILABLE = False
try:
    import gradio as gr
    import qrcode
    from PIL import Image
    GRADIO_AVAILABLE = True
except ImportError as e:
    logger.warning(f"无法使用 Web 功能。原因：{e}")
    logger.warning("请运行 `pip install gradio qrcode[pil]` 安装缺失的库")


def create_web_interface():
    """创建Web界面"""
    if not GRADIO_AVAILABLE:
        logger.error("Gradio未安装，无法创建Web界面")
        return None

    with gr.Blocks(
        title=WEB_CONFIG.title,
        theme=gr.themes.Soft(),
        css=WECHAT_CSS
    ) as demo:
        # 状态：每个用户独立的处理器
        handler_state = gr.State(None)

        # 顶部栏（微信风格近似）
        with gr.Row():
            gr.HTML(
                """
                <div class="wechat-topbar">
                    <p class="wechat-title">大学生五育并举访谈</p>
                    <p class="wechat-subtitle">像微信一样聊天式访谈，放松分享真实经历与感受</p>
                </div>
                """,
                elem_id="wechat_header"
            )

        with gr.Row():
            with gr.Column(scale=3):
                # 聊天区域
                chatbot = gr.Chatbot(
                    label="访谈对话",
                    height=500,
                    show_label=False,
                    bubble_full_width=False,
                    avatar_images=(None, "https://em-content.zobj.net/source/twitter/376/robot_1f916.png"),
                    elem_id="wechat_chat"
                )

                # 进度显示
                progress_html = gr.HTML("""
                <div class="stats-box">
                    <p><strong>📊 访谈进度</strong></p>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: 0%;"></div>
                    </div>
                    <p style="text-align: center; margin: 5px 0 0 0;">准备开始访谈...</p>
                </div>
                """)

                with gr.Row(elem_id="wechat_input_bar"):
                    msg = gr.Textbox(
                        label="你的回答",
                        placeholder="请输入你的回答…",
                        scale=6,
                        show_label=False,
                        lines=2,
                        max_lines=5
                    )
                    submit_btn = gr.Button("发送", variant="primary", scale=1, elem_id="wechat_send_btn")

                with gr.Row(elem_id="wechat_action_bar"):
                    undo_btn = gr.Button("↩️ 撤回", variant="secondary", scale=1)
                    skip_btn = gr.Button("⏭️ 跳过此题", variant="secondary", scale=1)
                    refresh_btn = gr.Button("🔄 重新开始", variant="secondary", scale=1)

            with gr.Column(scale=1, elem_id="wechat_sidebar"):
                # 侧边栏 - 使用说明和统计
                gr.Markdown("""
                ### 📖 使用说明

                欢迎参加访谈！本次访谈将围绕五育发展展开。

                **操作提示**：
                - 💬 在下方输入框输入回答
                - ⏭️ 不方便回答可点击跳过
                - 🔄 可随时重新开始

                **访谈规则**：
                - 共 6 个问题
                - 涵盖学校、家庭、社区场景
                - 包含德智体美劳五育内容
                - AI会根据你的回答智能追问

                ---

                ### 💡 小贴士

                回答时可以包含：
                - ✨ 具体的经历和例子
                - 💭 你的真实感受
                - 📈 你的收获和改变
                - 🔍 过程中的细节

                回答越详细，AI追问会越精准！
                """)

                # 实时统计（如果可用）
                stats_display = gr.Markdown("""
                ### 📊 实时统计

                *访谈开始后显示统计*
                """)
        
        # 事件处理函数
        def init_handler():
            """初始化处理器 - 延迟加载模式，快速返回欢迎页面"""
            handler = InterviewHandler()
            history, _ = handler.lazy_initialize()
            return handler, history

        def respond(user_input, history, handler):
            """处理用户输入"""
            if handler is None:
                handler = InterviewHandler()

            new_history, clear_input, input_update = handler.process_message(user_input, history)
            return new_history, clear_input, input_update, handler

        def undo_action(history, handler):
            """撤回最近一次操作"""
            if handler is None:
                return history, "", gr.update(), handler
            new_history, restored_input, input_update = handler.undo_last(history)
            return new_history, restored_input, input_update, handler

        def skip_question(history, handler):
            """跳过当前问题"""
            if handler is None or not handler._initialized:
                return history, handler, gr.update()

            new_history, clear_input, input_update = handler.skip_round(history)
            return new_history, handler, input_update

        def new_interview():
            """开始新访谈"""
            handler = InterviewHandler()
            history, _ = handler.lazy_initialize()
            return handler, history, gr.update(interactive=True)
        
        # 页面加载时初始化
        demo.load(
            init_handler,
            outputs=[handler_state, chatbot]
        )
        
        # 绑定事件
        msg.submit(
            respond,
            [msg, chatbot, handler_state],
            [chatbot, msg, msg, handler_state]
        )
        
        submit_btn.click(
            respond,
            [msg, chatbot, handler_state],
            [chatbot, msg, msg, handler_state]
        )
        
        skip_btn.click(
            skip_question,
            [chatbot, handler_state],
            [chatbot, handler_state, msg]
        )
        
        refresh_btn.click(
            new_interview,
            outputs=[handler_state, chatbot, msg]
        )

        undo_btn.click(
            undo_action,
            inputs=[chatbot, handler_state],
            outputs=[chatbot, msg, msg, handler_state]
        )
    
    return demo


def start_web_server(share: bool = None):
    """
    启动Web服务器
    
    Args:
        share: 是否生成公网链接（默认使用配置）
    """
    if not GRADIO_AVAILABLE:
        logger.error("无法启动Web服务：缺少 gradio 库")
        print("❌ 无法启动 Web 版：缺少 gradio 库。请先运行 pip install gradio qrcode[pil]")
        return
    
    demo = create_web_interface()
    if not demo:
        return
    
    local_ip = get_local_ip()
    port = WEB_CONFIG.port
    url = f"http://{local_ip}:{port}"
    should_share = share if share is not None else WEB_CONFIG.share
    
    print("\n" + "=" * 50)
    print(f"🚀 Web 服务器即将启动！")
    print(f"📍 局域网地址：{url}")
    if should_share:
        print("🌐 正在生成公网链接，请稍候...")
    print("=" * 50 + "\n")
    
    try:
        app, local_url, share_url = demo.launch(
            server_name=WEB_CONFIG.host,
            server_port=port,
            share=should_share,
            prevent_thread_lock=True
        )
        
        # 确定最终URL
        final_url = share_url if share_url else url
        
        print("\n" + "=" * 50)
        if share_url:
            print(f"✅ 公网链接已生成：{share_url}")
            print("📱 任何人都可以扫描下方二维码访问（无需同一WiFi）")
        else:
            print(f"📍 局域网地址：{url}")
            print("📱 请确保手机与电脑在同一WiFi下")
        print("=" * 50 + "\n")
        
        # 生成二维码
        try:
            qr = qrcode.QRCode()
            qr.add_data(final_url)
            qr.print_ascii()
            
            # 保存二维码图片
            img = qrcode.make(final_url)
            img.save("access_code.png")
            print(f"\n✅ 已生成二维码图片：access_code.png")
        except Exception as e:
            logger.warning(f"生成二维码失败: {e}")
        
        logger.info(f"Web服务器已启动 - {final_url}")
        
        # 保持运行
        import time
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n服务已停止。")
            logger.info("Web服务器已停止")
    
    except Exception as e:
        logger.error(f"启动Web服务器失败: {e}")
        print(f"❌ 启动失败: {e}")


def check_gradio_available() -> bool:
    """检查Gradio是否可用"""
    return GRADIO_AVAILABLE
