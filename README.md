# Mini AI Tutor + Evaluator System

A human-in-the-loop AI tutoring system with an automated evaluator agent and a continuous retraining pipeline.

---

## System Overview

```
Student → POST /ask → RAG Retrieval → Tutor Agent → POST /answer → Evaluator Agent → POST /review → Human Reviewer → Final JSON Output
```

---

## Flow 1 — Full Tutoring & Evaluation Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Student Journey                      │
└─────────────────────────────────────────────────────────┘

[Student]
    │
    ▼
POST /ask  ──────────────────►  RAG Retrieval
(Student submits question)       (Semantic search + chunks)
    │                                     │
    │◄────────────────────────────────────┘
    ▼
Tutor Agent
(Generate AI answer)
    │
    ▼
POST /answer
(Student submits their answer)
    │
    ▼
Evaluator Agent
(Score + AI feedback)
    │
    ▼
POST /review
(Human reviewer)
    │
    ▼
  ┌─────────────────┐
  │  Human Decision │
  └────────┬────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
 APPROVED     NOT APPROVED
    │             │
    ▼             ▼
AI score     Override /
confirmed    Edit feedback
    │             │
    └──────┬──────┘
           ▼
    Store Decisions
    (AI vs human audit log)
           │
           ▼
   Final JSON Output
   (score, feedback, source)
```

---

## Flow 2 — Human Approval: Approved Path

```
Evaluator Agent
    │
    ▼
POST /review ──► Human Reviewer
                      │
                      ▼
               [ Approve? YES ]
                      │
                      ▼
              AI Score Accepted
              (no change needed)
                      │
                      ▼
              Store in Audit Log
              (decision: AI-approved)
                      │
                      ▼
              Final JSON Output
```

---

## Flow 3 — Human Approval: Not Approved Path

```
Evaluator Agent
    │
    ▼
POST /review ──► Human Reviewer
                      │
                      ▼
               [ Approve? NO ]
                      │
                      ▼
              Override / Edit Feedback
              (human writes correction)
                      │
                      ▼
              Revised Score
              (human correction saved)
                      │
                      ▼
              Store in Audit Log
              (decision: human-overridden)
                      │
                      ▼
              Final JSON Output
```

---

## Flow 4 — Retraining Pipeline (Triggered by Drift)

```
Audit Log
(AI score + human correction pairs)
    │
    ▼
Drift Monitor
(Override rate > threshold?)
    │
    ├── NO  ──► Keep current model
    │
    └── YES
         │
         ▼
    ┌─────────────────────────────────────┐
    │         Retraining Pipeline         │
    │                                     │
    │  Dataset Curation                   │
    │  (filter high-confidence pairs)     │
    │            │                        │
    │            ▼                        │
    │  Format Training Pairs              │
    │  (question + answer → score)        │
    │            │                        │
    │            ▼                        │
    │  Fine-Tune Evaluator                │
    │  (SFT or RLHF on corrections)       │
    │            │                        │
    │            ▼                        │
    │  Offline Evaluation                 │
    │  (test on held-out human labels)    │
    │            │                        │
    │     ┌──────┴──────┐                 │
    │     │             │                 │
    │     ▼             ▼                 │
    │   PASS          FAIL                │
    │     │             │                 │
    │     │             └──► retry        │
    │     │                  (back to     │
    │     │                   curation)   │
    │     ▼                               │
    │  Deploy New Evaluator               │
    │  (replace prod, reset monitor)      │
    └─────────────────────────────────────┘
         │
         ▼
    (New cycle begins)
```

## Getting Started

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed

### Running with Docker

```bash
# Build and start all services
docker compose up --build

# Run in background
docker compose up --build -d

# Stop all services
docker compose down

# Stop and remove volumes (wipes database)
docker compose down -v
```

### Services

| Service | URL | Description |
|---|---|---|
| FastAPI App | http://localhost:8000 | Main AI tutor/evaluator API |
| API Docs (Swagger) | http://localhost:8000/docs | Interactive API documentation |
| Adminer | http://localhost:8080 | PostgreSQL web UI |
| PostgreSQL | localhost:5432 | Database (internal) |

### Adminer (PostgreSQL UI)

Open http://localhost:8080 and log in with:

| Field | Value |
|---|---|
| System | PostgreSQL |
| Server | `db` |
| Username | `postgres` |
| Password | `postgres` |
| Database | `ai_assessment` |

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@db:5432/ai_assessment` | PostgreSQL connection string |

### Local Development (without Docker)

```bash
# Install uv
pip install uv

# Install dependencies
uv sync

# Run the app
uv run uvicorn main:app --reload
```

---

## Key Metrics to Monitor

| Metric | Description | Action if high |
|---|---|---|
| Override rate | % of AI scores changed by human | Trigger retraining |
| Confidence distribution | How often model is uncertain | Review prompt / rubric |
| Score delta | Avg difference AI vs human score | Measure bias direction |
| Flagged rate | % flagged for review | Check for edge cases |

---

## Component Color Legend

| Color | Component Type |
|---|---|
| Purple | Student-facing API endpoints |
| Blue | AI agent / RAG internals |
| Teal | Human-in-the-Loop steps |
| Red | Not-approved / override path |
| Green | Approved / success path |
| Gray | Storage / output |
| Amber | Decision / monitoring |