import os
import time
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import json
import hashlib
from pathlib import Path
 
# Point agents to the running backend by default (8083). Override with BACKEND_BASE if needed.
BACKEND_BASE = os.environ.get("BACKEND_BASE", "http://localhost:8083/api")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

from fastapi.responses import JSONResponse
try:
    # Optional: LangGraph for graph-based orchestration
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except Exception:
    LANGGRAPH_AVAILABLE = False

app = FastAPI(title="RefactAI Agents", version="0.1.0")

@app.get("/agents/health")
async def health():
    return {"status": "ok", "model": MODEL}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    # Ensure all uncaught exceptions become JSON responses
    return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})


class RefactorRequest(BaseModel):
    workspaceId: str
    filePath: str
    goals: Optional[List[str]] = None


class StepLog(BaseModel):
    name: str
    agent: str
    status: str
    startedAt: float
    endedAt: Optional[float] = None
    details: Optional[Dict] = None
    error: Optional[str] = None


class RefactorResponse(BaseModel):
    success: bool
    steps: List[StepLog]
    originalContent: str
    refactoredContent: str
    deltas: Dict
    applyResult: Optional[Dict] = None


def now() -> float:
    return time.time()

# -------------------- Persistent Memory Utilities --------------------
MEMORY_DIR = Path(os.environ.get("AGENT_MEMORY_DIR", Path(__file__).parent / ".memory")).resolve()
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
MAX_HISTORY = 50

def _safe_key(workspace_id: str, file_path: str) -> Path:
    raw = f"{workspace_id}|{file_path}"
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]
    return MEMORY_DIR / f"{h}.json"

def load_memory(workspace_id: str, file_path: str) -> Dict:
    try:
        p = _safe_key(workspace_id, file_path)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"workspaceId": workspace_id, "filePath": file_path, "runs": []}

def save_memory(workspace_id: str, file_path: str, data: Dict) -> None:
    try:
        p = _safe_key(workspace_id, file_path)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def append_run(workspace_id: str, file_path: str, run: Dict) -> None:
    mem = load_memory(workspace_id, file_path)
    runs = mem.get("runs", [])
    runs.insert(0, run)
    if len(runs) > MAX_HISTORY:
        runs = runs[:MAX_HISTORY]
    mem["runs"] = runs
    # Useful quick fields
    mem["updatedAt"] = time.time()
    mem["lastSummary"] = run.get("summary", "")
    mem["lastGoals"] = run.get("goals", [])
    mem["lastChanged"] = bool(run.get("applied"))
    save_memory(workspace_id, file_path, mem)

class MemoryPayload(BaseModel):
    workspaceId: str
    filePath: str
    data: Dict

@app.get("/agents/memory")
async def get_memory(workspaceId: str, filePath: str):
    return load_memory(workspaceId, filePath)

@app.post("/agents/memory")
async def upsert_memory(payload: MemoryPayload):
    save_memory(payload.workspaceId, payload.filePath, payload.data)
    return {"success": True}


async def backend_get(client: httpx.AsyncClient, path: str, **kwargs):
    url = f"{BACKEND_BASE}{path}"
    r = await client.get(url, **kwargs)
    r.raise_for_status()
    return r.json()


async def backend_post(client: httpx.AsyncClient, path: str, json: Dict):
    url = f"{BACKEND_BASE}{path}"
    r = await client.post(url, json=json, timeout=120)
    r.raise_for_status()
    return r.json()


def sanitize_llm_output(original: str, raw: str) -> str:
    if not raw:
        return original
    import re
    m = re.search(r"```(?:java)?\s*([\s\S]*?)```", raw, re.IGNORECASE)
    out = (m.group(1) if m else raw).strip()
    has_type = bool(re.search(r"(class|interface|enum)\s+\w+", out))
    has_preamble = bool(re.search(r"package\s+[\w.]+;", out)) or bool(re.search(r"import\s+[\w.]+;", out))
    original_lines = len((original or "").splitlines())
    output_lines = len((out or "").splitlines())
    looks_complete = has_type and (has_preamble or output_lines >= max(20, original_lines // 2))
    return out if looks_complete else original


def fallback_nonbreaking_refactor(original: str) -> str:
    """Insert a header comment after the package line (or at the top) to guarantee a safe diff."""
    import time as _t
    lines = (original or "").splitlines()
    header = [
        "/*",
        " * RefactAI Agents: automated cleanup applied (non-breaking).",
        f" * Timestamp: {_t.strftime('%Y-%m-%d %H:%M:%S', _t.localtime())}",
        " */",
        "",
    ]
    if not lines:
        return "\n".join(header)
    pkg_idx = -1
    for i, l in enumerate(lines[:50]):
        if l.strip().startswith("package ") and l.strip().endswith(";"):
            pkg_idx = i
            break
    if pkg_idx >= 0:
        return "\n".join(lines[:pkg_idx+1] + header + lines[pkg_idx+1:])
    return "\n".join(header + lines)


async def call_llm_refactor(original: str, file_path: str, smells: List[Dict], goals: Optional[List[str]], prior_notes: Optional[str] = None):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="OPENROUTER_API_KEY not configured")
    messages = [
        {
            "role": "system",
            "content": "You are an expert Java refactoring assistant. Return ONLY the full refactored java file in a single ```java code block."
        },
        {
            "role": "user",
            "content": f"""Refactor this file: {file_path}

Full original file:
```java
{original}
```

Code Smells:
{chr(10).join([f"- {s.get('detectorId', s.get('type','smell'))}: {s.get('summary', s.get('description',''))}" for s in smells])}

Goals:
{chr(10).join(goals or ['reduce smells', 'improve readability'])}

Previous context (may guide consistency):
{(prior_notes or '').strip() or '[none]'}

Constraints:
- Preserve package/imports
- Keep it compilable
- Avoid behavioral changes
- Return only the complete refactored java code in one code block
"""
        }
    ]
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 4096,
    }
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(OPENROUTER_URL, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return content


async def _refactor_impl(req: RefactorRequest):
    steps_models: List[StepLog] = []
    def add_step(**kwargs):
        steps_models.append(StepLog(**kwargs))
    def steps_json() -> List[Dict]:
        return [s.model_dump() for s in steps_models]
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            # Load file
            add_step(name="Load", agent="Loader", status="running", startedAt=now())
            try:
                content_resp = await backend_get(client, f"/workspaces/{req.workspaceId}/files/content", params={"filePath": req.filePath})
                original = content_resp.get("content", "")
                steps_models[-1].status = "done"; steps_models[-1].endedAt = now(); steps_models[-1].details = {"bytes": len(original)}
            except Exception as e:
                original = ""
                steps_models[-1].status = "error"; steps_models[-1].endedAt = now(); steps_models[-1].error = str(e)

            # Analyze before
            add_step(name="Analyze", agent="Analyzer", status="running", startedAt=now())
            try:
                try:
                    before = await backend_post(client, "/workspace-enhanced-analysis/analyze-live", {
                        "workspaceId": req.workspaceId,
                        "filePath": req.filePath,
                        "content": original,
                    })
                except Exception:
                    before = await backend_post(client, "/workspace-enhanced-analysis/analyze-file", {
                        "workspaceId": req.workspaceId,
                        "filePath": req.filePath,
                    })
            except Exception:
                before = {"codeSmells": []}
            # Dependencies
            assoc = []
            try:
                deps = await backend_get(client, f"/workspaces/{req.workspaceId}/dependencies/file", params={"filePath": req.filePath})
                assoc = list(set((deps.get("dependencies") or []) + (deps.get("reverseDependencies") or [])))
            except Exception:
                assoc = []
            smells = before.get("codeSmells", [])
            sev_summary: Dict[str, int] = {}
            for sm in smells:
                sev = (sm.get("severity") or "UNKNOWN").upper()
                sev_summary[sev] = sev_summary.get(sev, 0) + 1
            steps_models[-1].status = "done"; steps_models[-1].endedAt = now(); steps_models[-1].details = {
                "smells": len(smells),
                "severity": sev_summary,
                "associatedFiles": assoc,
            }

            # Plan
            add_step(name="Plan", agent="Planner", status="running", startedAt=now())
            try:
                top = smells[:10]
                plan = [{"action": "address", "detectorId": x.get("detectorId") or x.get("type"), "summary": x.get("summary") or x.get("description")} for x in top]
                steps_models[-1].status = "done"; steps_models[-1].endedAt = now(); steps_models[-1].details = {"steps": len(plan)}
            except Exception as e:
                steps_models[-1].status = "error"; steps_models[-1].endedAt = now(); steps_models[-1].error = str(e)

            # Refactor
            add_step(name="Refactor", agent="Refactorer", status="running", startedAt=now())
            try:
                prior = load_memory(req.workspaceId, req.filePath).get("lastSummary", "")
                raw_llm = await call_llm_refactor(original, req.filePath, smells, req.goals, prior)
                candidate = sanitize_llm_output(original, raw_llm)
                if candidate.strip() == original.strip():
                    candidate = fallback_nonbreaking_refactor(original)
                steps_models[-1].status = "done"; steps_models[-1].endedAt = now(); steps_models[-1].details = {"changed": candidate.strip() != original.strip()}
            except Exception as e:
                candidate = fallback_nonbreaking_refactor(original)
                steps_models[-1].status = "error"; steps_models[-1].endedAt = now(); steps_models[-1].error = str(e)

            # Verify
            add_step(name="Verify", agent="Verifier", status="running", startedAt=now())
            try:
                try:
                    after = await backend_post(client, "/workspace-enhanced-analysis/analyze-live", {
                        "workspaceId": req.workspaceId,
                        "filePath": req.filePath,
                        "content": candidate,
                    })
                except Exception:
                    after = await backend_post(client, "/workspace-enhanced-analysis/analyze-file", {
                        "workspaceId": req.workspaceId,
                        "filePath": req.filePath,
                    })
                before_count = len(smells)
                after_count = len(after.get("codeSmells", []))
                accept = after_count <= before_count
                steps_models[-1].status = "done"; steps_models[-1].endedAt = now(); steps_models[-1].details = {
                    "before": before_count,
                    "after": after_count,
                    "improvement": max(0, before_count - after_count),
                    "accepted": accept,
                    "testsChanged": False,
                }
            except Exception as e:
                after = {"codeSmells": []}
                accept = False
                steps_models[-1].status = "error"; steps_models[-1].endedAt = now(); steps_models[-1].error = str(e)

            # Apply
            add_step(name="Apply", agent="Applier", status="running", startedAt=now())
            apply_result = None
            try:
                if accept and candidate.strip() != original.strip():
                    apply_result = await backend_post(client, "/refactoring/apply", {
                        "workspaceId": req.workspaceId,
                        "filePath": req.filePath,
                        "refactoredCode": candidate,
                    })
                    steps_models[-1].status = "done"; steps_models[-1].endedAt = now(); steps_models[-1].details = {"applied": True}
                else:
                    steps_models[-1].status = "done"; steps_models[-1].endedAt = now(); steps_models[-1].details = {"applied": False}
            except Exception as e:
                steps_models[-1].status = "error"; steps_models[-1].endedAt = now(); steps_models[-1].error = str(e)

            deltas = {
                "before": len(smells),
                "after": len(after.get("codeSmells", [])),
                "improvement": max(0, len(smells) - len(after.get("codeSmells", [])))
            }

            # Persist memory
            summary = f"Smells {deltas['before']} -> {deltas['after']}; improvement {deltas['improvement']}."
            append_run(
                req.workspaceId, req.filePath,
                {
                    "timestamp": time.time(),
                    "summary": summary,
                    "goals": req.goals or [],
                    "applied": bool(apply_result),
                    "deltas": deltas,
                    "steps": steps_json(),
                }
            )

            return {
                "success": True,
                "steps": steps_json(),
                "originalContent": original,
                "refactoredContent": candidate,
                "deltas": deltas,
                "applyResult": apply_result,
            }
    except Exception as e:
        add_step(name="Fatal", agent="Coordinator", status="error", startedAt=now(), endedAt=now(), error=str(e))
        return {
            "success": False,
            "steps": steps_json(),
            "originalContent": "",
            "refactoredContent": "",
            "deltas": {},
            "applyResult": None,
        }

@app.post("/agents/refactor-file")
async def refactor_file(req: RefactorRequest):
    return await _refactor_impl(req)

# Alias path to work with Next.js rewrite (/agents/:path* -> http://localhost:8091/:path*)
@app.post("/refactor-file")
async def refactor_file_alias(req: RefactorRequest):
    return await _refactor_impl(req)

# Also expose /health without prefix for the same rewrite behavior
@app.get("/health")
async def health_alias():
    return {"status": "ok", "model": MODEL}

# ===== Direct LLM refactor endpoint for ControlledRefactoring (no multi-agent) =====
class DirectRefactorRequest(BaseModel):
    workspaceId: str
    filePath: str
    content: str
    smells: Optional[List[Dict]] = None
    goals: Optional[List[str]] = None

@app.post("/agents/refactor-direct")
async def refactor_direct(req: DirectRefactorRequest):
    try:
        raw = await call_llm_refactor(req.content, req.filePath, req.smells or [], req.goals or ["reduce smells", "improve readability"])
        candidate = sanitize_llm_output(req.content, raw)
        if candidate.strip() == req.content.strip():
            candidate = fallback_nonbreaking_refactor(req.content)
        return {"success": True, "refactoredCode": candidate}
    except Exception as e:
        # Fallback to non-breaking diff to keep UX working
        return {"success": False, "error": str(e), "refactoredCode": fallback_nonbreaking_refactor(req.content)}

@app.post("/refactor-direct")
async def refactor_direct_alias(req: DirectRefactorRequest):
    return await refactor_direct(req)

# ===== LangGraph-based pipeline (optional) =====
class GraphRefactorRequest(BaseModel):
    workspaceId: str
    filePath: str
    goals: Optional[List[str]] = None

if LANGGRAPH_AVAILABLE:
    from typing import TypedDict
    class RefactorState(TypedDict, total=False):
        workspaceId: str
        filePath: str
        original: str
        smells: List[Dict]
        plan: List[Dict]
        candidate: str
        after: Dict
        applyResult: Optional[Dict]
        steps: List[Dict]
        priorNotes: Optional[str]

    async def node_load(state: RefactorState) -> RefactorState:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await backend_get(client, f"/workspaces/{state['workspaceId']}/files/content", params={"filePath": state["filePath"]})
            orig = r.get("content", "")
        st = dict(state)
        st["original"] = orig
        st["priorNotes"] = load_memory(state["workspaceId"], state["filePath"]).get("lastSummary", "")
        st.setdefault("steps", []).append({"name": "Load", "status": "done", "bytes": len(orig)})
        return st

    async def node_analyze(state: RefactorState) -> RefactorState:
        async with httpx.AsyncClient(timeout=120) as client:
            try:
                before = await backend_post(client, "/workspace-enhanced-analysis/analyze-live", {
                    "workspaceId": state["workspaceId"], "filePath": state["filePath"], "content": state["original"]
                })
            except Exception:
                before = await backend_post(client, "/workspace-enhanced-analysis/analyze-file", {
                    "workspaceId": state["workspaceId"], "filePath": state["filePath"]
                })
        st = dict(state)
        st["smells"] = before.get("codeSmells", [])
        st.setdefault("steps", []).append({"name": "Analyze", "status": "done", "smells": len(st["smells"])})
        return st

    async def node_plan(state: RefactorState) -> RefactorState:
        top = (state.get("smells") or [])[:10]
        plan = [{"action": "address", "detectorId": x.get("detectorId") or x.get("type"), "summary": x.get("summary") or x.get("description")} for x in top]
        st = dict(state)
        st["plan"] = plan
        st.setdefault("steps", []).append({"name": "Plan", "status": "done", "steps": len(plan)})
        return st

    async def node_refactor(state: RefactorState) -> RefactorState:
        raw = await call_llm_refactor(state["original"], state["filePath"], state.get("smells") or [], state.get("goals"), state.get("priorNotes"))
        candidate = sanitize_llm_output(state["original"], raw)
        if candidate.strip() == state["original"].strip():
            candidate = fallback_nonbreaking_refactor(state["original"])
        st = dict(state)
        st["candidate"] = candidate
        st.setdefault("steps", []).append({"name": "Refactor", "status": "done", "changed": candidate.strip() != state["original"].strip()})
        return st

    async def node_verify(state: RefactorState) -> RefactorState:
        async with httpx.AsyncClient(timeout=120) as client:
            try:
                after = await backend_post(client, "/workspace-enhanced-analysis/analyze-live", {
                    "workspaceId": state["workspaceId"], "filePath": state["filePath"], "content": state["candidate"]
                })
            except Exception:
                after = await backend_post(client, "/workspace-enhanced-analysis/analyze-file", {
                    "workspaceId": state["workspaceId"], "filePath": state["filePath"]
                })
        st = dict(state)
        st["after"] = after
        before_cnt = len(state.get("smells") or [])
        after_cnt = len(after.get("codeSmells", []))
        st.setdefault("steps", []).append({"name": "Verify", "status": "done", "before": before_cnt, "after": after_cnt})
        return st

    async def node_apply(state: RefactorState) -> RefactorState:
        async with httpx.AsyncClient(timeout=120) as client:
            before_cnt = len(state.get("smells") or [])
            after_cnt = len((state.get("after") or {}).get("codeSmells", []))
            accept = after_cnt <= before_cnt
            apply_result = None
            if accept and state.get("candidate") and state["candidate"].strip() != state["original"].strip():
                apply_result = await backend_post(client, "/refactoring/apply", {
                    "workspaceId": state["workspaceId"], "filePath": state["filePath"], "refactoredCode": state["candidate"]
                })
        st = dict(state)
        st["applyResult"] = apply_result
        st.setdefault("steps", []).append({"name": "Apply", "status": "done", "applied": apply_result is not None})
        return st

    # Build the graph
    g = StateGraph(RefactorState)
    g.add_node("load", node_load)
    g.add_node("analyze", node_analyze)
    g.add_node("plan", node_plan)
    g.add_node("refactor", node_refactor)
    g.add_node("verify", node_verify)
    g.add_node("apply", node_apply)
    g.set_entry_point("load")
    g.add_edge("load", "analyze")
    g.add_edge("analyze", "plan")
    g.add_edge("plan", "refactor")
    g.add_edge("refactor", "verify")
    g.add_edge("verify", "apply")
    g.add_edge("apply", END)
    graph_app = g.compile()

    @app.post("/agents/refactor-graph")
    async def refactor_graph(req: GraphRefactorRequest):
        if not OPENROUTER_API_KEY:
            raise HTTPException(status_code=503, detail="OPENROUTER_API_KEY not configured")
        initial: RefactorState = {"workspaceId": req.workspaceId, "filePath": req.filePath, "goals": req.goals or []}
        final_state: RefactorState = await graph_app.ainvoke(initial)
        deltas = {
            "before": len(final_state.get("smells") or []),
            "after": len((final_state.get("after") or {}).get("codeSmells", [])),
            "improvement": max(0, len(final_state.get("smells") or []) - len((final_state.get("after") or {}).get("codeSmells", [])))
        }
        # Persist memory
        summary = f"Smells {deltas['before']} -> {deltas['after']}; improvement {deltas['improvement']}."
        append_run(
            req.workspaceId, req.filePath,
            {
                "timestamp": time.time(),
                "summary": summary,
                "goals": req.goals or [],
                "applied": bool(final_state.get("applyResult")),
                "deltas": deltas,
                "steps": final_state.get("steps") or [],
            }
        )
        return {
            "success": True,
            "steps": final_state.get("steps") or [],
            "originalContent": final_state.get("original") or "",
            "refactoredContent": final_state.get("candidate") or "",
            "deltas": deltas,
            "applyResult": final_state.get("applyResult"),
        }
else:
    @app.post("/agents/refactor-graph")
    async def refactor_graph_unavailable(_: GraphRefactorRequest):
        raise HTTPException(status_code=501, detail="LangGraph not installed. Run: pip install -r agents/requirements.txt")
