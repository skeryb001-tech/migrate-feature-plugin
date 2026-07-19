# Migrate Feature Marketplace

用于分发 `migrate-feature-plugin` 的 Codex Plugin Marketplace 仓库。

## 功能

插件内置 `$migrate-feature`，用于将完整前端功能跨项目或跨页面迁移，并提供：

- P0/P1/P2 风险拦截。
- 九阶段迁移 SOP。
- 目标项目能力复用和文件冲突处理。
- 业务逻辑、UI、边界场景和回归校验。
- 100 分量化验收与故障兜底。

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

```text
使用 $migrate-feature，把 A 项目的图片上传功能迁移到 B 项目。

源项目：/path/to/project-a
源入口：pages/image-upload.vue
目标项目：/path/to/project-b
目标入口：pages/image-upload.vue

要求：
- 逻辑与 UI 一比一迁移
- 优先复用目标项目已有实现
- 同名文件不得覆盖
- 不新增依赖
```

## 目录

```text
.agents/plugins/marketplace.json
plugins/migrate-feature-plugin/.codex-plugin/plugin.json
plugins/migrate-feature-plugin/skills/migrate-feature/
```

## 版本

当前版本：`1.0.0`
