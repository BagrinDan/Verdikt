from dataclasses import dataclass


@dataclass(frozen = True)
class BenchmarkCase:
    test_name: str 
    category: str # например: sqli, xss
    is_vulnerable: str 
    cwe: str