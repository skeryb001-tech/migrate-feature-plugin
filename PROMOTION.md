# Migrate Feature

把一个项目里的完整功能，可靠地迁移到另一个项目、页面或客户端。

对于“完整功能、原样、所有功能、一比一”这类需求，插件会先建立源依赖闭包、结构化功能矩阵和渲染契约，再开始写入；存在未实现功能、入口未激活或缺少 UI 运行时/视觉证据时会阻断验收。

`$migrate-feature` 会帮助 Codex：

- 追踪真实入口、状态、API、Bridge 和副作用。
- 优先复用目标项目已有能力。
- 保持业务逻辑、数据契约、交互和 UI 等价。
- 根据风险区分普通迁移、增强验收和阻断项。
- 清楚报告已验证内容，以及仍需浏览器、App 或真机验证的部分。

## 安装

### Codex 桌面客户端

当前仓库通过 GitHub Marketplace 分发。首次使用时，先在终端注册 Marketplace：

```bash
codex plugin marketplace add skeryb001-tech/migrate-feature-plugin --ref main
```

然后回到 Codex 的 **Plugins** 页面，选择 `migrate-feature-marketplace`，找到
`migrate-feature-plugin` 并点击安装。安装完成后新建一个 Codex 任务。

如果插件已发布到公共 Plugin Directory，也可以直接在 **Plugins** 页面搜索
`migrate-feature-plugin` 并安装。

### Codex CLI

```bash
codex plugin marketplace add skeryb001-tech/migrate-feature-plugin --ref main
codex plugin add migrate-feature-plugin@migrate-feature-marketplace
```

安装后新建一个 Codex 会话。

### 本地源码

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

## 第一个任务

直接复制下面的提示词，把路径替换成你的项目路径：

```text
使用 $migrate-feature，把源项目的图片上传功能迁移到目标项目。

源项目：/path/to/source-project
源入口：pages/image-upload.vue

目标项目：/path/to/target-project
目标入口：pages/image-upload.vue

要求：
- 保持业务逻辑、状态和交互等价
- 优先复用目标项目已有组件和请求层
- 不覆盖同名文件
- 不新增依赖
- 完成后说明改动、验证结果和未验证项
```

也可以直接描述需求，插件会根据任务内容自动触发：

```text
把 A 项目的完整图片编辑功能迁移到 B 项目，保持行为和 UI 一致。
```

## 支持范围

- 跨项目迁移：`cross-project`
- 同项目跨页面或视图迁移：`cross-page`
- Web：Vue、React、Nuxt、Next 等
- 混合客户端：Electron、Tauri、WebView 等
- 原生客户端：iOS、Android、Flutter、React Native 等

## 迁移结果

- `PASS`：代码和必需的运行时/视觉验收均完成。
- `CODE_ONLY`：代码级检查完成，但运行时或视觉验收还未完成。
- `BLOCKED`：发现覆盖风险、未授权契约变更、安全/权限问题或其他阻断项。

## 更新插件

```bash
codex plugin marketplace upgrade migrate-feature-marketplace
```

更新后重新打开插件或新建 Codex 任务即可。

## 反馈与贡献

欢迎提交 Issue 或 Pull Request：

<https://github.com/skeryb001-tech/migrate-feature-plugin>

使用问题请附上：源/目标入口、执行提示词、Codex 版本和完整错误信息。不要提交密钥、Cookie、Token 或生产数据。
