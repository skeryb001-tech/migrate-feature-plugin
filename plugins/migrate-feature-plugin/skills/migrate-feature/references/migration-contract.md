# 增强验收与证据规则

本文件只用于高风险、跨运行时、共享公共契约或正式一比一验收。日常迁移不需要创建报告或逐项填写本文件。

`scripts/migrationSpec.py` 定义 C1–C4、迁移拓扑和平台运行时约束；`createMigrationReport.py` 生成精简报告；`validateMigrationReport.py` 校验机器摘要和四个检查点。报告中的明细表用于工作记录，可按实际范围合并或删除；机器摘要和 C1–C4 不得删除。

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

只有业务结果必须在真实运行环境中证明时才填写：

```text
runtime_required: YES
runtime_verified: YES
runtime_environment: <环境与版本>
runtime_evidence: <命令、操作、请求或结果>
```

纯静态映射、类型迁移或无运行时影响时可使用 `runtime_required: NO`，其余字段使用 `NOT_REQUIRED` 格式。需要但无法运行时，`runtime_verified: NO`、环境填 `UNVERIFIED`，结论为 `CODE_ONLY`。

## 3. 条件式视觉验收

只有迁移包含用户可见 UI，且用户或项目要求正式视觉验收时，才设置 `visual_required: YES`。完整证据至少包含：

```text
visual_verified: YES
visual_surface: <BROWSER / WEBVIEW / APP_WINDOW / SIMULATOR / EMULATOR / DEVICE>
visual_unit: <CSS_PX / PT / DP / LOGICAL_PX>
visual_environment: <OS、运行时、UI 框架及版本>
visual_evidence: screenshot=<源/目标>; rendered_style=<CSSOM 或 inspector>; viewport=<条件>; geometry=<对照>
```

误差阈值使用用户或项目给出的标准；没有明确数值时，以关键布局、状态和交互的用户可感知等价为准，不人为制造统一评分。静态 preview、snapshot renderer 和设计稿只能作为补充证据。

没有 UI 或不要求正式视觉验收时使用 `visual_required: NO` 和 `NOT_REQUIRED` 证据；需要但运行环境不可用时使用 `UNVERIFIED`，结论为 `CODE_ONLY`。

## 4. 结论

- `PASS`：C1–C4 通过、阻断项为 0，所有必需运行时/视觉验收完成。
- `CODE_ONLY`：C1–C4 和代码级证据有效、阻断项为 0，但必需运行时或视觉证据待补。
- `BLOCKED`：存在数据、安全、权限、生产配置、不可逆写入、同名覆盖、未授权公共契约变更或其他阻断项。

校验器退出码分别为 `0`、`3`、`1`。不再使用 100 分评分、P0/P1/P2 计数或不适用项逐条归一化。

## 5. 回滚

至少记录目标起始提交、入口关闭方式、共享能力/API/bridge/权限/埋点恢复方式，以及本次新增持久化数据的清理方式。回滚不得覆盖目标已有文件、数据或用户改动。
