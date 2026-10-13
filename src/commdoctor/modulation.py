"""
调制与解调模块

实现 BPSK (Binary Phase Shift Keying) 调制和解调功能。

BPSK 映射规则:
    比特 0 → 符号 -1
    比特 1 → 符号 +1

这种映射使得符号能量归一化为 1，且在能量上对称。

本文件迁移自旧项目 D:/CommDoctor/src/commdoctor/modulation.py
迁移日期: 2026-10-13
修改说明: 无修改，直接复用
"""

import numpy as np


def bpsk_modulate(bits: np.ndarray) -> np.ndarray:
    """
    BPSK 调制：将二进制比特转换为 BPSK 符号

    映射规则:
        0 → -1
        1 → +1

    参数:
        bits: 输入比特序列，只能包含 0 和 1

    返回:
        BPSK 符号序列，值为 -1 或 +1 的浮点数数组

    异常:
        ValueError: 当输入包含非 0/1 值时抛出

    数学原理:
        BPSK 使用两个相位相反的符号来表示二进制比特。
        符号能量 Es = 1（归一化），每个符号携带 1 比特信息。

    示例:
        >>> bits = np.array([0, 1, 0, 1, 1])
        >>> symbols = bpsk_modulate(bits)
        >>> symbols
        array([-1.,  1., -1.,  1.,  1.])
    """
    # 输入验证
    if not np.all((bits == 0) | (bits == 1)):
        raise ValueError("输入比特序列只能包含 0 和 1")

    # 将 bits 转换为有符号整数类型，避免无符号整数运算问题
    # 然后应用映射: 0 → -1, 1 → +1
    # 公式: symbol = 2 * bit - 1
    bits_signed = bits.astype(np.int32)
    symbols = 2 * bits_signed - 1

    # 转换为浮点数（符合实际通信系统中的信号表示）
    return symbols.astype(np.float64)


def bpsk_demodulate(received_symbols: np.ndarray) -> np.ndarray:
    """
    BPSK 解调：将接收到的符号转换回比特

    判决规则（硬判决）:
        received >= 0 → 比特 1
        received < 0  → 比特 0

    参数:
        received_symbols: 接收到的符号序列（可能被噪声污染）

    返回:
        解调后的比特序列，值为 0 或 1 的整数数组

    数学原理:
        硬判决解调器根据接收信号的符号（正负）来判定原始比特。
        判决门限为 0，这是 BPSK 在 AWGN 信道下的最优判决。

    示例:
        >>> received = np.array([-0.8, 1.2, -1.5, 0.3, 0.9])
        >>> bits = bpsk_demodulate(received)
        >>> bits
        array([0, 1, 0, 1, 1])
    """
    # 硬判决：接收值 >= 0 判为 1，< 0 判为 0
    bits = (received_symbols >= 0).astype(np.int8)

    return bits
