"""
Text processing utilities.
"""
import re
from typing import List, Tuple


def normalize_text(text: str, lang: str = "zh") -> str:
    """
    Normalize text for comparison.

    Args:
        text: Input text
        lang: Language code (zh, en, mixed)

    Returns:
        Normalized text
    """
    # Remove punctuation
    text = re.sub(r"[^\w\u4e00-\u9fff]", "", text)
    # Lowercase for mixed content
    text = text.lower()
    return text


def tokenize(text: str, lang: str = "zh") -> List[str]:
    """
    Tokenize text into words.

    Args:
        text: Input text
        lang: Language code

    Returns:
        List of tokens
    """
    # Remove punctuation and split
    text = re.sub(r"[^\w\u4e00-\u9fff]", " ", text)
    tokens = text.split()
    return [t.lower() for t in tokens if t]


def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """
    Calculate Jaccard similarity between two texts.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Jaccard similarity score (0-1)
    """
    tokens1 = set(tokenize(text1))
    tokens2 = set(tokenize(text2))

    if not tokens1 or not tokens2:
        return 0.0

    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)

    return intersection / union if union > 0 else 0.0


def calculate_lcs_ratio(text1: str, text2: str) -> float:
    """
    Calculate longest common subsequence ratio.

    Args:
        text1: First text
        text2: Second text

    Returns:
        LCS ratio (0-1)
    """
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)

    if not tokens1 or not tokens2:
        return 0.0

    m, n = len(tokens1), len(tokens2)

    # DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if tokens1[i-1] == tokens2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])

    lcs_length = dp[m][n]
    max_len = max(m, n)

    return lcs_length / max_len if max_len > 0 else 0.0


def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """
    Extract keywords from text.

    Args:
        text: Input text
        max_keywords: Maximum number of keywords

    Returns:
        List of keywords
    """
    tokens = tokenize(text)

    # Remove common stopwords
    stopwords = {"的", "是", "在", "了", "和", "与", "或", "以及", "the", "a", "an", "is", "are", "and", "or"}
    tokens = [t for t in tokens if t not in stopwords and len(t) > 1]

    # Count frequency
    freq = {}
    for token in tokens:
        freq[token] = freq.get(token, 0) + 1

    # Sort by frequency
    sorted_tokens = sorted(freq.items(), key=lambda x: x[1], reverse=True)

    return [t[0] for t in sorted_tokens[:max_keywords]]


def calculate_text_similarity(text1: str, text2: str, method: str = "jaccard") -> float:
    """
    Calculate text similarity using specified method.

    Args:
        text1: First text
        text2: Second text
        method: Similarity method ("jaccard" or "lcs")

    Returns:
        Similarity score (0-1)
    """
    if method == "jaccard":
        return calculate_jaccard_similarity(text1, text2)
    elif method == "lcs":
        return calculate_lcs_ratio(text1, text2)
    else:
        raise ValueError(f"Unknown method: {method}")


def remove_filler_words(text: str, filler_words: List[str] = None) -> str:
    """
    Remove filler words from text.

    Args:
        text: Input text
        filler_words: List of filler words to remove

    Returns:
        Text with filler words removed
    """
    if filler_words is None:
        filler_words = ["嗯", "啊", "这个", "那个", "就是说"]

    for filler in filler_words:
        text = text.replace(filler, "")

    # Clean up extra spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()
