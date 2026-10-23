# /v1 serving layer (PinoBio MVP-4)

FastAPI implementation of the SciACA workbench job contract
(`Default Project/specs/orchestrator.md` §10–11). The SciACA UI already ships the
client (`src/api/client.ts` `apiGet`/`apiPost`, merged 2026-10-23) and runs demo
data whenever `VITE_API_BASE` is unset — so this server is purely additive: point
the UI at it to go live.

## Run

```bash
pip install -r serving/requirements.txt
uvicorn serving.app:app --port 8080
# then in SciACA: VITE_API_BASE=http://localhost:8080
```

## Endpoints (contract §10.1)

| Method | Path | Role |
|---|---|---|
| POST | `/v1/jobs` | create `{task, model, project, inputs}` → `{id, status}` |
| GET | `/v1/jobs` | list |
| GET | `/v1/jobs/:id` | status + result (tool output schema) |
| GET | `/v1/models` · `/v1/models/:id` | model cards (SciACA `models.ts` shape) |
| GET | `/v1/projects` | demo projects |

## Hard rules enforced here

- **G7 (honesty):** tools return **honest `pending` results** when a model's
  checkpoint/container is not yet available — never fabricated molecules or
  sequences. The `note` field says exactly why, and `generated` stays empty.
- **G8 (secrets):** `GET /v1/*` needs no auth; any upstream key is read from env
  (`PINOBIO_*`), never committed. No secret ever enters a response.
- **G9 (scope):** only the MVP-4 task→tool mapping (§10.2) is served; an unknown
  `task` returns a `validation` error (§11).
- **§7 passthrough:** `design.backbone` carries `reasoning_depth` +
  `search_criteria` into the job trajectory (Unified-Latent-Reasoning workbench).

## Backend readiness (honest, as of 2026-10-23)

| Tool | Backend | State |
|---|---|---|
| `mol.generate` | Molek-30M (ours) | checkpoint pending run #7 → honest `pending` |
| `seq.generate` | Seqgen-small (ours) | config locked, untrained → honest `pending` |
| `design.backbone` | RFD4-Proteina (served, BSD-3) | needs pinned py3.12 container → honest `pending` |
| `esm.embed` / `esm.fold` | ESM-2 / ESMFold (served) | wrapper ready; model load gated on env |

Nothing here claims a result it did not compute.
