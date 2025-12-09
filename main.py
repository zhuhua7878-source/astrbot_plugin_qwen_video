import base64
import io
import random
import re
import asyncio
from pathlib import Path
from typing import List, Optional

import aiohttp
from PIL import Image as PILImage
import astrbot.core.message.components as Comp
from astrbot.api import logger
from astrbot.api.event import MessageChain, AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register
from astrbot.core.message.components import At, Image, Reply, Video

@register(
    "astrbot_plugin_qwen_video",
    "CCYellowStar2",
    "使用千问API生成视频。指令 文生视频 <提示词> 或 图生视频 <提示词> + 图片",
    "1.0.0"
)
class QwenVideoPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.api_key = config.get("api_key", "")
        self.api_url = config.get("api_url", "https://ai.gitee.com/v1/async/videos/generations")
        self.task_url = config.get("task_url", "https://ai.gitee.com/v1/task")
        self.model = config.get("model", "Wan2.1-T2V-1.3B")
        self.num_inference_steps = config.get("num_inference_steps", 50)
        self.num_frames = config.get("num_frames", 81)
        self.negative_prompt = config.get("negative_prompt", "")
        self.timeout = config.get("timeout", 1800)
        self.retry_interval = config.get("retry_interval", 10)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _ensure_session(self):
        """确保 session 已创建"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        
    async def terminate(self):
        """清理资源"""
        if self.session and not self.session.closed:
            await self.session.close()

    @filter.regex(r"^(文生视频)", priority=3)
    async def handle_text_to_video(self, event: AstrMessageEvent):
        """处理文生视频请求"""
        user_prompt = re.sub(
            r"^(文生视频)\s*", "", event.message_obj.message_str, count=1
        ).strip()

        if not self.api_key:
            yield event.plain_result("错误：请先在配置文件中设置api_key")
            return
        
        if not user_prompt:
            yield event.plain_result("请输入视频生成的提示词。用法: 文生视频 <提示词>")
            return

        yield event.plain_result("收到文生视频请求，生成中请稍候...")
        
        payload = {
            "prompt": user_prompt,
            "model": self.model,
            "num_inference_steps": self.num_inference_steps,
            "num_frames": self.num_frames,
        }
        
        if self.negative_prompt:
            payload["negative_prompt"] = self.negative_prompt
        
        await self._generate_and_send_video(event, payload)

    @filter.regex(r"^(图生视频)", priority=3)
    async def handle_image_to_video(self, event: AstrMessageEvent):
        """处理图生视频请求"""
        user_prompt = re.sub(
            r"^(图生视频)\s*", "", event.message_obj.message_str, count=1
        ).strip()
        
        if not self.api_key:
            yield event.plain_result("错误：请先在配置文件中设置api_key")
            return
            
        image_list = await self.get_images(event)
        if not image_list:
            yield event.plain_result("请提供一张图片来生成视频。用法: 图生视频 <提示词> + 图片")
            return

        if not user_prompt:
            user_prompt = "让画面动起来"
        
        yield event.plain_result(f"收到图生视频请求，共计 {len(image_list)} 张图片，生成中请稍候...")
        
        # 千问图生视频只支持单张图片，使用第一张
        base64_image = base64.b64encode(image_list[0]).decode("utf-8")
        
        payload = {
            "prompt": user_prompt,
            "model": self.model,
            "num_inference_steps": self.num_inference_steps,
            "num_frames": self.num_frames,
            "image": f"data:image/png;base64,{base64_image}"
        }
        
        if self.negative_prompt:
            payload["negative_prompt"] = self.negative_prompt
        
        await self._generate_and_send_video(event, payload)

    async def _generate_and_send_video(self, event: AstrMessageEvent, payload: dict):
        """生成并发送视频"""
        await self._ensure_session()
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            # 创建任务
            logger.info("正在创建视频生成任务...")
            async with self.session.post(self.api_url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    error_msg = f"API请求失败，状态码: {response.status}, 响应: {error_text}"
                    logger.error(error_msg)
                    await self.context.send_message(
                        event.unified_msg_origin, 
                        MessageChain().message(error_msg)
                    )
                    return
                
                data = await response.json()
                task_id = data.get("task_id")
                
                if not task_id:
                    error_msg = f"未能从API响应中获取task_id。响应内容: {data}"
                    logger.error(error_msg)
                    await self.context.send_message(
                        event.unified_msg_origin, 
                        MessageChain().message(error_msg)
                    )
                    return
                
                logger.info(f"任务创建成功，Task ID: {task_id}")
                await self.context.send_message(
                    event.unified_msg_origin, 
                    MessageChain().message(f"任务已创建 (ID: {task_id})，正在生成视频...")
                )
            
            # 轮询任务状态
            video_url = await self._poll_task(task_id, headers)
            
            if video_url:
                logger.info(f"成功获取视频链接: {video_url}，尝试发送...")
                await event.send(event.chain_result([Video.fromURL(url=video_url)]))
                logger.info("已成功向框架提交视频URL。")
            else:
                error_msg = "视频生成失败或超时"
                logger.error(error_msg)
                await self.context.send_message(
                    event.unified_msg_origin, 
                    MessageChain().message(error_msg)
                )

        except Exception as e:
            logger.error(f"视频生成过程中发生严重错误: {e}", exc_info=True)
            await self.context.send_message(
                event.unified_msg_origin, 
                MessageChain().message(f"生成失败: {str(e)}")
            )

    async def _poll_task(self, task_id: str, headers: dict) -> Optional[str]:
        """轮询任务状态直到完成或超时"""
        await self._ensure_session()
        
        status_url = f"{self.task_url}/{task_id}"
        max_attempts = int(self.timeout / self.retry_interval)
        attempts = 0
        
        while attempts < max_attempts:
            attempts += 1
            try:
                logger.info(f"检查任务状态 [{attempts}/{max_attempts}]...")
                
                async with self.session.get(status_url, headers=headers, timeout=10) as response:
                    if response.status != 200:
                        logger.warning(f"状态查询失败，状态码: {response.status}")
                        await asyncio.sleep(self.retry_interval)
                        continue
                    
                    result = await response.json()
                    
                    if result.get("error"):
                        error_msg = f"{result['error']}: {result.get('message', 'Unknown error')}"
                        logger.error(error_msg)
                        return None
                    
                    status = result.get("status", "unknown")
                    logger.info(f"任务状态: {status}")
                    
                    if status == "success":
                        if "output" in result and "file_url" in result["output"]:
                            file_url = result["output"]["file_url"]
                            duration = (result.get('completed_at', 0) - result.get('started_at', 0)) / 1000
                            logger.info(f"视频生成成功! 耗时: {duration:.2f}秒")
                            return file_url
                        else:
                            logger.error("任务成功但未找到视频URL")
                            return None
                    
                    elif status in ["failed", "cancelled"]:
                        logger.error(f"任务{status}")
                        return None
                    
                    # 任务仍在进行中
                    await asyncio.sleep(self.retry_interval)
                    
            except asyncio.TimeoutError:
                logger.warning("状态查询超时，重试...")
                await asyncio.sleep(self.retry_interval)
            except Exception as e:
                logger.error(f"轮询任务状态时发生错误: {e}")
                await asyncio.sleep(self.retry_interval)
        
        logger.error(f"达到最大重试次数 ({max_attempts})")
        return None

    async def get_images(self, event: AstrMessageEvent) -> List[bytes]:
        """从消息中提取图片"""
        images = []
        
        # 首先检查回复消息中的图片
        for s in event.message_obj.message:
            if isinstance(s, Comp.Reply) and s.chain:
                for seg in s.chain:
                    if isinstance(seg, Comp.Image):
                        if seg.url and (img := await self._load_bytes(seg.url)):
                            images.append(img)
                        elif seg.file and (img := await self._load_bytes(seg.file)):
                            images.append(img)
        
        if images:
            return images
        
        # 检查当前消息中的图片
        for seg in event.message_obj.message:
            if isinstance(seg, Comp.Image):
                if seg.url and (img := await self._load_bytes(seg.url)):
                    images.append(img)
                elif seg.file and (img := await self._load_bytes(seg.file)):
                    images.append(img)
        
        if images:
            return images
        
        # 检查 @ 的用户头像
        for seg in event.message_obj.message:
            if isinstance(seg, Comp.At):
                if avatar := await self._get_avatar(str(seg.qq)):
                    images.append(avatar)
        
        return images

    async def _download_image(self, url: str) -> Optional[bytes]:
        """下载图片"""
        await self._ensure_session()
        
        try:
            async with self.session.get(url) as resp:
                resp.raise_for_status()
                return await resp.read()
        except Exception as e:
            logger.error(f"图片下载失败: {e}")
            return None

    async def _get_avatar(self, user_id: str) -> Optional[bytes]:
        """获取用户头像"""
        await self._ensure_session()
        
        if not user_id.isdigit():
            user_id = "".join(random.choices("0123456789", k=9))
        
        avatar_url = f"https://q4.qlogo.cn/headimg_dl?dst_uin={user_id}&spec=640"
        
        try:
            async with self.session.get(avatar_url, timeout=10) as resp:
                resp.raise_for_status()
                return await resp.read()
        except Exception as e:
            logger.error(f"下载头像失败: {e}")
            return None

    def _extract_first_frame_sync(self, raw: bytes) -> bytes:
        """同步提取GIF第一帧"""
        img_io = io.BytesIO(raw)
        img = PILImage.open(img_io)
        
        if img.format != "GIF":
            return raw
        
        logger.info("检测到GIF，将抽取第一帧")
        first_frame = img.convert("RGBA")
        out_io = io.BytesIO()
        first_frame.save(out_io, format="PNG")
        return out_io.getvalue()

    async def _load_bytes(self, src: str) -> Optional[bytes]:
        """加载图片字节数据"""
        raw: Optional[bytes] = None
        loop = asyncio.get_running_loop()
        path = Path(src)
        
        if path.is_file():
            raw = await loop.run_in_executor(None, path.read_bytes)
        elif src.startswith("http"):
            raw = await self._download_image(src)
        elif src.startswith("base64://"):
            raw = await loop.run_in_executor(None, base64.b64decode, src[9:])
        
        if not raw:
            return None
        
        return await loop.run_in_executor(None, self._extract_first_frame_sync, raw)