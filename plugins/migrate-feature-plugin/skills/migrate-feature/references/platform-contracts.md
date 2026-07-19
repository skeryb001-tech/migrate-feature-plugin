# 平台执行契约

只读取并执行报告中选定的平台分支。迁移拓扑决定“从哪里迁到哪里”，平台模式决定运行时、生命周期、安全边界和视觉证据；两者必须同时记录。

## `web-frontend`

适用于浏览器中的 Vue、React、Nuxt、Next、H5 和同类 Web UI。

- 把 DOM/语义结构、CSS cascade、盒模型、SSR/CSR、hydration、URL/history、缓存和多标签页纳入契约。
- 复用目标组件、token、路由、请求层、状态管理、i18n 和可访问性模式。
- 使用真实 Chrome/Chromium、Firefox、Safari/WebKit 或 Edge，记录完整版本。
- `runtime_visual_surface=BROWSER`，`runtime_visual_unit=CSS_PX`。
- 视觉证据使用浏览器截图、CSSOM computed style、DOM geometry 和固定 viewport/DPR/zoom。

## `hybrid-client`

适用于 Electron、Tauri、WKWebView、Android WebView、WebView2 以及其他 Web UI + 原生宿主客户端。

- 分离主进程/宿主、渲染进程/WebView、preload/bridge 和共享业务层的职责。
- 复用目标 IPC/command/bridge；保持 channel、payload、序列化、权限、错误、取消和调用次数等价。
- 保持 context isolation、sandbox、CSP、origin、导航白名单和最小权限，不把宿主能力直接暴露给页面。
- 覆盖窗口创建、单实例、多窗口、最小化/恢复、前后台、休眠唤醒、离线恢复和退出清理。
- 检查文件系统、剪贴板、通知、托盘、deep link、自定义协议、secure storage、更新与签名边界。
- 使用实际构建/运行的 App Window 或 WebView；浏览器标签页只能作为补充证据。
- `runtime_visual_surface=APP_WINDOW|WEBVIEW`，`runtime_visual_unit=CSS_PX`。

## `native-client`

适用于 SwiftUI/UIKit/AppKit、Jetpack Compose/Android Views、Flutter、React Native、WinUI/WPF/.NET MAUI/Qt 等客户端。

- 记录 OS、SDK/toolchain、UI 框架、最低版本、设备、CPU 架构和构建 target/module。
- 复用目标 navigation、screen/view、view model/reducer、repository、DI、主题和本地化体系。
- 对齐 create/appear/disappear/destroy、前后台、进程重建、低内存、异步线程和取消语义。
- 对齐权限拒绝、系统设置返回、Keychain/Keystore、数据库、文件、偏好设置和 schema migration。
- 覆盖 safe area、状态/导航栏、刘海/折叠屏、键盘、旋转、字号缩放、RTL 和无障碍。
- 原生模块/bridge/plugin 复用必须验证 ABI、架构、版本和 release 构建兼容。
- 使用模拟器、仿真器或真机；静态 preview、snapshot renderer 和设计稿只能作为补充证据。
- `runtime_visual_surface=SIMULATOR|EMULATOR|DEVICE`；iOS/macOS 使用 `PT`，Android 使用 `DP`，Flutter/React Native 可使用 `LOGICAL_PX`。

## 共同视觉门禁

完整 PASS 必须记录：

```text
runtime_visual_verified: YES
runtime_visual_surface: <平台允许值>
runtime_visual_environment: <OS、运行时、UI 框架及版本>
runtime_visual_unit: <CSS_PX / PT / DP / LOGICAL_PX>
runtime_visual_max_error: <0 到 1>
runtime_visual_evidence: runtime=<环境>; screenshot=<源/目标>; rendered_style=<样式或 inspector>; viewport=<设备/视口/scale>; geometry=<测量>
```

任一运行时证据缺失时，把上述 surface/environment/unit/max_error 填为 `UNVERIFIED`，G6/G8 填为 `PENDING_RUNTIME`，结论填为 `CODE_ONLY`。环境缺失不是 `N/A`。
