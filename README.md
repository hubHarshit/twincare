# Twincare 💑

*A privacy ‑first virtual healthcare assistant that performs symptom triage, appointment booking, and insurance guidance — all powered by on ‑prem LLMs and FastAPI.*

---

## ✨ Key Features

| Feature                      | Description                                                                                                                                                      |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Multi ‑agent routing**     | MCPCore intelligently routes each user message to specialised agents (medical triage, booking, insurance) using semantic similarity + zero ‑shot classification. |
| **On ‑device LLM inference** | Uses a local **Llama.cpp** Med ‑Alpaca model for HIPAA ‑friendly, low ‑latency language generation.                                                              |
| **Context persistence**      | Conversation state is cached in Redis with TTL ‑controlled keys so agents retain short ‑term memory without long ‑term PII retention.                            |
| **FastAPI microservice**     | Thin HTTP layer exposes a clean JSON API (REST) with automatic OpenAPI docs.                                                                                     |
| **Plug ‑and ‑play agents**   | Agents share a common `BaseChatAgent` interface, making it trivial to add new verticals (nutrition, mental health, etc.).                                        |
| **Observability hooks**      | Core metrics (request latency, error count, token usage) emitted via `/stats` endpoint and ready for Prometheus / Grafana.                                       |

---

## 📇 System Architecture



![System Architecture](assets/architecture.png)

### Cloud-Native Deployment Overview

| Layer             | Service                | GCP Component                              |
| ----------------- | ---------------------- | ------------------------------------------ |
| **Compute**       | API + Agents           | Cloud Run / GKE                            |
| **LLM Inference** | Symptom check, triage  | Vertex AI Endpoints (e.g., MedPalm, Gemma) |
| **Search/RAG**    | Treatment retrieval    | FAISS / Vertex AI Matching Engine          |
| **Persistence**   | Session data           | Firestore                                  |
| **Analytics**     | Queryable logs & usage | BigQuery                                   |
| **Blob storage**  | Uploaded files         | Cloud Storage                              |
| **CI/CD**         | Build + deploy         | Cloud Build + Artifact Registry            |
| **Secrets**       | API keys, credentials  | Secret Manager                             |
| **Auth**          | User access control    | Firebase Auth / Identity Platform          |

> Full Terraform IaC and Helm charts available in `ops/` folder (coming soon).

*High ‑level message flow:*

1. **Client** sends `POST /route`.
2. **FastAPI Router** validates payload (`AgentRequest`).
3. **MCPCore** checks Redis for context ➔ chooses best agent.
4. Selected **Agent** generates a response (may call LLM / external APIs).
5. Response is returned as `AgentResponse` → client UI.

---

### MCPCore (Message Control Plane)

MCPCore is the **central routing brain** of TwinCare. It performs three critical tasks before delegating work to downstream agents:

1. **Intent inference & scoring**
   Utilises a Sentence ‑Transformer (`all ‑MiniLM ‑L6`) and a zero ‑shot NLI classifier to compute a confidence score for every registered agent. The highest ‑scoring agent wins; ties are broken by a deterministic round ‑robin.

2. **Context stitching**
   Pulls the user’s short ‑term context from Redis, merges it with the current prompt, and injects a conversation header that preserves PHI boundaries.

3. **Safety gatekeeping**
   Runs each outgoing prompt through a lightweight Med ‑ToxiScore model to block disallowed content before the LLM fires.

Because MCPCore is stateless **by design**, you can scale it horizontally behind any load balancer without sticky sessions.

---

## 📁 Repository Layout

```text
app/
├── agents/            # MedicalChatAgent, BookingAgent, ...
├── context/           # Redis ‑backed ContextManager
├── core/              # MCPCore orchestrator
├── config/            # settings.py, redis_config.py
├── protocol/          # Pydantic schemas + API router
├── utils/             # (e.g., encryption stubs)
├── main.py            # FastAPI startup
tests/                 # PyTest suites
requirements.txt       # Python deps
Dockerfile (coming soon)
```

---

## 🚀 Getting Started

### Prerequisites

* Python 3.9+
* Redis 5+
* GCC / clang (for llama.cpp build)
* (Optional) GPU w/ CUDA 11+ for HF pipelines

### 1 · Clone & create virtualenv

```bash
git clone https://github.com/hubHarshit/twincare.git
cd twincare-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2 · Download the LLM weights

```bash
wget https://huggingface.co/medalpaca/MedAlpaca-2-7B-GGUF/resolve/main/med-alpaca-2-7b-chat.Q4_K_M.gguf \
     -O models/Med-Alpaca-2-7b-chat.Q4_K_M.gguf
```

### 3 · Configure environment

```env
# .env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_TTL=86400
MODEL_PATH=models/Med-Alpaca-2-7b-chat.Q4_K_M.gguf
```

### 4 · Run the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access the Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🗾️ API Reference

### `POST /route`

| Field        | Type   | Description                |
| ------------ | ------ | -------------------------- |
| `user_id`    | string | Unique ID for user session |
| `input_text` | string | User’s message             |
| `context`    | object | (Optional) extra metadata  |

<details>
<summary>Sample cURL</summary>

```bash
curl -X POST http://localhost:8000/route \
     -H "Content-Type: application/json" \
     -d '{
           "user_id": "abc123",
           "input_text": "I have a sore throat and fever",
           "context": {}
         }'
```

</details>

### `GET /stats`

Returns JSON with request count, average latency, error tally, etc.

### `GET /agent/{agent_id}/status`

Returns health status of an individual agent.

---

## 🧪 Running Tests

```bash
pytest -q
```

---

## 📦 Docker (optional)

> **Coming soon** — multi ‑stage build with llama.cpp + poetry.

```Dockerfile
FROM python:3.9-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## ⚙️ Deployment

TwinCare can run everywhere—from a single GPU laptop to a fully managed, HIPAA ‑compliant stack on **Google Cloud Platform**.

### Infrastructure-as-Code (Terraform)

```bash
cd ops/terraform/envs/staging
terraform init
terraform apply -var-file=staging.tfvars
```

> Modules include GKE, Memorystore, Vertex AI, Secret Manager, Firestore, and IAM bindings.

---

### Local (Docker Compose)

```bash
docker compose -f ops/docker/docker-compose.local.yml up --build -d
```

### GKE + Helm

* Deploys FastAPI pods (HPA-enabled)
* Mounts model volume (PVC)
* Redis and Prometheus sidecar

---

### Cloud Run + Vertex AI

1. Cloud Build pushes image to Artifact Registry
2. Cloud Run spins up container (CPU/GPU)
3. Medical agent queries Vertex AI endpoints (PaLM, Gemma, etc.)
4. Metrics piped into Cloud Monitoring

---

## 🤝 Contributing

1. Fork & branch: `git checkout -b feature/your-feature`
2. Format code: `make precommit`
3. Open a PR with clear description

---

## 📄 License

MIT © Harshit Pant

---

## 🙏 Acknowledgements

* [Med-Alpaca](https://github.com/medalpaca)
* [Llama.cpp](https://github.com/ggerganov/llama.cpp)
* [FastAPI](https://fastapi.tiangolo.com/)
* Stanford HAI

> *Stay healthy, stay private — TwinCare has your back.*
