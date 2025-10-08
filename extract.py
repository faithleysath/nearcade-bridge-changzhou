import re

def extract_ordered_tuples(keywords, text):
    """
    从文本中提取 (关键词, 数字) 的元组, 假定关键词总在数字左侧。

    Args:
        keywords (list): 一个包含所有待查找关键词x的字符串列表。
        text (str): 待处理的大段文本。

    Returns:
        list: 一个包含所有提取出的 (关键词, 数字) 元组的列表。
              数字以整数形式存储。
    """
    # 1. 构建组合的正则表达式
    # 第一部分: (关键词1|关键词2|...) - 第1个捕获组
    # 第二部分: .*? - 非贪婪地匹配关键词和数字之间的任意字符
    # 第三部分: (\d+)\s*个?人 - 包含第2个捕获组 (\d+)
    keyword_part = '|'.join(map(re.escape, keywords))
    
    # 完整的正则表达式模式
    # group(1) 将是关键词, group(2) 将是数字
    pattern = re.compile(f"({keyword_part}).*?(\d+)\s*个?人")

    results = []
    # 2. 使用 finditer 遍历文本中的所有匹配项
    for match in pattern.finditer(text):
        # 从匹配对象中提取捕获组
        keyword = match.group(1)
        number = int(match.group(2)) # 将数字字符串转为整数
        
        results.append((keyword, number))
            
    return results

# --- 使用示例 ---
if __name__ == '__main__':
    # 定义你的关键词列表 x
    my_keywords = ['预算', '人力', '实际产出', '测试用例']

    # 你的大段文本
    # 注意：现在关键词必须在数字的左边才能被匹配
    corpus = """
    项目初期，预算 金额为 5000元，需要 人力 10 人。
    到了中期，实际产出 的价值是 8000元，但 人力 消耗了 12 个人。
    这是一个无关的句子。
    我们编写了 测试用例 共计 150个，需要 3人 进行评审。
    有 5个人 提出了关于 预算 的问题。 <--- 这一行不会被匹配，因为数字在关键词左边
    最终的报告显示，实际产出 非常惊人，统计有 100人 受益。
    """

    # 调用函数进行提取
    extracted_data = extract_ordered_tuples(my_keywords, corpus)

    # 打印结果
    print(extracted_data)
    # 预期输出:
    # [('预算', 5000), ('人力', 10), ('实际产出', 8000), ('人力', 12), ('测试用例', 3), ('实际产出', 100)]