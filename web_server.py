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
    
    def initialize(self, user_name: str = None) -> Tuple[List, str]:
        """
        初始化访谈会话
        
        Args:
            user_name: 用户名
            
        Returns:
            (聊天历史, 状态消息)
        """
        self.session, self.engine = create_interview(user_name or "Web访谈者")
        
        # 获取第一个问题
        first_question = self.engine.get_current_question()
        
        # 构建欢迎消息
        welcome = (
            "🎓 欢迎参加大学生五育并举访谈！\n\n"
            "本次访谈将随机抽取6题，涵盖学校、家庭、社区三场景及德、智、体、美、劳五育。\n"
            "请认真回答每个问题，系统会根据你的回答进行智能追问。\n\n"
            "提示：输入 /跳过 可跳过当前问题"
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
        if not self.session or not self.engine:
            # 会话未初始化
            return history, "", gr.update()
        
        if self.session.is_finished:
            # 访谈已结束
            history.append([user_input, "访谈已结束，请点击下方按钮导出日志或刷新页面开始新访谈。"])
            return history, "", gr.update(interactive=False)
        
        if not user_input.strip():
            return history, "", gr.update()
        
        # 处理跳过命令
        if user_input.strip() in ["/跳过", "跳过", "/skip"]:
            result = self.engine.skip_question()
            history.append([user_input, "好的，已跳过当前问题。"])
            
            if result.is_finished:
                history.append([None, "🎉 访谈结束！感谢你的参与。\n\n可以点击下方按钮导出访谈日志。"])
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
            # 访谈结束
            history[-1][1] = "收到。"
            history.append([None, "🎉 访谈结束！感谢你的参与。\n\n可以点击下方按钮导出访谈日志。"])
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
        gr.Markdown("基于百度千帆大模型的智能访谈系统，支持多人同时访谈")
        
        with gr.Row():
            with gr.Column(scale=3):
                # 聊天区域
                chatbot = gr.Chatbot(
                    label="访谈对话",
                    height=500,
                    show_label=False
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        label="你的回答",
                        placeholder="在这里输入回答，按回车发送... (输入 /跳过 可跳过当前问题)",
                        scale=4,
                        show_label=False
                    )
                    submit_btn = gr.Button("发送", variant="primary", scale=1)
                
                with gr.Row():
                    export_btn = gr.Button("📥 导出访谈日志", variant="secondary")
                    refresh_btn = gr.Button("🔄 开始新访谈", variant="secondary")
                
                export_file = gr.File(label="下载日志文件", visible=False)
            
            with gr.Column(scale=1):
                # 统计信息面板
                gr.Markdown("### 📊 访谈统计")
                stats_display = gr.Markdown("访谈开始后显示统计信息...")
                refresh_stats_btn = gr.Button("刷新统计", size="sm")
        
        # 事件处理函数
        def init_handler():
            """初始化处理器"""
            handler = WebInterviewHandler()
            history, _ = handler.initialize()
            stats = handler.get_statistics()
            return handler, history, stats
        
        def respond(user_input, history, handler):
            """处理用户输入"""
            if handler is None:
                handler = WebInterviewHandler()
                history, _ = handler.initialize()
            
            new_history, clear_input, input_update = handler.process_message(user_input, history)
            stats = handler.get_statistics()
            return new_history, clear_input, input_update, handler, stats
        
        def export_data(handler):
            """导出日志"""
            if handler is None:
                return None, gr.update(visible=False)
            
            path = handler.export_log()
            if path:
                return path, gr.update(visible=True)
            return None, gr.update(visible=False)
        
        def refresh_stats(handler):
            """刷新统计"""
            if handler is None:
                return "暂无统计信息"
            return handler.get_statistics()
        
        def new_interview():
            """开始新访谈"""
            handler = WebInterviewHandler()
            history, _ = handler.initialize()
            stats = handler.get_statistics()
            return handler, history, stats, gr.update(interactive=True), gr.update(visible=False)
        
        # 页面加载时初始化
        demo.load(
            init_handler,
            outputs=[handler_state, chatbot, stats_display]
        )
        
        # 绑定事件
        msg.submit(
            respond,
            [msg, chatbot, handler_state],
            [chatbot, msg, msg, handler_state, stats_display]
        )
        
        submit_btn.click(
            respond,
            [msg, chatbot, handler_state],
            [chatbot, msg, msg, handler_state, stats_display]
        )
        
        export_btn.click(
            export_data,
            inputs=[handler_state],
            outputs=[export_file, export_file]
        )
        
        refresh_stats_btn.click(
            refresh_stats,
            inputs=[handler_state],
            outputs=[stats_display]
        )
        
        refresh_btn.click(
            new_interview,
            outputs=[handler_state, chatbot, stats_display, msg, export_file]
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
