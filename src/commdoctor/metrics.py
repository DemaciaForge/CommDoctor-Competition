"""
性能度量模块

提供误码率 (BER) 计算功能，包括仿真 BER 和理论 BER。

本文件迁移自旧项目 D:/CommDoctor/src/commdoctor/metrics.py
迁移日期: 2026-10-13
修改说明: 无修改，直接复用
"""

import numpy as np
from scipy.special import erfc


def calculate_ber(transmitted_bits: np.ndarray, received_bits: np.ndarray) -> tuple[float, int, int]:
    """
    计算误码率 (Bit Error Rate)

    参数:
        transmitted_bits: 发送的比特序列
        received_bits: 接收的比特序列

    返回:
        元组 (ber, num_errors, num_bits):
        - ber: 误码率 (错误比特数 / 总比特数)
        - num_errors: 错误的比特数量
        - num_bits: 总比特数量

    异常:
        ValueError: 当两个序列长度不同时抛出

    数学定义:
        BER = (错误比特数) / (总比特数)

    示例:
        >>> tx = np.array([0, 1, 0, 1, 1, 0, 1, 0])
        >>> rx = np.array([0, 1, 0, 0, 1, 0, 1, 1])
        >>> ber, errors, total = calculate_ber(tx, rx)
        >>> ber
        0.25
        >>> errors
        2
        >>> total
        8
    """
    # 输入验证
    if len(transmitted_bits) != len(received_bits):
        raise ValueError(
            f"发送和接收序列长度必须相同。"
            f"发送: {len(transmitted_bits)}, 接收: {len(received_bits)}"
        )

    # 计算错误的比特数量
    num_errors = np.sum(transmitted_bits != received_bits)

    # 总比特数
    num_bits = len(transmitted_bits)

    # 计算误码率
    ber = num_errors / num_bits if num_bits > 0 else 0.0

    return ber, int(num_errors), int(num_bits)


def theoretical_ber(eb_n0_db: float) -> float:
    """
    计算 BPSK 在 AWGN 信道下的理论误码率

    参数:
        eb_n0_db: 每比特能量与噪声功率谱密度之比，单位 dB

    返回:
        理论误码率

    异常:
        ValueError: 当 eb_n0_db 为非有限数值时抛出

    数学公式:
        对于 BPSK 在 AWGN 信道下：
        BER = 0.5 * erfc(sqrt(Eb/N0))

        其中:
        - erfc 是互补误差函数
        - Eb/N0 是线性值（不是 dB）

    推导依据:
        BPSK 的最优判决是在接收信号为 0 时判决。
        在 AWGN 信道中，噪声服从高斯分布。
        错误概率等于噪声使接收信号越过判决门限的概率。

    示例:
        >>> ber_0db = theoretical_ber(0.0)
        >>> round(ber_0db, 5)
        0.07865
        >>> ber_6db = theoretical_ber(6.0)
        >>> round(ber_6db, 5)
        0.00239
    """
    # 输入验证
    if not np.isfinite(eb_n0_db):
        raise ValueError(f"Eb/N0 必须为有限数值，当前值: {eb_n0_db}")

    # 将 Eb/N0 从 dB 转换为线性值
    eb_n0_linear = 10 ** (eb_n0_db / 10)

    # 计算理论 BER
    # BER = 0.5 * erfc(sqrt(Eb/N0))
    ber = 0.5 * erfc(np.sqrt(eb_n0_linear))

    return float(ber)
