# -*- coding: utf-8 -*-
"""
论文查重程序单元测试
====================
运行方式：
    python -m unittest discover -s tests -v

共 15 个测试用例，覆盖：
    - 文本预处理（去空白标点、全角转半角）
    - n-gram 统计与非法参数
    - 余弦相似度与空向量
    - 正常 / 边界 / 异常输入
    - 端到端文件读写与命令行入口
"""

import os
import sys
import unittest

# 把项目根目录加入 import 路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from plagiarism_checker import (  # noqa: E402
    normalize_text,
    ngram_counter,
    cosine_similarity,
    calculate_similarity,
    read_text_file,
    write_result,
    check_files,
)
from collections import Counter  # noqa: E402

import main as entry  # noqa: E402


class TestNormalize(unittest.TestCase):
    """文本预处理相关测试。"""

    def test_01_normalize_removes_spaces_and_punctuation(self):
        """验证空格、标点被去除，只保留有效字符。"""
        raw = "今天是星期天，天气晴。 今天晚上我要去看电影！"
        result = normalize_text(raw)
        self.assertNotIn("，", result)
        self.assertNotIn("。", result)
        self.assertNotIn(" ", result)
        self.assertIn("今天是星期天天气晴", result)

    def test_02_normalize_unifies_full_width_characters(self):
        """验证全角字符被 NFKC 归一化为半角。"""
        raw = "Ｈｅｌｌｏ１２３"   # 全字母全角数字
        result = normalize_text(raw)
        self.assertEqual(result, "Hello123")

    def test_03_normalize_empty_string(self):
        """验证空字符串返回空串。"""
        self.assertEqual(normalize_text(""), "")


class TestNgram(unittest.TestCase):
    """n-gram 特征相关测试。"""

    def test_04_ngram_counter_counts_bigrams(self):
        """验证二元字符 gram 的数量与内容。"""
        vec = ngram_counter("今天天气", n=2)
        self.assertEqual(vec, Counter({"今天": 1, "天天": 1, "天气": 1}))

    def test_05_ngram_counter_rejects_invalid_n(self):
        """验证 n<1 时抛出 ValueError。"""
        with self.assertRaises(ValueError):
            ngram_counter("abc", n=0)

    def test_06_ngram_short_text_returns_empty(self):
        """验证文本长度小于 n 时返回空 Counter。"""
        self.assertEqual(ngram_counter("ab", n=3), Counter())


class TestSimilarity(unittest.TestCase):
    """相似度计算相关测试。"""

    def test_07_identical_text_returns_one(self):
        """完全相同文本相似度应为 1.0。"""
        text = "今天是星期天，天气晴，今天晚上我要去看电影。"
        self.assertAlmostEqual(calculate_similarity(text, text), 1.0, places=4)

    def test_08_empty_text_returns_zero(self):
        """空文本与任意文本相似度为 0。"""
        self.assertEqual(calculate_similarity("", "今天天气"), 0.0)
        self.assertEqual(calculate_similarity("今天天气", ""), 0.0)

    def test_09_completely_different_text_is_low(self):
        """完全无关文本相似度应很低。"""
        s1 = "aaaaaaaaaaaa"
        s2 = "bbbbbbbbbbbb"
        self.assertLess(calculate_similarity(s1, s2), 0.01)

    def test_10_assignment_example_is_similar(self):
        """验证题目给出的示例：改写后仍应高度相似。"""
        orig = "今天是星期天，天气晴，今天晚上我要去看电影。"
        plag = "今天是周天，天气晴朗，我晚上要去看电影。"
        score = calculate_similarity(orig, plag)
        # 示例语义高度重合，相似度应明显大于 0.5
        self.assertGreater(score, 0.5)
        self.assertLess(score, 1.0)

    def test_11_cosine_similarity_empty_vector(self):
        """验证空向量余弦相似度为 0，不除零。"""
        self.assertEqual(cosine_similarity(Counter(), Counter()), 0.0)
        self.assertEqual(cosine_similarity(Counter({"a": 1}), Counter()), 0.0)


class TestFileIO(unittest.TestCase):
    """文件读写与端到端测试。"""

    def setUp(self):
        self.tmpdir = os.path.join(PROJECT_ROOT, "tests", "tmp_io")
        os.makedirs(self.tmpdir, exist_ok=True)

    def tearDown(self):
        for name in os.listdir(self.tmpdir):
            os.remove(os.path.join(self.tmpdir, name))
        os.rmdir(self.tmpdir)

    def test_12_write_result_has_two_decimal_places(self):
        """验证答案文件只写两位小数浮点数。"""
        answer = os.path.join(self.tmpdir, "ans.txt")
        write_result(0.8, answer)
        with open(answer, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "0.80")

    def test_13_missing_file_raises_error(self):
        """验证读取不存在文件抛出 FileNotFoundError。"""
        with self.assertRaises(FileNotFoundError):
            read_text_file(os.path.join(self.tmpdir, "no_such_file.txt"))

    def test_14_check_files_end_to_end(self):
        """验证完整文件查重流程：写两个文本 -> 跑流程 -> 读答案。"""
        orig = os.path.join(self.tmpdir, "orig.txt")
        plag = os.path.join(self.tmpdir, "plag.txt")
        answer = os.path.join(self.tmpdir, "ans.txt")
        with open(orig, "w", encoding="utf-8") as f:
            f.write("今天是星期天，天气晴，今天晚上我要去看电影。")
        with open(plag, "w", encoding="utf-8") as f:
            f.write("今天是周天，天气晴朗，我晚上要去看电影。")

        score = check_files(orig, plag, answer)
        self.assertGreater(score, 0.5)
        with open(answer, "r", encoding="utf-8") as f:
            saved = f.read()
        # 答案文件内容长度应为 4 位（如 0.85）
        self.assertEqual(len(saved), 4)

    def test_15_main_rejects_wrong_argument_count(self):
        """验证命令行参数数量错误时 main 返回 1 且不崩溃。"""
        ret = entry.main(["main.py", "only_one_arg"])
        self.assertEqual(ret, 1)

    def test_16_main_creates_answer_file(self):
        """验证 main 在参数齐全时正确生成答案文件。"""
        orig = os.path.join(self.tmpdir, "o.txt")
        plag = os.path.join(self.tmpdir, "p.txt")
        answer = os.path.join(self.tmpdir, "a.txt")
        with open(orig, "w", encoding="utf-8") as f:
            f.write("hello world")
        with open(plag, "w", encoding="utf-8") as f:
            f.write("hello world")
        ret = entry.main(["main.py", orig, plag, answer])
        self.assertEqual(ret, 0)
        self.assertTrue(os.path.isfile(answer))
        with open(answer, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "1.00")

    def test_17_main_missing_file_returns_error(self):
        """验证 main 遇到不存在的输入文件时返回 1 且不崩溃。"""
        ghost = os.path.join(self.tmpdir, "ghost.txt")
        ret = entry.main(["main.py", ghost, ghost,
                          os.path.join(self.tmpdir, "a.txt")])
        self.assertEqual(ret, 1)


if __name__ == "__main__":
    unittest.main()
