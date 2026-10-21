from __future__ import annotations
 
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote, urlparse
 
from loguru import logger
 
from app.models.domain.code_snippet import CodeSnippet
from app.models.domain.taint_path import TaintPath  


_CWE_TAG = re.compile(r"external/cwe/cwe-(\d+)", re.IGNORECASE)


class SarifParser:
    def __init__(
            self,
            source_dir: Path,
            context_lines: int = 2,
            max_flows_per_result: int = 1,
            include_flowless: bool = False,
    ):
        self.source_dir = Path(source_dir).resolve()
        self.context_lines = context_lines
        self.max_flows_per_result = max_flows_per_result
        self.include_flowless = include_flowless
        self._file_cache: Dict[Path, List[str]] = {}
        self.stats: Dict[str, int] = {
            "results": 0, "results_without_flow": 0,
            "paths": 0, "nodes": 0, "nodes_with_empty_code": 0,
        }

    # Главный метод который позволяет объядинить sarif + исходник
    def parse(self, sarif_path: Path) -> List[TaintPath]:
        # Открываем файл sarif_path
        with open(sarif_path, "r", encoding="utf-8") as f: 
            sarif = json.load(f)

        # Обнуляем закешированные статы и инициализируем их 
        self._file_cache.clear()
        self.stats = {
            "results": 0,
            "results_without_flow": 0,
            "paths": 0,
            "nodes": 0,
            "nodes_with_empty_code": 0
        }   

        # Формируем путь
        paths: List[TaintPath] = []
        for run_idx, run in enumerate(sarif.get("runs", [])):
            rules = self._index_rules(run)
            for res_idx, results in enumerate(run.get("results", [])):
                self.stats["results"] += 1
                paths.extend(self._parse_result(run_idx, res_idx, results, rules))
        
        self.stats["paths"] = len(paths)
        logger.info(f"[INFO | SarifParser] {self.stats}")

        return paths 
    
    
    def _parse_result(self, run_idx: int, res_idx: int, result: dict,
                      rules: Dict[str, dict]) -> List[TaintPath]:
        rule_id = result.get("ruleId") or result.get("rule", {}).get("id") or "unknown"
        cwe_tags, security_severity = self._rule_meta(rules.get(rule_id, {}))
        message = result.get("message", {}).get("text", "")
        primary_file = self._primary_file(result)

        common = dict(
            rule_id = rule_id,
            full_message = message,
            primary_file = primary_file,
            severity = result.get("level"),
            security_severity = security_severity,
            cwe_tags = cwe_tags
        )

        flows = result.get("codeFlows") or []
        out: List[TaintPath] = []

        for flow_idx, flow in enumerate(flows[: self.max_flows_per_result]):
            thread_flows = flow.get("threadFlows") or [{}]
            locations = thread_flows[0].get("locations", [{}])
            nodes = [s for s in (self._snippet(loc.get("location", {})) for loc in locations) if s]

            if not nodes:
                continue
            out.append(TaintPath(
                finding_id=f"{rule_id}#{run_idx}.{res_idx}.{flow_idx}",
                source=nodes[0],
                sink=nodes[-1],
                intermediate_nodes=nodes[1:-1],
                **common,
            ))

        if not flows:
            self.stats["results_without_flow"] += 1
            if self.include_flowless:
                locs = result.get("locations") or []
                snippet = self._snippet(locs[0]) if locs else None 
                if snippet:
                    out.append(TaintPath(
                        finding_id=f"{rule_id}#{run_idx}.{res_idx}.0",
                        source=snippet, sink=snippet, **common,
                    ))
        return out

    def _snippet(self, location: dict) -> Optional[CodeSnippet]:
        phys = location.get("physicalLocation")
        if not phys:
            return None
        uri = phys.get("artifactLocation", {}).get("uri")
        if not uri:
            return None

        region = phys.get("region", {})
        start = int(region.get("startLine", 1))
        end = int(region.get("endLine", start))

        rel_path, full_path = self._resolve(uri)
        code = self._read_context(full_path, start, end) if full_path else ""

        self.stats["nodes"] += 1
        if not code.strip():
            self.stats["nodes_with_empty_code"] += 1

        return CodeSnippet(
            file_path=rel_path,
            start_line=start,
            end_line=end,
            start_column=region.get("startColumn"),
            end_column=region.get("endColumn"),
            code=code,
            message=location.get("message", {}).get("text", ""),
        )


    def _resolve(self, uri: str) -> Tuple[str, Optional[Path]]:
        parsed = urlparse(uri)
        raw = unquote(parsed.path if parsed.scheme == "file" else uri)

        candidate = Path(raw)
        full = (candidate if candidate.is_absolute() else self.source_dir / candidate).resolve()
        try:
            rel = full.relative_to(self.source_dir)
        except ValueError:
            logger.warning(f"[WARN | SarifParser] Path outside source_dir ignored: {uri}")
            return raw, None
        return rel.as_posix(), full


    def _read_context(self, path: Path, start_line: int, end_line: int) -> str:
        lines = self._file_cache.get(path)
        if lines is None:
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
            except (FileNotFoundError, IsADirectoryError, PermissionError):
                lines = []
            self._file_cache[path] = lines

        ctx_start = max(0, start_line - 1 - self.context_lines)
        ctx_end = min(len(lines), end_line + self.context_lines)
        return "".join(lines[ctx_start:ctx_end])


    def _primary_file(self, result: dict) -> str:
        locs = result.get("locations") or []
        if not locs:
            return ""
        uri = locs[0].get("physicalLocation", {}).get("artifactLocation", {}).get("uri")
        return self._resolve(uri)[0] if uri else ""


    @staticmethod
    def _index_rules(run: dict) -> Dict[str, dict]:
        """Правила CodeQL лежат в tool.driver.rules и/или tool.extensions[].rules."""
        tool = run.get("tool", {})
        components = [tool.get("driver", {}), *tool.get("extensions", [])]
        index: Dict[str, dict] = {}
        for comp in components:
            for rule in comp.get("rules") or []:
                if rule.get("id"):
                    index[rule["id"]] = rule
        return index

    @staticmethod
    def _rule_meta(rule: dict) -> Tuple[List[str], Optional[float]]:
        props = rule.get("properties", {})
        cwes = []
        for tag in props.get("tags", []):
            m = _CWE_TAG.match(tag)
            if m:
                cwes.append(f"CWE-{int(m.group(1))}")
        try:
            sec = float(props["security-severity"])
        except (KeyError, TypeError, ValueError):
            sec = None
        return cwes, sec
    

# Оставляю main на всякий случай. Вроде всё работает, но мало ли...

if __name__ == "__main__":    

    import argparse

    ap = argparse.ArgumentParser(description="Проверка SarifParser на реальных данных")
    ap.add_argument("sarif")
    ap.add_argument("source_dir")
    ap.add_argument("--show", type=int, default=3, help="сколько путей напечатать")
    args = ap.parse_args()

    parser = SarifParser(Path(args.source_dir))
    result = parser.parse(Path(args.sarif))

    print(f"\nstats: {parser.stats}\n")
    for tp in result[: args.show]:
        print(f"{tp.finding_id} | {tp.cwe_tags} | severity={tp.severity} | nodes={tp.path_length}")
        print(f"  SOURCE {tp.source.file_path}:{tp.source.start_line}")
        print("    " + tp.source.code.strip().replace("\n", "\n    ")[:300])
        print(f"  SINK   {tp.sink.file_path}:{tp.sink.start_line}")
        print("    " + tp.sink.code.strip().replace("\n", "\n    ")[:300])
        print("-" * 60)

