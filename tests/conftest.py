"""Pytest配置文件"""

import pytest
import numpy as np


@pytest.fixture(autouse=True)
def reset_random_seed():
    """在每個測試前重置隨機種子"""
    np.random.seed(42)
