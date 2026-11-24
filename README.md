# Verdikt

**Diploma Thesis at UTM (Technical University of Moldova)**

**Topic:** Hybrid static application analysis system for vulnerability detection based on taint analysis with exploitability validation using LLM

**Prepared by:** Bagrin Dan

**Scientific Advisor:** Alexei Arina

> Work in progress. The sections below describe the target architecture; see the roadmap at the end for what is done and what is planned.

### How it works

CodeQL finds potential vulnerabilities and records, for each one, the data-flow path from an untrusted source to a sink. Verdikt turns every path into a compact, cleaned-up piece of code and gives it to the **Verdikt LLM**, which decides whether untrusted data really reaches the sink unneutralized, i.e. whether the alert is exploitable. For the alerts that remain, **RAG** retrieves material about the vulnerability class (CWE description, typical fixes), and the **Report LLM** uses it to explain the problem and propose a fix. The result is a structured report that shows every finding together with the verdict, the confidence and the output of each component.

The system is designed to run **fully locally** (Docker + Ollama), so source code never leaves the machine. An external model can be enabled explicitly as an optional mode for demonstrations and measurements on public code.

### Pipeline

```
Code / Git repo -> CodeQL -> Verdikt LLM -> RAG -> Report LLM -> Report
```

```
[1] Source code / Git repository
          ↓
[2] CodeQL
    Builds a database and runs the security queries. Result: SARIF with alerts and taint paths.
          ↓
[3] SarifParser
    SARIF -> TaintPath objects (source -> steps -> sink) with the surrounding code.
          ↓
[4] Verdikt LLM (detector)
    Reads the cleaned path and answers: real vulnerability or false positive, with a confidence value.
    Alerts are never closed silently: the ones judged "false" go to a separate, collapsed section.
          ↓
[5] RAG
    For every real / uncertain alert retrieves material from the knowledge base by CWE
    (description, typical fixes, references).
          ↓
[6] Report LLM (advisor)
    Uses the retrieved material and the code path to write the explanation and a suggested fix,
    instead of relying on the model's own memory.
          ↓
[7] Report
    Web view and PDF: summary, findings with verdicts, advice, and the output of each component
    (what CodeQL returned, what the LLM saw and answered, timing and token usage).
```

Both LLM roles are configurable (model name, parameters) and work through a common client interface, so the pipeline does not depend on a particular model. Models are chosen by measurement on labeled benchmarks (OWASP Benchmark, Juliet, SecuriBench).

### Running

Docker Compose runs the application and the CodeQL container; the models are served by Ollama. Details: `docker-compose.yml`, `.env.example`, `docs/`.

### Roadmap / TODO

**Done**
- [x] CodeQL scan service (clone, database, analysis) with local and Docker executors
- [x] `SarifParser`: SARIF -> `TaintPath` with source code context
- [x] Scan orchestrator with streamed progress events
- [x] Web UI with a stepper and a status line

**Core pipeline**
- [ ] LLM client layer (common interface, Ollama implementation, token and timing metrics)
- [ ] Verdikt LLM (detector): prompt, answer parsing, verdict + confidence
- [ ] `Finding` record per alert (CodeQL data + LLM data) and `findings.json` per scan
- [ ] RAG over a CWE knowledge base
- [ ] Report LLM (advisor): explanation and fix suggestions grounded by the RAG material
- [ ] Report: web page + PDF export
- [ ] `ollama` service in `docker-compose.yml`
- [ ] Validation of stage outputs (SARIF parsed, LLM answer well-formed, no refusal, patch compiles)

**Quality and accuracy**
- [ ] Rules for provably safe code before the LLM (encoders by CWE, constant conditions)
- [ ] Stepwise context expansion (5 -> 10 -> 40 lines -> whole method) driven by the confidence threshold, with a hard limit
- [ ] Handling of alerts without a data-flow path (`codeFlows`)
- [ ] Confidence calibration per model (model profiles); unknown models show "not calibrated"
- [ ] Self-consistency checks and grounding checks (names mentioned by the LLM exist in the code)
- [ ] Verification of suggested fixes by re-running CodeQL on the patched code
- [ ] Model selection by measurement (local 7B/14B vs. external models) and a comparison table: quality vs. isolation

**Usability**
- [ ] Scan modes (Quick / Standard / Deep presets: query suite, `--max-paths`, flows per alert, context size)
- [ ] CodeQL settings: `security-extended` suite, `--threads`, `--max-paths`, query help in SARIF
- [ ] Automatic language detection by file extensions (Auto mode), scan of several languages in one repository
- [ ] Component outputs in the UI: what CodeQL returned, what the LLMs answered, duration and token counts per stage
- [ ] Scan time estimate before the run (linear regression over logged stage metrics: input tokens, output tokens -> seconds, per model and machine; shown as an estimate with a spread)
- [ ] Main UI ("Basic"): tabs Scan / Results / System, stage cards under the stepper, results list with a detail panel (sketch: `ml/ui_sketch/version_1.html`)
- [ ] UI version 2 ("Advanced", later, optional): cross-shaped navigation between panels with WASD / arrow keys and edge zones, preset and model settings, History and Components panels, Basic / Advanced switch (sketch: `ml/ui_sketch/version_2.html`)
- [ ] Scan history per repository with a trend chart (new / fixed / persisting findings, stable alert fingerprints from SARIF, SQLite)
- [ ] Fallback between `main` and `master` branches with a message to the user

**Optional external model mode**
- [ ] Provider adapter (Ollama and OpenAI-compatible APIs), enabled explicitly with a data-sharing warning
- [ ] Use only public code in this mode; the report states which model produced each verdict and where it ran

**Evaluation**
- [ ] Run the detector on the labeled review set with different context sizes and models
- [ ] Manually labeled real projects (PyGoat, WebGoat) for an independent check
- [ ] Comparison with similar tools (Vulnhalla, sast-triage) on the same models and benchmark
- [ ] Tests for the parser, the orchestrator and the output validators
