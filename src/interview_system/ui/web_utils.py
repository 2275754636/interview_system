#!/usr/bin/env python3
# coding: utf-8
"""
Web Utilities Module
Provides utility functions for web interface
"""

import socket
from typing import Dict


def get_local_ip() -> str:
    """Get local network IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def format_dict(d: Dict) -> str:
    """Format dictionary as text"""
    if not d:
        return "  无"
    return "\n".join(f"  - {k}: {v}" for k, v in d.items())
