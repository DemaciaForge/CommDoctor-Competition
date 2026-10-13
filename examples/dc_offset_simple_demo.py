"""
DC偏移故障演示 - 简化版

本脚本提供DC偏移故障的最小可运行演示。
用户可以在Windows上亲自复现实验结果。

运行方法:
    python examples/dc_offset_simple_demo.py

预期结果:
    - DC估计误差 < 5%
    - 修复后BER显著下降
    - 修复后BER接近理论值
"""

import numpy as np
from commdoctor.signal_gen import generate_bits
from commdoctor.modulation import bpsk_modulate, bpsk_demodulate
from commdoctor.channel import awgn_channel
from commdoctor.metrics import calculate_ber, theoretical_ber
from commdoctor.faults import inject_dc_offset, remove_dc_offset
from commdoctor.diagnosis import estimate_dc_offset


def main():
    """运行单个DC偏移故障实验"""
    print("=" * 70)
    print("DC偏移故障演示")
    print("=" * 70)

    # 实验参数
    num_bits_train = 10000  # 训练序列长度
    num_bits_eval = 100000  # 评价序列长度
    eb_n0_db = 8.0  # 信噪比
    dc_offset = 0.4  # DC偏移量

    print(f"\n实验参数:")
    print(f"  Eb/N0: {eb_n0_db} dB")
    print(f"  DC偏移: {dc_offset}")
    print(f"  训练序列: {num_bits_train} 比特")
    print(f"  评价序列: {num_bits_eval} 比特")

    # ========== 阶段1: 训练（DC估计） ==========
    print(f"\n{'阶段1: DC估计':=^70}")

    # 生成训练数据
    train_bits = generate_bits(num_bits_train, seed=42)
    train_symbols = bpsk_modulate(train_bits)

    # 注入DC偏移
    train_symbols_faulty = inject_dc_offset(train_symbols, dc_offset)

    # 添加噪声
    train_received = awgn_channel(train_symbols_faulty, eb_n0_db, seed=1042)

    # 估计DC偏移
    dc_result = estimate_dc_offset(train_received, training_bits=train_bits)
    dc_estimate = dc_result["dc_estimate"]

    print(f"  真实DC偏移: {dc_offset:.6f}")
    print(f"  估计DC偏移: {dc_estimate:.6f}")
    print(f"  估计误差: {abs(dc_estimate - dc_offset):.6f}")
    print(f"  相对误差: {abs(dc_estimate - dc_offset) / abs(dc_offset) * 100:.2f}%")

    # ========== 阶段2: 评价（独立数据） ==========
    print(f"\n{'阶段2: 性能评价':=^70}")

    # 生成评价数据（使用不同种子）
    eval_bits = generate_bits(num_bits_eval, seed=123)
    eval_symbols = bpsk_modulate(eval_bits)

    # 注入相同的DC偏移
    eval_symbols_faulty = inject_dc_offset(eval_symbols, dc_offset)

    # 添加噪声
    eval_received = awgn_channel(eval_symbols_faulty, eb_n0_db, seed=1123)

    # 修复前：直接解调
    eval_demod_before = bpsk_demodulate(eval_received)
    ber_before, errors_before, _ = calculate_ber(eval_bits, eval_demod_before)

    print(f"\n修复前:")
    print(f"  BER: {ber_before:.10f}")
    print(f"  错误比特数: {errors_before} / {num_bits_eval}")

    # 修复后：移除DC后解调
    eval_corrected, _ = remove_dc_offset(eval_received, dc_estimate=dc_estimate)
    eval_demod_after = bpsk_demodulate(eval_corrected)
    ber_after, errors_after, _ = calculate_ber(eval_bits, eval_demod_after)

    print(f"\n修复后:")
    print(f"  BER: {ber_after:.10f}")
    print(f"  错误比特数: {errors_after} / {num_bits_eval}")

    # 理论BER
    theo_ber_after = theoretical_ber(eb_n0_db)
    print(f"\n理论BER（完美修复）: {theo_ber_after:.10f}")

    # ========== 阶段3: 结果总结 ==========
    print(f"\n{'结果总结':=^70}")

    ber_reduction = (ber_before - ber_after) / ber_before * 100
    improvement = ber_before / ber_after if ber_after > 0 else float('inf')

    print(f"  BER下降: {ber_reduction:.2f}%")
    print(f"  改善倍数: {improvement:.2f}x")

    # 验收标准
    print(f"\n验收标准:")

    dc_error_percent = abs(dc_estimate - dc_offset) / abs(dc_offset) * 100
    pass_dc = dc_error_percent < 5.0
    print(f"  [{'PASS' if pass_dc else 'FAIL'}] DC估计误差 < 5%: {dc_error_percent:.2f}%")

    pass_reduction = ber_reduction > 50.0
    print(f"  [{'PASS' if pass_reduction else 'FAIL'}] BER下降 > 50%: {ber_reduction:.2f}%")

    ber_theory_dev = abs(ber_after - theo_ber_after) / theo_ber_after * 100
    pass_theory = ber_theory_dev < 20.0
    print(f"  [{'PASS' if pass_theory else 'FAIL'}] 修复后BER与理论偏差 < 20%: {ber_theory_dev:.2f}%")

    all_passed = pass_dc and pass_reduction and pass_theory

    print(f"\n{'=' * 70}")
    if all_passed:
        print("实验成功！所有验收标准通过。")
        print("DC偏移故障的注入、诊断、修复闭环工作正常。")
    else:
        print("部分验收标准未通过。")
    print("=" * 70)

    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
