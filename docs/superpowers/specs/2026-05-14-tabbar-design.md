# Tab Bar 功能设计文档

## 概述

在页面顶部新增 Tab Bar，支持多页面标签页切换功能。Dashboard 作为固定 Tab，其他页面动态添加和关闭。

## 需求确认

| 特性 | 选择 |
|------|------|
| 持久化 | 固定 Tab + 动态 Tab（Dashboard 固定，其他可关闭） |
| 关闭行为 | 关闭后无 Tab 时显示 Dashboard |
| 操作方式 | 关闭按钮（hover 显示）+ 右键菜单（关闭/关闭其他/关闭所有） |

## 设计方案

### 视觉风格

采用 VS Code 风格：
- Tab 栏固定在顶部导航下方，高度 40px
- 固定 Tab（Dashboard）左侧，有图标，无关闭按钮
- 动态 Tab 右侧有关闭按钮（×），hover 时显示
- 活动 Tab 有底部边框指示
- 右键菜单：关闭、关闭其他、关闭所有

### 组件结构

```
App.vue
├── Sidebar.vue (侧边栏)
├── TopNav.vue (顶部导航 - 保留标题)
└── TabBar.vue (新增：Tab 标签栏)
    └── TabBarItem.vue (单个 Tab)
        └── ContextMenu.vue (右键菜单)
```

### 状态管理

使用 Pinia store 管理 Tab 状态：

```ts
interface Tab {
  id: string        // 路由名称
  title: string     // Tab 标题
  path: string      // 路由路径
  closable: boolean // 是否可关闭
}

interface TabState {
  tabs: Tab[]        // Tab 列表
  activeTabId: string // 当前激活 Tab ID
}
```

### 交互行为

| 行为 | 实现 |
|------|------|
| 点击侧边栏 | 添加/激活 Tab（已存在则切换，不重复添加） |
| 点击 Tab | 切换到该 Tab |
| 点击关闭按钮 | 关闭 Tab，如果无 Tab 则显示 Dashboard |
| 右键菜单 - 关闭 | 关闭当前 Tab |
| 右键菜单 - 关闭其他 | 关闭除 Dashboard 外的所有 Tab |
| 右键菜单 - 关闭所有 | 关闭所有 Tab，显示 Dashboard |
| 刷新页面 | Tab 列表重置，只保留当前激活的 Tab |

### 样式变量

在 `style.css` 中添加：

```css
--tabbar-height: 40px
--tabbar-bg: var(--surface-color)
--tab-active-border: var(--primary-color)
--tab-hover-bg: var(--hover-color)
```

### 实现步骤

1. 创建 `useTabStore` Pinia store
2. 创建 `TabBar.vue` 组件
3. 创建 `TabBarItem.vue` 组件
4. 创建 `ContextMenu.vue` 组件
5. 修改 `App.vue` 集成 TabBar
6. 修改 `Sidebar.vue` 点击时添加/切换 Tab
7. 添加样式变量
8. 测试交互

## 技术选型

- 状态管理：Pinia（项目已集成）
- 右键菜单：自定义实现或使用现有组件库
- 无需新增依赖

## 测试场景

1. 点击侧边栏添加新 Tab
2. 点击已存在的 Tab 切换
3. 关闭单个 Tab
4. 关闭后无 Tab 时显示 Dashboard
5. 右键菜单各项功能
6. 刷新页面状态重置
