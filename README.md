# astrbot_plugin_qwen_video

## ✨ 简介
一个[Astrbot](https://github.com/Soulter/AstrBot)插件，接入千问(通义千问)图生视频API，实现图生视频功能。

## 📦安装
通过astrbot自带插件商店搜索`astrbot_plugin_qwen_video`一键安装。

## ⚙配置

请在Astrbot的控制面板配置。

插件管理 -> astrbot_plugin_qwen_video -> 操作 -> 插件配置

| 配置项 | 说明 | 默认值 |
| :-------- | :------------------- | :------------------------------------------- |
| `api_key` | 千问API服务提供的密钥 | 无 |
| `task_url` | 任务查询地址 | `https://ai.gitee.com/v1/task` |
| `model` | 视频生成模型名称 | `Wan2.1-I2V-14B-720P` |
| `num_inference_steps` | 推理步数(控制生成质量) | `50` |
| `num_frames` | 视频帧数(81帧约3-4秒) | `81` |
| `aspect_ratio` | 视频宽高比(16:9/9:16/1:1) | `16:9` |
| `orientation` | 视频方向(landscape/portrait/square) | `landscape` |

## ⌨️使用方法
**图生视频**：`图生视频 <提示词> + 图片`
> 根据你提供的图片和文字描述生成视频。注意：千问目前仅支持单张图片。

## 📌示例

### 图生视频
> **你:**
> 图生视频 让画面动起来
> `[此处附上一张图片]`
>
> **Bot:**
> `[此处会发送生成的视频]`

## 📝说明

- 视频生成采用异步任务模式，创建任务后会自动轮询状态
- 生成时间取决于服务器负载，通常需要几分钟
- 仅支持单张图片作为输入
- 可通过调整 `num_inference_steps` 和 `num_frames` 控制视频质量和时长
- 支持多种宽高比和方向配置

## 更新日志

`V1.0` 插件首次发布，支持千问图生视频API。

# 支持

[帮助文档](https://astrbot.app)
