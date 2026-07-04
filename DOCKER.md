# Docker & Deployment

## Quick Start

```bash
# Build and run everything
docker-compose up -d

# Chat UI available at http://localhost:8000
# API available at http://localhost:8000/api/recommend

# View logs
docker-compose logs -f app

# Stop
docker-compose down
```

## Services

| Service | Port | Role |
|---------|------|------|
| `app` | 8000 | FastAPI (retriever, generator, judge, chat UI) |
| `chroma` | 8001 | Vector DB (optional, for inspection) |

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Optional: provide API key for live Claude calls (mock mode used if unset)
ANTHROPIC_API_KEY=sk-ant-...

# Optional: override Chroma host/port
CHROMA_HOST=chroma
CHROMA_PORT=8000

# Optional: HuggingFace token for private models
HUGGINGFACE_TOKEN=hf_...
```

Then:

```bash
docker-compose --env-file .env up -d
```

### Mock Mode (Default)

Without `ANTHROPIC_API_KEY`, the app uses a deterministic keyword router and rule-based judge. Zero API calls, reproducible, free.

### API Mode

Set `ANTHROPIC_API_KEY` to use live Claude models (Haiku for gen, Sonnet for judge). Charges per call (~$0.003–0.01 each).

## Volumes

| Path | Purpose |
|------|---------|
| `.cache/huggingface/` | Embedding model cache (MiniLM-L6-v2, ~50MB). Persisted across restarts. |
| `eval/eval_results.db` | SQLite results database. Persisted. |
| `eval/reports/` | Markdown regression reports. Persisted. |

Remove volumes to reset:

```bash
docker-compose down -v
```

## Running Tests Inside Docker

```bash
# Unit + integration tests
docker-compose exec app python -m pytest -q

# Full golden-set eval
docker-compose exec app python -m eval.regression_runner

# Playwright E2E (requires npm in container; simpler to run locally)
docker-compose exec app bash -c "cd tests/e2e && npm install && npx playwright install && npx playwright test"
```

## Building for Production

### Single Image (Recommended for Small Deployments)

```bash
docker build -t clinceval:latest .
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e CHROMA_HOST=localhost \
  -v ~/.cache/huggingface:/app/.cache/huggingface \
  clinceval:latest
```

This requires Chroma running elsewhere (or embedded). For embedded Chroma, use `docker-compose`.

### Multi-Stage Build (If Optimization Needed)

```dockerfile
FROM python:3.12-slim as builder
# ... install deps, extract model cache ...

FROM python:3.12-slim
COPY --from=builder /app /app
# ... run app ...
```

Not necessary for current image size (~500MB with deps, ~1.5GB with Chroma).

### Push to Registry

```bash
docker tag clinceval:latest ghcr.io/ashrahossain/clinceval:latest
docker push ghcr.io/ashrahossain/clinceval:latest
```

## Kubernetes (Future)

Deployment manifest template:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: clinceval
spec:
  replicas: 2
  selector:
    matchLabels:
      app: clinceval
  template:
    metadata:
      labels:
        app: clinceval
    spec:
      containers:
      - name: app
        image: ghcr.io/ashrahossain/clinceval:latest
        ports:
        - containerPort: 8000
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: clinceval-secrets
              key: api-key
        - name: CHROMA_HOST
          value: "chroma"
        volumeMounts:
        - name: hf-cache
          mountPath: /app/.cache/huggingface
        - name: db
          mountPath: /app/eval
      volumes:
      - name: hf-cache
        emptyDir: {}  # Or persistentVolumeClaim for real deployments
      - name: db
        persistentVolumeClaim:
          claimName: clinceval-db
```

## Debugging

### Container won't start

```bash
docker-compose logs app
```

Common issues:
- **Chroma not ready**: Check `docker-compose logs chroma`, wait for "Uvicorn running"
- **Port in use**: `lsof -i :8000` and kill, or change port in `docker-compose.yml`
- **API key invalid**: Unset `ANTHROPIC_API_KEY` to use mock mode

### Slow first request

Embedding model is loaded on first `/api/recommend` call (~5–10s). The Dockerfile pre-warms it, but network delay may apply. Subsequent requests: <100ms.

### Database locked

SQLite can lock if multiple processes write simultaneously. Docker-compose serializes this via a single `app` service. For multiprocess (Kubernetes), switch to PostgreSQL:

```bash
# Update eval/db.py:
# engine = create_engine("postgresql://user:pass@postgres:5432/clinceval")

# Add postgres service to docker-compose.yml
postgres:
  image: postgres:15
  environment:
    POSTGRES_PASSWORD: password
    POSTGRES_DB: clinceval
  volumes:
    - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Performance Tuning

### Embedding Model Caching

Set `HF_HOME=/mnt/nvme/hf-cache` to a faster disk.

### Chroma Persistence

By default, Chroma uses SQLite. For high concurrency, consider replacing with Chroma Cloud or PostgreSQL backing.

### Uvicorn Workers

In production, add `--workers 4` to the CMD:

```dockerfile
CMD ["python", "-m", "uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Note: LLM calls are I/O-bound, so 2–4 workers sufficient.

## Cost Optimization (API Mode)

- **Mock mode is free.** Use in CI, dev, demos.
- **Batch queries.** Run `python -m eval.regression_runner` once with all 41 cases, not 41 separate requests.
- **Cache retrieved chunks.** Retriever output doesn't change per case; reuse across judge calls if the same chunks apply.

## Cleanup

```bash
# Stop containers
docker-compose down

# Remove images
docker rmi clinceval:latest ghcr.io/chroma-core/chroma:0.4.24

# Remove volumes (⚠️ loses data)
docker volume rm clinceval_chroma_data

# Prune unused resources
docker system prune -a
```
