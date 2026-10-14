# Verdikt

**Diploma Thesis at UTM (Technical University of Moldova)**

**Topic:** Hybrid static application analysis system for vulnerability detection based on taint analysis with exploitability validation using LLM

**Prepared by:** Bagrin Dan

**Scientific Advisor:** Alexei Arina

### How it works:

CodeQL identifies vulnerabilities via a taint graph and passes, for example, 1000 detected and potential vulnerabilities to the ML module. The algorithm filters out roughly 60%, leaving 400. The LLM then analyzes these remaining 400 and identifies the actual, exploitable vulnerabilities by understanding the semantics and logic of the code. Finally, utilizing RAG with a vulnerability database, it generates a comprehensive and well-structured report.

### Pipeline:

```

 Code/Github Repo -> CodeQL -> ML -> Small LLM -> Strong LLM -> Strong LLM + RAG -> PDF Report



[1] Source Code / Git Repository
          ↓
[2] ML filtering:
    ML will devide results in low and high based on parametrs
          ↓
[3] Weak LLM
    Small LLM will go fast through all low cases to find posibile vuls.
    It will mark them as escalated low vuls.
          ↓
[4] Strong LLM
    Will go through all high and escalated low vuls 
          ↓
[5] RAG
    Strong LLM will connected to RAG via API and will proced to generate .pdf results



Main plan:
    2 LLM & 1 ML (LLM Cascade):
        * ML фильтрует на low и high
        * Слабая LLM проверят все low. Если есть подозрительные, помечает их как escalated Low и отправляет Сильной LLM
        * Сильная LLM проверяет все high и escalated