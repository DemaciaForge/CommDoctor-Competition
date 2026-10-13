"""
DC偏移理论BER推导与验证

本脚本独立推导并验证DC偏移对BPSK误码率的影响。

数学模型:
    接收信号: r = s + b + w
    其中:
        s ∈ {-1, +1}: BPSK符号
        b: DC偏移
        w ~ N(0, σ²): AWGN噪声

    判决规则: r >= 0 → 比特1
             r < 0  → 比特0

理论BER推导:
    P(错误|发送-1) = P(r >= 0 | s=-1)
                  = P(-1 + b + w >= 0)
                  = P(w >= 1-b)
                  = Q((1-b)/σ)

    P(错误|发送+1) = P(r < 0 | s=+1)
                  = P(+1 + b + w < 0)
                  = P(w < -1-b)
                  = Q((1+b)/σ)

    BER = 0.5 × [Q((1-b)/σ) + Q((1+b)/σ)]

    其中 Q(x) = 0.5 × erfc(x/√2)

    对于Eb/N0 = 8 dB:
        Eb/N0_linear = 10^(8/10) = 6.3096
        对于实值、单位能量BPSK: σ² = 1/(2×Eb/N0)
        σ = sqrt(1/(2×6.3096)) = 0.28151
"""

import numpy as np
from scipy.special import erfc


def q_function(x):
    """高斯Q函数: Q(x) = 0.5 * erfc(x/√2)"""
    return 0.5 * erfc(x / np.sqrt(2))


def theoretical_ber_with_dc(eb_n0_db, dc_offset):
    """
    计算DC偏移下的理论BER

    参数:
        eb_n0_db: Eb/N0，单位dB
        dc_offset: DC偏移量b

    返回:
        理论BER
    """
    # 转换Eb/N0到线性值
    eb_n0_linear = 10 ** (eb_n0_db / 10)

    # 计算噪声标准差
    # 对于实值、单位能量BPSK: σ² = 1/(2×Eb/N0)
    sigma = np.sqrt(1.0 / (2.0 * eb_n0_linear))

    # 计算两种错误概率
    # P(错误|发送-1) = Q((1-b)/σ)
    p_error_given_minus1 = q_function((1.0 - dc_offset) / sigma)

    # P(错误|发送+1) = Q((1+b)/σ)
    p_error_given_plus1 = q_function((1.0 + dc_offset) / sigma)

    # 总BER（假设0和1等概）
    ber = 0.5 * (p_error_given_minus1 + p_error_given_plus1)

    return ber, sigma, p_error_given_minus1, p_error_given_plus1


def main():
    """验证用户提出的数值"""
    eb_n0_db = 8.0
    dc_offset = 0.4

    print("=" * 70)
    print("DC偏移理论BER推导验证")
    print("=" * 70)
    print(f"\n参数设置:")
    print(f"  Eb/N0 = {eb_n0_db} dB")
    print(f"  DC偏移 b = {dc_offset}")

    # 计算理论BER
    ber, sigma, p_err_minus1, p_err_plus1 = theoretical_ber_with_dc(
        eb_n0_db, dc_offset
    )

    print(f"\n中间计算:")
    print(f"  Eb/N0 (线性) = {10**(eb_n0_db/10):.6f}")
    print(f"  噪声标准差 σ = {sigma:.8f}")
    print(f"  (1-b)/σ = {(1.0-dc_offset)/sigma:.6f}")
    print(f"  (1+b)/σ = {(1.0+dc_offset)/sigma:.6f}")

    print(f"\n理论结果:")
    print(f"  P(错误|发送-1) = Q((1-b)/σ) = {p_err_minus1:.10f}")
    print(f"  P(错误|发送+1) = Q((1+b)/σ) = {p_err_plus1:.10f}")
    print(f"  修复前BER = {ber:.10f}")

    # 验证修复后BER（完美消除DC偏移）
    ber_after, sigma_after, _, _ = theoretical_ber_with_dc(eb_n0_db, 0.0)
    print(f"\n完美消除DC偏移后:")
    print(f"  修复后BER = {ber_after:.10f}")

    print(f"\n用户声称的数值:")
    print(f"  修复前BER: 0.15 (用户声称)")
    print(f"  修复后BER: 0.0002 (用户声称)")

    print(f"\n数值对比:")
    print(f"  修复前BER: 理论={ber:.10f}, 用户声称=0.15")
    print(f"  差异: {abs(ber - 0.15):.10f}")
    print(f"  修复后BER: 理论={ber_after:.10f}, 用户声称=0.0002")
    print(f"  差异: {abs(ber_after - 0.0002):.10f}")

    print(f"\n结论:")
    if abs(ber - 0.15) < 0.01:
        print("  ✓ 用户声称的修复前BER接近理论值")
    else:
        print(f"  ✗ 用户声称的修复前BER与理论值相差较大")
        print(f"    正确理论值应为: {ber:.10f}")

    if abs(ber_after - 0.0002) < 0.0001:
        print("  ✓ 用户声称的修复后BER接近理论值")
    else:
        print(f"  ✗ 用户声称的修复后BER与理论值相差较大")
        print(f"    正确理论值应为: {ber_after:.10f}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
