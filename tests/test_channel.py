"""
测试信道模块

本文件迁移自旧项目 D:/CommDoctor/tests/test_channel.py
迁移日期: 2026-10-13
修改说明: 无修改，直接复用
"""

import numpy as np
import pytest
from commdoctor.channel import awgn_channel


class TestAWGNChannel:
    """测试 AWGN 信道功能"""

    def test_channel_basic(self):
        """测试基本信道功能"""
        symbols = np.array([-1.0, 1.0, -1.0, 1.0])
        eb_n0_db = 10.0
        received = awgn_channel(symbols, eb_n0_db, seed=42)

        # 检查输出长度
        assert len(received) == len(symbols)

        # 检查输出不等于输入（添加了噪声）
        assert not np.array_equal(received, symbols)

    def test_channel_reproducibility(self):
        """测试随机种子可复现性"""
        symbols = np.array([-1.0, 1.0, -1.0, 1.0])
        eb_n0_db = 6.0

        # 相同种子应该产生相同结果
        received1 = awgn_channel(symbols, eb_n0_db, seed=123)
        received2 = awgn_channel(symbols, eb_n0_db, seed=123)
        np.testing.assert_array_equal(received1, received2)

        # 不同种子应该产生不同结果
        received3 = awgn_channel(symbols, eb_n0_db, seed=456)
        assert not np.array_equal(received1, received3)

    def test_channel_high_snr(self):
        """测试高信噪比情况（噪声应该很小）"""
        symbols = np.array([-1.0, 1.0, -1.0, 1.0])
        eb_n0_db = 30.0  # 非常高的信噪比
        received = awgn_channel(symbols, eb_n0_db, seed=42)

        # 高信噪比时，接收信号应该非常接近原始信号
        np.testing.assert_allclose(received, symbols, atol=0.1)

    def test_channel_low_snr(self):
        """测试低信噪比情况（噪声应该较大）"""
        symbols = np.array([-1.0, 1.0, -1.0, 1.0])
        eb_n0_db = -5.0  # 非常低的信噪比
        received = awgn_channel(symbols, eb_n0_db, seed=42)

        # 低信噪比时，接收信号可能与原始信号差异较大
        # 至少应该不完全相等
        assert not np.array_equal(received, symbols)

    def test_channel_invalid_snr(self):
        """测试非法 SNR 输入"""
        symbols = np.array([-1.0, 1.0])

        # NaN
        with pytest.raises(ValueError, match="必须为有限数值"):
            awgn_channel(symbols, np.nan)

        # Infinity
        with pytest.raises(ValueError, match="必须为有限数值"):
            awgn_channel(symbols, np.inf)

    def test_channel_noise_statistics(self):
        """测试噪声统计特性"""
        # 生成大量样本来验证噪声均值接近0
        symbols = np.ones(10000)  # 全1符号
        eb_n0_db = 6.0
        received = awgn_channel(symbols, eb_n0_db, seed=42)

        # 噪声 = 接收 - 发送
        noise = received - symbols

        # 噪声均值应该接近0（高斯白噪声的均值为0）
        noise_mean = np.mean(noise)
        assert abs(noise_mean) < 0.01  # 允许一定的统计波动

        # 验证噪声方差与理论值接近
        eb_n0_linear = 10 ** (eb_n0_db / 10)
        expected_std = np.sqrt(1.0 / (2.0 * eb_n0_linear))
        actual_std = np.std(noise)
        np.testing.assert_allclose(actual_std, expected_std, rtol=0.05)
