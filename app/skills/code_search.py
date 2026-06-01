"""代码搜索技能模块。

实现 CodeSearchSkill，用于在代码库中搜索相关文件和函数。

主要类：
    - CodeSearchSkill: 代码搜索技能。

使用示例：
    ```python
    from app.skills.code_search import CodeSearchSkill

    skill = CodeSearchSkill()
    result = await skill.execute({
        "query": "user authentication",
        "repo_path": "/path/to/repo"
    })
    ```
"""

from typing import Any

from app.skills.base import BaseSkill, SkillResult


class CodeSearchSkill(BaseSkill):
    """代码搜索技能，在代码库中搜索相关文件和函数。

    使用 CodeIndexer 和 CodeRetriever 对代码库进行索引和检索。

    Attributes:
        name: 技能名称，固定为 "code_search"。
        description: 技能描述。

    Example:
        ```python
        skill = CodeSearchSkill()
        result = await skill.execute({
            "query": "user authentication",
            "repo_path": "/path/to/repo"
        })
        print(result.output)  # 搜索结果列表
        ```
    """

    name = "code_search"
    description = "Search codebase for relevant files and functions"

    async def execute(self, context: dict[str, Any]) -> SkillResult:
        """执行代码搜索。

        对指定仓库路径进行索引，然后基于查询字符串检索相关代码。

        Args:
            context: 执行上下文，包含：
                - query: 搜索查询字符串。
                - repo_path: 仓库路径，默认为当前目录。

        Returns:
            SkillResult: 搜索结果，output 为结果列表。
        """
        query = context.get("query", "")
        repo_path = context.get("repo_path", ".")

        try:
            from app.code_intelligence.indexer import CodeIndexer
            from app.code_intelligence.retriever import CodeRetriever

            # 创建索引器并索引代码库
            indexer = CodeIndexer(root_path=repo_path)
            indexer.index()

            # 创建检索器并执行搜索
            retriever = CodeRetriever(indexer)
            results = retriever.search(query, top_k=5)  # type: ignore[attr-defined]

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
