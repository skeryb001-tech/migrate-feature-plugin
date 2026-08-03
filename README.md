# Migrate Feature Marketplace

用于分发 `migrate-feature-plugin` 的 Codex Plugin Marketplace 仓库。

## 功能

插件内置 `$migrate-feature`，用于将完整 Web 前端、混合客户端或原生客户端功能跨项目、跨页面/视图迁移，并提供：

- `cross-project` / `cross-page` 专项模式分流。
- `web-frontend` / `hybrid-client` / `native-client` 平台分流。
- 按风险自动选择日常流程或增强验收，小迁移默认不生成报告。
- 五步主流程与 C1–C4 四个检查点。
- 目标项目能力复用、目标规范落盘和文件冲突处理。
- 按实际影响执行业务逻辑、UI、边界场景和消费者回归。
- 共享消费者保护、回滚方案和条件式运行时/视觉验收。
- 冲突扫描、报告生成和报告自动校验脚本。
- 单一机器规范源维护检查点、迁移模式与平台运行时约束。
- 仅在 UI 正式验收时要求 Browser、App Window/WebView、模拟器/仿真器或真机的版本、截图、渲染样式和几何对照。
- 区分完整 `PASS` 与待运行时视觉验收的 `CODE_ONLY`，防止静态证据冒充视觉通过。

固定优先级：

1. 迁移后的逻辑、功能、交互和 UI 与源功能一致。
2. 优先复用目标项目已有实现。
3. 迁移后的代码规范、目录结构、模块分层、命名和运行时集成以目标项目与平台为准。
4. 只有符合目标规范且没有冲突时，才参考源目录和文件名。

## 安装

```bash
codex plugin marketplace add skeryb001-tech/migrate-feature-plugin
codex plugin add migrate-feature-plugin@migrate-feature-marketplace
```

安装后新建 Codex 任务。插件支持自然语言自动触发，例如：

```text
把 A 项目的图片上传功能迁移到 B 项目或客户端，保持逻辑和 UI 一致。
```

也可以显式调用 `$migrate-feature`。

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

### 混合客户端迁移

```text
使用 $migrate-feature，把 Web 项目的文件上传功能迁移到 Electron/Tauri 客户端。

要求：
- 使用 hybrid-client 平台模式
- 复用目标 preload/command、IPC/bridge、窗口与权限实现
- 保持 context isolation、sandbox、CSP 和最小权限
- 在实际 App Window 中完成截图、computed style 和几何验收
```

### 原生客户端迁移

```text
使用 $migrate-feature，把 A 客户端的图片编辑功能迁移到 B 客户端页面。

要求：
- 使用 native-client 平台模式
- 复用目标 navigation、view model/reducer、repository 和主题系统
- 覆盖权限、前后台、进程重建、安全区、键盘和无障碍
- 在模拟器/仿真器或真机中完成截图、view inspector 和几何验收
```

## 自动化门禁

```bash
python3 plugins/migrate-feature-plugin/skills/migrate-feature/scripts/scanMigrationConflicts.py \
  /path/to/source-feature \
  /path/to/target-root

python3 plugins/migrate-feature-plugin/skills/migrate-feature/scripts/createMigrationReport.py \
  --mode cross-page \
  --platform native-client \
  --source /path/to/source-page \
  --target /path/to/target-page \
  --reason "跨原生运行时并要求正式验收" \
  --output /tmp/migration-report.md

python3 plugins/migrate-feature-plugin/skills/migrate-feature/scripts/validateMigrationSpec.py

python3 plugins/migrate-feature-plugin/skills/migrate-feature/scripts/validateMigrationReport.py \
  /tmp/migration-report.md
```

日常迁移直接执行五步流程，无需运行报告脚本。高风险、跨运行时、共享公共契约或正式一比一验收时才创建增强报告。冲突扫描也只用于实际文件迁入或路径碰撞风险。报告由 `migrationSpec.py` 的单一规范生成；校验器检查 C1–C4、阻断项和条件式运行时/视觉证据：退出码 0 为 `PASS`，1 为失败或 `BLOCKED`，3 为代码证据有效但必需运行时/视觉验收待补的 `CODE_ONLY`。

## 目录

```text
.agents/plugins/marketplace.json
plugins/migrate-feature-plugin/.codex-plugin/plugin.json
plugins/migrate-feature-plugin/skills/migrate-feature/
```

## 版本

当前版本：`1.3.0`
