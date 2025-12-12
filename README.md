# astrbot_plugin_qwen_video

## ✨ 简介

一个[Astrbot](https://github.com/Soulter/AstrBot)插件，接入千问(通义千问)图生视频API，实现**图生视频**功能。基于官方 API 文档开发，使用标准 multipart/form-data 请求格式。

## 🎯 功能特性

- ✅ 支持图生视频生成
- ✅ 可配置的 API 端点和参数
- ✅ 完善的错误处理和日志记录
- ✅ 支持多种宽高比和视频方向
- ✅ 异步任务轮询，自动获取结果
- ✅ 网络问题自动重试

## 📦 安装

通过 AstrBot 自带插件商店搜索 `astrbot_plugin_qwen_video` 一键安装。

## ⚙️ 配置

请在 AstrBot 的控制面板配置。

**路径**: 插件管理 → astrbot_plugin_qwen_video → 操作 → 插件配置

### 配置参数

| 配置项 | 类型 | 说明 | 默认值 |
| :-------- | :---- | :------------------- | :------------------------------------------- |
| `api_key` | string | **[必填]** 千问API服务提供的密钥 | 无 |
| `image_to_video_url` | string | 图生视频API地址（可自定义） | `https://ai.gitee.com/v1/async/videos/image-to-video` |
| `task_url` | string | 任务查询地址 | `https://ai.gitee.com/v1/task` |
| `model` | string | 视频生成模型名称 | `Wan2.1-I2V-14B-720P` |
| `num_inference_steps` | int | 推理步数（30-50建议，越高质量越好） | `50` |
| `num_frames` | int | 视频帧数（81帧约3-4秒） | `81` |
| `aspect_ratio` | string | 视频宽高比（16:9/9:16/1:1） | `16:9` |
| `orientation` | string | 视频方向（landscape/portrait/square） | `landscape` |

### 参数说明

**aspect_ratio（宽高比）**:
- `16:9` - 标准横屏（推荐）
- `9:16` - 手机竖屏
- `1:1` - 社交媒体方形

**orientation（方向）**:
- `landscape` - 横屏
- `portrait` - 竖屏
- `square` - 方形

## ⌨️ 使用方法

### 图生视频指令

```
图生视频 <提示词> + 图片
```

根据你提供的图片和文字描述生成视频。

**注意**:
- 需要上传或回复一张图片
- 千问目前仅支持单张图片
- 图片格式支持：PNG, JPG, GIF
- 提示词为可选，默认为"让画面动起来"

## 📌 使用示例

### 例子 1：基础使用

```
你: 图生视频 让画面更生动
[上传一张图片]

Bot: [处理中...]
[发送生成的视频]
```

### 例子 2：详细提示词

```
你: 图生视频 让这个场景变成电影级别的动画效果
[上传风景照片]

Bot: [处理中...]
[发送高质量视频]
```

## 📝 工作原理

1. **接收请求**: 用户输入指令 `图生视频 <提示词> + 图片`
2. **提取图片**: 从消息中提取上传的图片
3. **构建请求**: 以 multipart/form-data 格式构建 API 请求
4. **调用 API**: 发送请求到千问图生视频 API
5. **获取任务ID**: API 返回异步任务 ID
6. **轮询状态**: 每 10 秒查询一次任务状态（最多 30 分钟）
7. **返回结果**: 任务完成后获取视频链接并发送给用户

## 🔧 故障排查

### 问题 1: 插件加载失败

**错误信息**: `TypeError: 不受支持的配置类型`

**解决**: 确保使用最新版本的 `_conf_schema.json`

### 问题 2: API 400 错误

**错误信息**: `API请求失败，状态码: 400`

**原因**:
- API 地址不正确
- API Key 没有图生视频权限

**解决**:
1. 在配置面板检查 `image_to_video_url` 是否正确
2. 确认 API Key 有图生视频权限

### 问题 3: JSON 解析失败

**错误信息**: `生成失败: Expecting value: line 1 column 1`

**原因**: API 返回了无效的 JSON 或空响应

**解决**:
1. 查看 AstrBot 日志中的 "API 响应内容"
2. 检查 API Key 和 API 地址
3. 确保网络连接正常

### 问题 4: 任务超时

**错误信息**: `视频生成失败或超时`

**原因**:
- API 服务过载
- 网络连接问题
- 参数设置过高

**解决**:
- 减少 `num_inference_steps` 到 30
- 减少 `num_frames` 到 50
- 稍后重试

### 问题 5: 图片识别失败

**错误信息**: `请提供一张图片来生成视频`

**解决**:
1. 确保上传了图片
2. 尝试其他图片格式（PNG, JPG）
3. 确保图片大小合理

## 📚 高级配置

### 自定义 API 地址

如果千问提供了其他 API 地址，可以在配置面板修改 `image_to_video_url`：

```
image_to_video_url: https://你的api地址
```

保存后重启 AstrBot 即可生效。

### 调整视频质量

- **高质量**: `num_inference_steps: 50`, `num_frames: 144`（耗时长）
- **平衡**: `num_inference_steps: 50`, `num_frames: 81`（推荐）
- **快速**: `num_inference_steps: 30`, `num_frames: 50`（质量较低）

## 🔐 API 说明

### 请求信息

- **端点**: `https://ai.gitee.com/v1/async/videos/image-to-video`
- **方法**: `POST`
- **格式**: `multipart/form-data`
- **认证**: Bearer Token (Authorization header)

### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| prompt | string | ✅ | 视频描述提示词 |
| model | string | ✅ | 模型名称 |
| num_inferenece_steps | int | ✅ | 推理步数 |
| num_frames | int | ✅ | 视频帧数 |
| image | file | ✅ | 输入图片（二进制） |
| aspect_ratio | string | ❌ | 宽高比 |
| orientation | string | ❌ | 方向 |

## 📝 更新日志

### V1.0.1 (最新)
- ✅ 增强了错误处理机制
- ✅ 添加了详细的日志记录
- ✅ 支持可配置的 API 地址
- ✅ 改进了 JSON 解析的容错能力
- ✅ 网络问题时自动重试

### V1.0.0
- ✅ 插件首次发布
- ✅ 支持千问图生视频 API
- ✅ 支持多种宽高比和方向配置

## 💡 Tips

- 提示词越详细，生成的视频质量越好
- 推理步数越高越好，但耗时更长
- 如果生成超时，可以减少参数重试
- 查看日志可以了解详细的处理过程

## 🤝 支持

遇到问题？

1. 查看本 README 的"故障排查"部分
2. 查看 AstrBot 日志了解详细错误信息
3. 确认 API Key 和网络连接正常

## 📖 相关链接

- [AstrBot 项目](https://github.com/Soulter/AstrBot)
- [AstrBot 文档](https://astrbot.app)
- [千问 API 文档](https://ai.gitee.com)
