# RAG Evaluation Dataset & Corpus Documentation

This directory contains the golden dataset, evaluation configuration, benchmark runner, and licensing documentation for the **AI Study Assistant** Retrieval-Augmented Generation (RAG) evaluation harness.

---

## 1. Corpus Documents & Licensing

All 6 documents in `backend/sample_docs/` were generated explicitly for this open-source project or adapted from standard academic open curriculum outlines. No proprietary or copyrighted material is included.

| Document Filename | Subject / Domain | Pages | Description & Role in Benchmark | Source & License |
| :--- | :--- | :---: | :--- | :--- |
| `Operating_Systems_Concurrency.pdf` | Computer Science: Operating Systems | 3 | Process states, threads, PCB, critical section synchronization, mutexes, counting semaphores, and Coffman deadlock conditions. | Synthetic academic course notes authored for project. **License: CC-BY 4.0 / Public Domain**. |
| `Distributed_Systems_Consensus.pdf` | Computer Science: Distributed Systems | 3 | System models, logical vs vector clocks, Paxos, Raft leader election, Two-Phase Commit (2PC), Chandy-Misra-Haas distributed deadlock detection. **Acts as a direct distractor for concurrency and deadlocks.** | Authored via ReportLab with open educational material. **License: CC-BY 4.0 / Public Domain**. |
| `Database_Systems_ACID.pdf` | Computer Science: Databases | 3 | ACID properties, serializability anomalies (dirty/phantom reads), Two-Phase Locking (2PL, Strict 2PL), Wait-Die vs Wound-Wait deadlock prevention, ARIES WAL recovery. **Acts as a direct distractor for concurrency, locking, and deadlocks.** | Authored via ReportLab with open educational material. **License: CC-BY 4.0 / Public Domain**. |
| `Computer_Networking_Protocols.pdf` | Computer Science: Networking | 4 | **Table-heavy structured document**. Contains comprehensive comparison tables for 7-layer OSI model, TCP vs UDP specifications, standard port numbers, dynamic routing protocols (RIP, OSPF, BGP), and IPv4 vs IPv6 headers. Tests retriever handling of tabular and columnar text. | Authored via ReportLab with open educational material. **License: CC-BY 4.0 / Public Domain**. |
| `Principles_of_Macroeconomics.pdf` | Economics & Monetary Policy | 3 | Distinct domain. GDP measurement (expenditure approach, GDP deflator), inflation, 3 types of unemployment, Phillips curve & NAIRU, IS-LM framework, central bank tools (OMO, discount rate, reserve requirements, Quantitative Easing), and Keynesian multiplier. | Authored via ReportLab with open educational material. **License: CC-BY 4.0 / Public Domain**. |
| `Cell_Biology_and_Metabolism.pdf` | Natural Sciences: Molecular Biology | 3 | Distinct domain. Eukaryotic organelle partitioning, enzyme kinetics (Michaelis-Menten), glycolysis stages (PFK-1 committed step), citric acid cycle yields, electron transport chain, chemiosmosis & ATP synthase, and anaerobic fermentation. | Authored via ReportLab with open educational material. **License: CC-BY 4.0 / Public Domain**. |

---

## 2. Golden Dataset Architecture (`golden_dataset.json`)

The golden dataset contains **72 curated evaluation queries** partitioned into two equal, balanced splits:
- **`dev` split (36 queries):** Used during engineering to evaluate and compare chunking configurations (e.g., chunk size, overlap) and tune the abstention similarity threshold.
- **`test` split (36 queries):** Held-out test set evaluated strictly once to report unbiased generalization performance.

### Query Categories

1. **`direct_lookup` (15 queries):** Straightforward factual queries where the answer resides directly in a single chunk (e.g. TCP header minimum size, default OSPF administrative distance).
2. **`paraphrased` (15 queries):** Queries phrased using synonyms, conceptual descriptions, and student language without repeating the exact text or keywords from the source document (e.g., asking about "preventing provisional updates from being viewed before rollback" instead of using "dirty read").
3. **`multi_chunk` (15 queries):** Complex queries requiring synthesis across multiple chunks or distinct pages within the document (e.g., comparing initial ATP investment in glycolysis on page 2 with final oxidative phosphorylation yields on page 3).
4. **`cross_document_distractor` (15 queries):** Queries targeting concepts shared across multiple documents (e.g., Deadlocks in OS vs Deadlocks in DBMS vs Deadlocks in Distributed Systems; 2PL in databases vs 2PC in distributed systems). Designed to stress-test whether semantic embeddings retrieve the correct document or get tricked by near-duplicate vocabulary.
5. **`unanswerable` (12 queries):** Queries on topics completely absent from the corpus (e.g., Quantum computing, Roman aqueducts, French Revolution, Plate tectonics). The correct behavior is to recognize that the information is not in the documents and abstain.

---

## 3. Evaluation Metrics

- **Hit@1 / Hit@3 / Hit@5:** Fraction of answerable queries where the correct source document and page are retrieved within the top 1, 3, or 5 candidates.
- **Mean Reciprocal Rank (MRR):** Average reciprocal rank ($1 / \text{rank}$) of the first relevant chunk.
- **Per-Category Breakdown:** Granular Hit@K and MRR reported individually across the 5 query categories.
- **No-Answer Abstention Accuracy:** Evaluates the cosine similarity threshold $\tau$:
  - Correctly abstains on unanswerable queries (true negative rate).
  - Avoids false rejections on answerable queries (low false positive rate).
- **Latency:** Average end-to-end retrieval time in milliseconds.

---

## 4. Running the Evaluation

To run the offline, deterministic benchmark:
```bash
python -m eval.run
```
Outputs are printed to the terminal and recorded in `backend/eval/results.md`.
