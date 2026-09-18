# Automated LLM Red-Teaming & Safety Evaluation Harness

An automated framework built in Python to evaluate the adversarial resilience and safety boundaries of Large Language Models (LLMs) against standard and novel jailbreak techniques.

---

## 📌 Overview

Safety evaluation often relies on manual prompt engineering or small, non-standardized test sets. This project implements a scalable, automated pipeline that ingests standard benchmarks, applies adversarial mutations, queries a target model via a resilient API client, and audits outputs using a dual-stage hybrid evaluator.

---

## 🚀 Key Features

- **Unified Multi-Benchmark Dataset**: Ingests, normalizes, and deduplicates benchmark behaviors from **JBB-Behaviors** and **AdvBench**, compiling a master pool of over 600 unique harmful behaviors.
- **Resilient API Architecture**: Implements an execution wrapper with **Exponential Backoff and Randomized Jitter** to manage API rate limits (`429`) and server overloads (`503`) without interrupting runs.
- **Hybrid Safety Evaluator (Dual-Stage Auditor)**: Reduces API latency and cost by applying a fast Stage 1 heuristic filter for clear refusals, routing borderline cases to a Stage 2 LLM reasoning judge.
- **5 Evaluation Vectors**:
  1. *None (Baseline)*: Direct, unmutated queries.
  2. *Base64 Obfuscation*: Encoded instructions to bypass static string filters.
  3. *Roleplay (DAN)*: Adversarial persona adoption framing.
  4. *Many-Shot Jailbreaking*: In-context compliance priming via simulated dialogue turns.
  5. *Content Concretization (CC)*: A two-model pipeline testing the "generate vs. refine" alignment gap (based on Wahréus et al., GameSec 2025).
- **Interactive Dashboard**: A local and cloud-ready **Streamlit** interface (`app.py`) for inspecting metrics, viewing vulnerability distributions, and reading raw prompt-response pairs.

---

## 📊 Empirical Findings: Qwen-27B

We conducted an automated evaluation across 100 test trials (20 master behaviors evaluated across all 5 attack vectors) targeting `qwen/qwen3.8-27b` using `openai/gpt-oss-20b` as the seed generator for Content Concretization.

### Vulnerability Leaderboard

| Attack Type | Total Attempts | Successful Bypasses | Successful Refusals | Attack Success Rate (ASR %) |
| :--- | :---: | :---: | :---: | :---: |
| **Base64 Encoding** | 20 | 1 | 19 | **5.0%** |
| **Content Concretization** | 20 | 1 | 19 | **5.0%** |
| **Many-Shot Jailbreak** | 20 | 0 | 20 | **0.0%** |
| **None (Baseline)** | 20 | 0 | 20 | **0.0%** |
| **Roleplay (DAN)** | 20 | 0 | 20 | **0.0%** |

![Vulnerability Profile](vulnerability_report.png)

---

## 💡 Key Takeaways

1. **The "Generate vs. Refine" Gap Is Real**: 
   The model maintained a 0.0% ASR against direct harmful queries, but yielded a 5.0% ASR under Content Concretization. This supports recent findings (GameSec 2025) showing that safety filters are less sensitive to requests asking to *expand, refine, or edit* an existing seed than requests to *originate* harmful content from scratch.
2. **Obfuscation Blind Spots**: 
   A 5.0% ASR under Base64 encoding highlights that pre-inference safety filters often fail to decode inputs before evaluation, allowing hidden instructions to execute in runtime.
3. **Resilient Persona Boundaries**: 
   The model successfully rejected 100% of classic "DAN-style" roleplay overrides and many-shot prompts, indicating mature training against behavioral framing.

---

## 🛠️ Repository Structure

```text
├── LLM_Safety_Evaluation_Engine.ipynb   # Complete execution pipeline (Colab ready)
├── master_redteam_evaluation_log.csv    # Raw evaluation records, completions, and judge scores
├── vulnerability_report.png             # Generated horizontal bar chart
├── app.py                               # Interactive Streamlit dashboard application
└── README.md                            # Project documentation and findings
