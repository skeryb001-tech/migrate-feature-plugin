# 验收与证据规则

阶段、门禁、评分项、迁移拓扑和平台 Checklist 的唯一机器规范源是 `scripts/migrationSpec.py`。使用 `createMigrationReport.py` 渲染执行报告，使用 `validateMigrationReport.py` 判定报告是否完成；本文件只解释评分、证据、视觉和回滚语义。

## 1. 证据

有效证据必须能让另一位执行者复现结论：

- 静态：命令、工具版本、退出码和关键输出。
- 功能：相同输入、环境、操作步骤、预期、实际结果和请求/事件记录。
- 视觉：相同数据、设备/视口、像素密度/scale、缩放、主题、语言和字体状态下，由目标平台真实运行时产生的源/目标截图、渲染样式和几何测量。
- 消费者：仓库级检索范围、直接/间接/动态/自动导入结果和聚焦回归。
- 回滚：起始提交、关闭入口、恢复公共模块/API/埋点和清理持久化的可执行步骤。

“已检查”“看起来一致”“应该没问题”属于结论，不属于证据。

无法运行检查时保留原始阻塞证据，对应评分状态使用 `UNVERIFIED`，原始得分为 0。环境缺失不是 `N/A`。缺少 Browser、App Window/WebView、模拟器/仿真器或真机的真实版本、截图、渲染样式或几何测量时，`runtime_visual_verified` 必须为 `NO`，G6/G8 为 `PENDING_RUNTIME`，最终结论为 `CODE_ONLY`。自定义 renderer、静态 preview/snapshot、设计稿和手工 geometry 只能作为补充证据。

完整运行时视觉证据使用以下机器字段：

```text
runtime_visual_verified: YES
runtime_visual_surface: <BROWSER / WEBVIEW / APP_WINDOW / SIMULATOR / EMULATOR / DEVICE>
runtime_visual_environment: <OS、运行时、UI 框架及版本>
runtime_visual_unit: <CSS_PX / PT / DP / LOGICAL_PX>
runtime_visual_max_error: <0 到 1 的实测值>
runtime_visual_evidence: runtime=<环境>; screenshot=<源/目标/差异图>; rendered_style=<CSSOM 或 view inspector>; viewport=<设备、视口、density/scale、主题、语言、字体>; geometry=<关键布局测量>
```

无法运行时使用：

```text
runtime_visual_verified: NO
runtime_visual_surface: UNVERIFIED
runtime_visual_environment: UNVERIFIED
runtime_visual_unit: UNVERIFIED
runtime_visual_max_error: UNVERIFIED
runtime_visual_evidence: UNVERIFIED: <原因>; evidence=<原始阻塞证据>
```

## 2. 评分状态

| 状态 | 原始得分 | 要求 |
| --- | ---: | --- |
| `PASS` | 该项满分 | 结果通过且证据完整 |
| `PARTIAL` | 大于 0、小于满分 | 仅限用户接受的 P2；记录 P2 编号和接受证据 |
| `FAIL` | 0 | 结果失败，阻断最终验收 |
| `UNVERIFIED` | 0 | 尚未验证；仅视觉运行时待验收可形成 `CODE_ONLY` |
| `N/A` | 0 | 业务上不适用；说明原因并提供证明材料 |

`N/A` 使用以下证据格式：

```text
N/A: <不适用原因>; evidence=<证明材料>
```

### N/A 归一化

有证据的 `N/A` 不扣分，其满分从分母剔除：

```text
raw_score = 所有适用项的原始得分之和
applicable_max_score = 100 - 所有 N/A 项满分之和
total_score = round(raw_score / applicable_max_score * 100, 2)
```

示例：5 分项目为 `N/A`，其余 95 分全部通过：

```text
raw_score = 95
applicable_max_score = 95
total_score = 100
```

`N/A` 只适用于确实不存在的评分分支。环境缺失、证据缺失、尚未执行或执行失败均不能使用 `N/A`。P0/P1、G0–G9、主流程、关键分支、关键 UI 状态、冲突和消费者兼容硬门禁始终需要真实结论。

## 3. UI 等价

在相同对照条件下：

- 关键组件宽高、间距、对齐、位置和布局几何误差必须 `≤1` 个平台逻辑显示单位。
- Web/混合客户端使用 `CSS_PX`；iOS/macOS 使用 `PT`；Android 使用 `DP`；Flutter/React Native 可使用 `LOGICAL_PX`。不得用物理像素密度放宽阈值。
- 颜色、透明度、边框、圆角、阴影和资源应与源一致；使用目标 token/theme 时，以真实运行时的 computed style 或 view inspector 与视觉等价为准。
- 字体栅格化可按 OS/渲染引擎差异解释，文字容器、行高、换行、基线和整体布局仍需满足阈值。
- 动效需对比触发条件、时长、缓动、关键状态、打断和 reduced-motion。

项目或用户给出更严格阈值时使用更严格值。放宽 1 个逻辑显示单位属于验收规则变更，先取得用户确认并记录风险。

## 4. 合格条件

同时满足以下条件才判定完整合格：

- `p0_open = 0`、`p1_open = 0`。
- `runtime_visual_verified = YES`，surface、运行环境和单位符合所选平台，实测最大误差 `≤1`，证据包含目标平台截图、渲染样式、对照环境和几何测量。
- G0–G9 全部 `PASS` 且证据有效。
- 完整阶段、所选迁移拓扑和平台 Checklist 全部保留原 ID、原文本并完成。
- `total_score ≥95`。
- 报告校验脚本返回 0。

报告结构、代码级检查和非视觉硬门禁有效，但运行时视觉证据缺失时，校验脚本返回 3；该状态不是合格，不得对外声明一比一验收通过。报告无效或验收失败时返回 1。

80–94 分为不合格，修复后重新验证。低于 80 分、任一 P0/P1、硬门禁失败、主流程失败、同名覆盖或未授权依赖/公共契约变更均需退回最早错误阶段重做。

## 5. 回滚

实现前记录：

- 目标起始提交和本次改动边界。
- 路由/导航、页面/screen/window、菜单、deep link、入口或 feature flag 的关闭方式。
- 公共组件、store/view model、hook/composable、service/repository/bridge、types 和 exports 的恢复方式及消费者。
- API/IPC/bridge、权限、鉴权、实验和埋点恢复方式。
- cache、storage、IndexedDB、数据库、文件、Keychain/Keystore 和其他持久化清理方式。

回滚步骤需保护目标原有数据、文件和用户改动，并通过演练或静态证据证明可执行。
