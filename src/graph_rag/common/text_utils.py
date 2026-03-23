import re
from typing import List


'''⭐ 升级1：用 nltk / spacy
lemmatization
stemming
NER
⭐ 升级2：短语提取
"graph database" → 一个term
⭐ 升级3：TF-IDF过滤
去掉低信息词
⭐ 升级4：embedding-based terms（高级）'''


STOPWORDS = {
    "the", "a", "an", "is", "are", "of", "to", "and", "or", "in", "on", "for",
    "with", "by", "as", "at", "from", "that", "this"
}

def extract_terms(text: str) -> List[str]:
    '''
    把一段文本，提取成“干净的关键词列表”
    文本 --> 小写 --> 正则切词 --> 去停用词 --> 去重 --> 返回terms列表
    这段代码的局限:
    1. 不支持中文; 2. 没有词干处理; 3. 没有实体识别; 4. 太简单
    '''
    if not text:
        return []
    tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    # re.findall(规则, 字符串)
    # 👉 返回：所有符合规则的“片段” 
    # 匹配：连续的字母 / 数字 / 下划线
    results = []
    seen = set()

    for token in tokens:
        if len(token) < 2:
            continue
        if token in STOPWORDS:
            continue
        if token in seen:
            continue
        seen.add(token)
        results.append(token)

    return results