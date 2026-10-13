"""
阶段02-B DC偏移故障完整闭环验证

本脚本演示DC偏移故障的完整诊断和修复流程：
1. 生成干净的BPSK信号
2. 注入DC偏移故障
3. 添加AWGN噪声
4. 使用训练序列估计DC偏移
5. 修复DC偏移
6. 对比修复前后的BER性能
7. 与理论值对照

验证目标:
- DC估计误差 < 5%
- 修复后BER显著下降
- 修复后BER接近理论值（误差<20%，考虑统计波动）
"""

import numpy as np
from commdoctor.signal_gen import generate_bits
from commdoctor.modulation import bpsk_modulate, bpsk_demodulate
from commdoctor.channel import awgn_channel
from commdoctor.metrics import calculate_ber, theoretical_ber
from commdoctor.faults import inject_dc_offset, remove_dc_offset
from commdoctor.diagnosis import estimate_dc_offset
from scipy.special import erfc


def q_function(x):
    """高斯Q函数"""
    return 0.5 * erfc(x / np.sqrt(2))


def theoretical_ber_with_dc(eb_n0_db, dc_offset):
    """计算DC偏移下的理论BER"""
    eb_n0_linear = 10 ** (eb_n0_db / 10)
    sigma = np.sqrt(1.0 / (2.0 * eb_n0_linear))

    p_err_minus1 = q_function((1.0 - dc_offset) / sigma)
    p_err_plus1 = q_function((1.0 + dc_offset) / sigma)

    ber = 0.5 * (p_err_minus1 + p_err_plus1)
    return ber


def run_dc_offset_experiment(
    num_bits_train=10000,
    num_bits_eval=100000,
    eb_n0_db=8.0,
    dc_offset=0.4,
    seed_train=42,
    seed_eval=123,
):
    """
    运行DC偏移故障实验

    参数:
        num_bits_train: 训练序列长度（用于DC估计）
        num_bits_eval: 评价序列长度（用于BER计算）
        eb_n0_db: Eb/N0 (dB)
        dc_offset: DC偏移量
        seed_train: 训练序列随机种子
        seed_eval: 评价序列随机种子

    返回:
        实验结果字典
    """
    print("=" * 70)
    print("DC偏移故障闭环验证实验")
    print("=" * 70)

    print(f"\n实验参数:")
    print(f"  训练序列长度: {num_bits_train} 比特")
    print(f"  评价序列长度: {num_bits_eval} 比特")
    print(f"  Eb/N0: {eb_n0_db} dB")
    print(f"  DC偏移: {dc_offset}")
    print(f"  训练种子: {seed_train}, 评价种子: {seed_eval}")

    # ========== 阶段1: 生成训练序列并估计DC偏移 ==========
    print(f"\n{'阶段1: 训练阶段（DC估计）':=^70}")

    # 生成训练比特
    train_bits = generate_bits(num_bits_train, seed=seed_train)
    print(f"  生成 {num_bits_train} 训练比特")
    print(f"  比特0数量: {np.sum(train_bits == 0)}")
    print(f"  比特1数量: {np.sum(train_bits == 1)}")

    # BPSK调制
    train_symbols = bpsk_modulate(train_bits)

    # 注入DC偏移
    train_symbols_faulty = inject_dc_offset(train_symbols, dc_offset)
    print(f"  注入DC偏移: {dc_offset}")

    # 添加AWGN噪声
    train_received = awgn_channel(train_symbols_faulty, eb_n0_db, seed=seed_train + 1000)

    # 估计DC偏移
    dc_result = estimate_dc_offset(train_received, training_bits=train_bits)
    dc_estimate = dc_result["dc_estimate"]
    dc_std_error = dc_result["std_error"]

    print(f"\nDC偏移估计结果:")
    print(f"  真实DC偏移: {dc_offset:.6f}")
    print(f"  估计DC偏移: {dc_estimate:.6f}")
    print(f"  估计误差: {abs(dc_estimate - dc_offset):.6f}")
    print(f"  相对误差: {abs(dc_estimate - dc_offset) / abs(dc_offset) * 100:.2f}%")
    print(f"  标准误差: {dc_std_error:.6f}")

    # ========== 阶段2: 评价序列（独立数据） ==========
    print(f"\n{'阶段2: 评价阶段（独立数据）':=^70}")

    # 生成评价比特（使用不同种子）
    eval_bits = generate_bits(num_bits_eval, seed=seed_eval)
    print(f"  生成 {num_bits_eval} 评价比特（独立于训练数据）")

    # BPSK调制
    eval_symbols = bpsk_modulate(eval_bits)

    # 注入相同的DC偏移
    eval_symbols_faulty = inject_dc_offset(eval_symbols, dc_offset)

    # 添加AWGN噪声
    eval_received = awgn_channel(eval_symbols_faulty, eb_n0_db, seed=seed_eval + 1000)

    # ========== 阶段3: 修复前性能 ==========
    print(f"\n{'阶段3: 修复前性能':=^70}")

    # 直接解调（不修复）
    eval_demod_before = bpsk_demodulate(eval_received)
    ber_before, errors_before, _ = calculate_ber(eval_bits, eval_demod_before)

    print(f"  修复前BER: {ber_before:.10f}")
    print(f"  错误比特数: {errors_before} / {num_bits_eval}")

    # 计算理论BER
    theo_ber_before = theoretical_ber_with_dc(eb_n0_db, dc_offset)
    print(f"  理论BER: {theo_ber_before:.10f}")
    print(f"  实测与理论偏差: {abs(ber_before - theo_ber_before) / theo_ber_before * 100:.2f}%")

    # ========== 阶段4: 修复后性能 ==========
    print(f"\n{'阶段4: 修复后性能':=^70}")

    # 使用训练阶段估计的DC偏移进行修复
    eval_corrected, _ = remove_dc_offset(eval_received, dc_estimate=dc_estimate)

    # 解调修复后的信号
    eval_demod_after = bpsk_demodulate(eval_corrected)
    ber_after, errors_after, _ = calculate_ber(eval_bits, eval_demod_after)

    print(f"  修复后BER: {ber_after:.10f}")
    print(f"  错误比特数: {errors_after} / {num_bits_eval}")

    # 完美修复的理论BER（DC=0）
    theo_ber_after = theoretical_ber(eb_n0_db)
    print(f"  理论BER（完美修复）: {theo_ber_after:.10f}")
    print(f"  实测与理论偏差: {abs(ber_after - theo_ber_after) / theo_ber_after * 100:.2f}%")

    # ========== 阶段5: 修复效果评估 ==========
    print(f"\n{'阶段5: 修复效果评估':=^70}")

    ber_reduction = (ber_before - ber_after) / ber_before * 100
    print(f"  BER下降: {ber_reduction:.2f}%")
    print(f"  BER改善倍数: {ber_before / ber_after:.2f}x")

    # 验收标准
    print(f"\n验收标准:")

    # 标准1: DC估计误差
    dc_error_percent = abs(dc_estimate - dc_offset) / abs(dc_offset) * 100
    pass_dc_estimate = dc_error_percent < 5.0
    status1 = "PASS" if pass_dc_estimate else "FAIL"
    print(f"  [{status1}] DC估计误差 < 5%: {dc_error_percent:.2f}%")

    # 标准2: BER显著下降
    pass_ber_reduction = ber_reduction > 50.0
    status2 = "PASS" if pass_ber_reduction else "FAIL"
    print(f"  [{status2}] BER下降 > 50%: {ber_reduction:.2f}%")

    # 标准3: 修复后BER接近理论值
    ber_theory_deviation = abs(ber_after - theo_ber_after) / theo_ber_after * 100
    pass_ber_theory = ber_theory_deviation < 20.0
    status3 = "PASS" if pass_ber_theory else "FAIL"
    print(f"  [{status3}] 修复后BER与理论偏差 < 20%: {ber_theory_deviation:.2f}%")

    all_passed = pass_dc_estimate and pass_ber_reduction and pass_ber_theory

    print(f"\n{'实验结论':=^70}")
    if all_passed:
        print("  [PASS] 所有验收标准通过！")
        print("  DC偏移故障的注入、诊断、修复闭环验证成功。")
    else:
        print("  [FAIL] 部分验收标准未通过。")

    print("=" * 70)

    return {
        "dc_offset_true": dc_offset,
        "dc_offset_estimate": dc_estimate,
        "dc_std_error": dc_std_error,
        "ber_before": ber_before,
        "ber_after": ber_after,
        "ber_theory_before": theo_ber_before,
        "ber_theory_after": theo_ber_after,
        "ber_reduction_percent": ber_reduction,
        "all_passed": all_passed,
    }


def main():
    """运行多组实验"""
    print("\n" + "=" * 70)
    print("CommDoctor 阶段02-B: DC偏移故障最小技术验证")
    print("=" * 70)
    print("\n本实验验证DC偏移故障的完整闭环：")
    print("  注入 → 测量 → 估计 → 修复 → 验证")
    print("\n训练数据与评价数据完全独立，确保估计器的泛化能力。")

    # 实验1: 标准参数（Eb/N0=8dB, DC=0.4）
    print("\n\n" + "=" * 70)
    print("实验1: 标准参数")
    print("=" * 70)
    result1 = run_dc_offset_experiment(
        num_bits_train=10000,
        num_bits_eval=100000,
        eb_n0_db=8.0,
        dc_offset=0.4,
        seed_train=42,
        seed_eval=123,
    )

    # 实验2: 较小DC偏移
    print("\n\n" + "=" * 70)
    print("实验2: 较小DC偏移")
    print("=" * 70)
    result2 = run_dc_offset_experiment(
        num_bits_train=10000,
        num_bits_eval=100000,
        eb_n0_db=8.0,
        dc_offset=0.1,
        seed_train=43,
        seed_eval=124,
    )

    # 实验3: 负DC偏移
    print("\n\n" + "=" * 70)
    print("实验3: 负DC偏移")
    print("=" * 70)
    result3 = run_dc_offset_experiment(
        num_bits_train=10000,
        num_bits_eval=100000,
        eb_n0_db=8.0,
        dc_offset=-0.5,
        seed_train=44,
        seed_eval=125,
    )

    # 实验4: 较低SNR
    print("\n\n" + "=" * 70)
    print("实验4: 较低SNR")
    print("=" * 70)
    result4 = run_dc_offset_experiment(
        num_bits_train=10000,
        num_bits_eval=100000,
        eb_n0_db=4.0,
        dc_offset=0.4,
        seed_train=45,
        seed_eval=126,
    )

    # 汇总结果
    print("\n\n" + "=" * 70)
    print("所有实验汇总")
    print("=" * 70)
    results = [result1, result2, result3, result4]
    names = ["实验1 (标准)", "实验2 (小DC)", "实验3 (负DC)", "实验4 (低SNR)"]

    print(f"\n{'实验':<20} {'DC真值':<10} {'DC估计':<10} {'修复前BER':<15} {'修复后BER':<15} {'通过':<10}")
    print("-" * 80)
    for name, res in zip(names, results):
        status = "PASS" if res["all_passed"] else "FAIL"
        print(
            f"{name:<20} {res['dc_offset_true']:<10.4f} {res['dc_offset_estimate']:<10.6f} "
            f"{res['ber_before']:<15.10f} {res['ber_after']:<15.10f} {status:<10}"
        )

    all_experiments_passed = all(res["all_passed"] for res in results)
    print("\n" + "=" * 70)
    if all_experiments_passed:
        print("[PASS] 所有实验验证通过！")
        print("DC偏移故障的注入、诊断、修复机制工作正常。")
    else:
        print("[FAIL] 部分实验未通过验收标准。")
    print("=" * 70)


if __name__ == "__main__":
    main()
