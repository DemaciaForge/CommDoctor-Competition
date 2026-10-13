"""
故障注入模块

实现各种通信系统故障的注入功能。

本模块提供可控、可验证的故障注入机制，用于教学和诊断训练。
所有故障注入函数都是纯函数，不修改输入数组。

阶段02-B实现：DC偏移故障
"""

import numpy as np


def inject_dc_offset(symbols: np.ndarray, dc_offset: float) -> np.ndarray:
    """
    注入DC偏移故障

    DC偏移是指接收信号上叠加的恒定直流分量，通常由以下原因引起：
    - 模拟电路直流漂移
    - ADC采样偏置
    - 自动增益控制（AGC）不完善
    - 接收机前端电容耦合失效

    数学模型:
        r[n] = s[n] + b + w[n]
        其中b为DC偏移量

    参数:
        symbols: 输入符号序列（BPSK调制后的信号）
        dc_offset: DC偏移量，可正可负

    返回:
        添加了DC偏移的符号序列

    示例:
        >>> symbols = np.array([-1., 1., -1., 1.])
        >>> faulty = inject_dc_offset(symbols, dc_offset=0.5)
        >>> faulty
        array([-0.5,  1.5, -0.5,  1.5])
        >>> np.mean(faulty)  # DC偏移反映在均值上
        0.5
    """
    # 输入验证
    if not isinstance(symbols, np.ndarray):
        raise TypeError(f"symbols必须是numpy数组，当前类型: {type(symbols)}")

    if not np.isfinite(dc_offset):
        raise ValueError(f"DC偏移必须是有限数值，当前值: {dc_offset}")

    # 注入DC偏移（加法操作）
    # 使用副本避免修改原始数组
    faulty_symbols = symbols + dc_offset

    return faulty_symbols


def remove_dc_offset(
    received_symbols: np.ndarray, dc_estimate: float | None = None
) -> tuple[np.ndarray, float]:
    """
    移除DC偏移

    基于统计测量估计并移除DC偏移。对于等概率的BPSK信号，
    理论均值应为0，实测均值即为DC偏移估计。

    数学依据:
        对于s ∈ {-1, +1}且P(s=-1) = P(s=+1) = 0.5:
        E[s] = 0.5×(-1) + 0.5×(+1) = 0

        接收信号: r = s + b + w
        E[r] = E[s] + b + E[w] = 0 + b + 0 = b

        因此: b_estimate = mean(r)

    参数:
        received_symbols: 接收到的符号序列
        dc_estimate: DC偏移估计值。如果为None，自动从接收信号计算

    返回:
        元组 (corrected_symbols, dc_estimate):
        - corrected_symbols: 移除DC后的符号序列
        - dc_estimate: 使用的DC估计值

    注意:
        自动估计假设输入信号中0和1比特数量大致平衡。
        对于严重不平衡的数据，估计可能不准确。

    示例:
        >>> received = np.array([-0.5, 1.5, -0.5, 1.5])
        >>> corrected, dc_est = remove_dc_offset(received)
        >>> dc_est
        0.5
        >>> corrected
        array([-1.,  1., -1.,  1.])
    """
    # 输入验证
    if not isinstance(received_symbols, np.ndarray):
        raise TypeError(f"received_symbols必须是numpy数组，当前类型: {type(received_symbols)}")

    if len(received_symbols) == 0:
        raise ValueError("received_symbols不能为空数组")

    # 估计DC偏移（如果未提供）
    if dc_estimate is None:
        dc_estimate = float(np.mean(received_symbols))
    else:
        if not np.isfinite(dc_estimate):
            raise ValueError(f"dc_estimate必须是有限数值，当前值: {dc_estimate}")

    # 移除DC偏移
    corrected_symbols = received_symbols - dc_estimate

    return corrected_symbols, dc_estimate
