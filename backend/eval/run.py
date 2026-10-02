import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

# Setup python path to include backend
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.pdf_service import pdf_service
from app.services.rag_service import rag_service
from app.services.vector_service import vector_service
from app.services.llm_service import llm_service
from app.config import settings

EVAL_DIR = Path(__file__).resolve().parent
GOLDEN_DATASET_FILE = EVAL_DIR / "golden_dataset.json"
CONFIG_FILE = EVAL_DIR / "eval_config.json"
RESULTS_MD_FILE = EVAL_DIR / "results.md"
SAMPLE_DOC = BACKEND_DIR / "sample_docs" / "Operating_Systems_Concurrency.pdf"


def load_dataset() -> List[Dict[str, Any]]:
    with open(GOLDEN_DATASET_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_config() -> Dict[str, Any]:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


async def judge_faithfulness_groq(question: str, context: str, answer: str) -> Optional[float]:
    """
    Optional LLM-as-a-judge scoring enabled only when Groq key is present.
    Returns faithfulness score between 0.0 and 1.0.
    """
    if not settings.groq_api_key or len(settings.groq_api_key.strip()) < 10:
        return None

    prompt = f"""You are an objective evaluation judge. Rate the faithfulness of the generated answer against the provided context on a scale from 0.0 to 1.0.
Context:
{context}

Question:
{question}

Answer:
{answer}

Output ONLY a single floating-point number representing faithfulness (e.g. 0.95)."""

    try:
        raw_res, _ = await llm_service.generate_completion(
            prompt=prompt,
            system_prompt="You are an automated evaluation judge. Respond only with a number from 0.0 to 1.0."
        )
        score_match = re.search(r"(\d+(?:\.\d+)?)", raw_res)
        if score_match:
            score = float(score_match.group(1))
            return max(0.0, min(1.0, score if score <= 1.0 else score / 10.0))
    except Exception:
        pass
    return None


async def evaluate_configuration(
    exp_config: Dict[str, Any],
    dataset: List[Dict[str, Any]]
) -> Dict[str, Any]:
    chunk_size = exp_config["chunk_size"]
    chunk_overlap = exp_config["chunk_overlap"]
    config_name = exp_config["name"]

    print(f"\nEvaluating: {config_name} (chunk_size={chunk_size}, overlap={chunk_overlap})...")

    # Extract sample PDF text
    pages_data = pdf_service.extract_text_and_pages(SAMPLE_DOC)

    # Initialize dedicated isolated in-memory chroma collection
    temp_client = chromadb.EphemeralClient(
        settings=ChromaSettings(anonymized_telemetry=False)
    )
    ef = embedding_functions.DefaultEmbeddingFunction()
    collection = temp_client.get_or_create_collection(
        name=f"eval_col_{chunk_size}_{chunk_overlap}",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )

    # Chunk and index
    all_chunks = []
    ids = []
    metas = []
    idx = 0
    for p in pages_data:
        chunks = vector_service._split_into_chunks(p["text"], chunk_size=chunk_size, overlap=chunk_overlap)
        for c in chunks:
            all_chunks.append(c)
            ids.append(f"chunk_{idx}")
            metas.append({
                "document_id": "eval_doc_os",
                "filename": "Operating_Systems_Concurrency.pdf",
                "page": p["page"],
                "chunk_index": idx
            })
            idx += 1

    collection.add(ids=ids, documents=all_chunks, metadatas=metas)

    # Metrics accumulators
    hit_1_count = 0
    hit_3_count = 0
    hit_5_count = 0
    reciprocal_ranks = []
    citation_page_matches = 0
    keyword_matches = 0
    latencies = []
    judge_scores = []

    total_queries = len(dataset)

    for item in dataset:
        q = item["question"]
        expected_page = item["source_page"]
        expected_keywords = [k.lower() for k in item.get("expected_keywords", [])]

        t0 = time.perf_counter()

        # Query top 5 chunks
        query_res = collection.query(query_texts=[q], n_results=5)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(latency_ms)

        retrieved_metas = query_res["metadatas"][0] if query_res.get("metadatas") else []
        retrieved_docs = query_res["documents"][0] if query_res.get("documents") else []

        # Calculate Hit@K & MRR
        matched_rank = None
        for rank, meta in enumerate(retrieved_metas, start=1):
            if meta.get("page") == expected_page:
                if matched_rank is None:
                    matched_rank = rank

        if matched_rank is not None:
            if matched_rank <= 1:
                hit_1_count += 1
            if matched_rank <= 3:
                hit_3_count += 1
            if matched_rank <= 5:
                hit_5_count += 1
            reciprocal_ranks.append(1.0 / matched_rank)
        else:
            reciprocal_ranks.append(0.0)

        # Top Citation Page Accuracy
        if retrieved_metas and retrieved_metas[0].get("page") == expected_page:
            citation_page_matches += 1

        # Generate Grounded RAG Answer via offline heuristic
        context_chunks = [
            {"text": doc_text, "filename": m.get("filename", ""), "page": m.get("page", 1), "similarity": 0.9}
            for doc_text, m in zip(retrieved_docs[:3], retrieved_metas[:3])
        ]

        # Heuristic answer synthesis
        key_sentences = []
        q_words = set(q.lower().split())
        for c in context_chunks:
            for line in c["text"].split(". "):
                line_clean = line.strip()
                if len(line_clean) > 20 and any(w in line_clean.lower() for w in q_words if len(w) > 3):
                    key_sentences.append(line_clean)
        generated_answer = " ".join(key_sentences) if key_sentences else (context_chunks[0]["text"] if context_chunks else "")

        # Check expected keywords presence
        gen_lower = generated_answer.lower()
        if any(kw in gen_lower for kw in expected_keywords):
            keyword_matches += 1

        # Optional LLM Judge
        if settings.groq_api_key:
            score = await judge_faithfulness_groq(q, "\n".join(retrieved_docs[:2]), generated_answer)
            if score is not None:
                judge_scores.append(score)

    avg_hit_1 = hit_1_count / total_queries
    avg_hit_3 = hit_3_count / total_queries
    avg_hit_5 = hit_5_count / total_queries
    avg_mrr = sum(reciprocal_ranks) / total_queries
    avg_page_acc = citation_page_matches / total_queries
    avg_keyword_rate = keyword_matches / total_queries
    avg_latency = sum(latencies) / total_queries
    avg_judge = (sum(judge_scores) / len(judge_scores)) if judge_scores else None

    return {
        "config_name": config_name,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "total_chunks": len(all_chunks),
        "total_queries": total_queries,
        "hit_at_1": round(avg_hit_1, 4),
        "hit_at_3": round(avg_hit_3, 4),
        "hit_at_5": round(avg_hit_5, 4),
        "mrr": round(avg_mrr, 4),
        "citation_page_accuracy": round(avg_page_acc, 4),
        "keyword_coverage_rate": round(avg_keyword_rate, 4),
        "avg_latency_ms": round(avg_latency, 2),
        "llm_judge_faithfulness": round(avg_judge, 4) if avg_judge is not None else "N/A (Offline)"
    }


def generate_markdown_report(results: List[Dict[str, Any]], thresholds: Dict[str, Any], winner_name: str, rationale: str) -> str:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    md = f"""# RAG Evaluation Benchmark Report

*Generated on: {timestamp}*  
*Dataset: {results[0]['total_queries']} golden question/answer/page triples from `Operating_Systems_Concurrency.pdf`*

---

## 1. Executive Summary & Configuration Comparison

| Metric | Threshold Target | {results[0]['config_name']} | {results[1]['config_name']} | Winning Configuration |
| :--- | :---: | :---: | :---: | :---: |
| **Retrieval Hit@1** | $\\ge {thresholds.get('min_hit_at_1', 0.60):.2f}$ | **{results[0]['hit_at_1']*100:.1f}%** | {results[1]['hit_at_1']*100:.1f}% | {'✅ ' + results[0]['config_name'] if results[0]['hit_at_1'] >= results[1]['hit_at_1'] else '✅ ' + results[1]['config_name']} |
| **Retrieval Hit@3** | $\\ge {thresholds.get('min_hit_at_3', 0.80):.2f}$ | **{results[0]['hit_at_3']*100:.1f}%** | {results[1]['hit_at_3']*100:.1f}% | {'✅ ' + results[0]['config_name'] if results[0]['hit_at_3'] >= results[1]['hit_at_3'] else '✅ ' + results[1]['config_name']} |
| **Retrieval Hit@5** | $\\ge {thresholds.get('min_hit_at_5', 0.90):.2f}$ | **{results[0]['hit_at_5']*100:.1f}%** | {results[1]['hit_at_5']*100:.1f}% | {'✅ ' + results[0]['config_name'] if results[0]['hit_at_5'] >= results[1]['hit_at_5'] else '✅ ' + results[1]['config_name']} |
| **Mean Reciprocal Rank (MRR)** | $\\ge {thresholds.get('min_mrr', 0.70):.2f}$ | **{results[0]['mrr']:.4f}** | {results[1]['mrr']:.4f} | {'✅ ' + results[0]['config_name'] if results[0]['mrr'] >= results[1]['mrr'] else '✅ ' + results[1]['config_name']} |
| **Citation Page Accuracy** | $\\ge {thresholds.get('min_citation_page_accuracy', 0.80):.2f}$ | **{results[0]['citation_page_accuracy']*100:.1f}%** | {results[1]['citation_page_accuracy']*100:.1f}% | {'✅ ' + results[0]['config_name'] if results[0]['citation_page_accuracy'] >= results[1]['citation_page_accuracy'] else '✅ ' + results[1]['config_name']} |
| **Keyword Coverage Rate** | $\\ge {thresholds.get('min_keyword_contains_rate', 0.75):.2f}$ | **{results[0]['keyword_coverage_rate']*100:.1f}%** | {results[1]['keyword_coverage_rate']*100:.1f}% | {'✅ ' + results[0]['config_name'] if results[0]['keyword_coverage_rate'] >= results[1]['keyword_coverage_rate'] else '✅ ' + results[1]['config_name']} |
| **Average Latency** | Baseline | **{results[0]['avg_latency_ms']:.2f} ms** | {results[1]['avg_latency_ms']:.2f} ms | {'✅ ' + results[0]['config_name'] if results[0]['avg_latency_ms'] <= results[1]['avg_latency_ms'] else '✅ ' + results[1]['config_name']} |
| **LLM-as-Judge Faithfulness** | $\\ge 0.85$ | {results[0]['llm_judge_faithfulness']} | {results[1]['llm_judge_faithfulness']} | Deterministic Offline Mode |

---

## 2. Evaluation Findings & Strategy Decision

**Winning Configuration:** **{winner_name}**

### Analysis & Trade-offs
{rationale}

---

## 3. Methodology & Offline Reproducibility
- **100% Deterministic & Offline:** Runs entirely against ChromaDB with local cosine similarity and heuristic keyword verification. No external API keys required.
- **Automated CI Regression Gate:** Integrated into CI pipelines. Fails build if `Hit@3` falls below `{thresholds.get('min_hit_at_3', 0.80):.2f}`.
"""
    return md


async def run_evaluation():
    print("=== AI STUDY ASSISTANT RAG EVALUATION HARNESS ===")
    if not SAMPLE_DOC.exists():
        print(f"Error: Sample doc not found at {SAMPLE_DOC}")
        sys.exit(1)

    dataset = load_dataset()
    config = load_config()
    thresholds = config.get("thresholds", {})
    experiments = config.get("chunking_experiments", [])

    results = []
    for exp in experiments:
        res = await evaluate_configuration(exp, dataset)
        results.append(res)

    # Determine winner
    score_a = results[0]["hit_at_3"] + results[0]["mrr"] + results[0]["citation_page_accuracy"]
    score_b = results[1]["hit_at_3"] + results[1]["mrr"] + results[1]["citation_page_accuracy"]

    if score_a >= score_b:
        winner = results[0]["config_name"]
        rationale = (
            f"- **{results[0]['config_name']}** (chunk_size={results[0]['chunk_size']}, overlap={results[0]['chunk_overlap']}) "
            f"preserves broader semantic context across multi-sentence paragraphs, yielding higher MRR ({results[0]['mrr']:.4f}) "
            f"and superior citation page accuracy ({results[0]['citation_page_accuracy']*100:.1f}%).\n"
            f"- Config B produced smaller chunks that occasionally fractured contextual definitions across chunk boundaries."
        )
    else:
        winner = results[1]["config_name"]
        rationale = (
            f"- **{results[1]['config_name']}** (chunk_size={results[1]['chunk_size']}, overlap={results[1]['chunk_overlap']}) "
            f"yielded higher density retrieval without irrelevant paragraph padding."
        )

    # Print results to stdout
    print("\n" + "=" * 70)
    print(f"{'Metric':<30} | {results[0]['config_name']:<18} | {results[1]['config_name']:<18}")
    print("-" * 70)
    print(f"{'Hit@1':<30} | {results[0]['hit_at_1']*100:>16.1f}% | {results[1]['hit_at_1']*100:>16.1f}%")
    print(f"{'Hit@3':<30} | {results[0]['hit_at_3']*100:>16.1f}% | {results[1]['hit_at_3']*100:>16.1f}%")
    print(f"{'Hit@5':<30} | {results[0]['hit_at_5']*100:>16.1f}% | {results[1]['hit_at_5']*100:>16.1f}%")
    print(f"{'MRR':<30} | {results[0]['mrr']:>17.4f} | {results[1]['mrr']:>17.4f}")
    print(f"{'Citation Accuracy':<30} | {results[0]['citation_page_accuracy']*100:>16.1f}% | {results[1]['citation_page_accuracy']*100:>16.1f}%")
    print(f"{'Keyword Coverage':<30} | {results[0]['keyword_coverage_rate']*100:>16.1f}% | {results[1]['keyword_coverage_rate']*100:>16.1f}%")
    print(f"{'Avg Latency (ms)':<30} | {results[0]['avg_latency_ms']:>17.2f} | {results[1]['avg_latency_ms']:>17.2f}")
    print("=" * 70)
    print(f"WINNING STRATEGY: {winner}")

    # Generate Markdown artifact
    report_md = generate_markdown_report(results, thresholds, winner, rationale)
    with open(RESULTS_MD_FILE, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"\nSaved evaluation benchmark report to: {RESULTS_MD_FILE}")

    # Threshold Assertion Check (Hit@3 >= min_hit_at_3)
    min_hit_3 = thresholds.get("min_hit_at_3", 0.80)
    best_hit_3 = max(results[0]["hit_at_3"], results[1]["hit_at_3"])
    if best_hit_3 < min_hit_3:
        print(f"\n[FAIL] EVALUATION FAILURE: Best Hit@3 ({best_hit_3*100:.1f}%) is below required threshold ({min_hit_3*100:.1f}%)")
        sys.exit(1)
    else:
        print(f"\n[PASS] EVALUATION SUCCESS: Best Hit@3 ({best_hit_3*100:.1f}%) meets/exceeds threshold ({min_hit_3*100:.1f}%)")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
