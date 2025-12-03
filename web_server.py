#!/usr/bin/env python3
# coding: utf-8
"""
Web服务模块 - 大学生五育并举访谈智能体
基于Gradio实现Web界面，支持多人同时访谈
"""

import socket
from typing import Tuple, List, Optional

import logger
from config import WEB_CONFIG
from session_manager import get_session_manager, InterviewSession
from interview_engine import InterviewEngine, create_interview

# 检查Gradio是否可用
GRADIO_AVAILABLE = False
try:
    import gradio as gr
    import qrcode
    from PIL import Image
    GRADIO_AVAILABLE = True
except ImportError as e:
    logger.warning(f"无法使用 Web 功能。原因：{e}")
    logger.warning("请运行 `pip install gradio qrcode[pil]` 安装缺失的库")


class WebInterviewHandler:
    """Web访谈处理器 - 处理单个用户的访谈会话"""
    
    def __init__(self):
        self.session: Optional[InterviewSession] = None
        self.engine: Optional[InterviewEngine] = None
        self._initialized = False
    
    def initialize(self, user_name: str = None) -> Tuple[List, str]:
        """
        初始化访谈会话
        
        Args:
            user_name: 用户名
            
        Returns:
            (聊天历史, 状态消息)
        """
        self.session, self.engine = create_interview(user_name or "Web访谈者")
        self._initialized = True
        
        # 获取第一个问题
        first_question = self.engine.get_current_question()
        
        # 构建欢迎消息
        welcome = (
            "👋 你好，欢迎参加本次访谈！\n\n"
            "接下来我会向你提出 6 个问题，话题涉及你在学校、家庭和社区中的经历与感受。\n\n"
            "💬 请放松心情，用自己的话分享真实想法，没有标准答案。\n"
            "⏭️ 如果某个问题不方便回答，可以点击「跳过」按钮。\n\n"
            "准备好了吗？让我们开始吧！"
        )
        
        history = [
            [None, welcome],
            [None, first_question]
        ]
        
        logger.log_interview(
            self.session.session_id,
            "Web访谈开始",
            {"user": self.session.user_name}
        )
        
        return history, ""
    
    def lazy_initialize(self) -> Tuple[List, str]:
        """
        延迟初始化 - 仅返回欢迎消息，不创建完整会话
        用于页面首次加载时快速响应
        
        Returns:
            (聊天历史, 状态消息)
        """
        # 直接返回欢迎消息，不做任何耗时操作
        welcome = (
            "👋 你好，欢迎参加本次访谈！\n\n"
            "接下来我会向你提出 6 个问题，话题涉及你在学校、家庭和社区中的经历与感受。\n\n"
            "💬 请放松心情，用自己的话分享真实想法，没有标准答案。\n"
            "⏭️ 如果某个问题不方便回答，可以点击「跳过」按钮。\n\n"
            "**点击下方输入框，输入任意内容开始访谈！**"
        )
        
        return [[None, welcome]], ""
    
    def process_message(
        self, 
        user_input: str, 
        history: List
    ) -> Tuple[List, str, dict]:
        """
        处理用户消息
        
        Args:
            user_input: 用户输入
            history: 聊天历史
            
        Returns:
            (更新后的历史, 清空输入框的值, 输入框更新)
        """
        # 延迟初始化：第一次用户输入时才真正初始化会话
        if not self._initialized or not self.session or not self.engine:
            # 真正初始化
            self.session, self.engine = create_interview("Web访谈者")
            self._initialized = True
            
            # 获取第一个问题
            first_question = self.engine.get_current_question()
            
            # 更新历史：移除"点击开始"提示，添加第一个问题
            if history and len(history) > 0:
                # 保留欢迎消息，替换最后的提示
                welcome = history[0] if history else [None, "欢迎参加访谈！"]
                history = [
                    welcome,
                    [None, first_question]
                ]
            else:
                history = [[None, first_question]]
            
            logger.log_interview(
                self.session.session_id,
                "Web访谈开始",
                {"user": self.session.user_name}
            )
            
            return history, "", gr.update()
        
        if self.session.is_finished:
            # 访谈已结束
            history.append([user_input, "访谈已结束，请点击下方按钮开始新访谈。"])
            return history, "", gr.update(interactive=False)
        
        if not user_input.strip():
            return history, "", gr.update()
        
        # 处理跳过命令
        if user_input.strip() in ["/跳过", "跳过", "/skip"]:
            result = self.engine.skip_question()
            history.append([user_input, "好的，已跳过当前问题。"])
            
            if result.is_finished:
                # 访谈结束，自动导出日志
                self.export_log()
                history.append([None, "🎉 访谈结束！感谢你的参与。"])
                return history, "", gr.update(interactive=False)
            else:
                history.append([None, result.next_question])
                return history, "", gr.update()
        
        # 处理普通回答
        result = self.engine.process_answer(user_input)
        
        # 添加用户回答到历史
        history.append([user_input, None])
        
        if result.need_followup:
            # 需要追问
            prefix = "💡 " if result.is_ai_generated else "📝 "
            history[-1][1] = "收到。"
            history.append([None, f"{prefix}{result.followup_question}"])
        elif result.is_finished:
            # 访谈结束，自动导出日志
            self.export_log()
            history[-1][1] = "收到。"
            history.append([None, "🎉 访谈结束！感谢你的参与。"])
            return history, "", gr.update(interactive=False)
        else:
            # 进入下一题
            history[-1][1] = "✅ 收到，进入下一题。"
            history.append([None, result.next_question])
        
        return history, "", gr.update()
    
    def export_log(self) -> Optional[str]:
        """
        导出访谈日志
        
        Returns:
            导出的文件路径
        """
        if not self.session:
            return None
        
        return get_session_manager().export_session(self.session.session_id)
    
    def get_statistics(self) -> str:
        """
        获取访谈统计信息
        
        Returns:
            统计信息文本
        """
        if not self.session or not self.engine:
            return "暂无统计信息"
        
        summary = self.engine.get_summary()
        stats = summary.get("statistics", {})
        
        text = f"""
📊 **访谈统计**

- 会话ID: {summary.get('session_id', 'N/A')}
- 用户: {summary.get('user_name', 'N/A')}
- 开始时间: {summary.get('start_time', 'N/A')}
- 总记录数: {stats.get('total_logs', 0)}

**场景分布:**
{self._format_dict(stats.get('scene_distribution', {}))}

**五育分布:**
{self._format_dict(stats.get('edu_distribution', {}))}

**追问统计:**
{self._format_dict(stats.get('followup_distribution', {}))}
"""
        return text.strip()
    
    def _format_dict(self, d: dict) -> str:
        """格式化字典为文本"""
        if not d:
            return "  无"
        return "\n".join(f"  - {k}: {v}" for k, v in d.items())


def get_local_ip() -> str:
    """获取本机局域网IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def create_web_interface():
    """创建Web界面"""
    if not GRADIO_AVAILABLE:
        logger.error("Gradio未安装，无法创建Web界面")
        return None
    
    with gr.Blocks(
        title=WEB_CONFIG.title,
        theme=gr.themes.Soft()
    ) as demo:
        # 状态：每个用户独立的处理器
        handler_state = gr.State(None)
        
        gr.Markdown(f"# 🎓 {WEB_CONFIG.title}")
        gr.Markdown("探索德、智、体、美、劳五育发展，记录你的成长故事")
        
        with gr.Row():
            with gr.Column():
                # 聊天区域
                chatbot = gr.Chatbot(
                    label="访谈对话",
                    height=480,
                    show_label=False,
                    bubble_full_width=False
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        label="你的回答",
                        placeholder="请在此输入你的回答，按回车或点击发送...",
                        scale=5,
                        show_label=False,
                        lines=2
                    )
                
                with gr.Row():
                    submit_btn = gr.Button("📤 发送", variant="primary", scale=2)
                    skip_btn = gr.Button("⏭️ 跳过此题", variant="secondary", scale=1)
                    refresh_btn = gr.Button("🔄 重新开始", variant="secondary", scale=1)
        
        # 事件处理函数
        def init_handler():
            """初始化处理器 - 延迟加载模式，快速返回欢迎页面"""
            handler = WebInterviewHandler()
            history, _ = handler.lazy_initialize()  # 使用延迟初始化
            return handler, history
        
        def respond(user_input, history, handler):
            """处理用户输入"""
            if handler is None:
                handler = WebInterviewHandler()
            
            new_history, clear_input, input_update = handler.process_message(user_input, history)
            return new_history, clear_input, input_update, handler
        
        def skip_question(history, handler):
            """跳过当前问题"""
            if handler is None or not handler._initialized:
                return history, handler, gr.update()
            
            # 调用跳过处理
            new_history, clear_input, input_update = handler.process_message("/跳过", history)
            return new_history, handler, input_update
        
        def new_interview():
            """开始新访谈"""
            handler = WebInterviewHandler()
            history, _ = handler.lazy_initialize()  # 使用延迟初始化
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
