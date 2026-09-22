# ASRS Knowledge Graph PoC — Project Context

This file is the shared context for all coding sessions on this project (Mistral Vibe in VS Code).
Read it before starting any task. Keep it updated as decisions evolve — it is the durable memory of the project.

---

## 1. Purpose and framing

This PoC is a small "wow" demo backing an applied-research program at IRT Antoine de Saint-Exupéry with three pillars:

1. **Native multimodal knowledge foundation** — structuring organizational knowledge into an agent-ready data model.
2. **Trustworthy agentic AI** — production-grade agentic architecture with uncertainty quantification.
3. **Evaluation framework** — continuous improvement via logged, measurable runs.

Every architectural element must map to a pillar (see §7). The demo is a side project, built by one person with a coding agent. Effort discipline matters: gates, timeboxes, minimum viable demo fallback.

**Vocabulary note.** ASRS data describes aviation incidents, not requirements. The requirements-engineering demos are reframed: impact analysis → anomaly-family impact, traceability matrix → report × anomaly × FAR matrix, consistency checking → coded-inconsistency candidates. Same graph mechanics, different wording.

## 2. Dataset — NASA ASRS

- **Source**: ASRS Database Online (asrs.arc.nasa.gov/search/database.html). Voluntary, confidential, sanitized incident reports from pilots, controllers, mechanics, flight attendants, dispatchers. Publicly funded, no license friction.
- **Structure**: every record has fixed (expert-coded, taxonomy-controlled) fields — ACN (unique key), date, location, aircraft make/model, flight phase, anomaly type, contributing factors, FAR references — and textual fields — narrative (sanitized reporter text) and synopsis (analyst summary).
- **Acquisition**: NO bulk API. Data is obtained by paging the query wizard and exporting CSV (.csv/.xls/.doc), max 10,000 records per export. Field selection is user-controlled, so the CSV schema is chosen by us. Multi-line narratives need quoted-field handling.
- **Scope decision**: slice to one aircraft family or anomaly domain, target ~2,000–5,000 reports.
- **Data freeze rule**: all data frozen to local files + manifest immediately after acquisition. The demo NEVER depends on live APIs. The extraction JSONL is the single source of truth.

## 3. Graph design — two layers

### Structural layer (loaded from coded fields, deterministic)

Nodes: `Report`, `Anomaly`, `Factor`, `Aircraft`, `FAR`, `Airport`.
Edges: `HAS_ANOMALY`, `HAS_FACTOR`, `CITES`, `INVOLVES_AIRCRAFT`, `AT`.

### Constructed layer (LLM-derived, post-load, with provenance)

Edge types: `DUPLICATE_OF`, `CAUSAL`, `SIMILAR_TO` — connections between reports that exist only in the narratives, invisible to any join on coded fields.

Construction pipeline:

1. **Candidate pre-filter** (cheap): same aircraft family + narrative-embedding cosine threshold + time window → a few hundred candidate pairs.
2. **LLM judge** (one call per pair): both narratives in, structured JSON verdict out — `{report_a, report_b, verdict ∈ {DUPLICATE_OF, CAUSAL, SIMILAR_TO, none}, confidence, evidence, method}`.
3. **Load as edges with provenance**: every constructed edge carries `{method, prompt_version, confidence, evidence, created}`.

This constructed layer is the research contribution (cross-document semantic joins) and the mechanism that makes all three demos work. Noise control: measure precision on a manually reviewed sample (~30 pairs), hand-correct the top-20 demo-critical pairs, surface confidence in the GUI.

## 4. Graph vs SQL — the honest position

- **Traceability matrix**: SQL's home ground. The matrix artifact itself is a cross-tab; never claim graph superiority there.
- **Consistency on coded fields only**: SQL self-join. Graph wins only on the constructed layer (linked-but-conflicting pairs).
- **Path retrieval**: the graph's structural advantage — variable-depth, mixed-edge-type traversal where recursive CTEs (text-to-SQL) fail.

Defensible justification for Neo4j: (1) agent reliability on variable-length traversal, (2) schema plasticity for post-load LLM edges, (3) native evidence-subgraph result shape for the GUI. Hedge: extraction JSONL is the source of truth; an SQL variant is one loader away. Optional pitch-grade proof: run scripted questions on both backends, show measured success rates.

## 5. Agentic architecture (LangGraph)

Single ReAct pipeline — classify → agent loop ↔ tools → synthesize/degrade. All demos are questions asked of ONE pipeline, not three.

- **AgentState** (TypedDict): question, route, messages (add_messages reducer), trace (list of ToolCallRecord), answer, citations, confidence, confidence_rationale, loop_count, error.
- **Classify node**: small LLM — agent question / chitchat / refusal.
- **Agent loop**: single ReAct node, large LLM, all tools bound, MAX_STEPS = 8. Not a router branching to separate nodes — mixed questions decompose across tools and metrics fall out of one loop's trace.
- **Tools** — curated parameterized Cypher primitives + one exploratory:
  - `semantic_search(query, k)` — vector index + one-hop expansion. Mode: retrieval.
  - `connect_reports(source_acn, target_acn, max_hops, min_confidence)` — variable-length confidence-gated path. Mode: curated.
  - `consistency_candidates(...)` — constructed-linked pairs with conflicting coded fields. Mode: curated.
  - `traceability_matrix(...)` — report × anomaly × FAR counts. Mode: curated.
  - `text_to_cypher(question)` — generate → validate (EXPLAIN) → execute, exactly ONE retry; status ∈ {ok, empty, invalid, retry_ok, retry_failed}. Mode: exploratory.
- **ToolCallRecord**: step, tool_name, args, mode, latency_ms, result_rows, status, retry_count.
- **Synthesize node**: evidence-only answers, inline [ACN] citations, rubric-based confidence from the trace — all-curated = high; any exploratory or retry = capped.
- **Degrade path**: step budget exhausted → answer + truncation disclosure, confidence ≤ 0.4.
- **Run-log**: every run appended to JSONL (question, route, trace, hops, answer, confidence) — simultaneously the metrics source and the pillar-3 evaluation dataset.
- **Models**: Mistral small for classify, large for agent loop and synthesis.

## 6. GUI (Streamlit)

- Chat panel: `st.chat_message`, history in `session_state`.
- Trace drawer (expander): route badge, tool calls with modes, Cypher, retries, latency, confidence rationale.
- Graph panel: **streamlit-agraph** (pip package wrapping vis.js; it renders, it does not query — our code fetches via Neo4j driver and maps to Node/Edge objects). Colors per node label; constructed edges styled by confidence (e.g., dashed/greyed below threshold). Known limits: no rich selection events → node details via selectbox, not click-to-inspect; set physics=False after first layout for stable stage rendering.
- Matrix view: `st.dataframe` pivot, `on_select` cell click → drill-down Cypher → subgraph in graph panel. The matrix is tabular and honestly so; the drill-down (evidence subgraph + constructed edges) is the graph moment.
- Property card: selectbox → narrative + link to ASRS record.
- `st.cache_resource` for Neo4j driver and compiled graph. Read Streamlit docs before session-state work — reruns are the classic pitfall.
- Preload one scripted question. Rehearse: full demo without touching code.

## 7. Demo narratives and pillar mapping

Three scripted questions, one pipeline:

1. **Path retrieval** (lead demo — the one where the graph is required): "connect these two reports" — variable-depth traversal mixing structural + constructed edges, confidence-gated (`WHERE r.confidence IS NULL OR r.confidence > threshold`). Pillars 1+2 visible: unanticipated relationships traversed, machine confidence governable.
2. **Traceability matrix**: cross-tab render → cell click → evidence subgraph with DUPLICATE_OF/CAUSAL edges. Matrix = deterministic layer; expansion = constructed, scored, auditable layer.
3. **Consistency candidates**: pairs linked by constructed edge but with conflicting coded fields — output is candidates for human review (Human-in-the-Loop), never verdicts.

Every answer carries inline citations and trace-based confidence. Per-edge provenance visible in property cards.

## 8. Build plan — four phases, 43 tasks

### Phase 1 — ASRS ingestion (data frozen locally)

1. Project setup: repo structure, venv, requirements, .env for API keys, README skeleton.
2. ASRS reconnaissance: explore Database Online query wizard, field selection, export limits, quirks.
3. Define acquisition scope: one aircraft family or anomaly domain, target 2,000–5,000 reports.
4. Write paging acquisition script (CSV export per query batch, rate-limit aware).
5. Handle quoted multi-line narrative fields in CSV parsing; unit-test edge cases.
6. Normalize: parse dates, split multi-value coded fields, build canonical record schema.
7. Validate: field fill rates, ACN uniqueness, value distributions; fail loudly on schema drift.
8. Freeze corpus to local files + manifest (date, query, row count).
9. Write extraction JSONL as source of truth, one normalized record per line, with schema doc.
10. Manual precision spot-check: 30 random records vs on-screen ASRS records.

### Phase 2 — Graph construction (GATE at end)

11. Write ontology document (nodes/edges above) — doubles as LLM schema prompt.
12. Docker-compose Neo4j instance + constraints/uniqueness on keys.
13. Structural loader from JSONL, idempotent MERGEs; verify counts vs manifest.
14. Narrative embeddings + Neo4j vector index; sanity-check nearest-neighbor quality.
15. Graph sanity checks: connectivity, orphan rate, degree distributions; spot-fix top-10 demo-critical reports.
16. Constructed pass 1: candidate pair generation (aircraft family + embedding cosine pre-filter + time window).
17. Constructed pass 2: LLM judge per candidate pair, structured JSON verdict.
18. Load constructed edges with full provenance properties.
19. Measure constructed-edge precision on ~30 manually reviewed pairs; hand-correct top-20 demo-critical pairs.
20. **GATE: believable graph** — verified counts, measured precision, demo pairs known-good in browser.

### Phase 3 — Minimal LangGraph engine + tools

21. LangGraph skeleton: AgentState TypedDict, classify node.
22. ToolCallRecord structure + TOOLS registry with mode tags.
23. Curated primitive 1: semantic_search, unit tests.
24. Curated primitive 2: connect_reports, verified-answer tests.
25. Curated primitive 3: consistency_candidates, verified-answer tests.
26. Curated primitive 4: traceability_matrix, verified-answer tests.
27. Exploratory tool: text_to_cypher with validation, one retry, status codes.
28. Agent loop: single ReAct node, bound tools, MAX_STEPS=8; tools executor dispatching to registry.
29. Synthesize node: citations, rubric confidence from trace (cap if exploratory/retry).
30. Degrade path: truncation disclosure, confidence ≤ 0.4.
31. JSONL run-log writer on every run.
32. CLI runner + scripted question set of 8 (one per demo ×3, no-evidence refusal, forced-retry, one exploratory).
33. Prompt/tool-description iteration to 8/8 — TIMEBOXED; improve tool descriptions over prompt magic.
34. Run-log analyzer: tool distribution, curated/exploratory ratio, hops, retry rate, latency.

### Phase 4 — Minimal Streamlit interface

35. Streamlit skeleton: cache_resource for driver + compiled graph, session_state history.
36. Chat panel wired to pipeline.
37. Trace drawer: route, tools, modes, Cypher, retries, latency, confidence rationale.
38. Graph panel: agraph renderer, colors per label, constructed edges styled by confidence.
39. Matrix view: dataframe pivot, on_select cell click → drill-down subgraph.
40. Node details: selectbox → property card (narrative + ASRS URL).
41. Citations rendered as links to ASRS records.
42. Preload scripted question; verify graceful-failure variants (empty graph, retry case).
43. Rehearsal: full demo run-through (path → matrix → consistency) without touching code.

## 9. Risks and mitigations

- **Acquisition is manual-ish** (no bulk API): freeze data first; everything inherits its quirks.
- **Constructed-edge noise**: strict per-type criteria, sample precision measurement, hand-correct demo-critical pairs, confidence visible in GUI.
- **Prompt-iteration sink**: timeboxed; tool descriptions over prompt magic.
- **Schedule collapse**: minimum viable demo = text-only chat with citations after Phase 3; Phases 1–2 gates are hard.
- **Primitives returning wrong-but-plausible results**: unit-test against manually verified answers.
- **Streamlit reruns/session state**: read docs first; cache_resource everything.
- **Confidence not calibrated**: presented honestly; the research program quantifies it properly (pillar 2).

## 10. Skills and environment of the builder

Python, classical ML, intro-level LangGraph/LangChain/Neo4j, no Streamlit experience. Working with a coding agent in VS Code. Effort target: realistic side-project pace, two hard gates, text-only fallback.

## 11. Known prior art (for positioning, not re-implementation)

- KG + deep-learning QA over NTSB/ASRS/AD documents: arXiv 2205.15952 (LREC 2022).
- LLM-ACNC aerospace requirement-text KG (MDPI Aerospace 12/6/463) — validates prompting-only extraction at ~80–95% precision.
- Chinese Airworthiness Directive KG via LLM (IJSEKE 2025): F1 81.6 NER / 88.3 RE.
- Differentiators: curated-primitives tool-calling agent, measured text-to-Cypher reliability with per-edge provenance, requirements-engineering demo features rather than generic QA.