"""RBAC 初始化脚本。

初始化 RBAC 基础数据，包括菜单、角色、角色权限关联和超级管理员用户。
"""

from app.core.security import hash_password
from app.state.models import (
    MenuModel,
    RoleAgentModel,
    RoleMenuModel,
    RoleModel,
    UserModel,
    UserRoleModel,
    get_db,
    init_db,
)


def init_rbac_data():
    """初始化 RBAC 基础数据。"""
    init_db()
    db = next(get_db())

    try:
        # 1. 创建菜单
        menus_data = [
            # 顶级菜单
            {
                "name": "dashboard",
                "title": "sidebar.dashboard",
                "path": "/",
                "icon": "LayoutDashboard",
                "menu_type": "page",
                "permission": "dashboard:view",
                "sort_order": 1,
            },
            {
                "name": "workbench",
                "title": "sidebar.workbench",
                "path": "/workbench",
                "icon": "ClipboardCheck",
                "menu_type": "page",
                "permission": "workbench:view",
                "sort_order": 2,
            },
            {
                "name": "projects",
                "title": "sidebar.projects",
                "path": "/projects",
                "icon": "FolderKanban",
                "menu_type": "page",
                "permission": "project:view",
                "sort_order": 3,
            },
            {
                "name": "task_management",
                "title": "sidebar.taskManagement",
                "path": "/tasks",
                "icon": "KanbanSquare",
                "menu_type": "directory",
                "permission": "task:view",
                "sort_order": 4,
            },
            {
                "name": "scheduled_tasks",
                "title": "sidebar.scheduledTasks",
                "path": "/scheduled-tasks",
                "icon": "Clock",
                "menu_type": "page",
                "permission": "scheduled_task:view",
                "sort_order": 5,
            },
            {
                "name": "agents",
                "title": "sidebar.agents",
                "path": "/agents",
                "icon": "Bot",
                "menu_type": "page",
                "permission": "agent:view",
                "sort_order": 6,
            },
            {
                "name": "skills",
                "title": "sidebar.skills",
                "path": "/skills",
                "icon": "Wrench",
                "menu_type": "page",
                "permission": "skill:view",
                "sort_order": 7,
            },
            {
                "name": "code_reviews",
                "title": "sidebar.codeReviews",
                "path": "/code-reviews",
                "icon": "GitPullRequest",
                "menu_type": "page",
                "permission": "code_review:view",
                "sort_order": 8,
            },
            {
                "name": "workflow",
                "title": "sidebar.workflow",
                "path": "/workflow",
                "icon": "GitBranch",
                "menu_type": "directory",
                "permission": "workflow:view",
                "sort_order": 9,
            },
            {
                "name": "settings",
                "title": "sidebar.settings",
                "path": "/settings",
                "icon": "Settings",
                "menu_type": "directory",
                "permission": "setting:view",
                "sort_order": 10,
            },
            {
                "name": "user_management",
                "title": "sidebar.userManagement",
                "path": "/users",
                "icon": "Users",
                "menu_type": "page",
                "permission": "user:manage",
                "sort_order": 11,
            },
            {
                "name": "role_management",
                "title": "sidebar.roleManagement",
                "path": "/roles",
                "icon": "UserCog",
                "menu_type": "page",
                "permission": "role:manage",
                "sort_order": 12,
            },
            {
                "name": "menu_management",
                "title": "sidebar.menuManagement",
                "path": "/menus",
                "icon": "Menu",
                "menu_type": "page",
                "permission": "menu:manage",
                "sort_order": 13,
            },
            # 子菜单
            {
                "name": "my_tasks",
                "title": "sidebar.myTasks",
                "path": "/tasks/my",
                "icon": "ListTodo",
                "menu_type": "page",
                "permission": "task:view",
                "parent_id": None,
                "sort_order": 1,
            },
            {
                "name": "task_board",
                "title": "sidebar.taskBoard",
                "path": "/tasks/board",
                "icon": "KanbanSquare",
                "menu_type": "page",
                "permission": "task:view",
                "parent_id": None,
                "sort_order": 2,
            },
            {
                "name": "workflow_editor",
                "title": "sidebar.workflowEditor",
                "path": "/workflow/editor",
                "icon": "Workflow",
                "menu_type": "page",
                "permission": "workflow:edit",
                "parent_id": None,
                "sort_order": 1,
            },
            {
                "name": "workflow_list",
                "title": "sidebar.workflowList",
                "path": "/workflow/list",
                "icon": "List",
                "menu_type": "page",
                "permission": "workflow:view",
                "parent_id": None,
                "sort_order": 2,
            },
            {
                "name": "workflow_instances",
                "title": "sidebar.workflowInstances",
                "path": "/workflow/instances",
                "icon": "Layers",
                "menu_type": "page",
                "permission": "workflow_instance:view",
                "parent_id": None,
                "sort_order": 3,
            },
            {
                "name": "settings_system",
                "title": "sidebar.settingsSystem",
                "path": "/settings/system",
                "icon": "Monitor",
                "menu_type": "page",
                "permission": "setting:system",
                "parent_id": None,
                "sort_order": 1,
            },
            {
                "name": "settings_llm",
                "title": "sidebar.settingsLlm",
                "path": "/settings/llm",
                "icon": "BrainCircuit",
                "menu_type": "page",
                "permission": "setting:llm",
                "parent_id": None,
                "sort_order": 2,
            },
            {
                "name": "settings_database",
                "title": "sidebar.settingsDatabase",
                "path": "/settings/database",
                "icon": "Database",
                "menu_type": "page",
                "permission": "setting:database",
                "parent_id": None,
                "sort_order": 3,
            },
            {
                "name": "settings_security",
                "title": "sidebar.settingsSecurity",
                "path": "/settings/security",
                "icon": "Shield",
                "menu_type": "page",
                "permission": "setting:security",
                "parent_id": None,
                "sort_order": 4,
            },
            {
                "name": "settings_about",
                "title": "sidebar.settingsAbout",
                "path": "/settings/about",
                "icon": "Info",
                "menu_type": "page",
                "permission": "setting:about",
                "parent_id": None,
                "sort_order": 5,
            },
        ]

        menu_map = {}
        for data in menus_data:
            menu = MenuModel(**{k: v for k, v in data.items() if k != "parent_id"})
            db.add(menu)
            db.flush()
            menu_map[data["name"]] = menu.id

        # 更新子菜单 parent_id
        parent_map = {
            "my_tasks": "task_management",
            "task_board": "task_management",
            "workflow_editor": "workflow",
            "workflow_list": "workflow",
            "workflow_instances": "workflow",
            "settings_system": "settings",
            "settings_llm": "settings",
            "settings_database": "settings",
            "settings_security": "settings",
            "settings_about": "settings",
        }
        for child_name, parent_name in parent_map.items():
            menu = db.query(MenuModel).filter(MenuModel.name == child_name).first()
            if menu:
                menu.parent_id = menu_map[parent_name]

        db.commit()

        # 2. 创建角色
        roles_data = [
            {
                "name": "super_admin",
                "display_name": "超级管理员",
                "description": "拥有所有权限",
                "data_scope": "all",
                "is_system": 1,
            },
            {
                "name": "admin",
                "display_name": "系统管理员",
                "description": "管理用户、角色、菜单",
                "data_scope": "all",
                "is_system": 1,
            },
            {
                "name": "project_manager",
                "display_name": "项目经理",
                "description": "管理项目和工作流",
                "data_scope": "all",
                "is_system": 1,
            },
            {
                "name": "developer",
                "display_name": "开发工程师",
                "description": "开发项目、查看代码审查",
                "data_scope": "self",
                "is_system": 1,
            },
            {
                "name": "tester",
                "display_name": "测试工程师",
                "description": "执行测试、查看代码审查",
                "data_scope": "self",
                "is_system": 1,
            },
            {
                "name": "viewer",
                "display_name": "访客",
                "description": "只读权限",
                "data_scope": "self",
                "is_system": 1,
            },
        ]

        role_map = {}
        for data in roles_data:
            role = RoleModel(**data)
            db.add(role)
            db.flush()
            role_map[data["name"]] = role.id

        db.commit()

        # 3. 为角色分配菜单
        all_menu_ids = list(menu_map.values())

        # super_admin 和 admin 拥有所有菜单
        for role_name in ["super_admin", "admin"]:
            for menu_id in all_menu_ids:
                db.add(RoleMenuModel(role_id=role_map[role_name], menu_id=menu_id))

        # project_manager 拥有除用户/角色/菜单管理外的所有菜单
        pm_exclude = ["user_management", "role_management", "menu_management"]
        pm_menu_ids = [menu_map[m] for m in menu_map if m not in pm_exclude]
        for menu_id in pm_menu_ids:
            db.add(RoleMenuModel(role_id=role_map["project_manager"], menu_id=menu_id))

        # developer 拥有仪表盘、工作台、项目管理、任务管理、代码审查、流程管理
        dev_menus = [
            "dashboard",
            "workbench",
            "projects",
            "task_management",
            "my_tasks",
            "task_board",
            "code_reviews",
            "workflow",
            "workflow_list",
            "workflow_instances",
            "settings",
            "settings_about",
        ]
        for m in dev_menus:
            if m in menu_map:
                db.add(RoleMenuModel(role_id=role_map["developer"], menu_id=menu_map[m]))

        # tester 类似 developer
        for m in dev_menus:
            if m in menu_map:
                db.add(RoleMenuModel(role_id=role_map["tester"], menu_id=menu_map[m]))

        # viewer 只读
        viewer_menus = [
            "dashboard",
            "projects",
            "task_management",
            "my_tasks",
            "task_board",
            "code_reviews",
            "workflow",
            "workflow_list",
            "workflow_instances",
        ]
        for m in viewer_menus:
            if m in menu_map:
                db.add(RoleMenuModel(role_id=role_map["viewer"], menu_id=menu_map[m]))

        db.commit()

        # 4. 为角色分配 Agent
        agent_map = {
            "super_admin": [
                "business_analyst",
                "product_manager",
                "architect",
                "developer",
                "qa",
                "project_manager",
                "code_reviewer",
            ],
            "admin": [
                "business_analyst",
                "product_manager",
                "architect",
                "developer",
                "qa",
                "project_manager",
                "code_reviewer",
            ],
            "project_manager": [
                "business_analyst",
                "product_manager",
                "architect",
                "developer",
                "qa",
                "project_manager",
                "code_reviewer",
            ],
            "developer": ["developer", "qa", "code_reviewer"],
            "tester": ["qa", "code_reviewer"],
            "viewer": [],
        }

        for role_name, agents in agent_map.items():
            for agent_name in agents:
                db.add(RoleAgentModel(role_id=role_map[role_name], agent_name=agent_name))

        db.commit()

        # 5. 创建超级管理员用户
        admin_user = UserModel(
            username="admin",
            password_hash=hash_password("admin123"),
            nickname="管理员",
            email="admin@devmatrix.local",
            data_scope="all",
        )
        db.add(admin_user)
        db.flush()

        # 分配 super_admin 角色
        db.add(UserRoleModel(user_id=admin_user.id, role_id=role_map["super_admin"]))
        db.commit()

        print("RBAC data initialized successfully!")
        print(f"  - {len(menus_data)} menus")
        print(f"  - {len(roles_data)} roles")
        print("  - 1 user (admin / admin123)")

    except Exception as e:
        db.rollback()
        print(f"Error initializing RBAC data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_rbac_data()
