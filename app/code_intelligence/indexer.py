import ast
import hashlib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CodeSymbol:
    name: str
    symbol_type: str
    file_path: str
    line_start: int
    line_end: int
    docstring: str | None = None
    signature: str | None = None
    dependencies: list[str] = field(default_factory=list)
    content_hash: str = ""


@dataclass
class FileIndex:
    file_path: str
    language: str
    symbols: list[CodeSymbol] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    content_hash: str = ""
    last_indexed: str | None = None


class CodeIndexer:
    SUPPORTED_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
    }

    def __init__(self, root_path: str):
        self.root_path = Path(root_path).resolve()
        self._index: dict[str, FileIndex] = {}
        self._symbol_map: dict[str, list[CodeSymbol]] = {}

    def _compute_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def _detect_language(self, file_path: Path) -> str | None:
        return self.SUPPORTED_EXTENSIONS.get(file_path.suffix)

    def _parse_python_file(self, file_path: Path, content: str) -> FileIndex:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return FileIndex(
                file_path=str(file_path.relative_to(self.root_path)),
                language="python",
                content_hash=self._compute_hash(content),
            )

        symbols: list[CodeSymbol] = []
        imports: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                line_end = getattr(node, "end_lineno", node.lineno)
                docstring = ast.get_docstring(node)

                signature = None
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = []
                    for arg in node.args.args:
                        args.append(arg.arg)
                    signature = f"({', '.join(args)})"

                symbol = CodeSymbol(
                    name=node.name,
                    symbol_type="function"
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    else "class",
                    file_path=str(file_path.relative_to(self.root_path)),
                    line_start=node.lineno,
                    line_end=line_end or node.lineno,
                    docstring=docstring,
                    signature=signature,
                    content_hash=self._compute_hash(
                        ast.unparse(node) if hasattr(ast, "unparse") else ""
                    ),
                )
                symbols.append(symbol)

        return FileIndex(
            file_path=str(file_path.relative_to(self.root_path)),
            language="python",
            symbols=symbols,
            imports=imports,
            content_hash=self._compute_hash(content),
        )

    def _index_file(self, file_path: Path) -> FileIndex | None:
        language = self._detect_language(file_path)
        if not language:
            return None

        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None

        if language == "python":
            return self._parse_python_file(file_path, content)

        return FileIndex(
            file_path=str(file_path.relative_to(self.root_path)),
            language=language,
            content_hash=self._compute_hash(content),
        )

    def index(self, paths: list[str] | None = None) -> dict[str, FileIndex]:
        target_paths = [self.root_path]
        if paths:
            target_paths = [self.root_path / p for p in paths]

        for target in target_paths:
            if target.is_file():
                result = self._index_file(target)
                if result:
                    self._index[result.file_path] = result
            elif target.is_dir():
                for file_path in target.rglob("*"):
                    if file_path.is_file() and not any(
                        part.startswith(".")
                        or part in {"__pycache__", "node_modules", ".git", "venv", ".venv"}
                        for part in file_path.parts
                    ):
                        result = self._index_file(file_path)
                        if result:
                            self._index[result.file_path] = result

        self._rebuild_symbol_map()
        return self._index.copy()

    def _rebuild_symbol_map(self) -> None:
        self._symbol_map.clear()
        for file_index in self._index.values():
            for symbol in file_index.symbols:
                if symbol.name not in self._symbol_map:
                    self._symbol_map[symbol.name] = []
                self._symbol_map[symbol.name].append(symbol)

    def get_file_index(self, file_path: str) -> FileIndex | None:
        return self._index.get(file_path)

    def find_symbol(self, name: str) -> list[CodeSymbol]:
        return self._symbol_map.get(name, []).copy()

    def search_files(self, pattern: str) -> list[FileIndex]:
        results = []
        lower_pattern = pattern.lower()
        for file_index in self._index.values():
            if lower_pattern in file_index.file_path.lower():
                results.append(file_index)
        return results

    def get_all_symbols(self) -> dict[str, list[CodeSymbol]]:
        return {k: v.copy() for k, v in self._symbol_map.items()}

    def get_statistics(self) -> dict[str, int]:
        total_files = len(self._index)
        total_symbols = sum(len(f.symbols) for f in self._index.values())
        language_counts: dict[str, int] = {}
        for f in self._index.values():
            language_counts[f.language] = language_counts.get(f.language, 0) + 1

        return {
            "total_files": total_files,
            "total_symbols": total_symbols,
            "languages": len(language_counts),
            **{f"files_{lang}": count for lang, count in language_counts.items()},
        }
