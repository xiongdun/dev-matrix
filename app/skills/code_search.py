from typing import Any, Dict

from app.skills.base import BaseSkill, SkillResult


class CodeSearchSkill(BaseSkill):
    name = "code_search"
    description = "Search codebase for relevant files and functions"

    async def execute(self, context: Dict[str, Any]) -> SkillResult:
        query = context.get("query", "")
        repo_path = context.get("repo_path", ".")

        try:
            from app.code_intelligence.indexer import CodeIndexer
            from app.code_intelligence.retriever import CodeRetriever

            indexer = CodeIndexer(root_path=repo_path)
            indexer.index()

            retriever = CodeRetriever(indexer)
            results = retriever.search(query, top_k=5)

            return SkillResult(
                output=results,
                metadata={"query": query, "result_count": len(results)},
            )
        except Exception as e:
            return SkillResult(
                output=[],
                success=False,
                error=str(e),
                metadata={"query": query},
            )
