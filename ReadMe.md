![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Mistral](https://img.shields.io/badge/Mistral-API-orange)
![Telegram](https://img.shields.io/badge/Telegram-bot-blue)
![ChromaDB](https://img.shields.io/badge/ChromaDB-vector--db-yellow)

AI-powered resume search tool. Ingests PDF resumes, indexes them via Mistral embeddings into ChromaDB, builds structured candidate profiles with LLM, performs deep GitHub code analysis via MCP, and finds the best match for any job query using two-stage ranking.
### Supporting all languages

## How it works

### 1. Indexing (`/index`)

- Scans a folder for `.pdf` files
- Extracts text via `pdfplumber`, splits into 500-char chunks with 100-char overlap
- Each chunk → Mistral embedding → stored in ChromaDB (persistent vector DB)
- **GitHub Analysis (New):** Automatically extracts GitHub links, collects repository data (README, code samples) via **MCP (Machine Communication Protocol)**, and performs a balanced LLM assessment of code quality and technical depth.
- For every new resume, LLM builds a structured profile (summary, skills, experience, projects, education, **github_analysis**) and saves it to SQLite
- Profiles persist between runs and are used during reranking (Stage B)

### 2. Search flow

```
User query → LLM Validation → embedding → ChromaDB (top-10 chunks) → group by file → embedding_score → fetch profiles from SQLite → LLM rerank → final_score → explain top-3
```

**Stage 0 — Validation (New)**
- Query is analyzed by LLM to ensure it's a valid candidate search request.
- Greetings, general questions, or irrelevant text are rejected with a polite explanation.

**Stage A — Embedding retrieval**

- Query is converted to a Mistral embedding
- ChromaDB finds the 10 nearest chunks (by cosine distance)
- Chunks are grouped by source filename
- For each file: `embedding_score = 0.7 * best_chunk_distance + 0.3 * avg_chunk_distance`
- **Lower embedding_score = better match** (distance ~0 = identical, ~1.0 = unrelated)

**Stage B — LLM rerank via profiles**
- Structured profiles (including GitHub analysis) for those 10 candidates are loaded from SQLite
- **Single** LLM call sends all 10 profiles + query, asks to rate each 1-10
- Final score combines embedding distance and LLM rating:

`final_score = 0.3 * embedding_score + 0.7 * (1 - llm_rating / 10)`

- `embedding_score` is ~0.2–0.8 typically
- `llm_rating` is 1–10 (10 = best)
- `(1 - llm_rating / 10)` inverts LLM so both terms go the same direction: **lower = better**
- Typical final scores: ~0.15–0.6

**Stage C — Explanation**
- For top-3 candidates: LLM explains the match in under 50 words (skills, company, tasks) and displays GitHub insights.

### 3. Analytics flow

```
User question → fetch all profiles from SQLite → LLM analysis → answer
```

- The system retrieves all structured JSON profiles from the database.
- A single LLM call processes the entire dataset to answer complex analytical questions (e.g., "How many candidates have a PhD?", "Compare candidates by experience level").

**Mistral API calls budget:**

**During Indexing (per 1 new resume):**
- **~5-10** embedding calls (depends on resume length)
- **1** GitHub analysis call (if link found)
- **1** Profile building call
- *Total: ~7-12 calls per resume*

**During Search (per 1 query):**
- **1** validation call (LLM check for relevance)
- **1** embedding call (query → vector)
- **1** rerank call (10 profiles + query → JSON ratings)
- **3** explanation calls (one per top candidate)
- *Total: **6** Mistral API calls per search*

**During Analytics (per 1 question):**
- **1** LLM call (all profiles + question → answer)
- *Total: **1** Mistral API call per analytics question*

## Setup

```bash
git clone https://github.com/alexcfv/resume-rag-ranker.git
cd resume-rag-ranker
python -m venv venv
source venv/bin/activate
pip install -e .
cp config.example.yaml config.yaml
# Edit config.yaml — insert your Mistral API key and Telegram bot token
python bot.py
```

## Commands

- `/index /path/to/resumes` — index PDFs and build profiles
- Send any text message — search for candidates.
  
  **Message example:**

  ```bash
  Tech stack:
  Backend(main language): Golang.
  Data Bases: PostgreSQL, Cassandra, ElasticSearch, Redis.
  Infrastructure: Kafka, Kubernetes, Docker, gRPC.
  Experience:  Java, Python.
  ```
  ---
  **Answer example:**
  ```bash
  CV_name.pdf (score: 0.174)
  The candidate matches all backend and infrastructure requirements
  (Golang, PostgreSQL, Kafka, Kubernetes, Docker, gRPC, Redis)
  and has Java/Python experience. Worked at an NDA company as a Senior Golang Engineer,
  leading DevOps, CI/CD pipelines, and high-load system architecture,
  improving test coverage and release cycles.
  Designed telemetry tools for 50K+ users.
  ```
## The more specific your request, the more accurate your answer will be.
