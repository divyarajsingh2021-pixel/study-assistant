# RAG Evaluation Benchmark Report

*Generated on: 2026-10-02 11:22:44*  
*Dataset: 25 golden question/answer/page triples from `Operating_Systems_Concurrency.pdf`*

---

## 1. Executive Summary & Configuration Comparison

| Metric | Threshold Target | Config A (Balanced) | Config B (Fine-Grained) | Winning Configuration |
| :--- | :---: | :---: | :---: | :---: |
| **Retrieval Hit@1** | $\ge 0.60$ | **96.0%** | 100.0% | ✅ Config B (Fine-Grained) |
| **Retrieval Hit@3** | $\ge 0.80$ | **100.0%** | 100.0% | ✅ Config A (Balanced) |
| **Retrieval Hit@5** | $\ge 0.90$ | **100.0%** | 100.0% | ✅ Config A (Balanced) |
| **Mean Reciprocal Rank (MRR)** | $\ge 0.70$ | **0.9800** | 1.0000 | ✅ Config B (Fine-Grained) |
| **Citation Page Accuracy** | $\ge 0.80$ | **96.0%** | 100.0% | ✅ Config B (Fine-Grained) |
| **Keyword Coverage Rate** | $\ge 0.75$ | **92.0%** | 88.0% | ✅ Config A (Balanced) |
| **Average Latency** | Baseline | **588.00 ms** | 576.60 ms | ✅ Config B (Fine-Grained) |
| **LLM-as-Judge Faithfulness** | $\ge 0.85$ | N/A (Offline) | N/A (Offline) | Deterministic Offline Mode |

---

## 2. Evaluation Findings & Strategy Decision

**Winning Configuration:** **Config B (Fine-Grained)**

### Analysis & Trade-offs
- **Config B (Fine-Grained)** (chunk_size=400, overlap=80) yielded higher density retrieval without irrelevant paragraph padding.

---

## 3. Methodology & Offline Reproducibility
- **100% Deterministic & Offline:** Runs entirely against ChromaDB with local cosine similarity and heuristic keyword verification. No external API keys required.
- **Automated CI Regression Gate:** Integrated into CI pipelines. Fails build if `Hit@3` falls below `0.80`.
