#!/usr/bin/env python3
"""Web 与客户端功能迁移的单一机器规范源。"""

from __future__ import annotations

import re
from typing import TypedDict


class ChecklistItem(TypedDict):
    """可校验的 Checklist 项。"""

    id: str
    text: str


class StageSpec(TypedDict):
    """迁移阶段规范。"""

    id: str
    title: str
    action: str
    completion: str
    gates: list[str]
    checklist: list[ChecklistItem]


class ModeSpec(TypedDict):
    """迁移模式规范。"""

    title: str
    checklist: list[ChecklistItem]


class PlatformSpec(TypedDict):
    """迁移平台规范。"""

    title: str
    runtime_surfaces: list[str]
    runtime_units: list[str]
    runtime_patterns: list[str]
    runtime_unit_patterns: dict[str, list[str]]
    checklist: list[ChecklistItem]


def item(item_id: str, text: str) -> ChecklistItem:
    """创建 Checklist 项。"""

    return {"id": item_id, "text": text}


GATES = [
    ("G0", "准入门禁"),
    ("G1", "资产门禁"),
    ("G2", "冲突门禁"),
    ("G3", "目标结构与规范门禁"),
    ("G4", "底层能力门禁"),
    ("G5", "逻辑门禁"),
    ("G6", "UI 门禁"),
    ("G7", "共享消费者门禁"),
    ("G8", "验收门禁"),
    ("G9", "归档与回滚门禁"),
]

RUNTIME_VISUAL_GATE_IDS = {"G6", "G8"}

RUNTIME_VISUAL_CHECKLIST_IDS = {
    "PH5-04",
    "PH7-04",
    "PH8-06",
    "PH8-07",
    "WF06",
    "HC11",
    "NC13",
}


STAGES: list[StageSpec] = [
    {
        "id": "PH1",
        "title": "梳理盘点",
        "action": "建立源基线，追踪真实调用链，盘点目标能力、UI 状态、运行平台、消费者和风险。",
        "completion": "G0、G1 通过；源基线、调用链、UI 状态矩阵和复用候选均有证据。",
        "gates": ["G0", "G1"],
        "checklist": [
            item("PH1-01", "读取源、目标及目录级生效规范，记录允许写入边界"),
            item("PH1-02", "记录源/目标基准分支或提交以及工作区已有改动"),
            item("PH1-03", "从用户入口追到 handler/intent/action、状态所有者、service/bridge/API、结果、导航和埋点"),
            item("PH1-04", "记录输入、输出、默认值、状态转换、异常和副作用"),
            item("PH1-05", "建立初始、加载、空、成功、失败、禁用和交互 UI 状态矩阵"),
            item("PH1-06", "仓库级搜索目标已有组件、hook/composable、view model/store、service/repository、utils、types 和依赖"),
            item("PH1-07", "识别权限、支付、实验、上传下载、缓存、持久化和埋点边界"),
            item("PH1-08", "选择唯一迁移拓扑与平台模式并记录权威逻辑、运行时和视觉验收来源"),
        ],
    },
    {
        "id": "PH2",
        "title": "环境与目标映射",
        "action": "先确定目标目录、分层、依赖和验证方式，再执行冲突扫描与回滚设计。",
        "completion": "G2、G3 通过；每项源职责都有目标落点，阻断性冲突为 0。",
        "gates": ["G2", "G3"],
        "checklist": [
            item("PH2-01", "读取目标包/依赖管理、锁定文件、SDK/toolchain、构建和测试约定"),
            item("PH2-02", "记录框架、导航、渲染运行时、代码生成、环境变量和配置差异"),
            item("PH2-03", "把每项源职责映射到目标目录、模块分层和命名规则"),
            item("PH2-04", "按复用、适配、迁入、阻塞为每项能力作出决策"),
            item("PH2-05", "运行精确路径、大小写、文件类型、导航标识、状态容器、导出/注册和自动发现冲突检查"),
            item("PH2-06", "扫描拟修改共享能力的直接、间接、动态和自动导入消费者"),
            item("PH2-07", "记录起始提交、入口关闭、共享模块恢复和持久化清理方案"),
            item("PH2-08", "确认开发运行环境、浏览器/WebView/模拟器/真机验证、依赖变更和公共契约修改权限"),
        ],
    },
    {
        "id": "PH3",
        "title": "底层能力落地",
        "action": "在目标结构中实现类型、请求/bridge、状态、基础 UI、token、资源和最窄适配层。",
        "completion": "G4 通过；底层能力可独立验证，且没有未授权依赖或临时伪实现。",
        "gates": ["G4"],
        "checklist": [
            item("PH3-01", "契约等价能力直接复用目标实现"),
            item("PH3-02", "部分等价能力通过最窄适配层统一契约"),
            item("PH3-03", "目标缺失能力只迁入最小必要实现并直接按目标结构落盘"),
            item("PH3-04", "类型、默认值、序列化、鉴权和错误格式已对齐"),
            item("PH3-05", "基础组件、设计 token、图标、资源和 i18n 使用目标系统"),
            item("PH3-06", "新增依赖或公共契约变更均有明确授权"),
            item("PH3-07", "底层验证不依赖静态数据、吞错或临时 mock 伪装成功"),
        ],
    },
    {
        "id": "PH4",
        "title": "业务逻辑落地",
        "action": "保持业务契约、状态机、异步时序、权限、缓存、异常和埋点语义等价。",
        "completion": "G5 通过；主流程和关键分支等价，副作用次数与源基准一致。",
        "gates": ["G5"],
        "checklist": [
            item("PH4-01", "输入、输出、默认值、校验和状态转换与源一致"),
            item("PH4-02", "请求方法、参数、次数、顺序、响应解析和错误反馈与源一致"),
            item("PH4-03", "重试、取消、超时、慢请求和乱序响应行为已对齐"),
            item("PH4-04", "登录、权限、额度、支付、实验和灰度分支已对齐"),
            item("PH4-05", "缓存、持久化、刷新恢复和业务 id 隔离已对齐"),
            item("PH4-06", "埋点事件名、字段、触发边缘和次数已对齐"),
            item("PH4-07", "请求、订阅、watcher、计时器和写入均有唯一职责所有者"),
        ],
    },
    {
        "id": "PH5",
        "title": "页面与 UI 复刻",
        "action": "用目标 UI 系统实现源功能的结构、全部状态、交互、自适应和动效。",
        "completion": "实现完成；完整 PASS 时 G6 通过，且目标平台运行时关键尺寸和位置误差 ≤1 逻辑显示单位。",
        "gates": ["G6"],
        "checklist": [
            item("PH5-01", "页面/视图结构、内容层级、文案和语义元素与源一致"),
            item("PH5-02", "初始、加载、空、成功、失败和禁用状态完整"),
            item("PH5-03", "hover/pressed、active、focus、选中、弹层、键盘和触控行为完整"),
            item("PH5-04", "目标平台实测宽高、间距、对齐、滚动和关键位置误差均 ≤1 逻辑显示单位"),
            item("PH5-05", "颜色、透明度、边框、圆角、阴影和资源视觉一致或 token 等价"),
            item("PH5-06", "响应式/自适应、安全区、主题、多语言、长文案和极端数据状态已覆盖"),
            item("PH5-07", "动效触发、时长、缓动、打断和 reduced-motion 行为已覆盖"),
        ],
    },
    {
        "id": "PH6",
        "title": "上下文集成",
        "action": "完成导航、布局/窗口、i18n、deep link/SEO、命名、引用和生命周期集成，不再重组目标架构。",
        "completion": "G2、G3 复验通过；最终路径、命名、引用和上下文符合目标规范。",
        "gates": ["G2", "G3"],
        "checklist": [
            item("PH6-01", "路由/导航、layout/screen/window、guard/middleware、deep link、metadata/SEO 和权限入口已接入"),
            item("PH6-02", "最终文件路径、命名、导出和测试结构符合目标规范"),
            item("PH6-03", "同名职责等价时复用或最小合并，非等价时语义化重命名"),
            item("PH6-04", "组件名、静态/动态导入、自动发现/注册、barrel export 和资源引用已同步"),
            item("PH6-05", "生命周期初始化、离开/后台清理、缓存恢复、窗口/滚动和焦点所有权已接入"),
            item("PH6-06", "旧调用点、无效 shim、临时适配和死代码已确认并清理"),
            item("PH6-07", "重新运行冲突扫描并确认阻断性冲突为 0"),
        ],
    },
    {
        "id": "PH7",
        "title": "多层校验",
        "action": "执行静态、功能、视觉、边界、副作用和共享消费者回归。",
        "completion": "G7 通过；除明确待运行时视觉验收项外，每个检查都有可复现证据，迁移新增错误为 0。",
        "gates": ["G7"],
        "checklist": [
            item("PH7-01", "按目标项目方式执行 lint、typecheck、测试或构建"),
            item("PH7-02", "用相同输入验证主流程和全部关键分支"),
            item("PH7-03", "验证空、错、慢、取消、重复提交、并发和快速切换"),
            item("PH7-04", "在目标平台真实运行时固定对照条件，记录环境版本并保留截图、渲染样式和几何测量"),
            item("PH7-05", "核对请求、订阅、watcher、计时器、写入和埋点次数"),
            item("PH7-06", "回归源入口、目标入口和全部关键共享消费者"),
            item("PH7-07", "记录跳过项的原始阻塞证据、替代证据和残余风险"),
        ],
    },
    {
        "id": "PH8",
        "title": "回归验收",
        "action": "读取验收规则，按证据评分，剔除有证据的 N/A 并归一化到 100 分。",
        "completion": "完整 PASS 时 G8 通过、P0=0、P1=0、全部硬门禁 PASS、归一化总分 ≥95。",
        "gates": ["G8"],
        "checklist": [
            item("PH8-01", "每个 PASS 和 PARTIAL 评分项都有可复现证据"),
            item("PH8-02", "每个 N/A 都有不适用原因和证明材料"),
            item("PH8-03", "N/A 满分已从适用满分分母中剔除"),
            item("PH8-04", "raw_score、applicable_max_score 和 total_score 计算一致"),
            item("PH8-05", "P0 未解决项和 P1 未解决项均为 0"),
            item("PH8-06", "完整 PASS 时 G0–G8 门禁均有 PASS 证据"),
            item("PH8-07", "目标平台运行时截图、渲染样式和几何测量证明关键误差 ≤1 逻辑显示单位"),
        ],
    },
    {
        "id": "PH9",
        "title": "归档沉淀",
        "action": "归档映射、风险、验证、评分、影响、回滚和剩余事项。",
        "completion": "G9 通过且报告校验脚本返回 0 或 3；交付记录可复现且不含敏感信息。",
        "gates": ["G9"],
        "checklist": [
            item("PH9-01", "范围、基准、环境、模式和权威验收来源完整"),
            item("PH9-02", "调用链、能力映射、文件映射和重命名记录完整"),
            item("PH9-03", "风险、处理、复验、P2 接受记录和残余风险完整"),
            item("PH9-04", "验证命令、环境、结果、证据和评分完整"),
            item("PH9-05", "用户影响、接口、状态、权限、埋点、性能和消费者影响完整"),
            item("PH9-06", "回滚起点、入口关闭、公共模块恢复和持久化清理完整"),
            item("PH9-07", "报告不包含密钥、cookie、token、个人数据或生产敏感响应"),
        ],
    },
]


MODES: dict[str, ModeSpec] = {
    "cross-project": {
        "title": "跨项目专项 Checklist",
        "checklist": [
            item("CP01", "读取两个工程及相关 monorepo package 的生效规范"),
            item("CP02", "对比框架、语言、渲染模式、构建工具和目标运行平台范围"),
            item("CP03", "对比包/依赖管理器、锁定文件、workspace/module 和构建边界"),
            item("CP04", "对比路径别名、自动导入/注册、代码生成、SDK 和运行时配置"),
            item("CP05", "把每个源依赖映射为目标已有依赖、目标封装、无需依赖或待授权"),
            item("CP06", "保持目标锁文件、构建配置和基础设施为唯一实现"),
            item("CP07", "只迁移环境变量名称与用途，保护 secret 和生产值"),
            item("CP08", "适配代理、base URL、CDN/资源包、public path、应用容器和部署前缀"),
            item("CP09", "确认第三方 SDK、字体、图片和资产许可边界"),
            item("CP10", "区分服务端配置、客户端公开配置和 secret"),
            item("CP11", "复用目标请求层、鉴权、错误格式、超时、重试和取消机制"),
            item("CP12", "把跨项目字段差异收敛在类型明确的边界适配器"),
            item("CP13", "检查跨 package/module/target 类型、导出和运行时依赖边界"),
            item("CP14", "把资源接入目标 assets、bundle、public 或 CDN 管线并验证构建路径"),
            item("CP15", "回归 monorepo/multi-module 受影响构建单元和反向依赖"),
            item("CP16", "验证生产构建、按需加载、bundle/chunk、冷启动和目标运行时渲染"),
            item("CP17", "确认目标全局样式、provider、plugin 和初始化逻辑没有重复注册"),
        ],
    },
    "cross-page": {
        "title": "同项目跨页面/视图专项 Checklist",
        "checklist": [
            item("PG01", "明确源页面/视图迁移后保留、替换或下线的行为边界"),
            item("PG02", "对比 params/query/hash、route/screen name、deep link、redirect 和动态导航 key"),
            item("PG03", "对比 layout/shell、guard/middleware、page/screen meta、权限和 SEO 适用项"),
            item("PG04", "对比渲染模式、keep-alive/视图缓存、状态恢复和 hydration 适用项"),
            item("PG05", "覆盖直接入口、应用内导航、deep link、重定向和 back stack/history"),
            item("PG06", "区分组件私有、页面/视图私有、会话共享和全局共享状态"),
            item("PG07", "保持页面/视图私有状态在正确作用域内"),
            item("PG08", "按业务 id、用户或会话隔离需要共享的状态"),
            item("PG09", "对齐初始化、导航参数变化重置、再次进入和刷新/重启恢复行为"),
            item("PG10", "覆盖目标框架 activate/deactivate、mount/unmount、appear/disappear 和前后台生命周期"),
            item("PG11", "只持久化耐久且可序列化的数据"),
            item("PG12", "验证 A→B、B→A 和 A→B→A 连续导航"),
            item("PG13", "验证返回/前进、直接刷新或应用重启以及状态恢复"),
            item("PG14", "验证不同导航参数、deep link 和业务 id 的切换"),
            item("PG15", "验证 A、B 并行标签页、窗口、任务或分屏时的状态隔离"),
            item("PG16", "在离开、deactivate 或业务 id 变化时清理失效副作用"),
            item("PG17", "验证返回页面时不会重复扣费、写入、埋点或弹窗"),
            item("PG18", "回归仍需保留的源页面入口、功能、UI 和共享契约"),
            item("PG19", "适配目标页面/视图容器、安全区、滚动所有权、弹层挂载点、键盘和焦点恢复"),
        ],
    },
}


PLATFORMS: dict[str, PlatformSpec] = {
    "web-frontend": {
        "title": "Web 前端平台 Checklist",
        "runtime_surfaces": ["BROWSER"],
        "runtime_units": ["CSS_PX"],
        "runtime_patterns": [
            r"\b(?:Chrome|Chromium|Firefox|WebKit|Safari|Edge)\b.*\d",
        ],
        "runtime_unit_patterns": {"CSS_PX": [r".+"]},
        "checklist": [
            item("WF01", "记录目标浏览器引擎、版本矩阵、DPR、缩放和字体加载条件"),
            item("WF02", "对齐 DOM/语义结构、CSS cascade、盒模型和设计 token 最终值"),
            item("WF03", "对齐 SSR/CSR、hydration、client-only 和首次可交互行为"),
            item("WF04", "对齐 URL、history、刷新、缓存和多标签页行为"),
            item("WF05", "验证键盘、焦点、ARIA、屏幕阅读器语义和 reduced-motion"),
            item("WF06", "使用真实浏览器截图、CSSOM computed style 和 DOM 几何完成视觉验收"),
        ],
    },
    "hybrid-client": {
        "title": "混合客户端平台 Checklist",
        "runtime_surfaces": ["WEBVIEW", "APP_WINDOW"],
        "runtime_units": ["CSS_PX"],
        "runtime_patterns": [
            r"\b(?:Electron|Tauri|WKWebView|Android\s+WebView|WebView2)\b.*\d",
        ],
        "runtime_unit_patterns": {"CSS_PX": [r".+"]},
        "checklist": [
            item("HC01", "识别 Electron/Tauri/WebView 的主进程、渲染进程、宿主和版本边界"),
            item("HC02", "复用目标 preload、command、IPC、bridge 和序列化契约"),
            item("HC03", "保持 context isolation、sandbox、CSP、origin 和导航白名单"),
            item("HC04", "对齐窗口创建、单实例、多窗口、最小化、恢复和退出生命周期"),
            item("HC05", "对齐前后台、休眠唤醒、离线、网络恢复和系统主题变化"),
            item("HC06", "对齐文件系统、剪贴板、通知、托盘、协议和外部链接权限"),
            item("HC07", "对齐 deep link、自定义协议、应用内导航和 back stack"),
            item("HC08", "保护本地路径、凭证、secure storage、更新通道和签名配置"),
            item("HC09", "验证 bridge/IPC 请求次数、取消、超时、错误和销毁后清理"),
            item("HC10", "验证目标 OS、窗口尺寸、DPR、缩放、安全区和输入设备矩阵"),
            item("HC11", "使用真实 App Window/WebView 截图、computed style 和几何完成视觉验收"),
            item("HC12", "验证打包产物、资源协议、asar/bundle 路径和冷启动行为"),
        ],
    },
    "native-client": {
        "title": "原生客户端平台 Checklist",
        "runtime_surfaces": ["SIMULATOR", "EMULATOR", "DEVICE"],
        "runtime_units": ["PT", "DP", "LOGICAL_PX"],
        "runtime_patterns": [
            r"\b(?:iOS|iPadOS|macOS|tvOS|visionOS|Android|Windows|Linux)\b.*\d",
            r"\b(?:SwiftUI|UIKit|AppKit|Jetpack\s+Compose|Android\s+Views|Flutter|React\s+Native|WinUI|WPF|\.NET\s+MAUI|Qt)\b",
        ],
        "runtime_unit_patterns": {
            "PT": [r"\b(?:SwiftUI|UIKit|AppKit)\b"],
            "DP": [r"\b(?:Jetpack\s+Compose|Android\s+Views)\b"],
            "LOGICAL_PX": [
                r"\b(?:Flutter|React\s+Native|WinUI|WPF|\.NET\s+MAUI|Qt)\b"
            ],
        },
        "checklist": [
            item("NC01", "记录 OS、SDK/toolchain、UI 框架、最低版本、设备和架构矩阵"),
            item("NC02", "复用目标 screen/view、navigation、view model/reducer 和 repository 分层"),
            item("NC03", "对齐 push/pop/modal/tab/deep link、返回手势和状态恢复"),
            item("NC04", "对齐 create/appear/disappear/destroy、前后台、终止和恢复生命周期"),
            item("NC05", "对齐线程/协程/isolate、异步取消、竞态和主线程 UI 更新"),
            item("NC06", "对齐权限申请、拒绝、永久拒绝、系统设置返回和隐私声明"),
            item("NC07", "对齐 Keychain/Keystore、数据库、文件、偏好设置和迁移版本"),
            item("NC08", "对齐相机、相册、文件、分享、通知、定位和后台任务适用项"),
            item("NC09", "对齐安全区、状态栏、导航栏、刘海/折叠屏、键盘和旋转"),
            item("NC10", "对齐字号缩放、深色模式、本地化、RTL 和无障碍语义"),
            item("NC11", "复用目标原生模块/bridge/plugin，验证 ABI、架构和版本兼容"),
            item("NC12", "验证启动、低内存、进程重建、离线、弱网和后台恢复"),
            item("NC13", "使用模拟器/仿真器或真机截图、view inspector 样式和几何完成视觉验收"),
            item("NC14", "验证 debug/release 构建、资源包、签名边界和受影响测试 target"),
        ],
    },
}


SCORE_ITEMS = [
    ("S01", "静态代码", "语法与类型", 4),
    ("S02", "静态代码", "lint、格式与工程检查", 3),
    ("S03", "静态代码", "路径、命名、导出与自动导入冲突", 4),
    ("S04", "静态代码", "残留引用、shim 与死代码", 2),
    ("S05", "静态代码", "目标规范、结构与无关改动", 2),
    ("F01", "功能逻辑", "主流程", 10),
    ("F02", "功能逻辑", "关键分支与失败分支", 8),
    ("F03", "功能逻辑", "API 与数据契约", 6),
    ("F04", "功能逻辑", "状态、缓存与恢复", 4),
    ("F05", "功能逻辑", "权限、支付与实验", 3),
    ("F06", "功能逻辑", "埋点与副作用次数", 4),
    ("U01", "视觉还原", "结构与内容", 5),
    ("U02", "视觉还原", "几何、布局与响应式/自适应", 7),
    ("U03", "视觉还原", "颜色、透明度与设计 token", 6),
    ("U04", "视觉还原", "交互与无障碍", 5),
    ("U05", "视觉还原", "全部关键 UI 状态", 5),
    ("U06", "视觉还原", "动效与资源", 2),
    ("B01", "边界场景", "空数据与极端数据", 3),
    ("B02", "边界场景", "异常与网络边界", 4),
    ("B03", "边界场景", "重复、并发与取消", 3),
    ("B04", "边界场景", "导航、刷新与恢复", 3),
    ("B05", "边界场景", "设备、主题与 i18n", 2),
    ("A01", "归档完整", "能力、文件映射与风险", 2),
    ("A02", "归档完整", "验证证据与客观评分", 2),
    ("A03", "归档完整", "差异、回滚与后续项", 1),
]


def expected_checklist_ids(mode: str, platform: str) -> set[str]:
    """返回指定拓扑与平台必须出现的全部 Checklist ID。"""

    stage_ids = {
        checklist_item["id"]
        for stage in STAGES
        for checklist_item in stage["checklist"]
    }
    mode_ids = {
        checklist_item["id"]
        for checklist_item in MODES[mode]["checklist"]
    }
    platform_ids = {
        checklist_item["id"]
        for checklist_item in PLATFORMS[platform]["checklist"]
    }
    return stage_ids | mode_ids | platform_ids


def total_score_weight() -> int:
    """返回原始评分总权重。"""

    return sum(maximum for _, _, _, maximum in SCORE_ITEMS)


def specification_errors() -> list[str]:
    """返回机器规范源自身的完整性错误。"""

    errors: list[str] = []
    gate_ids = [gate_id for gate_id, _ in GATES]
    expected_gate_ids = [f"G{index}" for index in range(10)]
    if gate_ids != expected_gate_ids:
        errors.append("硬门禁必须按 G0–G9 唯一且有序定义")

    stage_ids = [stage["id"] for stage in STAGES]
    expected_stage_ids = [f"PH{index}" for index in range(1, 10)]
    if stage_ids != expected_stage_ids:
        errors.append("迁移阶段必须按 PH1–PH9 唯一且有序定义")

    known_gate_ids = set(gate_ids)
    all_checklist_ids: list[str] = []
    for stage in STAGES:
        invalid_gates = sorted(set(stage["gates"]) - known_gate_ids)
        if invalid_gates:
            errors.append(
                f"{stage['id']} 引用了未知门禁：{', '.join(invalid_gates)}"
            )
        all_checklist_ids.extend(
            checklist_item["id"] for checklist_item in stage["checklist"]
        )

    if set(MODES) != {"cross-project", "cross-page"}:
        errors.append("迁移模式必须包含且只包含 cross-project、cross-page")
    for mode_spec in MODES.values():
        all_checklist_ids.extend(
            checklist_item["id"] for checklist_item in mode_spec["checklist"]
        )

    expected_platforms = {"web-frontend", "hybrid-client", "native-client"}
    if set(PLATFORMS) != expected_platforms:
        errors.append(
            "平台模式必须包含且只包含 web-frontend、hybrid-client、native-client"
        )
    for platform_name, platform_spec in PLATFORMS.items():
        all_checklist_ids.extend(
            checklist_item["id"]
            for checklist_item in platform_spec["checklist"]
        )
        if not platform_spec["runtime_surfaces"]:
            errors.append(f"{platform_name} 必须定义运行时 surface")
        if not platform_spec["runtime_units"]:
            errors.append(f"{platform_name} 必须定义视觉测量单位")
        if not platform_spec["runtime_patterns"]:
            errors.append(f"{platform_name} 必须定义运行环境匹配规则")
        if set(platform_spec["runtime_unit_patterns"]) != set(
            platform_spec["runtime_units"]
        ):
            errors.append(f"{platform_name} 的单位与单位匹配规则必须一一对应")
        for runtime_pattern in platform_spec["runtime_patterns"]:
            try:
                re.compile(runtime_pattern)
            except re.error as error:
                errors.append(
                    f"{platform_name} 运行环境匹配规则非法：{error}"
                )
        for unit_patterns in platform_spec["runtime_unit_patterns"].values():
            if not unit_patterns:
                errors.append(f"{platform_name} 的单位匹配规则不能为空")
            for unit_pattern in unit_patterns:
                try:
                    re.compile(unit_pattern)
                except re.error as error:
                    errors.append(
                        f"{platform_name} 单位匹配规则非法：{error}"
                    )

    duplicate_checklist_ids = sorted(
        {
            checklist_id
            for checklist_id in all_checklist_ids
            if all_checklist_ids.count(checklist_id) > 1
        }
    )
    if duplicate_checklist_ids:
        errors.append(
            "Checklist ID 重复：" + ", ".join(duplicate_checklist_ids)
        )

    invalid_runtime_checklists = sorted(
        RUNTIME_VISUAL_CHECKLIST_IDS - set(all_checklist_ids)
    )
    if invalid_runtime_checklists:
        errors.append(
            "运行时视觉 Checklist 不存在："
            + ", ".join(invalid_runtime_checklists)
        )

    invalid_runtime_gates = sorted(RUNTIME_VISUAL_GATE_IDS - known_gate_ids)
    if invalid_runtime_gates:
        errors.append(
            "运行时视觉门禁不存在：" + ", ".join(invalid_runtime_gates)
        )

    score_ids = [item_id for item_id, *_ in SCORE_ITEMS]
    duplicate_score_ids = sorted(
        {score_id for score_id in score_ids if score_ids.count(score_id) > 1}
    )
    if duplicate_score_ids:
        errors.append("评分 ID 重复：" + ", ".join(duplicate_score_ids))
    if any(maximum <= 0 for *_, maximum in SCORE_ITEMS):
        errors.append("评分权重必须全部大于 0")
    if total_score_weight() != 100:
        errors.append("评分总权重必须为 100")

    return errors
