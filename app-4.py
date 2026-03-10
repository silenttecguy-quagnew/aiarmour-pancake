import streamlit as st
import requests
import json
import re
from datetime import datetime

# ─── SECRETS ──────────────────────────────────────────────────────────────────
def get_secret(key, fallback=""):
    try:
        return st.secrets[key]
    except:
        return fallback

DEEPSEEK_KEY_DEFAULT = get_secret("DEEPSEEK_API_KEY")
OLLAMA_ENDPOINT_DEFAULT = get_secret("OLLAMA_ENDPOINT", "http://localhost:11434")
OLLAMA_MODEL_DEFAULT = get_secret("OLLAMA_MODEL", "llama3")

st.set_page_config(page_title="ROOMAN", page_icon="🤖", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #040810; }
    div[data-testid="stSidebar"] { background-color: #060c16; }
    h1,h2,h3 { color: #00ff94 !important; }
    .loop-box { background:#060c16; border:1px solid #0f1d2e; border-radius:10px; padding:14px; margin:6px 0; font-family:monospace; font-size:12px; color:#94a3b8; }
    .loop-analyze { border-left:4px solid #38bdf8; }
    .loop-plan    { border-left:4px solid #a855f7; }
    .loop-execute { border-left:4px solid #f59e0b; }
    .loop-observe { border-left:4px solid #00ff94; }
    .loop-repair  { border-left:4px solid #f43f5e; }
    .loop-done    { border-left:4px solid #00ff94; background:#0a1a12; }
    .mem-box { background:#060c16; border:1px solid #0f1d2e; border-radius:8px; padding:10px; margin:4px 0; font-size:11px; color:#64748b; }
    .todo-done { color:#00ff94; text-decoration:line-through; }
    .todo-active { color:#f59e0b; font-weight:bold; }
    .todo-pending { color:#334155; }
    .fault-box { background:#1a0608; border:1px solid #f43f5e; border-radius:8px; padding:12px; margin:6px 0; }
    .output-box { background:#060c16; border:1px solid #0f1d2e; border-radius:10px; padding:14px; white-space:pre-wrap; font-family:monospace; font-size:12px; color:#94a3b8; max-height:380px; overflow-y:auto; }
</style>
""", unsafe_allow_html=True)

# ─── ROOMAN AGENT DEFINITIONS ─────────────────────────────────────────────────

AGENTS = {
    "Workflow Director": {
        "emoji":"🎯", "group":"TASKLET", "role":"ORCHESTRATION",
        "description":"Master orchestrator. Decomposes goals into todo.md steps. Assigns agents. Never loses its place.",
        "system":"""You are Workflow Director for ROOMAN — a private offline-first AI agent system.
You use the CodeAct paradigm: Analyze → Plan → Execute → Observe loop.
Your job is to decompose any goal into a concrete, ordered todo list.

Return ONLY this JSON:
{
  "goal": "what we are building",
  "analysis": "what this requires and why",
  "todo": [
    {"id": 1, "agent": "Apex Coder", "task": "specific actionable task", "output": "what this produces", "depends_on": []}
  ],
  "estimated_loops": 3,
  "self_repair_triggers": ["what would cause a retry"],
  "notes": "any important context"
}
Available agents: Research Scout, Prompt Forge, QA Sentinel, Data Parser, Memory Keeper, Apex Coder, Code Reviewer, Test Brain, Debug Doctor, Arch Mind, Doc Writer.
Return ONLY valid JSON.""",
    },
    "Research Scout": {
        "emoji":"🔍", "group":"TASKLET", "role":"RESEARCH",
        "description":"Deep research. Feeds structured briefings into the loop.",
        "system":"You are Research Scout inside ROOMAN's CodeAct loop. Research any topic. Return: key facts, insights, data points, sources, actionable next steps. Be specific.",
    },
    "Prompt Forge": {
        "emoji":"⚒️", "group":"TASKLET", "role":"PROMPT ENGINEERING",
        "description":"Builds precision prompts for any agent in the loop.",
        "system":"You are Prompt Forge inside ROOMAN. Craft precise optimised prompts for any target agent. Return: optimised prompt, system prompt, usage notes.",
    },
    "QA Sentinel": {
        "emoji":"🧪", "group":"TASKLET", "role":"QUALITY ASSURANCE",
        "description":"Reviews every output. Scores it. Triggers self-repair if below threshold.",
        "system":"""You are QA Sentinel inside ROOMAN's self-repair loop.
Review any output. Return ONLY this JSON:
{
  "score": 85,
  "passed": true,
  "issues": [{"severity":"high/medium/low","description":"issue","fix":"how to fix"}],
  "corrected_output": "improved version if needed",
  "trigger_repair": false,
  "repair_instruction": "what to fix if repair needed"
}""",
    },
    "Data Parser": {
        "emoji":"🗂️", "group":"TASKLET", "role":"DATA TRANSFORMATION",
        "description":"Cleans and structures any raw data for the loop.",
        "system":"You are Data Parser inside ROOMAN. Clean and structure any raw data. Fix anomalies. Return clean structured output with schema and confidence score.",
    },
    "Memory Keeper": {
        "emoji":"🧠", "group":"TASKLET", "role":"CIRCULAR MEMORY",
        "description":"Manages the circular memory layer. Injects context into every loop iteration.",
        "system":"""You are Memory Keeper inside ROOMAN's circular memory system.
You maintain the 100-year brain — indexing all decisions, outputs, and context so knowledge is never lost.
When storing: summarise clearly with timestamp and source agent.
When retrieving: return the most relevant context for the current task.
Format: {"stored": [...], "retrieved": [...], "summary": "current state of project"}""",
    },
    "Apex Coder": {
        "emoji":"⚡", "group":"CODE BRAIN", "role":"ELITE CODE AGENT",
        "description":"Writes and executes production code. Core of the CodeAct paradigm.",
        "system":"""You are Apex Coder inside ROOMAN's CodeAct execution engine.
You write and explain production-ready code. You operate in the Execute phase of the Analyze→Plan→Execute→Observe loop.
Rules: (1) Always explain your approach. (2) Write complete working code — no placeholders. (3) Include error handling. (4) Flag anything that could cause a fault. (5) If given previous output as context, improve on it.
Always end with: OBSERVE: [what to check to confirm this worked]""",
    },
    "Code Reviewer": {
        "emoji":"🔬", "group":"CODE BRAIN", "role":"REVIEW & CRITIQUE",
        "description":"Reviews code in the Observe phase. Triggers repair if issues found.",
        "system":"""You are Code Reviewer inside ROOMAN's Observe phase.
Review code exhaustively. Return JSON:
{"score":85,"passed":true,"critical_issues":[],"all_issues":[],"fixed_code":"improved code if needed","trigger_repair":false}""",
    },
    "Test Brain": {
        "emoji":"🧬", "group":"CODE BRAIN", "role":"TEST ENGINEERING",
        "description":"Generates tests. Validates execution in the Observe phase.",
        "system":"You are Test Brain inside ROOMAN. Write comprehensive tests for any code. Cover: unit, integration, edge cases, error states. Estimate coverage. Flag gaps.",
    },
    "Debug Doctor": {
        "emoji":"🩺", "group":"CODE BRAIN", "role":"SELF-REPAIR",
        "description":"Self-repair engine. Activates when a fault is detected in any loop.",
        "system":"""You are Debug Doctor — ROOMAN's self-repair engine.
You activate when a fault is detected in the execution loop.
Find the ROOT CAUSE (not symptoms). Return:
{
  "root_cause": "exactly what went wrong",
  "fault_type": "logic/syntax/dependency/timeout/hallucination",
  "fix": "complete corrected code or output",
  "prevention": "how to stop this recurring",
  "confidence": 95,
  "loop_again": true
}""",
    },
    "Arch Mind": {
        "emoji":"🏛️", "group":"CODE BRAIN", "role":"SYSTEM ARCHITECTURE",
        "description":"Designs the system in the Plan phase. Sets the blueprint for execution.",
        "system":"You are Arch Mind inside ROOMAN's Plan phase. Design robust scalable architectures. Justify every tech choice. Cover: components, data flow, infra, tradeoffs, cost.",
    },
    "Doc Writer": {
        "emoji":"📖", "group":"CODE BRAIN", "role":"DOCUMENTATION",
        "description":"Documents everything produced by the loop.",
        "system":"You are Doc Writer inside ROOMAN. Write clear complete documentation for any output. Include: overview, setup, usage, API reference.",
    },
}

# ─── SESSION STATE ────────────────────────────────────────────────────────────

DEFAULTS = {
    "log": [],
    "todo": [],          # The todo.md — source of truth
    "current_todo": 0,   # Which todo item we're on
    "outputs": {},       # All agent outputs
    "circular_memory": [], # Circular memory buffer (last 20 items)
    "loop_count": 0,     # How many CodeAct loops run
    "fault_count": 0,    # Self-repair triggers
    "tasks_done": 0,
    "executing": False,
    "waiting_approval": False,
    "plan": None,
    "phase": "idle",     # analyze | plan | execute | observe | repair | done
    "repair_attempts": 0,
    "max_repairs": 3,
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── BRAIN API ────────────────────────────────────────────────────────────────

def call_brain(system, message, brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl):
    try:
        if brain == "DeepSeek API":
            res = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                json={"model": "deepseek-chat", "messages": [{"role":"system","content":system},{"role":"user","content":message}], "max_tokens":3000, "temperature":0.7},
                timeout=90
            )
            data = res.json()
            if "error" in data:
                return None, f"API Error: {data['error']['message']}"
            return data["choices"][0]["message"]["content"], None

        elif brain == "Ollama Local":
            res = requests.post(
                f"{ollama_ep.rstrip('/')}/api/chat",
                json={"model": ollama_mdl, "messages":[{"role":"system","content":system},{"role":"user","content":message}], "stream":False},
                timeout=180
            )
            return res.json().get("message",{}).get("content","No response."), None

        elif brain == "LM Studio / Custom":
            res = requests.post(
                f"{custom_url.rstrip('/')}/chat/completions",
                headers={"Content-Type":"application/json","Authorization":f"Bearer {api_key}"},
                json={"model":custom_mdl,"messages":[{"role":"system","content":system},{"role":"user","content":message}],"max_tokens":3000},
                timeout=180
            )
            data = res.json()
            if "error" in data:
                return None, f"API Error: {data['error']['message']}"
            return data["choices"][0]["message"]["content"], None

    except Exception as e:
        return None, f"Connection error: {str(e)}"

def parse_json(text):
    """Safely extract JSON from any response"""
    try:
        clean = text.strip()
        for marker in ["```json", "```"]:
            if marker in clean:
                clean = clean.split(marker)[1].split("```")[0].strip()
                break
        return json.loads(clean), None
    except Exception as e:
        return None, str(e)

def add_memory(agent, content, phase):
    """Add to circular memory buffer — keeps last 20 items"""
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "agent": agent,
        "phase": phase,
        "content": content[:400],
    }
    st.session_state.circular_memory.append(entry)
    if len(st.session_state.circular_memory) > 20:
        st.session_state.circular_memory.pop(0)

def get_memory_context():
    """Get recent memory as context string"""
    if not st.session_state.circular_memory:
        return ""
    recent = st.session_state.circular_memory[-5:]
    return "\n\nCircular Memory (recent context):\n" + "\n".join([
        f"[{m['time']} | {m['agent']} | {m['phase']}]: {m['content']}"
        for m in recent
    ])

def log(msg, t="normal"):
    st.session_state.log.append({"time": datetime.now().strftime("%H:%M:%S"), "msg": msg, "type": t})

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("# 🤖 ROOMAN")
    st.caption("Private · Offline-First · 100-Year Brain")
    st.markdown("---")

    brain = st.radio("🧠 Brain", ["DeepSeek API", "Ollama Local", "LM Studio / Custom"], label_visibility="collapsed")

    api_key = DEEPSEEK_KEY_DEFAULT
    ollama_ep = OLLAMA_ENDPOINT_DEFAULT
    ollama_mdl = OLLAMA_MODEL_DEFAULT
    custom_url = ""
    custom_mdl = ""

    if brain == "DeepSeek API":
        api_key = st.text_input("API Key", type="password", value=DEEPSEEK_KEY_DEFAULT, placeholder="sk-...")
        if DEEPSEEK_KEY_DEFAULT:
            st.success("✅ Key auto-loaded")
        else:
            st.caption("Enter key or save in Streamlit Secrets")

    elif brain == "Ollama Local":
        ollama_ep = st.text_input("Endpoint", value=OLLAMA_ENDPOINT_DEFAULT)
        ollama_mdl = st.text_input("Model", value=OLLAMA_MODEL_DEFAULT)
        st.success("✅ Free local — no key")

    elif brain == "LM Studio / Custom":
        custom_url = st.text_input("Base URL", placeholder="http://localhost:1234/v1")
        api_key = st.text_input("Key (if needed)", type="password")
        custom_mdl = st.text_input("Model", placeholder="qwen3")

    st.markdown("---")
    st.markdown("### 📊 ROOMAN Stats")

    phase_colors = {"idle":"⚫","analyze":"🔵","plan":"🟣","execute":"🟡","observe":"🟢","repair":"🔴","done":"✅"}
    st.markdown(f"**Phase:** {phase_colors.get(st.session_state.phase,'⚫')} `{st.session_state.phase.upper()}`")

    c1, c2 = st.columns(2)
    c1.metric("Loop Count", st.session_state.loop_count)
    c2.metric("Self-Repairs", st.session_state.fault_count)
    c1.metric("Tasks Done", st.session_state.tasks_done)
    c2.metric("Memory Items", len(st.session_state.circular_memory))

    st.markdown("---")
    st.markdown("### 📝 Todo.md")
    if st.session_state.todo:
        for i, item in enumerate(st.session_state.todo):
            cur = st.session_state.current_todo
            if i < cur:
                st.markdown(f'<div class="todo-done">✅ {item.get("id","")}: {item.get("agent","")} — {item.get("task","")[:40]}...</div>', unsafe_allow_html=True)
            elif i == cur:
                st.markdown(f'<div class="todo-active">▶ {item.get("id","")}: {item.get("agent","")} — {item.get("task","")[:40]}...</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="todo-pending">⏳ {item.get("id","")}: {item.get("agent","")}</div>', unsafe_allow_html=True)
    else:
        st.caption("Empty — set a goal to populate")

    st.markdown("---")
    if st.button("🔄 Full Reset", use_container_width=True):
        for k, v in DEFAULTS.items():
            st.session_state[k] = v if not isinstance(v, list) else []
        st.rerun()

# ─── MAIN ─────────────────────────────────────────────────────────────────────

st.markdown("# 🤖 ROOMAN — 100-Year Brain")
st.markdown("*CodeAct Loop · Circular Memory · Self-Repair · Private & Offline-First*")

# Phase indicator bar
phases = ["analyze", "plan", "execute", "observe", "repair"]
cols = st.columns(5)
phase_info = {
    "analyze": ("🔵", "ANALYZE"),
    "plan":    ("🟣", "PLAN"),
    "execute": ("🟡", "EXECUTE"),
    "observe": ("🟢", "OBSERVE"),
    "repair":  ("🔴", "SELF-REPAIR"),
}
for i, (p, (icon, label)) in enumerate(phase_info.items()):
    active = st.session_state.phase == p
    cols[i].markdown(f"{'**' if active else ''}{icon} {label}{'**' if active else ''}")

st.markdown("---")

tabs = st.tabs(["🔄 CodeAct Loop", "🤖 Single Agent", "📝 Todo.md", "🧠 Memory", "📋 Outputs", "📊 Log"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CODEACT LOOP
# ══════════════════════════════════════════════════════════════════════════════

with tabs[0]:
    st.markdown("### 🔄 CodeAct Loop — Analyze → Plan → Execute → Observe → (Self-Repair if needed)")

    # ── IDLE: Set Goal ──
    if st.session_state.phase == "idle":
        st.info("ROOMAN is ready. Set a goal and it will Analyze, Plan, Execute, and self-repair if anything goes wrong.")
        goal = st.text_area(
            "Goal:",
            height=100,
            placeholder="Example: Rebuild my AI business dashboard with Agents, Avatars, Social, Email, Leads and Revenue tabs. Include MRR/ARR metrics. Dark theme. DeepSeek API.",
        )

        # Pre-load memory
        st.markdown("**Pre-load context into memory (optional):**")
        mem_preload = st.text_area("Brand voice, business context, existing code...", height=60, placeholder="Paste anything you want agents to know from the start")

        if st.button("🚀 START ROOMAN", type="primary", use_container_width=True):
            if not goal.strip():
                st.warning("Enter a goal.")
            else:
                if mem_preload.strip():
                    add_memory("User", mem_preload, "preload")
                    log("🧠 Pre-loaded context into memory", "memory")

                st.session_state.phase = "analyze"
                st.session_state.plan = {"goal": goal}
                log(f"🚀 Goal set: {goal[:80]}...", "start")
                st.rerun()

    # ── ANALYZE PHASE ──
    elif st.session_state.phase == "analyze":
        st.markdown("#### 🔵 ANALYZE — Workflow Director decomposing your goal")
        goal = st.session_state.plan.get("goal", "")
        st.info(f"**Goal:** {goal}")

        with st.spinner("🎯 Workflow Director analyzing..."):
            mem_ctx = get_memory_context()
            result, err = call_brain(
                AGENTS["Workflow Director"]["system"],
                f"Goal: {goal}{mem_ctx}",
                brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl
            )

        if err:
            st.error(f"Brain error: {err}")
            st.session_state.phase = "idle"
        else:
            plan_data, parse_err = parse_json(result)
            if parse_err or not plan_data:
                # Couldn't parse — still show and let user proceed
                st.warning("Plan returned as text (not JSON). Review below.")
                st.markdown(f'<div class="loop-box loop-analyze">{result}</div>', unsafe_allow_html=True)
                st.session_state.plan = {"goal": goal, "raw": result, "todo": [], "analysis": result}
                st.session_state.todo = []
            else:
                st.session_state.plan = plan_data
                st.session_state.todo = plan_data.get("todo", [])
                st.session_state.plan["goal"] = goal

                add_memory("Workflow Director", plan_data.get("analysis",""), "analyze")
                log(f"🔵 Analyzed — {len(st.session_state.todo)} tasks planned", "analyze")

                st.markdown(f'<div class="loop-box loop-analyze"><strong>Analysis:</strong><br>{plan_data.get("analysis","")}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="loop-box loop-plan"><strong>Self-repair triggers:</strong><br>{", ".join(plan_data.get("self_repair_triggers",[]))}</div>', unsafe_allow_html=True)

            st.session_state.loop_count += 1
            st.session_state.phase = "plan"
            st.rerun()

    # ── PLAN PHASE — Show todo, get approval ──
    elif st.session_state.phase == "plan":
        st.markdown("#### 🟣 PLAN — Review todo.md before execution")
        plan = st.session_state.plan
        st.info(f"**Goal:** {plan.get('goal','')}")

        if st.session_state.todo:
            st.markdown("**Todo.md — Execution Order:**")
            for item in st.session_state.todo:
                agent_emoji = AGENTS.get(item.get("agent",""),{}).get("emoji","🤖")
                st.markdown(f"""
<div class="loop-box loop-plan">
<strong>#{item.get('id','')} {agent_emoji} {item.get('agent','')}</strong><br>
<span style="color:#94a3b8">{item.get('task','')}</span><br>
<span style="color:#334155;font-size:11px">→ {item.get('output','')}</span>
</div>""", unsafe_allow_html=True)

            if plan.get("notes"):
                st.caption(f"📝 Notes: {plan['notes']}")
        else:
            st.markdown(f'<div class="loop-box loop-plan">{plan.get("raw","No plan generated")}</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ APPROVE — START EXECUTE", type="primary", use_container_width=True):
                st.session_state.phase = "execute"
                st.session_state.current_todo = 0
                st.session_state.repair_attempts = 0
                log("✅ Plan approved — entering Execute phase", "approve")
                st.rerun()
        with col2:
            if st.button("❌ REJECT — REANALYZE", use_container_width=True):
                st.session_state.phase = "analyze"
                log("❌ Rejected — reanalyzing", "warn")
                st.rerun()

    # ── EXECUTE PHASE ──
    elif st.session_state.phase == "execute":
        todo = st.session_state.todo
        cur = st.session_state.current_todo

        st.markdown(f"#### 🟡 EXECUTE — Loop #{st.session_state.loop_count}")

        # Progress
        if todo:
            st.progress(cur / len(todo) if todo else 0)
            st.caption(f"Task {cur+1} of {len(todo)}")

            if cur < len(todo):
                item = todo[cur]
                agent_name = item.get("agent","")
                task = item.get("task","")

                agent = AGENTS.get(agent_name)
                if not agent:
                    # Fuzzy match
                    for n, d in AGENTS.items():
                        if agent_name.lower() in n.lower():
                            agent = d
                            agent_name = n
                            break

                if agent:
                    st.markdown(f'<div class="loop-box loop-execute"><strong>▶ {agent.get("emoji","🤖")} {agent_name}</strong><br>{task}</div>', unsafe_allow_html=True)

                    mem_ctx = get_memory_context()
                    # Include last output as context
                    last_ctx = ""
                    if st.session_state.outputs:
                        last_key = list(st.session_state.outputs.keys())[-1]
                        last_ctx = f"\n\nPrevious output ({last_key}):\n{st.session_state.outputs[last_key][:800]}"

                    with st.spinner(f"⚡ {agent_name} executing..."):
                        result, err = call_brain(
                            agent["system"],
                            task + mem_ctx + last_ctx,
                            brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl
                        )

                    if err:
                        st.session_state.phase = "repair"
                        st.session_state.plan["repair_context"] = {"error": err, "agent": agent_name, "task": task}
                        log(f"🔴 Fault detected in {agent_name}: {err}", "repair")
                        st.rerun()
                    else:
                        output_key = f"#{cur+1} {agent_name}"
                        st.session_state.outputs[output_key] = result
                        add_memory(agent_name, result, "execute")
                        st.session_state.tasks_done += 1
                        log(f"✅ #{cur+1} {agent_name} — done", "success")

                        st.markdown(f'<div class="loop-box loop-done"><strong>✅ {agent_name} output:</strong><br>{result[:600]}{"..." if len(result)>600 else ""}</div>', unsafe_allow_html=True)

                        st.download_button(f"⬇ Download #{cur+1}", data=result, file_name=f"step_{cur+1}_{agent_name.replace(' ','_')}.txt", mime="text/plain")

                        # Move to observe
                        st.session_state.plan["last_output"] = result
                        st.session_state.plan["last_agent"] = agent_name
                        st.session_state.current_todo = cur + 1
                        st.session_state.phase = "observe"
                        st.rerun()
                else:
                    st.warning(f"Agent '{agent_name}' not found — skipping")
                    st.session_state.current_todo = cur + 1
                    if cur + 1 >= len(todo):
                        st.session_state.phase = "done"
                    st.rerun()
            else:
                st.session_state.phase = "done"
                st.rerun()
        else:
            st.warning("No todo items — going to single agent mode")
            st.session_state.phase = "idle"

    # ── OBSERVE PHASE ──
    elif st.session_state.phase == "observe":
        st.markdown("#### 🟢 OBSERVE — QA Sentinel reviewing output")
        last_output = st.session_state.plan.get("last_output","")
        last_agent = st.session_state.plan.get("last_agent","")
        cur = st.session_state.current_todo
        todo = st.session_state.todo

        with st.spinner("🧪 QA Sentinel reviewing..."):
            result, err = call_brain(
                AGENTS["QA Sentinel"]["system"],
                f"Review this output from {last_agent}:\n\n{last_output}",
                brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl
            )

        if err:
            # Can't review — just continue
            log(f"⚠️ QA couldn't run: {err} — continuing", "warn")
            if cur >= len(todo):
                st.session_state.phase = "done"
            else:
                st.session_state.phase = "execute"
            st.rerun()
        else:
            qa_data, parse_err = parse_json(result)

            if qa_data:
                score = qa_data.get("score", 100)
                passed = qa_data.get("passed", True)
                trigger_repair = qa_data.get("trigger_repair", False)

                add_memory("QA Sentinel", f"Score: {score}, Passed: {passed}", "observe")

                col1, col2 = st.columns(2)
                col1.metric("QA Score", f"{score}/100")
                col2.metric("Status", "✅ PASSED" if passed else "❌ FAILED")

                if qa_data.get("issues"):
                    for issue in qa_data["issues"]:
                        st.markdown(f'<div class="loop-box loop-observe"><strong>{issue.get("severity","").upper()}:</strong> {issue.get("description","")}<br><em>Fix: {issue.get("fix","")}</em></div>', unsafe_allow_html=True)

                if trigger_repair or not passed and st.session_state.repair_attempts < st.session_state.max_repairs:
                    st.session_state.fault_count += 1
                    st.session_state.repair_attempts += 1
                    st.session_state.plan["repair_context"] = {
                        "error": qa_data.get("repair_instruction","QA failed"),
                        "agent": last_agent,
                        "task": todo[cur-1].get("task","") if cur > 0 else "",
                        "bad_output": last_output,
                    }
                    log(f"🔴 QA triggered self-repair (score:{score}) — attempt {st.session_state.repair_attempts}/{st.session_state.max_repairs}", "repair")
                    st.session_state.phase = "repair"
                    st.rerun()
                else:
                    log(f"🟢 QA passed (score:{score}) — continuing", "observe")
                    if cur >= len(todo):
                        st.session_state.phase = "done"
                    else:
                        st.session_state.phase = "execute"
                    st.rerun()
            else:
                # JSON parse failed — just continue
                log("🟢 QA reviewed (text mode) — continuing", "observe")
                if cur >= len(todo):
                    st.session_state.phase = "done"
                else:
                    st.session_state.phase = "execute"
                st.rerun()

    # ── REPAIR PHASE ──
    elif st.session_state.phase == "repair":
        repair_ctx = st.session_state.plan.get("repair_context",{})
        attempt = st.session_state.repair_attempts
        max_rep = st.session_state.max_repairs

        st.markdown(f"#### 🔴 SELF-REPAIR — Attempt {attempt}/{max_rep}")
        st.markdown(f'<div class="fault-box"><strong>🩺 Debug Doctor activating...</strong><br>Agent: {repair_ctx.get("agent","")}<br>Issue: {repair_ctx.get("error","")}</div>', unsafe_allow_html=True)

        with st.spinner("🩺 Debug Doctor diagnosing and repairing..."):
            repair_prompt = f"""
Fault detected in ROOMAN execution loop.
Agent that failed: {repair_ctx.get("agent","")}
Original task: {repair_ctx.get("task","")}
Error/Issue: {repair_ctx.get("error","")}
Bad output (if any): {repair_ctx.get("bad_output","")[:500]}
Circular memory context: {get_memory_context()}

Diagnose and fix this. Return the corrected output."""

            result, err = call_brain(
                AGENTS["Debug Doctor"]["system"],
                repair_prompt,
                brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl
            )

        if err:
            st.error(f"Debug Doctor also failed: {err}")
            if attempt >= max_rep:
                st.error("Max repairs reached. Manual intervention needed.")
                st.session_state.phase = "idle"
                log(f"💀 Max repairs reached — manual needed", "fault")
            else:
                st.session_state.phase = "idle"
        else:
            repair_data, _ = parse_json(result)

            st.markdown(f'<div class="loop-box loop-repair">{result[:800]}</div>', unsafe_allow_html=True)

            if repair_data:
                confidence = repair_data.get("confidence", 0)
                loop_again = repair_data.get("loop_again", True)
                fixed = repair_data.get("fix", result)
                root = repair_data.get("root_cause","")
                fault_type = repair_data.get("fault_type","unknown")

                st.metric("Repair Confidence", f"{confidence}%")
                st.markdown(f"**Root Cause:** {root}")
                st.markdown(f"**Fault Type:** `{fault_type}`")

                # Save repaired output
                cur = st.session_state.current_todo
                agent_name = repair_ctx.get("agent","")
                output_key = f"#{cur} {agent_name} [REPAIRED]"
                st.session_state.outputs[output_key] = fixed
                add_memory("Debug Doctor", f"Repaired {agent_name}: {root}", "repair")
                log(f"🩺 Repaired — {fault_type} — confidence: {confidence}%", "repair")

                if loop_again and attempt < max_rep:
                    st.success("✅ Repair complete — continuing loop")
                    st.session_state.plan["last_output"] = fixed
                    st.session_state.phase = "observe"
                else:
                    st.warning("⚠️ Repair done — continuing with best available output")
                    st.session_state.phase = "execute" if cur < len(st.session_state.todo) else "done"
                st.rerun()
            else:
                # Text repair — save and continue
                cur = st.session_state.current_todo
                st.session_state.outputs[f"#{cur} Repaired"] = result
                st.session_state.plan["last_output"] = result
                add_memory("Debug Doctor", result[:300], "repair")
                log("🩺 Repair complete (text mode)", "repair")
                st.session_state.phase = "observe"
                st.rerun()

    # ── DONE ──
    elif st.session_state.phase == "done":
        st.success("🎉 ROOMAN COMPLETE — All tasks executed")
        st.markdown(f"**Loops run:** {st.session_state.loop_count} | **Self-repairs:** {st.session_state.fault_count} | **Tasks done:** {st.session_state.tasks_done}")

        all_out = "\n\n".join([f"{'='*50}\n{k}\n{'='*50}\n{v}" for k, v in st.session_state.outputs.items()])
        st.download_button("⬇ Download Complete Output", data=all_out, file_name="rooman_complete_output.txt", mime="text/plain", use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Run New Goal", type="primary", use_container_width=True):
                for k in ["phase","todo","current_todo","executing","plan","repair_attempts","loop_count","fault_count","tasks_done"]:
                    st.session_state[k] = DEFAULTS[k]
                st.rerun()
        with col2:
            if st.button("📋 View All Outputs", use_container_width=True):
                st.session_state["_show_outputs"] = True

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SINGLE AGENT
# ══════════════════════════════════════════════════════════════════════════════

with tabs[1]:
    st.markdown("### 🤖 Single Agent — Direct task with memory context")

    col1, col2 = st.columns([1, 2])
    with col1:
        sel = st.selectbox("Agent", [f"{d['emoji']} {n}" for n, d in AGENTS.items()])
        aname = sel.split(" ",1)[1] if " " in sel else sel
        agent = AGENTS.get(aname, list(AGENTS.values())[0])
        st.markdown(f"**{agent['role']}** · {agent['group']}")
        st.markdown(f"*{agent['description']}*")

    with col2:
        task = st.text_area("Task:", height=130, placeholder=f"Tell {aname} what to do...")
        use_mem = st.checkbox("Inject circular memory context", value=True)

        if st.button(f"▶ RUN {aname}", type="primary", use_container_width=True):
            if task.strip():
                full = task + (get_memory_context() if use_mem else "")
                with st.spinner(f"{aname} working..."):
                    result, err = call_brain(agent["system"], full, brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl)

                if err:
                    st.error(err)
                else:
                    key = f"[Single] {aname}"
                    st.session_state.outputs[key] = result
                    add_memory(aname, result, "single")
                    st.session_state.tasks_done += 1
                    log(f"✅ {aname} — single task done", "success")

                    st.markdown("### ✅ Output")
                    st.markdown(f'<div class="output-box">{result}</div>', unsafe_allow_html=True)

                    c1, c2 = st.columns(2)
                    with c1:
                        st.download_button("⬇ Download", data=result, file_name=f"{aname.replace(' ','_')}_output.txt", mime="text/plain")
                    with c2:
                        if st.button("🧪 Send to QA"):
                            with st.spinner("QA reviewing..."):
                                qa, _ = call_brain(AGENTS["QA Sentinel"]["system"], f"Review:\n\n{result}", brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl)
                            if qa:
                                st.markdown(f'<div class="output-box">{qa}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — TODO.MD
# ══════════════════════════════════════════════════════════════════════════════

with tabs[2]:
    st.markdown("### 📝 Todo.md — Source of Truth")
    st.caption("ROOMAN never loses its place. This is the live execution tracker.")

    if st.session_state.todo:
        cur = st.session_state.current_todo
        for item in st.session_state.todo:
            i = item.get("id",0) - 1
            if i < cur:
                css = "todo-done"; icon = "✅"
            elif i == cur:
                css = "todo-active"; icon = "▶"
            else:
                css = "todo-pending"; icon = "⏳"
            agent_emoji = AGENTS.get(item.get("agent",""),{}).get("emoji","🤖")
            st.markdown(f'<div class="{css}">{icon} #{item.get("id","")} {agent_emoji} <strong>{item.get("agent","")}</strong> — {item.get("task","")}<br><small style="color:#334155">→ {item.get("output","")}</small></div>', unsafe_allow_html=True)
    else:
        st.info("Todo list empty — set a goal in CodeAct Loop to populate.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — CIRCULAR MEMORY
# ══════════════════════════════════════════════════════════════════════════════

with tabs[3]:
    st.markdown("### 🧠 Circular Memory — 100-Year Brain")
    st.caption("Last 20 items. Auto-injected into every agent call. Knowledge is never lost.")

    if st.session_state.circular_memory:
        for m in reversed(st.session_state.circular_memory):
            phase_icon = {"analyze":"🔵","plan":"🟣","execute":"🟡","observe":"🟢","repair":"🔴","single":"⚪","preload":"💜","memory":"🧠"}.get(m.get("phase",""),"⚪")
            st.markdown(f'<div class="mem-box">{phase_icon} <strong>[{m["time"]}] {m["agent"]}</strong> <em>({m["phase"]})</em><br>{m["content"]}</div>', unsafe_allow_html=True)

        if st.button("🗑️ Clear Memory"):
            st.session_state.circular_memory = []
            st.rerun()
    else:
        st.info("Empty — fills as agents execute.")

    st.markdown("---")
    st.markdown("### ➕ Pre-load Context")
    mk = st.text_input("Label")
    mv = st.text_area("Content (brand voice, business context, code snippets...)", height=80)
    if st.button("💾 Add to Memory") and mk and mv:
        add_memory("User", f"{mk}: {mv}", "preload")
        st.success(f"✅ Added: {mk}")
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — OUTPUTS
# ══════════════════════════════════════════════════════════════════════════════

with tabs[4]:
    st.markdown("### 📋 All Outputs")
    if st.session_state.outputs:
        all_out = "\n\n".join([f"{'='*50}\n{k}\n{'='*50}\n{v}" for k, v in st.session_state.outputs.items()])
        st.download_button("⬇ Download ALL", data=all_out, file_name="rooman_all_outputs.txt", mime="text/plain", use_container_width=True)
        st.markdown("---")
        for k, v in st.session_state.outputs.items():
            with st.expander(f"📄 {k}"):
                st.markdown(f'<div class="output-box">{v}</div>', unsafe_allow_html=True)
                st.download_button("⬇", data=v, file_name=f"{k[:30].replace(' ','_')}.txt", mime="text/plain", key=f"dl_{k}")
    else:
        st.info("No outputs yet.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — LOG
# ══════════════════════════════════════════════════════════════════════════════

with tabs[5]:
    st.markdown("### 📊 Execution Log")
    icons = {"success":"🟢","plan":"🔵","analyze":"🔵","observe":"🟢","repair":"🔴","fault":"💀","warn":"🟡","start":"🚀","approve":"✅","memory":"🧠","normal":"⚪"}
    if st.session_state.log:
        for e in reversed(st.session_state.log):
            st.markdown(f"`{e['time']}` {icons.get(e['type'],'⚪')} {e['msg']}")
    else:
        st.info("No log yet.")
    if st.button("🗑️ Clear Log"):
        st.session_state.log = []
        st.rerun()
