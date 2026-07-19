# Migrate Feature Marketplace

用于分发 `migrate-feature-plugin` 的 Codex Plugin Marketplace 仓库。

## 功能

插件内置 `$migrate-feature`，用于将完整前端功能跨项目或跨页面迁移，并提供：

- `cross-project` / `cross-page` 专项模式分流。
- P0/P1/P2 风险拦截。
- 九阶段迁移 SOP。
- 目标项目能力复用、目标规范落盘和文件冲突处理。
- 业务逻辑、UI、边界场景和回归校验。
- 共享消费者保护、回滚方案和 100 分量化验收。
- 冲突扫描、报告生成和报告自动校验脚本。

固定优先级：

1. 迁移后的逻辑、功能、交互和 UI 与源功能一致。
2. 优先复用目标项目已有实现。
3. 迁移后的代码规范、目录结构、模块分层和命名以目标项目为准。
4. 只有符合目标规范且没有冲突时，才参考源目录和文件名。

## 安装

```bash
codex plugin marketplace add skeryb001-tech/migrate-feature-plugin
codex plugin add migrate-feature-plugin@migrate-feature-marketplace
```

安装后新建 Codex 任务并调用：

```text
$migrate-feature
```

## 使用示例

### 跨项目迁移

```text
使用 $migrate-feature，把 A 项目的图片上传功能迁移到 B 项目。

源项目：/path/to/project-a
源入口：pages/image-upload.vue
目标项目：/path/to/project-b
目标入口：pages/image-upload.vue

要求：
- 逻辑与 UI 一比一迁移
- 优先复用目标项目已有实现
- 迁移后代码结构和规范以 B 项目为准
- 同名文件不得覆盖
- 不新增依赖
```

### 同项目跨页面迁移

```text
使用 $migrate-feature，把当前项目 A 页面中的完整图片编辑功能迁移到 B 页面。

项目：/path/to/project
源页面：pages/page-a.vue
目标页面：pages/page-b.vue

要求：
- B 页面的逻辑、UI、状态和交互与 A 页面一致
- 优先复用项目已有组件、composable、store 和请求层
- 代码按当前项目目录与命名规范组织
- 保持 A 页面原行为不回归
- 验证 A→B→A、前进后退、刷新和离开页面后的副作用清理
```

## 自动化门禁

```bash
python3 plugins/migrate-feature-plugin/skills/migrate-feature/scripts/scanMigrationConflicts.py \
  /path/to/source-feature \
  /path/to/target-root

python3 plugins/migrate-feature-plugin/skills/migrate-feature/scripts/createMigrationReport.py \
  --mode cross-page \
  --source /path/to/source-page \
  --target /path/to/target-page \
  --output /tmp/migration-report.md

python3 plugins/migrate-feature-plugin/skills/migrate-feature/scripts/validateMigrationReport.py \
  /tmp/migration-report.md
```

冲突扫描发现不同内容同名、大小写或路径类型冲突时返回非 0；报告校验在存在占位符、缺少证据、P0/P1、硬门禁失败或总分低于 95 时返回非 0。

## 目录

```text
.agents/plugins/marketplace.json
plugins/migrate-feature-plugin/.codex-plugin/plugin.json
plugins/migrate-feature-plugin/skills/migrate-feature/
```

## 版本

当前版本：`1.1.0`
