import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from app.code_intelligence.indexer import CodeIndexer, CodeSymbol, FileIndex


@dataclass
class RetrievalResult:
    symbol: CodeSymbol
    score: float
    snippet: str


class CodeRetriever:
    def __init__(self, indexer: CodeIndexer):
        self.indexer = indexer

    def _read_snippet(self, file_path: str, line_start: int, line_end: int, context: int = 3) -> str:
        full_path = self.indexer.root_path / file_path
        try:
            lines = full_path.read_text(encoding="utf-8").splitlines()
        except (IOError, UnicodeDecodeError):
            return ""

        start = max(0, line_start - context - 1)
        end = min(len(lines), line_end + context)
        snippet_lines = lines[start:end]

        result = []
        for i, line in enumerate(snippet_lines, start=start + 1):
            prefix = ">>> " if line_start <= i <= line_end else "    "
            result.append(f"{prefix}{i:4d}: {line}")
        return "\n".join(result)

    def _score(self, query: str, symbol: CodeSymbol) -> float:
        query_lower = query.lower()
        name_lower = symbol.name.lower()
        doc_lower = (symbol.docstring or "").lower()

        score = 0.0
        if query_lower == name_lower:
            score += 10.0
        elif query_lower in name_lower:
            score += 5.0

        if query_lower in doc_lower:
            score += 2.0

        if symbol.symbol_type == "class":
            score += 0.5

        return score

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        symbol_type: Optional[str] = None,
        file_pattern: Optional[str] = None,
    ) -> List[RetrievalResult]:
        candidates: List[RetrievalResult] = []

        all_symbols = self.indexer.get_all_symbols()
        for symbol_list in all_symbols.values():
            for symbol in symbol_list:
                if symbol_type and symbol.symbol_type != symbol_type:
                    continue
                if file_pattern and not re.search(file_pattern, symbol.file_path):
                    continue

                score = self._score(query, symbol)
                if score > 0:
                    snippet = self._read_snippet(
                        symbol.file_path, symbol.line_start, symbol.line_end
                    )
                    candidates.append(RetrievalResult(symbol=symbol, score=score, snippet=snippet))

        candidates.sort(key=lambda r: r.score, reverse=True)
        return candidates[:top_k]

    def retrieve_by_signature(self, signature_hint: str, top_k: int = 5) -> List[RetrievalResult]:
        results = []
        all_symbols = self.indexer.get_all_symbols()
        for symbol_list in all_symbols.values():
            for symbol in symbol_list:
                if symbol.signature and signature_hint.lower() in symbol.signature.lower():
                    snippet = self._read_snippet(
                        symbol.file_path, symbol.line_start, symbol.line_end
                    )
                    results.append(RetrievalResult(symbol=symbol, score=5.0, snippet=snippet))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def retrieve_related(self, symbol_name: str) -> List[RetrievalResult]:
        symbols = self.indexer.find_symbol(symbol_name)
        if not symbols:
            return []

        related: Dict[str, RetrievalResult] = {}
        for sym in symbols:
            for dep in sym.dependencies:
                for found in self.indexer.find_symbol(dep):
                    key = f"{found.file_path}:{found.name}"
                    if key not in related:
                        snippet = self._read_snippet(
                            found.file_path, found.line_start, found.line_end
                        )
                        related[key] = RetrievalResult(symbol=found, score=3.0, snippet=snippet)

            all_symbols = self.indexer.get_all_symbols()
            for symbol_list in all_symbols.values():
                for other in symbol_list:
                    if other.name != sym.name and sym.name in other.dependencies:
                        key = f"{other.file_path}:{other.name}"
                        if key not in related:
                            snippet = self._read_snippet(
                                other.file_path, other.line_start, other.line_end
                            )
                            related[key] = RetrievalResult(symbol=other, score=2.0, snippet=snippet)

        return sorted(related.values(), key=lambda r: r.score, reverse=True)

    def get_file_overview(self, file_path: str) -> Optional[Dict]:
        file_index = self.indexer.get_file_index(file_path)
        if not file_index:
            return None

        return {
            "file_path": file_index.file_path,
            "language": file_index.language,
            "symbol_count": len(file_index.symbols),
            "symbols": [
                {
                    "name": s.name,
                    "type": s.symbol_type,
                    "line": s.line_start,
                    "signature": s.signature,
                    "docstring": s.docstring,
                }
                for s in file_index.symbols
            ],
            "imports": file_index.imports,
        }
