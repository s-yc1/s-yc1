# -*- coding: utf-8 -*-
"""
论文查重核心模块
================
职责：
  1. 读取 / 写入文本文件
  2. 文本规范化（全半角统一、去标点与空白）
  3. N-gram 字符特征统计
  4. 余弦相似度计算
  5. 串联上述步骤完成一次完整查重

设计说明：
  - 与命令行入口 main.py 解耦，核心算法不依赖 sys.argv，便于单元测试。
  - 全部文本按 utf-8 读写，避免中文乱码。
"""

import os
import unicodedata
from collections import Counter


# ---------------------------------------------------------------------------
# 文件读写
# ---------------------------------------------------------------------------
def read_text_file(file_path):
    """读取文本文件全部内容，统一使用 utf-8 编码。

    :param file_path: 文件绝对路径
    :return: 文件内容字符串
    :raises FileNotFoundError: 文件不存在时抛出
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"输入文件不存在: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def write_result(similarity, answer_path):
    """将相似度结果写入答案文件，只保留两位小数，不含其它文字。

    :param similarity: 0~1 之间的浮点数
    :param answer_path: 答案文件绝对路径
    """
    with open(answer_path, "w", encoding="utf-8") as f:
        f.write(f"{similarity:.2f}")


# ---------------------------------------------------------------------------
# 文本预处理
# ---------------------------------------------------------------------------
def normalize_text(text):
    """文本规范化，降低无关差异对查重结果的影响。

    处理步骤：
      1. unicodedata.NFKC 归一化 —— 全角字符转半角、兼容字符统一；
      2. 去除所有空白字符（空格、换行、制表符等）；
      3. 仅保留字母(L*)与数字(N*)，丢弃标点与符号。

    :param text: 原始文本
    :return: 规范化后的纯字符序列
    """
    if not text:
        return ""

    # 全角 -> 半角、兼容字符统一（一次性完成，避免重复字符串遍历）
    text = unicodedata.normalize("NFKC", text)

    kept = []
    append = kept.append
    for ch in text:
        if ch.isspace():
            continue
        category = unicodedata.category(ch)
        # L* = 字母（含中文汉字），N* = 数字
        if category[0] == "L" or category[0] == "N":
            append(ch)
    return "".join(kept)


# ---------------------------------------------------------------------------
# 特征提取
# ---------------------------------------------------------------------------
def ngram_counter(text, n=2):
    """对规范化文本生成 n 元字符组（n-gram）的计数器。

    例如 "今天天气很好" 在 n=2 时得到:
        {"今天":1, "天天":1, "天气":1, "气很":1, "很好":1}

    :param text: 规范化后的文本
    :param n: 元组长度，必须 >= 1
    :return: collections.Counter
    :raises ValueError: n < 1 时抛出
    """
    if n < 1:
        raise ValueError("n-gram 的 n 必须大于等于 1")
    if len(text) < n:
        return Counter()
    return Counter(text[i:i + n] for i in range(len(text) - n + 1))


# ---------------------------------------------------------------------------
# 相似度计算
# ---------------------------------------------------------------------------
def cosine_similarity(vec_a, vec_b):
    """计算两个稀疏词频向量的余弦相似度。

    cos(A,B) = (A·B) / (|A| * |B|)

    :param vec_a: Counter，文本 A 的特征向量
    :param vec_b: Counter，文本 B 的特征向量
    :return: 0~1 之间的浮点数
    """
    # 点积：只遍历 vec_a，按共有 key 累加
    dot = 0
    for key, count_a in vec_a.items():
        count_b = vec_b.get(key)
        if count_b:
            dot += count_a * count_b
    if dot == 0:
        return 0.0

    norm_a = 0.0
    for c in vec_a.values():
        norm_a += c * c
    norm_b = 0.0
    for c in vec_b.values():
        norm_b += c * c

    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a ** 0.5 * norm_b ** 0.5)


def calculate_similarity(text1, text2, n=2):
    """计算两段文本的相似度（对外主接口）。

    :param text1: 原文
    :param text2: 抄袭版文本
    :param n: n-gram 长度，默认二元
    :return: 0~1 之间的浮点数
    """
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)

    # 空文本或空特征向量直接判 0，避免除零
    if not norm1 or not norm2:
        return 0.0

    vec1 = ngram_counter(norm1, n)
    vec2 = ngram_counter(norm2, n)
    return cosine_similarity(vec1, vec2)


# ---------------------------------------------------------------------------
# 完整流程
# ---------------------------------------------------------------------------
def check_files(orig_path, plag_path, answer_path):
    """完整查重流程：读文件 -> 算相似度 -> 写答案文件。

    :param orig_path: 原文文件绝对路径
    :param plag_path: 抄袭版文件绝对路径
    :param answer_path: 答案文件绝对路径
    :return: 相似度浮点数
    """
    text1 = read_text_file(orig_path)
    text2 = read_text_file(plag_path)
    similarity = calculate_similarity(text1, text2)
    write_result(similarity, answer_path)
    return similarity
