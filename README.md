# ESP32 Agent iPad personal test build

Based on [ESP32 iPhone Agent](https://github.com/onehumanbeing/esp32-iphone-agent) by Henry Yuan.
Copyright (c) 2026 Henry Yuan. The upstream MIT license and NOTICE are included.
Public demos, videos, and posts of derived work should credit that project.

此目录是可审查的编译脚本；IPA 安装包从 Actions 构建产物下载。

## 编译内容

- 固定使用上游 v0.2.4 的提交 `0b22d9a99ce7bc887860e46fa1a61761836a55d2`。
- 用 GitHub 标准 `macos-26` 运行器的 Xcode 生成 arm64 真机应用。
- 明确启用 iPhone 和 iPad 设备类型，不改动 Swift 控制算法或开发板固件。
- 不添加热点配置、VPN、App Groups 等付费账号能力，不内置模型密钥或官方试用服务。
- 核验真机架构、iPad 设备类型、未加密状态、ZIP 完整性和 SHA-256，再输出未签名 IPA。
- 另在 iPad 模拟器运行上游单元测试；模拟器测试不能替代 USB、蓝牙和 AirPlay 实机验证。

## 运行方式

把本目录的 6 个文件（含隐藏目录 `.github`）放入你自己的 GitHub 仓库。
在 Actions 中手动运行 `Build ESP32 Agent iPad IPA`。
下载 `ESP32-Agent-iPad-unsigned` 构建产物，再使用 Windows 上已登录的 iLoader 签名并安装。
Apple ID、密码、验证码、证书、配对凭据、Wi-Fi 密码和开发板原始固件备份都不需要上传。

GitHub 标准运行器在公开仓库的计算免费；仅使用标准运行器，产物保留 1 天。
计费以 [GitHub 文档](https://docs.github.com/en/billing/concepts/product-billing/github-actions) 为准。

## 安装与验证边界

这是独立的 ESP32 Agent 测试应用，与现有 DSH Go 是两个应用。
本测试版通过本地签名安装，不依赖 TestFlight；自行构建不代表已完成 iPad 控制适配。
安装后仍要依次验证蓝牙连接、屏幕镜像、USB 指针和实际点击。
Wi-Fi 版 iPad 需要开发板与 iPad 接入同一路由器；仅连接开发板热点可能无法访问互联网。
现有固件支持路由器模式，已验证可通过 USB 配置并连接路由器。
模型服务需要在应用中自行配置，本构建不包含免费模型额度。

## 已验证结果（2026-11-09）

[首次云端构建](https://github.com/luke96778875-eng/esp32-agent-ipad-build/actions/runs/42608472729)已成功：

- 已生成 arm64 真机 IPA，明确包含 iPad 设备类型；主应用和扩展均为未加密 iOS 真机程序。
- iPad 模拟器测试：272 项，2 项跳过，0 项失败。
- 本地 SHA-256 和 ZIP 完整性检查通过。
- 已通过 iLoader 个人签名安装，系统确认签名配置有效；已确认应用能进入欢迎或连接开发板页面。
- 开发板已连接路由器；iPad 上的蓝牙连接、屏幕镜像及实际点击尚待实机验证。

原始未签名 IPA 的 SHA-256：
`6f60f21988a2c84ddd12ab0051da5b8c0d5fd57420a0927c4ba0736a043277fc`。

上游该提交的 iOS CI 已编译并运行测试，但有一项屏幕稳定检测测试失败：
`StillScreenTests.testSettledIgnoresThePointerButNotContent`，实际等待约 0.93 秒，断言要求超过 1.9 秒。
见 [上游测试记录](https://github.com/onehumanbeing/esp32-iphone-agent/actions/runs/42354473042)。
本构建保留该测试，本次 iPad 模拟器运行时该项通过；没有修改或隐藏上游测试。
