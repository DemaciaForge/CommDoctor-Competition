"""
信道模块

实现 AWGN (Additive White Gaussian Noise) 信道模型。

AWGN 是数字通信中最基础的信道模型，表示加性高斯白噪声。

本文件迁移自旧项目 D:/CommDoctor/src/commdoctor/channel.py
迁移日期: 2026-10-13
修改说明: 无修改，直接复用
"""

import numpy as np


def awgn_channel(symbols: np.ndarray, eb_n0_db: float, seed: int | None = None) -> np.ndarray:
    """
    AWGN 信道：向信号添加加性高斯白噪声

    参数:
        symbols: 输入符号序列（BPSK 调制后的信号）
        eb_n0_db: 每比特能量与噪声功率谱密度之比，单位 dB
        seed: 随机种子，用于噪声生成的可复现性

    返回:
        添加噪声后的接收信号

    异常:
        ValueError: 当 eb_n0_db 为非有限数值（NaN 或 Inf）时抛出

    数学原理:
        Eb/N0 是数字通信中最重要的信噪比参数：
        - Eb: 每比特能量
        - N0: 噪声功率谱密度

        对于实值、单位符号能量的 BPSK:
        - 符号能量 Es = 1
        - 每符号携带 1 比特，因此 Eb = Es = 1
        - 噪声方差 σ² = N0/2
        - Eb/N0 = 1/(2σ²)
        - 因此: σ = sqrt(1 / (2 * Eb/N0_linear))

        其中 Eb/N0_linear = 10^(Eb/N0_dB / 10)

    适用条件:
        本公式适用于:
        1. 实值信号（不是复数）
        2. 符号能量归一化为 1
        3. BPSK 调制（每符号 1 比特）

    示例:
        >>> symbols = np.array([-1., 1., -1., 1.])
        >>> received = awgn_channel(symbols, eb_n0_db=6.0, seed=42)
        >>> # 接收信号应该接近原始符号，但有随机噪声
        >>> received.shape
        (4,)
    """
    # 输入验证
    if not np.isfinite(eb_n0_db):
        raise ValueError(f"Eb/N0 必须为有限数值，当前值: {eb_n0_db}")

    # 将 Eb/N0 从 dB 转换为线性值
    # dB 转线性: linear = 10^(dB/10)
    eb_n0_linear = 10 ** (eb_n0_db / 10)

    # 计算噪声标准差
    # 对于实值、单位能量 BPSK: σ = sqrt(1 / (2 * Eb/N0))
    noise_std = np.sqrt(1.0 / (2.0 * eb_n0_linear))

    # 生成高斯白噪声
    rng = np.random.default_rng(seed)
    noise = rng.normal(loc=0.0, scale=noise_std, size=symbols.shape)

    # 添加噪声到符号上
    received = symbols + noise

    return received
