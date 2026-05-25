#!/usr/bin/env python3
"""
BriefSignal 知乎文章质量评分器 v2
改进：
  1. 深度 → 中文原生指标（句长/句数/段落/词汇丰富度/逻辑词密度）
  2. 权威 → E-E-A-T 框架
  3. 实操 → 领域特化
  4. 标题 → 标题党检测
  5. 置信度 → Wilson-style 低样本惩罚

输入：zhihu_search API JSON (stdin)
"""

from __future__ import annotations
import json, sys, re
from typing import Any

# ════════════════════════ 配置 ════════════════════════

DOMAIN_AUTHORITY = {
    "zhuanlan.zhihu.com": 7,
    "www.zhihu.com": 6,
    "github.com": 8, "arxiv.org": 9,
    "nature.com": 10, "science.org": 10,
}

LOW_DOMAINS = {
    "csdn.net": -4, "gitcode.csdn.net": -5, "devpress.csdn.net": -5,
    "book118.com": -5, "doc88.com": -5,
    "sohu.com": -3, "163.com": -3,
}

CLICKBAIT = [
    r"烂大街", r"炸裂", r"疯了", r"彻底.*了", r"看这一篇就够了",
    r"不看后悔", r"全网最全", r"重磅", r"震惊", r"跪了",
    r"必看", r"建议收藏", r"绝了", r"刷爆", r"逆天",
    r"白干", r"劝退", r"天花板", r"封神", r"杀疯了",
]

ACTION_KW = [
    r"(第[一二三四五六七八九十\d]+)[步阶段章]",
    r"\d+[.、）\)]\s",
    r"(怎么做|如何做|怎么学|如何学|怎么练)",
    r"(建议|推荐|方案|路线|路径|清单|框架|方法论)",
    r"(项目|案例|实战|练习|动手|落地|实操)",
    r"\d+\s*(?:个月|周|天|小时|分钟|年)",
    r"(总结|结论|核心|关键|重点|要点)",
]

PERSONAL_KW = [
    r"(我认为|我的建议|我的经验|我推荐|我总结|我发现)",
    r"(我.*(?:做过|写过|用过|踩过|试过|经历过))",
    r"(个人认为|我的看法|我的判断|在我看来)",
]

TRUST_KW = [
    r"(https?://)", r"(arxiv|paper|论文|研究|实验|数据|统计|报告)",
    r"(\d+%|\d+\.\d+%|\d+亿|\d+万)",
    r"(根据|依据|来源|引用|参考|据)",
]

LOGIC_KW = [
    r"(首先|其次|然后|最后|接着|此外|另外)",
    r"(因此|所以|因为|由于|从而|导致)",
    r"(但是|然而|不过|虽然|尽管|无论)",
    r"(例如|比如|譬如|举例|具体来说)",
    r"(总之|综上所述|归根结底|总体而言)",
]

# ════════════════════════ 评分函数 ════════════════════════

def score_depth(text: str) -> tuple[float, dict]:
    """深度维度 (0-40) — 中文原生"""
    d = {}
    if len(text) < 80:
        return 3.0, {"chars": len(text), "note": "过短"}

    wc = len(text)
    d["chars"] = wc
    score = 0.0

    # 1. 字数基础分
    if wc >= 1000: score += 12
    elif wc >= 700: score += 10
    elif wc >= 400: score += 7
    elif wc >= 200: score += 4
    else: score += 2

    # 2. 句子分析
    sentences = [s.strip() for s in re.split(r'[。！？；\n]', text) if len(s.strip()) > 2]
    d["sentences"] = len(sentences)
    if sentences:
        avg_len = sum(len(s) for s in sentences) / len(sentences)
        d["avg_sent_len"] = round(avg_len, 1)
        # 技术文章理想句长 15-35 字
        if 15 <= avg_len <= 35: score += 8
        elif 10 <= avg_len <= 45: score += 5
        else: score += 2

    # 3. 词汇丰富度 (TTR)
    words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', text)
    d["unique_terms"] = len(set(words))
    if words and len(words) > 10:
        ttr = len(set(words)) / len(words)
        d["ttr"] = round(ttr, 3)
        if ttr > 0.55: score += 8
        elif ttr > 0.35: score += 5
        else: score += 2

    # 4. 段落结构
    paragraphs = [p for p in text.split('\n') if len(p.strip()) > 10]
    d["paragraphs"] = len(paragraphs)
    if len(paragraphs) >= 8: score += 6
    elif len(paragraphs) >= 4: score += 3

    # 5. 逻辑词密度（思维深度指标）
    logic_count = sum(len(re.findall(p, text)) for p in LOGIC_KW)
    d["logic_signals"] = logic_count
    if logic_count >= 8: score += 6
    elif logic_count >= 4: score += 3

    return min(score, 40), d


def score_authority(item: dict, text: str) -> tuple[float, dict]:
    """E-E-A-T 权威 (0-30)"""
    d = {}
    url = item.get("Url", "")
    score = 10.0

    for dom, boost in DOMAIN_AUTHORITY.items():
        if dom in url:
            score += boost
            d["domain"] = dom
            break

    for dom, penalty in LOW_DOMAINS.items():
        if dom in url:
            score += penalty
            d["low_domain"] = dom
            break

    trust = sum(len(re.findall(p, text)) for p in TRUST_KW)
    d["trust"] = trust
    if trust >= 5: score += 6
    elif trust >= 2: score += 3

    personal = sum(len(re.findall(p, text)) for p in PERSONAL_KW)
    d["personal"] = personal
    if personal >= 3: score += 6
    elif personal >= 1: score += 3

    ct = item.get("ContentType", "")
    score += 3 if ct == "Article" else 2 if ct == "Answer" else 0

    return max(0, min(score, 30)), d


def score_action(text: str) -> tuple[float, dict]:
    """实操 (0-20)"""
    d = {}
    matches = sum(len(re.findall(p, text)) for p in ACTION_KW)
    d["matches"] = matches
    score = 18 if matches >= 8 else 14 if matches >= 5 else 10 if matches >= 2 else 5 if matches >= 1 else 0
    return score, d


def score_title(item: dict) -> tuple[float, dict]:
    """标题健康 (0-10)"""
    d = {}
    title = item.get("Title", "")
    score = 10.0
    for pat in CLICKBAIT:
        if re.search(pat, title):
            score -= 3
            d.setdefault("bad", []).append(pat)
    q = title.count("？") + title.count("?")
    if q >= 3: score -= 2
    elif q >= 2: score -= 1
    if title.count("！") + title.count("!") >= 2: score -= 2
    if len(title) > 70: score -= 1
    return max(0, score), d


def confidence_penalty(item: dict) -> float:
    """Wilson-style 低样本惩罚"""
    wc = len(item.get("ContentText", ""))
    if wc >= 600: return 0
    if wc >= 300: return -3
    if wc >= 150: return -7
    return -12


def grade(total: float) -> str:
    if total >= 72: return "A"
    if total >= 56: return "B"
    if total >= 36: return "C"
    return "D"


# ════════════════════════ 主流程 ════════════════════════

def load_items() -> list[dict]:
    data = json.load(sys.stdin)
    items = data.get("Data", {}).get("Items", [])
    return items or data.get("items", [])


def main():
    items = load_items()
    print(f"📊 知乎质量评分 v2 ({len(items)} 篇)\n")
    print(f"{'等':<4} {'总':<5} {'深度':<5} {'权威':<5} {'实操':<5} {'标题':<5} {'字数':<5}  标题")
    print("─" * 85)

    results = []
    for item in items:
        text = item.get("ContentText", "") or item.get("summary", "")
        title = item.get("Title", "") or ""
        url = item.get("Url", "")

        r, rd = score_depth(text)
        a, ad = score_authority(item, text)
        ac, acd = score_action(text)
        t, td = score_title(item)
        cp = confidence_penalty(item)
        total = r + a + ac + t + cp
        g = grade(total)
        wc = len(text)

        results.append({
            "title": title, "url": url.split("?")[0],
            "total": total, "grade": g,
            "depth": r, "authority": a,
            "action": ac, "title_score": t,
            "penalty": cp, "chars": wc,
            "details": {**rd, **ad, **acd, **td}
        })

        print(f"{g:<4} {total:<5.0f} {r:<5.0f} {a:<5.0f} {ac:<5.0f} {t:<5.0f} {wc:<5}   {title[:50]}")

    counts = {g: sum(1 for r in results if r["grade"] == g) for g in "ABCD"}
    print(f"\n✅ A:{counts.get('A',0)}  🟡 B:{counts.get('B',0)}  🟠 C:{counts.get('C',0)}  ❌ D:{counts.get('D',0)}")
    print("\n推荐 (A级):")
    for r in results:
        if r["grade"] == "A":
            print(f"  [{r['grade']}{r['total']:.0f}] {r['title'][:75]}")
            print(f"       {r['url']}")

    return results


if __name__ == "__main__":
    main()
