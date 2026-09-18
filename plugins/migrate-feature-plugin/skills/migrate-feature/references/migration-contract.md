# 增强验收与证据规则

本文件只用于高风险、跨运行时、共享公共契约或正式一比一验收。请求包含“完整功能、原样、所有功能、一比一”时必须创建严格报告；日常迁移不需要创建报告或逐项填写本文件。

`scripts/migrationSpec.py` 定义 C1–C4、迁移拓扑和平台运行时约束；`createMigrationReport.py` 生成精简报告；`validateMigrationReport.py` 校验机器摘要和四个检查点。报告中的明细表用于工作记录，可按实际范围合并或删除；机器摘要和 C1–C4 不得删除。

当前报告 schema 为 `3`。严格模式的源依赖闭包和功能矩阵使用报告目录下的 JSON 文件；包含 UI 时渲染契约也必须使用 JSON 文件，不能只填写关键词或不存在的文件路径。

## 0. 严格完整迁移字段

严格模式必须填写以下机器字段：

```text
parity_mode: STRICT
visible_ui: YES|NO
source_inventory: file=source-inventory.json
feature_matrix: file=feature-matrix.json
rendering_contract: file=rendering-contract.json 或 visible_ui=NO 时 NOT_REQUIRED: <证据>
route_activation: PASS|PENDING|BLOCKED
unimplemented_items: <非负整数>
adapted_items: <非负整数>
```

`unimplemented_items` 统计 `MISSING`、没有目标落点、没有入口激活证明、未决关键分支以及未经等价证明的替换。严格模式下数量大于 0 时必须为 `BLOCKED`；不能用 `CODE_ONLY` 掩盖功能缺失。`adapted_items` 只统计已实现但存在明确目标差异的职责，不等于缺失项。

`rendering_contract` 是源渲染实现到目标渲染实现的硬性映射，不是“有相似组件”的描述。每个可见功能区至少要说明源模板/组件、源数据源、目标模板/组件、DOM/结构、CSS/几何、状态、交互、错误、API 参数/响应和副作用的对照证据。源项目已有完整模板时，目标同名或相似组件只有在这些职责全部等价时才能标记 `PRESERVED`；未证明等价时必须迁入源实现，或标记 `ADAPTED` 并记录用户可感知差异。

`feature-matrix.json` 必须是非空数组，每项至少包含：

```json
{
  "id": "upload-flow",
  "source": "src/pages/upload.vue",
  "target": "pages/upload.vue",
  "status": "MIGRATED",
  "unimplemented": false,
  "evidence": "matrix evidence: source and target call chains compared"
}
```

`source-inventory.json` 必须是非空数组，每项至少包含 `id`、`kind`、`source`、`dependencies` 和 `evidence`。`dependencies` 必须是字符串数组，用于证明入口到组件、模板、样式、状态、API/Bridge、权限、支付、持久化、路由、资源、埋点和生命周期的递归闭包。

`rendering-contract.json` 必须是非空数组，每个可见区域至少包含 `id`、`source_render`、`target_render`、`decision`、`status`、`template`、`dom`、`css`、`data`、`state`、`interaction`、`error`、`side_effect` 和 `evidence`。`status` 必须与 `decision` 一致；每个字段都必须是可复现的非空证据，而不是“看起来一致”。

## 1. 有效证据

证据应让另一位执行者复现结论：

- 静态：命令、工具版本、退出码和关键输出。
- 功能：输入、环境、操作、预期、实际结果和请求/事件记录。
- 视觉：相同数据、设备/视口、scale、主题、语言和字体下的源/目标截图、渲染样式和几何对照。
- 消费者：检索范围、直接/间接/动态/自动发现结果和聚焦回归。
- 回滚：起始提交、入口关闭、共享能力恢复和持久化清理步骤。

“已检查”“看起来一致”“应该没问题”属于结论，不属于证据。无法运行时使用：

```text
UNVERIFIED: <原因>; evidence=<原始阻塞证据>
```

确实无需执行时使用：

```text
NOT_REQUIRED: <原因>; evidence=<范围或调用链证明>
```

## 2. 条件式运行时验收

严格模式中 `visible_ui=YES` 时必须填写并通过真实运行环境；非严格模式或 `visible_ui=NO` 的纯逻辑迁移才可以不要求运行时：

```text
runtime_required: YES
runtime_verified: YES
runtime_environment: <环境与版本>
runtime_evidence: <命令、操作、请求或结果>
```

纯静态映射、类型迁移或无运行时影响时可使用 `runtime_required: NO`，其余字段使用 `NOT_REQUIRED` 格式。需要但无法运行时，`runtime_verified: NO`、环境填 `UNVERIFIED`，结论为 `CODE_ONLY`。

## 3. 条件式视觉验收

严格模式中 `visible_ui=YES` 时必须设置 `visual_required: YES`。非严格模式下，只有迁移包含用户可见 UI 且用户或项目要求正式视觉验收时，才设置 `visual_required: YES`。完整证据至少包含：

```text
visual_verified: YES
visual_surface: <BROWSER / WEBVIEW / APP_WINDOW / SIMULATOR / EMULATOR / DEVICE>
visual_unit: <CSS_PX / PT / DP / LOGICAL_PX>
visual_environment: <OS、运行时、UI 框架及版本>
visual_evidence: screenshot=<源/目标>; rendered_style=<CSSOM 或 inspector>; viewport=<条件>; geometry=<对照>
```

误差阈值使用用户或项目给出的标准；没有明确数值时，以关键布局、状态和交互的用户可感知等价为准，不人为制造统一评分。静态 preview、snapshot renderer 和设计稿只能作为补充证据。

没有 UI 时使用 `visible_ui=NO`、`visual_required: NO` 和 `NOT_REQUIRED` 证据；严格模式 UI 迁移不能用“不要求正式视觉验收”跳过视觉验证。需要但运行环境不可用时使用 `UNVERIFIED`，结论为 `CODE_ONLY`。

## 4. 结论

- `PASS`：C1–C4 通过、阻断项为 0，所有必需运行时/视觉验收完成。
- `CODE_ONLY`：C1–C4 和代码级证据有效、阻断项为 0，但必需运行时或视觉证据待补。
- `BLOCKED`：存在数据、安全、权限、生产配置、不可逆写入、同名覆盖、未授权公共契约变更或其他阻断项。

严格模式额外要求：`source_inventory`、`feature_matrix` 和可见 UI 对应的 `rendering_contract` JSON 有效，`route_activation=PASS`，功能矩阵逐项解析，`unimplemented_items` 与矩阵统计一致且为 `0`。否则结论只能为 `BLOCKED` 或在仅缺运行时/视觉证据时为 `CODE_ONLY`，但不能声称完整迁移已完成。

校验器退出码分别为 `0`、`3`、`1`。不再使用 100 分评分、P0/P1/P2 计数或不适用项逐条归一化。

## 5. 回滚

至少记录目标起始提交、入口关闭方式、共享能力/API/bridge/权限/埋点恢复方式，以及本次新增持久化数据的清理方式。回滚不得覆盖目标已有文件、数据或用户改动。
