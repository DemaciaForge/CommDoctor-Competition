"""
信号生成模块

提供随机比特序列生成功能，支持可复现的随机性。

本文件迁移自旧项目 D:/CommDoctor/src/commdoctor/signal_gen.py
迁移日期: 2026-10-13
修改说明: 无修改，直接复用
"""

import numpy as np


def generate_bits(num_bits: int, seed: int | None = None) -> np.ndarray:
    """
    生成随机比特序列

    参数:
        num_bits: 要生成的比特数量，必须为正整数
        seed: 随机种子，用于结果复现。若为 None 则使用随机种子

    返回:
        numpy 数组，包含 0 和 1 的比特序列

    异常:
        ValueError: 当 num_bits <= 0 时抛出

    示例:
        >>> bits = generate_bits(10, seed=42)
        >>> bits.shape
        (10,)
        >>> np.all((bits == 0) | (bits == 1))
        True
        >>> # 相同种子产生相同结果
        >>> bits2 = generate_bits(10, seed=42)
        >>> np.array_equal(bits, bits2)
        True
    """
    if num_bits <= 0:
        raise ValueError(f"比特数量必须为正整数，当前值: {num_bits}")

    # 设置随机种子以确保可复现性
    rng = np.random.default_rng(seed)

    # 生成随机比特 (0 或 1)
    # 使用 integers 方法生成 [0, 2) 范围内的整数
    bits = rng.integers(0, 2, size=num_bits, dtype=np.int8)

    return bits
