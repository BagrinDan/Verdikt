# Verdikt

**Diploma Thesis at UTM (Technical University of Moldova)**

**Topic:** Hybrid static application analysis system for vulnerability detection based on taint analysis with exploitability validation using LLM

**Prepared by:** Bagrin Dan

**Scientific Advisor:** Alexei Arina

### How it works:

CodeQL identifies vulnerabilities via a taint graph and passes, for example, 1000 detected and potential vulnerabilities to the ML module. The algorithm filters out roughly 60%, leaving 400. The LLM then analyzes these remaining 400 and identifies the actual, exploitable vulnerabilities by understanding the semantics and logic of the code. Finally, utilizing RAG with a vulnerability database, it generates a comprehensive and well-structured report.

### Pipeline:

```



 Code/Github Repo -> CodeQL -> ML -> LLM + RAG -> PDF Report



[1] Source Code / Git Repository
          ↓
[2] Taint Graph Construction (CodeQL / Custom AST Analyzer)
    — Identifying sources (request.args, request.form, request.values)
    — Identifying sinks (cursor.execute, db.session.execute, raw SQL)
    — Tracing data propagation from source → sink
            ↓
[3] Candidate Path Extraction
    — Each path is represented as a subgraph with intermediate nodes 
      (assignments, string concatenations, function calls, conditional checks)  
            ↓
[4] ML Pre-filtering
    — Filtering out obvious false positives to optimize token usage and reduce overhead for the LLM.    
            ↓
[4] LLM Exploitability Validation (without RAG)
    — Input: path + few-shot examples (reference vulnerable/safe cases)
    — Task: determine if the data is sanitized, even in non-standard ways
    — Output: structured JSON — verdict, confidence, reasoning_steps
            ↓
[5] Confirmed Findings Filtering
    — False positives are filtered out based on the validation results
            ↓
[6] LLM Report Generation (with RAG)
    — Retrieval from knowledge base: CWE-89, OWASP SQLi Cheat Sheet, 
      SQLAlchemy/Flask documentation on safe queries
    — Input: confirmed finding + reasoning from Step 4 + retrieved context
    — Output: coherent text — vulnerability description, risk assessment, fix recommendations
            ↓
[7] Final Report Generation
    — Rendering to PDF (WeasyPrint / ReportLab)
    — Optional: web dashboard for viewing scan history

```


Идеи:
    2 LLM & 1 ML (LLM Cascade):
        * ML фильтрует на low и high
        * Слабая LLM проверят все low. Если есть подозрительные, помечает их как escalated Low и отправляет Сильной LLM
        * Сильная LLM проверяет все high и escalated