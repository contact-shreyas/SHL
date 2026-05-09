# SHL Assessment Recommender

Conversational agent that takes hiring managers from vague intent to a grounded shortlist of SHL Individual Test Assessments through multi-turn dialogue.

## Architecture

```
User → POST /chat (full history)
         ↓
  Sentence-Transformers (all-MiniLM-L6-v2)
  retrieves top-20 catalog candidates via FAISS
         ↓
  System prompt + catalog context + conversation
  → Gemini 1.5 Flash (Groq fallback)
         ↓
  JSON response validated & URL-sanitized
         ↓
  {"reply":..., "recommendations":[...], "end_of_conversation":...}
```

## Quickstart (local)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Scrape the SHL catalog (needs internet access, ~5-10 min)
python scripts/scrape_catalog.py

# 3. Build the FAISS vector index (~1 min)
python scripts/build_index.py

# 4. Set your LLM API key (get free Gemini key at aistudio.google.com)
export GEMINI_API_KEY=your_key_here
# Optionally: export GROQ_API_KEY=your_groq_key (fallback)

# 5. Start the server
uvicorn app:app --host 0.0.0.0 --port 8000

# 6. Smoke test
python scripts/smoke_test.py --url http://localhost:8000

# 7. Evaluate against traces (place trace JSON files in data/traces/)
python scripts/evaluate.py --url http://localhost:8000 --traces data/traces/
```

## Deploy to Render (free tier)

1. Push this repo to GitHub.
2. Go to render.com → New Web Service → connect your repo.
3. Render auto-detects `render.yaml`.
4. Set env vars `GEMINI_API_KEY` (and optionally `GROQ_API_KEY`) in the Render dashboard.
5. Deploy. The build step scrapes the catalog and builds the index automatically.
6. Your public URL will be `https://shl-recommender.onrender.com`.

## API

### GET /health
```json
{"status": "ok"}
```

### POST /chat
Request:
```json
{
  "messages": [
    {"role": "user", "content": "Hiring a Java developer who works with stakeholders"},
    {"role": "assistant", "content": "Sure. What is seniority level?"},
    {"role": "user", "content": "Mid-level, around 4 years"}
  ]
}
```

Response:
```json
{
  "reply": "Here are 5 assessments for a mid-level Java developer...",
  "recommendations": [
    {"name": "Java 8 (New)", "url": "https://www.shl.com/...", "test_type": "K"},
    {"name": "OPQ32r", "url": "https://www.shl.com/...", "test_type": "P"}
  ],
  "end_of_conversation": false
}
```

## Agent Behavior

| Scenario | Behavior |
|---|---|
| Vague query ("I need an assessment") | Clarifies — no recs on turn 1 |
| Enough context provided | Recommends 1–10 assessments from catalog |
| User refines mid-conversation | Updates shortlist, doesn't restart |
| "Difference between X and Y?" | Grounds answer in catalog data only |
| Off-topic (legal, GDPR, etc.) | Politely refuses, no recs |
| Prompt injection attempt | Ignores, stays on task |

## Constraints

- Max 8 turns per conversation (stateless, history sent each call)
- 30-second timeout per call
- URLs validated against scraped catalog — hallucinated URLs rejected
- Only Individual Test Solutions (type=1) — Pre-packaged Job Solutions excluded

## Files

```
├── app.py                    # FastAPI application
├── requirements.txt
├── render.yaml               # Render deployment config
├── Procfile                  # Heroku/Railway compatible
├── scripts/
│   ├── scrape_catalog.py     # Scrape SHL catalog → data/catalog.json
│   ├── build_index.py        # Build FAISS index → data/index.faiss
│   ├── evaluate.py           # Recall@10 + behavior probe evaluator
│   └── smoke_test.py         # Quick sanity check
└── data/
    ├── catalog.json          # (generated)
    ├── index.faiss           # (generated)
    └── index_meta.json       # (generated)
```
