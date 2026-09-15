# -*- coding: utf-8 -*-
"""
论文查重程序入口
================
用法：
    python main.py <原文文件绝对路径> <抄袭版论文文件绝对路径> <答案文件绝对路径>

说明：
    - 接收三个命令行参数，分别为原文、抄袭版、答案文件路径；
    - 计算两篇文本相似度，结果以两位小数写入答案文件；
    - 答案文件只保存浮点数（如 0.80），不含任何多余文字。
"""

import sys

from plagiarism_checker import check_files


def main(argv):
    """程序主入口。

    :param argv: 命令行参数列表，argv[0] 为脚本名
    :return: 退出码，0 表示成功
    """
    if len(argv) != 4:
        print("用法：python main.py <原文文件绝对路径> "
              "<抄袭版论文文件绝对路径> <答案文件绝对路径>")
        return 1

    orig_path = argv[1]
    plag_path = argv[2]
    answer_path = argv[3]

    try:
        similarity = check_files(orig_path, plag_path, answer_path)
    except FileNotFoundError as e:
        print(f"错误：{e}")
        return 1
    except ValueError as e:
        print(f"错误：参数不合法 -> {e}")
        return 1
    except OSError as e:
        print(f"错误：文件读写失败 -> {e}")
        return 1

    # 控制台同时打印一次结果，方便手动测试
    print(f"{similarity:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
