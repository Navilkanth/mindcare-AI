"""
MindCare AI — Psychology Knowledge Base & Evidence-Based Retrieval
Retrieves relevant clinical concepts, therapeutic frameworks (CBT, DBT, Schema, Attachment),
and peer-reviewed articles from the psychology catalog to ground AI responses.
"""
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

KB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "psychology_knowledge.json")
_kb_cache: Optional[Dict[str, Any]] = None

# Synonym expansion for common emotional expressions to clinical terms
SYNONYMS = {
    "overthinking": ["rumination", "worry", "cognitive distortions", "anxiety", "hypervigilance"],
    "stressed": ["stress", "burnout", "exhaustion", "somatic", "relaxation"],
    "sad": ["depression", "grief", "hopelessness", "loss", "mood"],
    "anxious": ["anxiety", "panic", "social anxiety", "avoidance", "fear"],
    "lonely": ["isolation", "attachment", "connection", "belonging"],
    "unmotivated": ["behavioral activation", "procrastination", "depression", "fatigue"],
    "relationship": ["attachment", "couples", "communication", "codependency", "hypervigilance"],
    "anger": ["emotional regulation", "frustration", "temper", "impulse"],
    "worthless": ["schema", "self-esteem", "defectiveness", "inner critic", "cbt"],
    "panic": ["panic disorder", "hyperventilation", "grounding", "somatization"],
    "sleep": ["insomnia", "circadian", "sleep hygiene", "rumination"],
}


def load_kb() -> Dict[str, Any]:
    """Load cached psychology knowledge base (concepts, articles, books)."""
    global _kb_cache
    if _kb_cache is not None:
        return _kb_cache

    if os.path.exists(KB_PATH):
        try:
            with open(KB_PATH, "r", encoding="utf-8") as f:
                _kb_cache = json.load(f)
                return _kb_cache
        except Exception as e:
            logger.error("Failed to load psychology knowledge base: %s", e)

    return {"concepts": [], "articles": [], "books": []}


def retrieve_clinical_context(user_query: str) -> str:
    """
    Search articles and clinical concepts relevant to the user's situation.
    Returns a structured context block to be injected into the system prompt.
    """
    kb = load_kb()
    query_lower = user_query.lower()

    # Extract query words
    words = set(re.findall(r"\b[a-zA-Z]{3,}\b", query_lower))

    # Add clinical synonyms
    expanded_words = set(words)
    for trigger, syns in SYNONYMS.items():
        if trigger in query_lower or any(w.startswith(trigger[:4]) for w in words):
            expanded_words.update(syns)

    # 1. Match Articles
    article_scores = []
    for art in kb.get("articles", []):
        score = 0
        title = (art.get("title") or "").lower()
        desc = (art.get("description") or "").lower()
        content = title + " " + desc

        for w in expanded_words:
            if re.search(r"\b" + re.escape(w) + r"\b", title):
                score += 3
            elif w in content:
                score += 1

        if score > 0:
            article_scores.append((score, art))

    article_scores.sort(key=lambda x: x[0], reverse=True)
    top_articles = [item[1] for item in article_scores[:2]]

    # 2. Match Clinical Concepts
    concept_scores = []
    for concept in kb.get("concepts", []):
        score = 0
        name = (concept.get("name") or "").lower()
        short_name = (concept.get("shortName") or "").lower()
        desc = (concept.get("description") or "").lower()
        cat = (concept.get("category") or "").lower()
        full_concept = f"{name} {short_name} {desc} {cat}"

        for w in expanded_words:
            if w in short_name or w in name:
                score += 3
            elif w in full_concept:
                score += 1

        if score > 0:
            concept_scores.append((score, concept))

    concept_scores.sort(key=lambda x: x[0], reverse=True)
    top_concepts = [item[1] for item in concept_scores[:2]]

    # If no specific matches, provide standard foundational CBT & Mindfulness concepts
    if not top_articles and not top_concepts:
        return ""

    context_lines = ["\n--- CLINICAL PSYCHOLOGY REFERENCES & THERAPEUTIC EVIDENCE ---"]
    if top_concepts:
        context_lines.append("Relevant Clinical Concepts & Frameworks:")
        for c in top_concepts:
            name = c.get("shortName") or c.get("name")
            desc = c.get("description") or ""
            authors = ", ".join(c.get("authors", []))
            author_str = f" ({authors})" if authors else ""
            context_lines.append(f"• Concept: {name}{author_str} — {desc}")

    if top_articles:
        context_lines.append("\nRelevant Clinical Articles & Solutions:")
        for a in top_articles:
            title = a.get("title")
            desc = a.get("description") or ""
            author = a.get("author") or "Clinical Psychology Reference"
            url = a.get("url") or ""
            context_lines.append(f"• Article: \"{title}\" by {author}")
            if desc:
                context_lines.append(f"  Summary: {desc}")
            if url:
                context_lines.append(f"  Reference URL: {url}")

    context_lines.append(
        "Therapeutic Instruction: Use these clinical insights to explain the psychological mechanism gently to the user, validate what they are experiencing, offer step-by-step evidence-based exercises (e.g. CBT cognitive reframing, mindfulness grounding, or schema awareness), and recommend the article or concept reference where appropriate."
    )
    context_lines.append("-------------------------------------------------------------\n")

    return "\n".join(context_lines)
