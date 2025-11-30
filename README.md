# Quick start

```bash
HF_HOME=./models_cache DEVICE=gpu uvicorn app.main:app --host 0.0.0.0 --port 8000
```

# Docker start
## CPU
```bash
docker compose up --build
```

## GPU
```bash
DEVICE=gpu docker compose up --build
```