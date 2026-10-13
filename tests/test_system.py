"""
测试完整的 BPSK 通信系统
包括四个核心验收测试：A、B、C、D

本文件迁移自旧项目 D:/CommDoctor/tests/test_system.py
迁移日期: 2026-10-13
修改说明: 无修改，直接复用
"""

import numpy as np
import pytest
from commdoctor import (
    generate_bits,
    bpsk_modulate,
    bpsk_demodulate,
    awgn_channel,
    calculate_ber,
    theoretical_ber,
)


class TestSignalGeneration:
    """测试信号生成功能"""

    def test_generate_bits_basic(self):
        """测试基本比特生成"""
        bits = generate_bits(100, seed=42)
        assert len(bits) == 100
        assert np.all((bits == 0) | (bits == 1))

    def test_generate_bits_reproducibility(self):
        """测试可复现性"""
        bits1 = generate_bits(50, seed=123)
        bits2 = generate_bits(50, seed=123)
        np.testing.assert_array_equal(bits1, bits2)

    def test_generate_bits_invalid_count(self):
        """测试非法比特数量"""
        with pytest.raises(ValueError, match="必须为正整数"):
            generate_bits(0)
        with pytest.raises(ValueError, match="必须为正整数"):
            generate_bits(-10)


class TestBERCalculation:
    """测试 BER 计算功能"""

    def test_ber_no_errors(self):
        """测试无错误情况"""
        tx = np.array([0, 1, 0, 1, 1, 0])
        rx = np.array([0, 1, 0, 1, 1, 0])
        ber, errors, total = calculate_ber(tx, rx)
        assert ber == 0.0
        assert errors == 0
        assert total == 6

    def test_ber_some_errors(self):
        """测试部分错误情况"""
        tx = np.array([0, 1, 0, 1, 1, 0, 1, 0])
        rx = np.array([0, 1, 0, 0, 1, 0, 1, 1])
        ber, errors, total = calculate_ber(tx, rx)
        assert ber == 0.25  # 2 errors out of 8
        assert errors == 2
        assert total == 8

    def test_ber_all_errors(self):
        """测试全部错误情况"""
        tx = np.array([0, 0, 0, 0])
        rx = np.array([1, 1, 1, 1])
        ber, errors, total = calculate_ber(tx, rx)
        assert ber == 1.0
        assert errors == 4
        assert total == 4

    def test_ber_length_mismatch(self):
        """测试长度不匹配"""
        tx = np.array([0, 1, 0])
        rx = np.array([0, 1])
        with pytest.raises(ValueError, match="长度必须相同"):
            calculate_ber(tx, rx)


class TestTheoreticalBER:
    """测试理论 BER 计算"""

    def test_theoretical_ber_values(self):
        """测试特定 Eb/N0 下的理论 BER 值"""
        # 0 dB
        ber_0db = theoretical_ber(0.0)
        assert abs(ber_0db - 0.07865) < 0.0001

        # 6 dB
        ber_6db = theoretical_ber(6.0)
        assert abs(ber_6db - 0.00239) < 0.00001

        # 10 dB
        ber_10db = theoretical_ber(10.0)
        assert ber_10db < 0.0001  # 应该非常小

    def test_theoretical_ber_monotonic(self):
        """测试 BER 随 Eb/N0 单调递减"""
        ber_values = [theoretical_ber(snr) for snr in range(0, 11)]
        # 检查是否单调递减
        for i in range(len(ber_values) - 1):
            assert ber_values[i] > ber_values[i + 1]

    def test_theoretical_ber_invalid_snr(self):
        """测试非法 SNR"""
        with pytest.raises(ValueError):
            theoretical_ber(np.nan)
        with pytest.raises(ValueError):
            theoretical_ber(np.inf)


class TestSystemIntegration:
    """系统集成测试"""

    def test_a_noiseless_transmission(self):
        """
        测试 A：无噪声传输
        预期：BER = 0，所有比特完全恢复
        """
        # 生成随机比特
        num_bits = 1000
        tx_bits = generate_bits(num_bits, seed=42)

        # 调制
        tx_symbols = bpsk_modulate(tx_bits)

        # 无噪声传输（不添加噪声，相当于无限大的 Eb/N0）
        rx_symbols = tx_symbols.copy()

        # 解调
        rx_bits = bpsk_demodulate(rx_symbols)

        # 计算 BER
        ber, errors, total = calculate_ber(tx_bits, rx_bits)

        # 验证
        assert ber == 0.0, f"无噪声传输应该 BER=0，实际 BER={ber}"
        assert errors == 0, f"无噪声传输不应有错误，实际错误数={errors}"
        np.testing.assert_array_equal(rx_bits, tx_bits)

    def test_b_theoretical_ber_comparison_0db(self):
        """
        测试 B1：理论 BER 对照 - 0 dB
        使用 100 万比特，验证仿真 BER 接近理论值
        """
        num_bits = 1000000
        eb_n0_db = 0.0
        seed = 42

        # 生成比特
        tx_bits = generate_bits(num_bits, seed=seed)

        # 调制
        tx_symbols = bpsk_modulate(tx_bits)

        # 通过 AWGN 信道
        rx_symbols = awgn_channel(tx_symbols, eb_n0_db, seed=seed)

        # 解调
        rx_bits = bpsk_demodulate(rx_symbols)

        # 计算仿真 BER
        sim_ber, errors, total = calculate_ber(tx_bits, rx_bits)

        # 计算理论 BER
        theo_ber = theoretical_ber(eb_n0_db)

        # 统计验收标准
        # 二项分布标准差: σ = sqrt(p * (1-p) / n)
        std_error = np.sqrt(theo_ber * (1 - theo_ber) / num_bits)
        # 允许 5 倍标准误差
        tolerance = 5 * std_error

        print(f"\n0 dB 测试结果:")
        print(f"  理论 BER: {theo_ber:.6f}")
        print(f"  仿真 BER: {sim_ber:.6f}")
        print(f"  错误数: {errors} / {total}")
        print(f"  标准误差: {std_error:.6f}")
        print(f"  允许范围: [{theo_ber - tolerance:.6f}, {theo_ber + tolerance:.6f}]")

        # 验证仿真值在合理范围内
        assert abs(sim_ber - theo_ber) <= tolerance, (
            f"仿真 BER ({sim_ber:.6f}) 与理论 BER ({theo_ber:.6f}) "
            f"偏差超过 5 倍标准误差 ({tolerance:.6f})"
        )

    def test_b_theoretical_ber_comparison_6db(self):
        """
        测试 B2：理论 BER 对照 - 6 dB
        使用 100 万比特，验证仿真 BER 接近理论值
        """
        num_bits = 1000000
        eb_n0_db = 6.0
        seed = 42

        # 生成比特
        tx_bits = generate_bits(num_bits, seed=seed)

        # 调制
        tx_symbols = bpsk_modulate(tx_bits)

        # 通过 AWGN 信道
        rx_symbols = awgn_channel(tx_symbols, eb_n0_db, seed=seed)

        # 解调
        rx_bits = bpsk_demodulate(rx_symbols)

        # 计算仿真 BER
        sim_ber, errors, total = calculate_ber(tx_bits, rx_bits)

        # 计算理论 BER
        theo_ber = theoretical_ber(eb_n0_db)

        # 统计验收标准
        std_error = np.sqrt(theo_ber * (1 - theo_ber) / num_bits)
        tolerance = 5 * std_error

        print(f"\n6 dB 测试结果:")
        print(f"  理论 BER: {theo_ber:.6f}")
        print(f"  仿真 BER: {sim_ber:.6f}")
        print(f"  错误数: {errors} / {total}")
        print(f"  标准误差: {std_error:.6f}")
        print(f"  允许范围: [{theo_ber - tolerance:.6f}, {theo_ber + tolerance:.6f}]")

        # 验证
        assert abs(sim_ber - theo_ber) <= tolerance, (
            f"仿真 BER ({sim_ber:.6f}) 与理论 BER ({theo_ber:.6f}) "
            f"偏差超过 5 倍标准误差 ({tolerance:.6f})"
        )

    def test_c_snr_variation(self):
        """
        测试 C：信噪比变化
        测试 Eb/N0 从 0 dB 到 6 dB 时，BER 整体下降
        """
        num_bits = 100000
        seed = 42
        snr_range = [0, 2, 4, 6]

        ber_sim_list = []
        ber_theo_list = []

        print("\n信噪比变化测试:")
        print(f"{'Eb/N0 (dB)':<12} {'仿真 BER':<12} {'理论 BER':<12} {'错误数':<10} {'总比特数'}")
        print("-" * 60)

        for eb_n0_db in snr_range:
            # 生成比特
            tx_bits = generate_bits(num_bits, seed=seed)

            # 调制
            tx_symbols = bpsk_modulate(tx_bits)

            # 通过信道
            rx_symbols = awgn_channel(tx_symbols, eb_n0_db, seed=seed + eb_n0_db)

            # 解调
            rx_bits = bpsk_demodulate(rx_symbols)

            # 计算 BER
            sim_ber, errors, total = calculate_ber(tx_bits, rx_bits)
            theo_ber = theoretical_ber(eb_n0_db)

            ber_sim_list.append(sim_ber)
            ber_theo_list.append(theo_ber)

            print(f"{eb_n0_db:<12} {sim_ber:<12.6f} {theo_ber:<12.6f} {errors:<10} {total}")

        # 验证 BER 整体下降趋势
        for i in range(len(ber_sim_list) - 1):
            assert ber_sim_list[i] >= ber_sim_list[i + 1] * 0.8, (
                f"BER 应该随 Eb/N0 增加而下降，但在 {snr_range[i]} dB 到 {snr_range[i+1]} dB 之间未观察到下降"
            )

    def test_d_exception_handling(self):
        """
        测试 D：异常输入处理
        验证系统对各种异常输入的健壮性
        """
        # D1: 比特数量非法
        with pytest.raises(ValueError):
            generate_bits(0)
        with pytest.raises(ValueError):
            generate_bits(-10)

        # D2: 调制输入包含非法比特
        invalid_bits = np.array([0, 1, 2, 1])
        with pytest.raises(ValueError):
            bpsk_modulate(invalid_bits)

        # D3: BER 计算序列长度不同
        tx = np.array([0, 1, 0])
        rx = np.array([0, 1])
        with pytest.raises(ValueError):
            calculate_ber(tx, rx)

        # D4: 信噪比非有限数值
        symbols = np.array([-1.0, 1.0])
        with pytest.raises(ValueError):
            awgn_channel(symbols, np.nan)
        with pytest.raises(ValueError):
            awgn_channel(symbols, np.inf)
        with pytest.raises(ValueError):
            theoretical_ber(np.nan)
