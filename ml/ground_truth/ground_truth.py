
from __future__ import annotations
 
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Iterable, List, Optional, Set


from ml.ground_truth.benchmark_case import BenchmarkCase
from ml.ground_truth.label_status import LabelStatus
from ml.ground_truth.label_path import LabeledPath


TEST_NAME_RE = re.compile(r"(BenchmarkTest\d+)")
 
TAINT_CATEGORIES = frozenset({
    "cmdi", "codeinj", "deserialization", "ldapi", "pathtraver",
    "redirect", "sqli", "xpathi", "xss", "xxe",
})
 
MIN_FP_FOR_TRAINING = 100

class GroundTruth:
    def __init__(self):
        pass


    def load_expected_results(csv_path: Path) -> Dict[str, BenchmarkCase]:
        """Читает expectedresults-*.csv.

        Формат (одинаков для Java 1.2 и Python 0.1):
            # test name, category, real vulnerability, cwe, Benchmark version: ...
            BenchmarkTest00001,pathtraver,true,22
        """
        cases: Dict[str, BenchmarkCase] = {}
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            for lineno, raw in enumerate(f, start=1):
                if not raw.strip() or raw.lstrip().startswith("#"):
                    continue
                row = next(csv.reader([raw]))
                if len(row) < 4:
                    raise ValueError(f"{csv_path}:{lineno}: ожидалось 4 колонки, получено {len(row)}: {raw!r}")
                name, category, real, cwe = (c.strip() for c in row[:4])
                if real.lower() not in ("true", "false"):
                    raise ValueError(f"{csv_path}:{lineno}: 'real vulnerability' должно быть true/false: {real!r}")
                if not cwe.isdigit():
                    raise ValueError(f"{csv_path}:{lineno}: CWE должен быть числом: {cwe!r}")
                if name in cases:
                    raise ValueError(f"{csv_path}:{lineno}: дубликат теста {name}")
                cases[name] = BenchmarkCase(
                    test_name=name,
                    category=category.lower(),
                    is_vulnerable=real.lower() == "true",
                    cwe=f"CWE-{int(cwe)}",
                )
        if not cases:
            raise ValueError(f"{csv_path}: не найдено ни одной строки разметки")
        return cases


    # --------------------------------------------------------------------- разметка

    def extract_test_name(*file_paths: Optional[str]) -> Optional[str]:
        for p in file_paths:
            if p:
                m = TEST_NAME_RE.search(p)
                if m:
                    return m.group(1)
        return None


    def label_path(self, tp, truth: Dict[str, BenchmarkCase]) -> LabeledPath:
        """Размечает один алерт.

        Метка ставится, только если совпали и тест-кейс, и CWE. Иначе, например, SQLi-алерт
        в файле XSS-теста получил бы чужую метку.
        """
        test_name = self.extract_test_name(
            getattr(tp, "primary_file", None),
            getattr(getattr(tp, "sink", None), "file_path", None),
            getattr(getattr(tp, "source", None), "file_path", None),
        )
        case = truth.get(test_name) if test_name else None
        if case is None:
            return LabeledPath(tp.finding_id, test_name, None, LabelStatus.NOT_A_TEST)

        if case.cwe not in (getattr(tp, "cwe_tags", None) or []):
            return LabeledPath(tp.finding_id, test_name, case.category, LabelStatus.CWE_MISMATCH)

        status = LabelStatus.TP if case.is_vulnerable else LabelStatus.FP
        return LabeledPath(tp.finding_id, test_name, case.category, status)


    def label_all(self, paths: Iterable, truth: Dict[str, BenchmarkCase]) -> List[LabeledPath]:
        return [self.label_path(tp, truth) for tp in paths]


    # ----------------------------------------------------------------------- отчёт

    def coverage_report(
        truth: Dict[str, BenchmarkCase],
        labeled: List[LabeledPath],
        categories: Optional[Set[str]] = None,
    ) -> Dict[str, dict]:
        """Сколько тестов и алертов по классам; сколько реальных уязвимостей CodeQL пропустил.

        categories=None берёт TAINT_CATEGORIES.
        """
        scope = set(categories) if categories is not None else set(TAINT_CATEGORIES)
        rep: Dict[str, dict] = defaultdict(lambda: dict(
            tests_real=0, tests_safe=0, alerts_tp=0, alerts_fp=0,
            alerts_cwe_mismatch=0, real_detected=0, real_missed=0,
        ))

        for case in truth.values():
            if case.category in scope:
                rep[case.category]["tests_real" if case.is_vulnerable else "tests_safe"] += 1

        detected: Set[str] = set()
        for lp in labeled:
            if lp.category not in scope:
                continue
            if lp.status is LabelStatus.TP:
                rep[lp.category]["alerts_tp"] += 1
                detected.add(lp.test_name)
            elif lp.status is LabelStatus.FP:
                rep[lp.category]["alerts_fp"] += 1
            elif lp.status is LabelStatus.CWE_MISMATCH:
                rep[lp.category]["alerts_cwe_mismatch"] += 1

        for case in truth.values():
            if case.category in scope and case.is_vulnerable:
                key = "real_detected" if case.test_name in detected else "real_missed"
                rep[case.category][key] += 1

        total = dict(tests_real=0, tests_safe=0, alerts_tp=0, alerts_fp=0,
                    alerts_cwe_mismatch=0, real_detected=0, real_missed=0)
        for row in rep.values():
            for k in total:
                total[k] += row[k]
        out = dict(sorted(rep.items()))
        out["TOTAL"] = total
        out["_not_a_test"] = {"alerts": sum(1 for lp in labeled if lp.status is LabelStatus.NOT_A_TEST)}
        return out


    def format_report(rep: Dict[str, dict]) -> str:
        head = (f"{'category':16s}{'real':>6s}{'safe':>6s} | {'TP':>5s}{'FP':>5s}{'other':>6s}"
                f" | {'found':>6s}{'missed':>7s} | {'precision':>9s}{'recall':>8s}")
        lines = [head, "-" * len(head)]

        def row(name: str, r: dict) -> str:
            n_alerts = r["alerts_tp"] + r["alerts_fp"]
            prec = f"{r['alerts_tp'] / n_alerts:.2f}" if n_alerts else "-"
            rec = f"{r['real_detected'] / r['tests_real']:.2f}" if r["tests_real"] else "-"
            return (f"{name:16s}{r['tests_real']:6d}{r['tests_safe']:6d} | {r['alerts_tp']:5d}{r['alerts_fp']:5d}"
                    f"{r['alerts_cwe_mismatch']:6d} | {r['real_detected']:6d}{r['real_missed']:7d} | {prec:>9s}{rec:>8s}")

        for name, r in rep.items():
            if name not in ("TOTAL", "_not_a_test"):
                lines.append(row(name, r))
        lines += ["-" * len(head), row("TOTAL", rep["TOTAL"])]
        lines.append(f"\nалертов вне тест-кейсов бенчмарка: {rep['_not_a_test']['alerts']}")
        lines.append("precision = TP/(TP+FP) среди алертов CodeQL (baseline); "
                    "recall = доля реальных тестов, найденных CodeQL")

        t = rep["TOTAL"]
        if t["alerts_fp"] < MIN_FP_FOR_TRAINING:
            lines.append(f"\n! ложных срабатываний всего {t['alerts_fp']} (< {MIN_FP_FOR_TRAINING}): "
                        "классификатору может не хватить примеров класса 0")
        return "\n".join(lines)
    



    # ------------------------------------------------------------------------- CLI

    def _load_jsonl_as_objects(path: Path) -> List[SimpleNamespace]:
        with open(path, "r", encoding="utf-8") as f:
            return [json.loads(line, object_hook=lambda d: SimpleNamespace(**d)) for line in f if line.strip()]


    if __name__ == "__main__":
        import argparse

        ap = argparse.ArgumentParser(description="Отчёт по TP/FP алертам CodeQL на бенчмарке")
        ap.add_argument("expected_csv", help="expectedresults-*.csv")
        ap.add_argument("paths_jsonl", help="taint_paths.jsonl, сохранённый после SarifParser")
        ap.add_argument("--all-categories", action="store_true",
                        help="учитывать и категории без taint-запросов (hash, weakrand, ...)")
        args = ap.parse_args()

        truth = load_expected_results(Path(args.expected_csv))
        labeled = label_all(_load_jsonl_as_objects(Path(args.paths_jsonl)), truth)
        cats = {c.category for c in truth.values()} if args.all_categories else None
        print(format_report(coverage_report(truth, labeled, cats)))