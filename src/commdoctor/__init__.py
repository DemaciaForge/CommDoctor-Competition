"""
CommDoctor - 数字通信仿真与故障诊断平台

版本: 0.1.0
作者: j1379
描述: BPSK 数字通信仿真内核

本文件迁移自旧项目 D:/CommDoctor/src/commdoctor/__init__.py
迁移日期: 2026-10-13
迁移原因: 阶段01核心仿真内核迁移
修改说明: 无修改，直接复用
"""

__version__ = "0.1.0"
__author__ = "j1379"

from .modulation import bpsk_modulate, bpsk_demodulate
from .channel import awgn_channel
from .metrics import calculate_ber, theoretical_ber
from .signal_gen import generate_bits

__all__ = [
    "generate_bits",
    "bpsk_modulate",
    "bpsk_demodulate",
    "awgn_channel",
    "calculate_ber",
    "theoretical_ber",
]
