# -*- coding: utf-8 -*-
"""
ESG text commitment-action analysis.
Extracts and classifies sentences from ESG report text into:
  - Commitments (promises, targets, pledges)
  - Actions (implemented measures, completed projects)
Computes Commitment-Fulfillment Ratio (CFR) for GWI index.
"""
import pandas as pd, numpy as np, os, re, json
from collections import Counter

# === Commitment & Action Keyword Dictionaries ===
COMMITMENT_KEYWORDS = [
    # Chinese commitment indicators
    "承诺", "目标", "计划", "致力于", "力争", "确保", "推动",
    "将要", "预期", "规划", "战略", "愿景", "展望", "布局",
    "拟投资", "拟建设", "拟推进", "加快", "加大", "持续提升",
    "不断优化", "进一步", "深入贯彻", "积极践行", "强化",
    "打造", "构建", "建立", "完善", "推进", "促进",
    # English equivalents
    "commit", "target", "goal", "plan to", "aim to", "will achieve",
    "strive to", "pursue", "objective", "initiative", "roadmap",
    "pledge", "promise", "aspire", "envision", "intend to"
]

ACTION_KEYWORDS = [
    # Chinese action indicators (completed/ongoing concrete actions)
    "已完成", "已建成", "已投入", "已实现", "已获得", "已通过",
    "达标", "减排", "降低", "减少", "节约", "回收", "利用",
    "改造", "升级", "安装", "建设了", "投运", "发电",
    "植树", "治理", "监测", "认证", "获评", "获证",
    "实际", "共计", "累计", "年度", "全年", "当年",
    # Past tense / completed indicators
    "完成了", "达到了", "实现了", "超过了", "建成了",
    "比上年", "同比下降", "同比上升", "环比", "提升了",
    # English equivalents
    "achieved", "reduced", "completed", "installed", "implemented",
    "decreased", "saved", "recycled", "certified", "launched",
    "operational", "in operation", "generated", "treated"
]

def analyze_esg_text(text, company_name=""):
    """Analyze ESG text for commitment vs action patterns."""
    if not text or len(text) < 200:
        return {"total_chars": 0, "error": "text too short"}
    
    # Split into sentences (Chinese + English aware)
    sentences = re.split(r'[。！？；\n\.\!\?\;]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    
    total_sentences = len(sentences)
    commitment_sentences = []
    action_sentences = []
    commitment_count = 0
    action_count = 0
    
    for sent in sentences:
        sent_lower = sent.lower()
        has_commit = any(kw.lower() in sent_lower for kw in COMMITMENT_KEYWORDS)
        has_action = any(kw.lower() in sent_lower for kw in ACTION_KEYWORDS)
        
        if has_commit:
            commitment_count += 1
            commitment_sentences.append(sent)
        if has_action:
            action_count += 1
            action_sentences.append(sent)
    
    # Compute Commitment-Fulfillment Ratio (CFR)
    # CFR = action_sentences / (commitment_sentences + action_sentences)
    # High CFR = more action than talk (genuine), Low CFR = more talk than action (potential greenwash)
    both = commitment_count + action_count
    cfr = action_count / both if both > 0 else 0.5  # Neutral if no data
    cfr = round(cfr, 4)
    
    # Additional metrics
    commitment_ratio = commitment_count / total_sentences if total_sentences > 0 else 0
    action_ratio = action_count / total_sentences if total_sentences > 0 else 0
    
    # Keyword frequency
    all_words = []
    for kw in COMMITMENT_KEYWORDS + ACTION_KEYWORDS:
        count = text.lower().count(kw.lower())
        if count > 0:
            all_words.extend([kw] * count)
    keyword_freq = Counter(all_words).most_common(20)
    
    return {
        "total_chars": len(text),
        "total_sentences": total_sentences,
        "commitment_count": commitment_count,
        "action_count": action_count,
        "cfr": cfr,
        "commitment_ratio": round(commitment_ratio, 4),
        "action_ratio": round(action_ratio, 4),
        "top_keywords": dict(keyword_freq[:10]),
        "sample_commitments": commitment_sentences[:3],
        "sample_actions": action_sentences[:3],
    }

if __name__ == "__main__":
    # Test with a sample text
    sample = """
    本公司承诺到2025年实现碳排放强度降低20%。公司已完成3个光伏项目，装机容量达500MW。
    2020年全年减排二氧化碳10万吨，比上年降低15%。我们计划进一步加大清洁能源投资，
    力争2023年清洁能源占比达到50%。目前已建成污水处理设施3座，年处理能力200万吨。
    持续推进绿色工厂建设，已获得国家级绿色工厂认证。未来将构建完善的碳管理体系。
    """
    result = analyze_esg_text(sample)
    print("Sample ESG Analysis:")
    for k, v in result.items():
        if k not in ["sample_commitments", "sample_actions"]:
            print(f"  {k}: {v}")
    
    print(f"\nReady. Load ESG text from pdfplumber output and call analyze_esg_text().")
    print(f"Key output: CFR (Commitment-Fulfillment Ratio) for GWI construction.")
