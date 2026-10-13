"""
测试调制与解调功能

本文件迁移自旧项目 D:/CommDoctor/tests/test_modulation.py
迁移日期: 2026-10-13
修改说明: 无修改，直接复用
"""

import numpy as np
import pytest
from commdoctor.modulation import bpsk_modulate, bpsk_demodulate


class TestBPSKModulation:
    """测试 BPSK 调制功能"""

    def test_modulate_basic(self):
        """测试基本调制功能"""
        bits = np.array([0, 1, 0, 1, 1, 0])
        symbols = bpsk_modulate(bits)

        # 检查输出长度
        assert len(symbols) == len(bits)

        # 检查映射正确性: 0 -> -1, 1 -> +1
        expected = np.array([-1.0, 1.0, -1.0, 1.0, 1.0, -1.0])
        np.testing.assert_array_equal(symbols, expected)

    def test_modulate_all_zeros(self):
        """测试全0序列"""
        bits = np.array([0, 0, 0, 0])
        symbols = bpsk_modulate(bits)
        expected = np.array([-1.0, -1.0, -1.0, -1.0])
        np.testing.assert_array_equal(symbols, expected)

    def test_modulate_all_ones(self):
        """测试全1序列"""
        bits = np.array([1, 1, 1, 1])
        symbols = bpsk_modulate(bits)
        expected = np.array([1.0, 1.0, 1.0, 1.0])
        np.testing.assert_array_equal(symbols, expected)

    def test_modulate_invalid_bits(self):
        """测试非法输入"""
        # 包含非 0/1 值
        invalid_bits = np.array([0, 1, 2, 1])
        with pytest.raises(ValueError, match="只能包含 0 和 1"):
            bpsk_modulate(invalid_bits)

    def test_modulate_output_type(self):
        """测试输出数据类型"""
        bits = np.array([0, 1])
        symbols = bpsk_modulate(bits)
        assert symbols.dtype == np.float64


class TestBPSKDemodulation:
    """测试 BPSK 解调功能"""

    def test_demodulate_basic(self):
        """测试基本解调功能"""
        received = np.array([-0.8, 1.2, -1.5, 0.3, 0.9])
        bits = bpsk_demodulate(received)

        # 检查判决规则: >= 0 -> 1, < 0 -> 0
        expected = np.array([0, 1, 0, 1, 1])
        np.testing.assert_array_equal(bits, expected)

    def test_demodulate_boundary(self):
        """测试边界情况（接收值恰好为0）"""
        received = np.array([-0.1, 0.0, 0.1])
        bits = bpsk_demodulate(received)
        # 0.0 判定为 1（因为 >= 0）
        expected = np.array([0, 1, 1])
        np.testing.assert_array_equal(bits, expected)

    def test_demodulate_output_type(self):
        """测试输出数据类型"""
        received = np.array([-1.0, 1.0])
        bits = bpsk_demodulate(received)
        assert bits.dtype == np.int8


class TestModulationDemodulationChain:
    """测试调制-解调链路"""

    def test_perfect_channel(self):
        """测试无噪声情况下的调制-解调"""
        # 生成随机比特
        np.random.seed(42)
        original_bits = np.random.randint(0, 2, size=100, dtype=np.int8)

        # 调制
        symbols = bpsk_modulate(original_bits)

        # 无噪声传输
        received = symbols.copy()

        # 解调
        decoded_bits = bpsk_demodulate(received)

        # 应该完全恢复
        np.testing.assert_array_equal(decoded_bits, original_bits)
