"""工作流定义模块。

定义 Temporal 工作流类 DevWorkflow。
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from app.workflow.activities import ACTIVITY_MAP


@workflow.defn
class DevWorkflow:
    """DevMatrix 开发工作流。

    通过 Temporal 编排多 Agent 协作流程，
    支持审批节点、回滚和并行执行。
    """

    @workflow.run
    async def run(self, config: dict) -> dict:
        project_id = config.get("project_id", "")
        stages = config.get("stages", [])

        if not project_id or not stages:
            return {"status": "error", "message": "project_id and stages required"}

        snapshot_result = await workflow.execute_activity(
            ACTIVITY_MAP["create_state_snapshot"],
            project_id,
            start_to_close_timeout=timedelta(seconds=30),
        )

        results = []
        for stage in stages:
            stage_id = stage.get("id", "")
            stage_name = stage.get("name", stage_id)
            agent_role = stage.get("agent_role", "")
            agent_name = stage.get("agent", "")
            requires_approval = stage.get("requires_approval", False)
            timeout = stage.get("timeout_seconds", 300)

            execute_result = await workflow.execute_activity(
                ACTIVITY_MAP["execute_agent_task"],
                project_id,
                stage_id,
                stage_name,
                agent_role,
                agent_name,
                stage.get("context", {}),
                start_to_close_timeout=timedelta(seconds=timeout),
            )

            if execute_result.get("status") == "failed":
                return {"status": "failed", "stage": stage_id, "results": results}

            results.append(execute_result)

            if requires_approval:
                task_id = execute_result.get("task_id", 0)

                await workflow.execute_activity(
                    ACTIVITY_MAP["send_approval_request"],
                    project_id,
                    stage_id,
                    stage_name,
                    agent_role,
                    start_to_close_timeout=timedelta(seconds=30),
                )

                approval_result = await workflow.execute_activity(
                    ACTIVITY_MAP["wait_for_approval"],
                    project_id,
                    task_id,
                    start_to_close_timeout=timedelta(days=7),
                )

                if approval_result.get("status") == "rejected":
                    snapshot_id = snapshot_result.get("snapshot_id")
                    if snapshot_id:
                        await workflow.execute_activity(
                            ACTIVITY_MAP["rollback_state"],
                            project_id,
                            snapshot_id,
                            start_to_close_timeout=timedelta(seconds=30),
                        )
                    return {"status": "rejected", "stage": stage_id, "results": results}

        await workflow.execute_activity(
            ACTIVITY_MAP["notify_completion"],
            project_id,
            start_to_close_timeout=timedelta(seconds=30),
        )

        return {"status": "completed", "project_id": project_id, "results": results}
