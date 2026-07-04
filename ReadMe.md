![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Mistral](https://img.shields.io/badge/Mistral-API-orange)
![ChromaDB](https://img.shields.io/badge/ChromaDB-vector--db-yellow)

Languages:
- 🇬🇧 English
- 🇷🇺 [Русский](./ReadMeRu.md)

---

AI-powered recruitment intelligence platform. It automates candidate sourcing by ingesting PDF resumes, performing deep GitHub code analysis via MCP (Machine Communication Protocol), and executing a multi-stage RAG (Retrieval-Augmented Generation) pipeline to match candidates against complex job requirements.

## Key Technical Features

- **Multi-Stage RAG Pipeline**: Combines semantic vector search with LLM-based re-ranking for optimal precision.
- **Deep GitHub Integration**: Uses MCP to analyze actual code samples, repository structure, and contribution quality, integrating these insights directly into the candidate's professional profile. This allows the system to match resume claims with actual code evidence.
- **Automated Profile Synthesis**: Generates structured JSON profiles from unstructured data (PDFs + GitHub), enabling complex analytical queries.
- **Asynchronous Architecture**: Built on `FastAPI` and `asyncio` for high-performance, non-blocking data processing.
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

### Local Installation

```bash
git clone https://github.com/alexcfv/resume-rag-ranker.git
cd resume-rag-ranker
python -m venv venv
source venv/bin/activate
pip install -e .
cp config.example.yaml config.yaml
# Edit config.yaml — insert your Mistral API key and GitHub token for mcp. You can also change the model in the config to a more advanced one for better results.
python main.py
```

### Docker Setup (Recommended)

The easiest way to run the entire stack (Backend, Frontend, and Bot) is using Docker Compose.

1. **Configure environment:**
   Copy `config.example.yaml` to `config.yaml` and fill in your API keys:
   ```bash
   cp config.example.yaml config.yaml
   ```

2. **Run with Docker Compose:**
   ```bash\n   docker-compose up --build
   ```

3. **Indexing Resumes in Docker:**
   To index your resumes, place them in the `./data/resumes` folder on your host machine. It is automatically mounted to `/app/data/resumes` inside the container.
   When using the UI or Bot to index, use the path: `/app/data/resumes`

## Usage (API)

The system provides a REST API for frontend interaction. Main endpoints:
- `POST /api/index` — index PDFs and build profiles
- `POST /api/search` — search for candidates
- `POST /api/analytics` — analytical questions about the candidate database

### Find Candidate Example:
**Question:**
```text
Intern Go developer with python experience.
Tech stack:
Backend (main language): Golang.
Databases: PostgreSQL, Redis.
Infrastructure: Docker, REST API, gRPC, Git.
Experience: Python.
```

 **System Response:**
```text
The candidate matches the intern Go developer role with Python experience.
Key skills include Golang, Python (Flask, scikit-learn, pandas),
PostgreSQL, and REST/gRPC (implied by microservices).
  
GitHub shows moderate code quality with Go projects (e.g., go-pcaplite in *awesome-go*),
network tools (gopacket/libpcap), and ML integration (scikit-learn).
Python experience aligns with job requirements, but async/advanced Go features aren’t confirmed.
Achievements (hackathon wins, production ML integration) suggest practical exposure.
```

### Database Analytics Example:

**Question:**
```text
Compare all candidates with Golang experience. Who has the best understanding of high-load architecture and verified GitHub code?
```

**System Response:**
```text
Based on the analysis of 15 profiles with Golang experience:
1. Ivan I. (ivanov_dev): Highest score. The 'highload-starter' repository implements DB sharding and a custom worker pool. The code demonstrates a deep understanding of Go concurrency.
2. Peter S. (spetrov): Good resume experience, but GitHub only contains forks. Architectural skills are only confirmed by the resume text.
3. Alex S.: Senior experience, but GitHub code is mostly Python scripts; Go projects are missing.
Recommendation: Ivan I. is the most suitable candidate.
```
## The more specific your request, the more accurate your answer will be.

## How it look like
<img width="1893" height="942" alt="image" src="https://github.com/user-attachments/assets/3a974fa4-d697-4be1-b95a-43707d80ddf2" />
