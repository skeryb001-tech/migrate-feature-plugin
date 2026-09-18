# Migrate Feature Marketplace

`migrate-feature-plugin` 是一个 Codex 插件，用于将完整功能迁移到另一个项目、页面或客户端，并保持业务行为、数据契约、交互和必要 UI 等价。

它不是代码复制器，而是一套以目标项目为优先的迁移流程：先追踪真实调用链，再复用目标能力，最后按风险完成验证。

快速上手说明见：[PROMOTION.md](PROMOTION.md)。

## 安装

### 傻瓜式安装（推荐非开发人员使用）

在 Codex 客户端新建一个任务，点击下面代码块右上角的复制按钮，直接粘贴并发送：

```text
[skeryb001-tech/migrate-feature-plugin](https://github.com/skeryb001-tech/migrate-feature-plugin) 帮我安装这个插件
```

Codex 会根据 GitHub 仓库完成插件安装。安装完成后重新打开或新建一个 Codex 任务，即可使用 `$migrate-feature`。

如果已经安装过，也可以复制同一句话，让 Codex 检查并更新到最新版本。

如果 Codex 请求访问 GitHub 或执行安装命令，请选择允许。

### Codex 桌面客户端

当前仓库通过 GitHub Marketplace 分发。首次使用时，先在终端注册 Marketplace：

```bash
codex plugin marketplace add skeryb001-tech/migrate-feature-plugin --ref main
```

然后回到 Codex 桌面客户端：

1. 打开 **Plugins** 页面。
2. 选择 `migrate-feature-marketplace`。
3. 找到 `migrate-feature-plugin`，点击安装。
4. 安装完成后新建一个 Codex 任务。

如果插件已发布到公共 Plugin Directory，也可以直接在 **Plugins** 页面搜索 `migrate-feature-plugin` 并安装。

### Codex CLI

```bash
codex plugin marketplace add skeryb001-tech/migrate-feature-plugin --ref main
codex plugin add migrate-feature-plugin@migrate-feature-marketplace
```

安装后新建 Codex 会话，再使用 `$migrate-feature`。

### 本地源码

适合贡献代码或测试本地修改：

```bash
git clone https://github.com/skeryb001-tech/migrate-feature-plugin.git
cd migrate-feature-plugin
codex plugin marketplace add .
codex plugin add migrate-feature-plugin@migrate-feature-marketplace
```

更新插件：

```bash
codex plugin marketplace upgrade migrate-feature-marketplace
```

## 快速开始

```text
使用 $migrate-feature，把源项目的图片上传功能迁移到目标项目。

源项目：/path/to/source-project
源入口：pages/image-upload.vue
目标项目：/path/to/target-project
目标入口：pages/image-upload.vue

要求：
- 保持业务逻辑、状态和交互等价
- 优先复用目标项目已有能力
- 不覆盖同名文件
- 不新增依赖
- 报告改动、验证结果和未验证项
```

也可以直接描述迁移需求，插件会根据任务内容自动触发。

## 支持范围

迁移模式：

- `cross-project`：跨项目迁移。
- `cross-page`：同项目跨页面或视图迁移。

目标平台：

- `web-frontend`：Vue、React、Nuxt、Next 等 Web 应用。
- `hybrid-client`：Electron、Tauri、WebView 等混合客户端。
- `native-client`：iOS、Android、Flutter、React Native 等原生客户端。

## 执行原则

1. 明确源入口、目标入口、输入、输出、状态、错误和副作用。
2. 沿真实调用链追踪到组件、状态、请求层、API、Bridge 或 Repository。
3. 按“复用 → 最窄适配 → 最小迁入”映射到目标项目。
4. 根据影响范围验证逻辑、UI、生命周期、共享消费者和运行时行为。
5. 保留未验证项、残余风险和回滚起点。

源项目保持只读；目标项目已有改动受保护。同名覆盖、未授权依赖或公共契约变更、数据/安全/权限问题和不可逆写入必须先停止并处理。

## 验收结果

- `PASS`：代码和所有必需的运行时/视觉验收均完成。
- `CODE_ONLY`：代码级证据完成，但必需的运行时或视觉验收待补。
- `BLOCKED`：存在未解决的冲突、安全、权限、数据或公共契约问题。

静态检查不能替代浏览器、App Window、WebView、模拟器或真机验证。

## 开发与校验

仓库不需要构建产物。提交前运行：

```bash
python3 -B plugins/migrate-feature-plugin/skills/migrate-feature/scripts/validatePluginMetadata.py
python3 -B plugins/migrate-feature-plugin/skills/migrate-feature/scripts/validateMigrationSpec.py
python3 -B plugins/migrate-feature-plugin/skills/migrate-feature/scripts/testScanMigrationConflicts.py
python3 -B plugins/migrate-feature-plugin/skills/migrate-feature/scripts/testMigrationReportValidator.py
git diff --check
```

高风险、跨运行时、共享公共契约或正式“一比一”验收时，再生成并校验增强报告：

```bash
python3 plugins/migrate-feature-plugin/skills/migrate-feature/scripts/createMigrationReport.py \
  --mode cross-project \
  --platform web-frontend \
  --source /path/to/source \
  --target /path/to/target \
  --reason "跨运行时或正式验收" \
  --output /tmp/migration-report.md

python3 plugins/migrate-feature-plugin/skills/migrate-feature/scripts/validateMigrationReport.py \
  /tmp/migration-report.md
```

## 目录结构

```text
.agents/plugins/marketplace.json                 # Marketplace 注册
plugins/migrate-feature-plugin/.codex-plugin/    # 插件清单
plugins/migrate-feature-plugin/skills/           # Codex skill
plugins/migrate-feature-plugin/skills/.../references/  # 平台与验收规则
plugins/migrate-feature-plugin/skills/.../scripts/     # 校验与报告脚本
PROMOTION.md                                     # 推广与快速上手
```

## 版本

当前版本：`1.4.0`
