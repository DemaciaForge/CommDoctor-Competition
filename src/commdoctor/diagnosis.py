"""
诊断模块

提供信号测量和故障诊断功能。

本模块实现基于实际信号测量的诊断算法，不依赖故障注入器的隐藏真值。
所有测量都基于统计学原理，并报告测量不确定性。

阶段02-B实现：DC偏移诊断
"""

import numpy as np
from typing import Dict, Any


def estimate_dc_offset(
    received_symbols: np.ndarray,
    training_bits: np.ndarray | None = None,
    transmitted_symbols: np.ndarray | None = None,
) -> Dict[str, Any]:
    """
    估计DC偏移

    方法1: 如果提供了已知的训练序列，使用两点法精确估计
    方法2: 如果只有接收信号，假设0/1等概，用均值估计

    数学原理:
        方法1（两点法）:
            E[r|s=-1] = -1 + b
            E[r|s=+1] = +1 + b
            DC偏移 b = (E[r|s=-1] + E[r|s=+1]) / 2

        方法2（均值法）:
            假设P(0) = P(1) = 0.5
            E[r] = E[s] + b = 0 + b = b

    参数:
        received_symbols: 接收符号序列
        training_bits: 已知的训练比特序列（可选）
        transmitted_symbols: 已知的发送符号序列（可选）

    返回:
        字典包含:
        - dc_estimate: DC偏移估计值
        - std_error: 标准误差
        - method: 使用的估计方法
        - num_samples: 样本数量
        - mean_for_minus1: 发送-1时的平均接收值（仅方法1）
        - mean_for_plus1: 发送+1时的平均接收值（仅方法1）

    示例:
        >>> # 方法1: 有训练序列
        >>> rx = np.array([-0.5, 1.5, -0.6, 1.4])
        >>> tx_bits = np.array([0, 1, 0, 1])
        >>> result = estimate_dc_offset(rx, training_bits=tx_bits)
        >>> result['dc_estimate']  # 应该接近0.5
        0.5

        >>> # 方法2: 仅有接收信号
        >>> result = estimate_dc_offset(rx)
        >>> result['dc_estimate']
        0.45
    """
    if len(received_symbols) == 0:
        raise ValueError("received_symbols不能为空")

    result = {
        "num_samples": len(received_symbols),
    }

    # 方法1: 两点法（如果提供了训练序列）
    if transmitted_symbols is not None:
        # 直接使用已知符号
        mask_minus1 = transmitted_symbols == -1
        mask_plus1 = transmitted_symbols == +1

        if not np.any(mask_minus1) or not np.any(mask_plus1):
            raise ValueError("训练序列必须包含-1和+1符号")

        mean_minus1 = np.mean(received_symbols[mask_minus1])
        mean_plus1 = np.mean(received_symbols[mask_plus1])

        # DC偏移是两个均值的中点
        dc_estimate = (mean_minus1 + mean_plus1) / 2.0

        # 标准误差（简化估计）
        std_minus1 = np.std(received_symbols[mask_minus1], ddof=1)
        std_plus1 = np.std(received_symbols[mask_plus1], ddof=1)
        n_minus1 = np.sum(mask_minus1)
        n_plus1 = np.sum(mask_plus1)

        # 两个独立均值的组合误差
        std_error = 0.5 * np.sqrt(
            (std_minus1 ** 2 / n_minus1) + (std_plus1 ** 2 / n_plus1)
        )

        result.update(
            {
                "dc_estimate": float(dc_estimate),
                "std_error": float(std_error),
                "method": "two_point",
                "mean_for_minus1": float(mean_minus1),
                "mean_for_plus1": float(mean_plus1),
            }
        )

    elif training_bits is not None:
        # 从比特转换为符号
        from .modulation import bpsk_modulate

        transmitted_symbols = bpsk_modulate(training_bits)
        return estimate_dc_offset(received_symbols, transmitted_symbols=transmitted_symbols)

    else:
        # 方法2: 均值法（假设等概）
        dc_estimate = np.mean(received_symbols)
        std_error = np.std(received_symbols, ddof=1) / np.sqrt(len(received_symbols))

        result.update(
            {
                "dc_estimate": float(dc_estimate),
                "std_error": float(std_error),
                "method": "mean",
            }
        )

    return result


def measure_signal_statistics(received_symbols: np.ndarray) -> Dict[str, Any]:
    """
    测量接收信号的统计特性

    计算信号的基本统计量，用于故障诊断。

    参数:
        received_symbols: 接收符号序列

    返回:
        字典包含:
        - mean: 均值
        - variance: 方差
        - std: 标准差
        - num_samples: 样本数量
        - mean_std_error: 均值的标准误差
        - var_std_error: 方差的标准误差（近似）

    示例:
        >>> symbols = np.array([-1.2, 1.3, -0.8, 1.1])
        >>> stats = measure_signal_statistics(symbols)
        >>> stats['mean']
        0.1
    """
    if len(received_symbols) == 0:
        raise ValueError("received_symbols不能为空")

    n = len(received_symbols)
    mean_val = np.mean(received_symbols)
    var_val = np.var(received_symbols, ddof=1)
    std_val = np.sqrt(var_val)

    # 均值的标准误差
    mean_std_error = std_val / np.sqrt(n)

    # 方差的标准误差（近似公式，假设正态分布）
    var_std_error = var_val * np.sqrt(2.0 / (n - 1))

    return {
        "mean": float(mean_val),
        "variance": float(var_val),
        "std": float(std_val),
        "num_samples": int(n),
        "mean_std_error": float(mean_std_error),
        "var_std_error": float(var_std_error),
    }
