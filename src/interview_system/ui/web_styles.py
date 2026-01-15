"""WeChat-style CSS for Gradio interface"""

WECHAT_CSS = """
:root {
    --wechat-bg: #f5f5f5;
    --wechat-card: #ffffff;
    --wechat-border: #e9e9e9;
    --wechat-text: #111111;
    --wechat-subtext: #6b6b6b;
    --wechat-green: #07c160;
    --wechat-bubble-green: #95ec69;
    --wechat-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.gradio-container {
    background: var(--wechat-bg);
}

#wechat_header .wechat-topbar {
    background: var(--wechat-card);
    border: 1px solid var(--wechat-border);
    border-radius: 12px;
    padding: 12px 16px;
    box-shadow: var(--wechat-shadow);
}
#wechat_header .wechat-title {
    font-size: 18px;
    font-weight: 700;
    color: var(--wechat-text);
    line-height: 1.2;
    margin: 0;
}
#wechat_header .wechat-subtitle {
    font-size: 13px;
    color: var(--wechat-subtext);
    margin: 6px 0 0 0;
    line-height: 1.4;
}

#wechat_chat {
    border: none;
    background: transparent;
}
#wechat_chat .wrap,
#wechat_chat .message-wrap,
#wechat_chat .message-list {
    background: var(--wechat-bg);
}
#wechat_chat .message {
    padding: 6px 0;
}

#wechat_chat .message.user .bubble,
#wechat_chat .message.user .bubble-wrap,
#wechat_chat .message.user .bubble-content {
    background: var(--wechat-bubble-green) !important;
    color: #000 !important;
    border: 1px solid rgba(0, 0, 0, 0.04);
    border-radius: 18px 6px 18px 18px;
    box-shadow: var(--wechat-shadow);
}
#wechat_chat .message.bot .bubble,
#wechat_chat .message.bot .bubble-wrap,
#wechat_chat .message.bot .bubble-content {
    background: var(--wechat-card) !important;
    color: var(--wechat-text) !important;
    border: 1px solid var(--wechat-border);
    border-radius: 6px 18px 18px 18px;
    box-shadow: var(--wechat-shadow);
}

#wechat_chat img.avatar,
#wechat_chat .avatar img {
    width: 32px;
    height: 32px;
    border-radius: 50%;
}

.stats-box {
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid var(--wechat-border);
    border-radius: 12px;
    padding: 10px 12px;
    margin-top: 10px;
    box-shadow: var(--wechat-shadow);
}
.progress-bar {
    background: #ededed;
    border-radius: 999px;
    height: 10px;
    margin: 8px 0;
    overflow: hidden;
}
.progress-fill {
    background: var(--wechat-green);
    height: 100%;
    border-radius: 999px;
    transition: width 0.3s ease;
}

#wechat_input_bar {
    position: sticky;
    bottom: 0;
    z-index: 10;
    background: rgba(245, 245, 245, 0.96);
    backdrop-filter: blur(6px);
    padding: 10px 8px 12px 8px;
    border-top: 1px solid var(--wechat-border);
    border-radius: 12px;
}
#wechat_input_bar textarea,
#wechat_input_bar input {
    border-radius: 18px !important;
    border: 1px solid #d9d9d9 !important;
    background: var(--wechat-card) !important;
    padding: 10px 12px !important;
    font-size: 14px !important;
    line-height: 1.4 !important;
}
#wechat_send_btn {
    border-radius: 18px !important;
    background: var(--wechat-green) !important;
    color: #fff !important;
    border: none !important;
}

#wechat_action_bar button {
    border-radius: 18px !important;
}

@media (max-width: 900px) {
    #wechat_sidebar {
        display: none;
    }
}
@media (max-width: 640px) {
    #wechat_header .wechat-topbar {
        border-radius: 10px;
        padding: 10px 12px;
    }
    #wechat_header .wechat-title {
        font-size: 16px;
    }
    #wechat_header .wechat-subtitle {
        font-size: 12px;
    }
    #wechat_input_bar {
        border-radius: 10px;
        padding: 8px 6px 10px 6px;
    }
}
"""
