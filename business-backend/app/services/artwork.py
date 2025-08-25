from typing import List, Optional, Dict, Any, Tuple, Union
from datetime import datetime
import logging
import asyncio
import base64
import io
import random
from fastapi import HTTPException
import json
import httpx
import os
from PIL import Image, ImageDraw, ImageFont
import re

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, asc, or_, and_
import httpx

from app.models.artwork import Artwork, ArtworkStatus
from app.models.user import User
from app.models.style import Style
from app.schemas.artwork import ArtworkCreate, ArtworkUpdate, ArtworkListParams, PublishArtworkRequest
from app.services.file_storage import FileStorageService
from app.services.credit import CreditService
from app.services.cos_service import cos_service  # 导入COS服务单例
from app.core.config import settings
from app.db.utils import get_base_query, soft_delete

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ArtworkService:
    @staticmethod
    async def create(
        db: Session, 
        user_id: int, 
        style_id: int, 
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        创建新作品
        """
        # 检查用户和风格
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, {"error": "用户不存在"}
        
        style = db.query(Style).filter(Style.id == style_id).first()
        if not style:
            return False, {"error": "风格不存在"}
        
        if not style.is_active:
            return False, {"error": "该风格已禁用"}
        
        # 检查用户积分
        credits_cost = style.credits_cost
        if user.credits < credits_cost:
            return False, {"error": "积分不足"}
        
        # 获取原始图片宽高比
        aspect_ratio = None
        if image_base64:
            try:
                if "," in image_base64:
                    image_base64 = image_base64.split(",")[1]     
                image_bytes = base64.b64decode(image_base64)
                img = Image.open(io.BytesIO(image_bytes))
                aspect_ratio = f"{img.width}:{img.height}"
            except Exception as e:
                logger.error(f"解析image_base64获取宽高比失败: {e}")
        elif image_url:
            try:
                async with httpx.AsyncClient() as client:
                    presigned_source_url = cos_service.generate_presigned_url(image_url, expires=600)
                    response = await client.get(presigned_source_url, timeout=60.0)
                    response.raise_for_status()
                    image_bytes = await response.aread()
                    img = Image.open(io.BytesIO(image_bytes))
                    aspect_ratio = f"{img.width}:{img.height}"
            except Exception as e:
                logger.error(f"下载image_url获取宽高比失败: {e}")
        
        # 设置来源图片URL
        source_image_url = image_url
        
        # 如果提供了base64图片数据，则上传原图
        if image_base64:
            success, result = await FileStorageService.upload_base64_image(
                image_base64, 
                folder="source_images"
            )
            
            if not success:
                return False, {"error": f"上传图片失败: {result}"}
            
            source_image_url = result
        
        # 如果没有source_image_url，则返回错误
        if not source_image_url:
            return False, {"error": "必须提供有效的图片来源（base64或URL）"}
        
        try:
            # 创建作品记录
            db_artwork = Artwork(
                user_id=user_id,
                style_id=style_id,
                source_image_url=source_image_url,
                status=ArtworkStatus.PROCESSING.value,
                is_public=False
            )
            db.add(db_artwork)
            db.flush()  # 获取ID但不提交
            
            # 扣除积分
            success, credit_result = CreditService.update_credits(
                db=db,
                user_id=user_id,
                amount=-credits_cost,
                type="create",
                description=f"创建作品《{style.name}》风格",
                related_id=db_artwork.id
            )
            
            if not success:
                # 回滚并返回错误
                db.rollback()
                # 如果上传了新图片，则删除
                if image_base64:
                    await FileStorageService.delete_file(source_image_url)
                return False, {"error": credit_result["error"]}
            
            # 提交事务
            db.commit()
            db.refresh(db_artwork)
            
            # 异步处理图片风格转换
            asyncio.create_task(
                ArtworkService.process_artwork_style(db_artwork.id, aspect_ratio)
            )
            
            return True, {"artwork": db_artwork}
            
        except Exception as e:
            db.rollback()
            # 如果上传了新图片，则删除
            if image_base64:
                await FileStorageService.delete_file(source_image_url)
            logger.error(f"创建作品时发生错误: {str(e)}")
            return False, {"error": f"创建作品失败: {str(e)}"}
    
    @staticmethod
    async def process_artwork_style(artwork_id: int, aspect_ratio: Optional[str] = None):
        """
        处理作品的风格转换（异步）
        """
        # 创建独立的数据库会话
        from app.db.session import SessionLocal
        db = SessionLocal()
        
        try:
            artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
            if not artwork or artwork.status != ArtworkStatus.PROCESSING.value:
                return
            
            style = db.query(Style).filter(Style.id == artwork.style_id).first()
            if not style:
                # 更新作品状态为失败
                artwork.status = ArtworkStatus.FAILED.value
                artwork.error_message = "找不到对应的风格"
                db.commit()
                return
            
            # 获取原图URL和风格参考图URL
            source_image_url = artwork.source_image_url
            style_reference_image_url = getattr(style, 'reference_image_url', None)
            
            # 为这些URL生成预签名URL（有效期10分钟）
            presigned_source_url = cos_service.generate_presigned_url(source_image_url, expires=600)
            presigned_reference_url = None
            if style_reference_image_url:
                presigned_reference_url = cos_service.generate_presigned_url(style_reference_image_url, expires=600)
            
            logger.info(f"Artwork {artwork_id}: 原始URL: {source_image_url}")
            logger.info(f"Artwork {artwork_id}: 预签名URL: {presigned_source_url}")
            
            if style_reference_image_url:
                logger.info(f"Artwork {artwork_id}: 参考图原始URL: {style_reference_image_url}")
                logger.info(f"Artwork {artwork_id}: 参考图预签名URL: {presigned_reference_url}")
            
            # 调用生成函数，使用预签名URL
            success, final_message = await ArtworkService._generate_styled_image_with_progress(
                db=db,
                artwork_id=artwork_id,
                source_image_url=presigned_source_url,  # 使用预签名URL
                style_name=style.name,
                style_description=style.prompt,
                style_reference_image_url=presigned_reference_url,  # 使用预签名参考图URL
                aspect_ratio=aspect_ratio  # 传递宽高比
            )
            
            if success:
                # 更新作品信息
                artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
                if artwork:
                    artwork.result_image_url = final_message
                    artwork.status = ArtworkStatus.COMPLETED.value
                    db.commit()
            else:
                # 处理失败，不再需要在这里退还积分，handle_failure 已经处理
                artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
                if not artwork:
                    return
                
                # 更新作品状态为失败 (状态已由 handle_failure 设置，这里可以保留以防万一)
                artwork.status = ArtworkStatus.FAILED.value
                artwork.error_message = final_message  # 错误信息
                db.commit()
        
        except Exception as e:
            logger.error(f"处理作品风格时发生错误: {str(e)}")
            try:
                # 尝试更新作品状态为失败
                artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
                if artwork and artwork.status == ArtworkStatus.PROCESSING.value:
                    artwork.status = ArtworkStatus.FAILED.value
                    artwork.error_message = f"处理过程中发生错误: {str(e)}"
                    
                    # 退还积分
                    user = db.query(User).filter(User.id == artwork.user_id).first()
                    style = db.query(Style).filter(Style.id == artwork.style_id).first()
                    if user and style:
                        credits_cost = style.credits_cost
                        try:
                            CreditService.update_credits(
                                db=db,
                                user_id=user.id,
                                amount=credits_cost,  # 退还积分
                                type="other",
                                description=f"作品ID {artwork.id} 风格转换失败退还积分",
                                related_id=artwork.id
                            )
                            logger.info(f"Refunded {credits_cost} credits to user {user.id} for failed artwork {artwork_id}")
                        except Exception as refund_e:
                             logger.error(f"Failed to refund credits for artwork {artwork_id}: {refund_e}")
                             # Don't overwrite original error message if refund fails
                             if not artwork.error_message:
                                 artwork.error_message = f"{final_message} (积分退还失败: {refund_e})"


                try:
                    db.commit()
                except Exception as commit_e:
                     logger.error(f"Error committing failure status for artwork {artwork_id}: {commit_e}")
                     db.rollback() # Rollback on commit error

            except Exception as inner_e:
                logger.error(f"更新失败状态时发生错误: {str(inner_e)}")
        finally:
            db.close()
    
    @staticmethod
    async def _generate_styled_image_with_progress(
        db: Session,
        artwork_id: int,
        source_image_url: str,
        style_name: str,
        style_description: Optional[str] = None,
        style_reference_image_url: Optional[str] = None,
        aspect_ratio: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        调用AI服务生成风格化图片，使用健壮的SSE流处理逻辑，并实时更新进度。
        """
        artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
        if not artwork:
            logger.error(f"Artwork ID {artwork_id} not found for progress update.")
            return False, "作品记录未找到"

        # --- Helper function for failure handling ---
        async def handle_failure(error_message: str, should_refund: bool = True):
            logger.error(f"Artwork {artwork_id} failed: {error_message}")
            artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first() # Re-fetch in case session changed
            if artwork and artwork.status == ArtworkStatus.PROCESSING.value:
                artwork.status = ArtworkStatus.FAILED.value
                artwork.error_message = error_message

                if should_refund:
                    user = db.query(User).filter(User.id == artwork.user_id).first()
                    style = db.query(Style).filter(Style.id == artwork.style_id).first()
                    if user and style:
                        credits_cost = style.credits_cost
                        try:
                            CreditService.update_credits(
                                db=db,
                                user_id=user.id,
                                amount=credits_cost,  # 退还积分
                                type="refund",
                                description=f"作品ID {artwork_id} 风格转换失败退还积分",
                                related_id=artwork.id
                            )
                            logger.info(f"Refunded {credits_cost} credits to user {user.id} for failed artwork {artwork_id}")
                        except Exception as refund_e:
                             logger.error(f"Failed to refund credits for artwork {artwork_id}: {refund_e}")
                             # Don't overwrite original error message if refund fails
                             if not artwork.error_message:
                                 artwork.error_message = f"{error_message} (积分退还失败: {refund_e})"


                try:
                    db.commit()
                except Exception as commit_e:
                     logger.error(f"Error committing failure status for artwork {artwork_id}: {commit_e}")
                     db.rollback() # Rollback on commit error

            return False, error_message

        # --- Regex patterns and Keywords (from hehe.py) ---
        progress_percent_pattern = re.compile(r"进度：\s*(\d{1,3}(?:\.\d+)?)\s*%")
        url_pattern = re.compile(r"(?:点击)?下载\s*(https?://\S+?)\s*|!\[.*?\]\((https?://\S+?)\)")
        failure_pattern = re.compile(r">\s*生成失败\s*❌\s*(?:\n?>\s*失败原因：\s*(.*))?", re.MULTILINE)
        json_block_pattern = re.compile(r"```json\n.*?\n```", re.DOTALL)

        progress_keywords = ["进度", "🏃‍"]
        generating_keywords = ["生成中", "⚡", "绘制中"]
        queued_keywords = ["排队中", "🕐", "队列中"]
        completion_keywords = ["生成完成", "✅", "绘制成功"]
        error_keywords = ["错误", "异常", "failed", "error", "unable", "cannot", "失败"]

        # --- State variables ---
        full_response_content = ""
        last_reported_progress = artwork.progress or 0 # Initialize with current progress
        url_yielded = False
        error_yielded = False
        stream_done = False
        potential_error_fragments = []
        final_image_url = None
        final_result_url_internal = None # For internal storage URL

        try:
            # 准备API请求
            api_url = f"{settings.OPENAI_API_URL}/chat/completions"
            prompt = style_description
            # 如果存在宽高比，则在提示词末尾添加比例信息
            if aspect_ratio:
                prompt = f"{prompt} .保持图片比例为{aspect_ratio}"
            logger.info(f"Artwork {artwork_id}: Generating image with prompt: '{prompt}' and source URL: {source_image_url}")

            # 构建基础 content 列表
            content_list = [
                {"type": "text", "text": prompt},
                # 占位符，稍后添加 source_image
            ]

            # 如果有参考图，将其添加到列表（在文本之后，源图之前）
            if style_reference_image_url:
                logger.info(f"Artwork {artwork_id}: Using reference image URL: {style_reference_image_url}")
                content_list.insert(1, {"type": "image_url", "image_url": {"url": style_reference_image_url}})

            # 最后添加源图
            content_list.append({"type": "image_url", "image_url": {"url": source_image_url}})


            payload = {
                "model": settings.OPENAI_IMAGE_MODEL, # Use model from settings
                "messages": [
                    # {"role": "system", "content": "你是一个有用的助手，擅长图像风格转换。"}, # Optional system prompt
                    {
                        "role": "user",
                        "content": content_list # 使用构建好的列表
                    }
                ],
                "stream": True
            }

            print("载荷", json.dumps(payload, indent=4, ensure_ascii=False))
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream" # Ensure correct Accept header
            }

            # 使用 get_float 获取配置，并提供默认值
            async with httpx.AsyncClient(timeout=settings.get_float("OPENAI_TIMEOUT", 600.0)) as client:
                async with client.stream("POST", api_url, json=payload, headers=headers) as response:
                    logger.info(f"Artwork {artwork_id}: Connection established (Status: {response.status_code})")
                    if response.status_code != 200:
                        error_body = await response.aread()
                        error_msg = f"AI服务API请求失败: HTTP {response.status_code} - {error_body.decode('utf-8', errors='ignore')}"
                        return await handle_failure(error_msg)

                    async for line in response.aiter_lines():
                        if error_yielded: continue # Stop processing if a definitive error occurred

                        if line:
                            decoded_line = line # httpx handles decoding by default
                            # logger.debug(f"Artwork {artwork_id} Raw line: {decoded_line}") # Very verbose debug

                            if decoded_line.startswith('data: '):
                                json_str = decoded_line[len('data: '):].strip()

                                if json_str == '[DONE]':
                                    logger.info(f"Artwork {artwork_id}: Stream finished ([DONE] received).")
                                    logger.info(f"Artwork {artwork_id}: decoded_line content: {decoded_line}")
                                    stream_done = True
                                    break

                                try:
                                    chunk = json.loads(json_str)
                                    delta = chunk.get('choices', [{}])[0].get('delta', {})
                                    content = delta.get('content')

                                    if content:
                                        full_response_content += content
                                        # logger.debug(f"Artwork {artwork_id} Accumulated: '{full_response_content}'")

                                        # --- Create a version of content excluding JSON blocks for status checks ---
                                        content_for_status_check = json_block_pattern.sub("", full_response_content)

                                        # --- Check for Specific Failure Pattern (Highest Priority) ---
                                        if not error_yielded:
                                            failure_match = failure_pattern.search(full_response_content)
                                            if failure_match:
                                                reason = failure_match.group(1)
                                                error_message = "生成失败 ❌"
                                                if reason:
                                                    error_message += f" 原因：{reason.strip()}"
                                                logger.warning(f"Artwork {artwork_id}: Specific failure detected: {error_message}")
                                                _, final_msg = await handle_failure(error_message) # Set state to failed
                                                error_yielded = True
                                                last_reported_progress = "生成失败" # Update display state
                                                continue # Move to next chunk

                                        # --- Check Progress (if not failed) ---
                                        if not error_yielded:
                                            current_progress_value = None
                                            progress_type = None
                                            progress_message = None

                                            # Check Percentage
                                            if any(kw in content_for_status_check for kw in progress_keywords):
                                                matches = list(progress_percent_pattern.finditer(content_for_status_check))
                                                if matches:
                                                    try:
                                                        latest_percentage_float = float(matches[-1].group(1))
                                                        current_progress_value = min(int(latest_percentage_float), 100)
                                                        progress_type = 'percentage'
                                                    except (ValueError, IndexError): pass

                                            # Check Generating
                                            if current_progress_value is None and any(kw in content_for_status_check for kw in generating_keywords):
                                                progress_message = '生成中...'
                                                progress_type = 'message'

                                            # Check Queued
                                            if current_progress_value is None and any(kw in content_for_status_check for kw in queued_keywords):
                                                progress_message = '排队中...'
                                                progress_type = 'message'

                                            # Check Completion
                                            if any(kw in content_for_status_check for kw in completion_keywords):
                                                if last_reported_progress != '生成完成':
                                                    progress_message = '生成完成'
                                                    progress_type = 'message'
                                                if last_reported_progress != 100: # Also ensure 100%
                                                     # Yield 100% progress immediately
                                                     artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
                                                     if artwork and artwork.status == ArtworkStatus.PROCESSING.value:
                                                         artwork.progress = 100
                                                         try:
                                                             db.commit()
                                                             logger.info(f"Artwork {artwork_id}: Progress updated to 100% (Completion Keyword)")
                                                             last_reported_progress = 100
                                                         except Exception as commit_e:
                                                             logger.error(f"Artwork {artwork_id}: Error committing 100% progress: {commit_e}")
                                                             db.rollback()


                                            # Update DB if progress changed
                                            progress_to_report = None
                                            if progress_type == 'percentage' and current_progress_value is not None and current_progress_value != last_reported_progress:
                                                 progress_to_report = current_progress_value
                                            elif progress_type == 'message' and progress_message is not None and progress_message != last_reported_progress:
                                                 # For message-based progress, we still store a percentage if possible,
                                                 # but use the message for comparison. We don't store the message itself.
                                                 if progress_message == '生成完成':
                                                     progress_to_report = 100 # Completion implies 100%
                                                 # elif progress_message == '生成中...': # Assign intermediate percentages if needed
                                                 #     progress_to_report = 50 # Example
                                                 # elif progress_message == '排队中...':
                                                 #     progress_to_report = 10 # Example
                                                 else:
                                                      # If it's just a message like "Generating...", try to keep the last numeric progress
                                                      if isinstance(last_reported_progress, int):
                                                          pass # Keep last numeric progress
                                                      else: # Or set a default if none exists
                                                          progress_to_report = artwork.progress if artwork.progress else 1 # Minimal progress


                                            if progress_to_report is not None and progress_to_report > (artwork.progress or 0):
                                                artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
                                                if artwork and artwork.status == ArtworkStatus.PROCESSING.value:
                                                    artwork.progress = progress_to_report
                                                    try:
                                                        db.commit()
                                                        logger.info(f"Artwork {artwork_id}: Progress updated to {progress_to_report}%")
                                                        last_reported_progress = progress_to_report if progress_type == 'percentage' else progress_message
                                                    except Exception as commit_e:
                                                        logger.error(f"Artwork {artwork_id}: Error committing progress {progress_to_report}%: {commit_e}")
                                                        db.rollback()


                                        # --- Check for Result URL (if not failed and not found yet) ---
                                        if not url_yielded and not error_yielded:
                                            url_match = url_pattern.search(full_response_content)
                                            if url_match:
                                                potential_url = url_match.group(1) or url_match.group(2)
                                                if potential_url:
                                                    logger.info(f"Artwork {artwork_id}: Result URL found: {potential_url}")
                                                    final_image_url = potential_url # Store the found URL
                                                    url_yielded = True
                                                    # Ensure 100% progress is shown when URL appears
                                                    if last_reported_progress != 100 and last_reported_progress != '生成完成':
                                                         artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
                                                         if artwork and artwork.status == ArtworkStatus.PROCESSING.value and artwork.progress < 100:
                                                             artwork.progress = 100
                                                             try:
                                                                 db.commit()
                                                                 logger.info(f"Artwork {artwork_id}: Progress set to 100% (URL found)")
                                                                 last_reported_progress = 100
                                                             except Exception as commit_e:
                                                                 logger.error(f"Artwork {artwork_id}: Error committing 100% progress (URL found): {commit_e}")
                                                                 db.rollback()


                                        # --- Basic Error Keyword Check (Fallback) ---
                                        if not error_yielded and not url_yielded: # Only check if no definite outcome yet
                                            content_lower = content.lower()
                                            # Check keywords AND avoid checking inside potential JSON fragments
                                            if not content.strip().startswith(("{",'"')) and not content.strip().endswith(("}",'"')) and any(keyword in content_lower for keyword in error_keywords):
                                                 # Avoid flagging progress/completion/URL markdown
                                                 if not content.startswith(('>', '✅', '[', '![', '🏃‍', '🕐', '⚡')) and len(content) < 150: # Increased length limit slightly
                                                    logger.warning(f"Artwork {artwork_id}: Potential fallback error text detected: {content.strip()}")
                                                    potential_error_fragments.append(content.strip())


                                except json.JSONDecodeError:
                                    if not error_yielded:
                                        logger.warning(f"Artwork {artwork_id}: Could not decode JSON: {json_str}")
                                        _, final_msg = await handle_failure('Stream decode error: Invalid JSON received.')
                                        error_yielded = True
                                except Exception as e:
                                     if not error_yielded:
                                        logger.error(f"Artwork {artwork_id}: Error processing chunk content: {e}", exc_info=True)
                                        _, final_msg = await handle_failure(f'处理流数据块时出错: {e}')
                                        error_yielded = True

            # --- Final Check after stream ends ---
            logger.info(f"Artwork {artwork_id}: Performing final check. Stream Done: {stream_done}, Error Yielded: {error_yielded}, URL Yielded: {url_yielded}")

            # Refresh artwork state before final checks
            artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
            if not artwork:
                return False, "作品记录在最终检查时丢失" # Should not happen normally

            # If already failed, return the stored message
            if artwork.status == ArtworkStatus.FAILED.value:
                logger.info(f"Artwork {artwork_id}: Final check confirms failure state.")
                return False, artwork.error_message or "处理失败"

            # Check URL one last time if not already found (search full content)
            if not url_yielded and not error_yielded:
                url_match = url_pattern.search(full_response_content)
                if url_match:
                    potential_url = url_match.group(1) or url_match.group(2)
                    if potential_url:
                        logger.info(f"Artwork {artwork_id}: Result URL found in final check: {potential_url}")
                        final_image_url = potential_url
                        url_yielded = True


            # --- Process Final State ---
            if url_yielded and final_image_url:
                logger.info(f"Artwork {artwork_id}: Proceeding with final image URL: {final_image_url}")

                # Download the generated image with retries
                download_success = False
                download_error = ""
                image_base64 = None
                max_retries = 3 # Reduced retries for faster failure
                retry_delay = 2 # Base delay

                for attempt in range(max_retries):
                    try:
                        async with httpx.AsyncClient() as img_client:
                            img_response = await img_client.get(final_image_url, timeout=60.0) # Increased download timeout
                            img_response.raise_for_status() # Raise HTTP errors
                            image_bytes = await img_response.aread()
                            # Optional: Verify image data (e.g., using Pillow)
                            try:
                                Image.open(io.BytesIO(image_bytes)).verify()
                                # 添加水印 (在上传到COS之前)
                                # image_base64 = await ArtworkService.add_watermark_to_image(image_bytes)
                                # 暂时禁用水印功能，直接使用原始图片
                                image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                                download_success = True
                                logger.info(f"Artwork {artwork_id}: Image downloaded successfully from {final_image_url}")
                                break # Exit retry loop on success
                            except Exception as img_verify_e:
                                download_error = f"下载的文件无效或不是图片: {img_verify_e}"
                                logger.error(f"Artwork {artwork_id}: {download_error}")
                                break # Don't retry if file is invalid

                    except httpx.HTTPStatusError as e:
                        download_error = f"下载图片时HTTP错误: {e.response.status_code}"
                        logger.warning(f"Artwork {artwork_id}: Attempt {attempt + 1}/{max_retries} failed: {download_error}")
                    except httpx.TimeoutException:
                        download_error = "下载图片超时"
                        logger.warning(f"Artwork {artwork_id}: Attempt {attempt + 1}/{max_retries} failed: {download_error}")
                    except Exception as e:
                        download_error = f"下载图片时发生未知错误: {e}"
                        logger.warning(f"Artwork {artwork_id}: Attempt {attempt + 1}/{max_retries} failed: {download_error}", exc_info=True)

                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt) # Exponential backoff
                        logger.info(f"Artwork {artwork_id}: Waiting {wait_time}s before next download attempt.")
                        await asyncio.sleep(wait_time)

                if not download_success or not image_base64:
                    err_msg = f"无法下载或验证最终图片 (已重试 {max_retries} 次): {download_error}"
                    return await handle_failure(err_msg)

                # 上传到内部存储
                upload_success, cos_result = await FileStorageService.upload_base64_image(
                    image_base64,
                    folder="result_images" # Ensure this folder exists or is handled
                )

                if upload_success:
                    final_result_url_internal = cos_result
                    logger.info(f"Artwork {artwork_id}: Result image uploaded to: {final_result_url_internal}")
                    # Final success update
                    artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
                    if artwork:
                         artwork.result_image_url = final_result_url_internal
                         artwork.status = ArtworkStatus.COMPLETED.value
                         artwork.progress = 100 # Ensure progress is 100
                         artwork.error_message = None # Clear any previous transient errors
                         try:
                            db.commit()
                            logger.info(f"Artwork {artwork_id}: Status set to COMPLETED.")
                            return True, final_result_url_internal
                         except Exception as commit_e:
                              logger.error(f"Artwork {artwork_id}: Error committing completion status: {commit_e}")
                              db.rollback()
                              # Even if commit fails, the image is generated and uploaded,
                              # but the status is inconsistent. Treat as failure for now.
                              return await handle_failure(f"完成状态提交失败: {commit_e}", should_refund=False) # Don't refund if image was generated

                    else:
                        # Should not happen if initial check passed
                         logger.error(f"Artwork {artwork_id}: Record disappeared before final update.")
                         return await handle_failure("作品记录在最终更新前丢失", should_refund=False)

                else:
                    err_msg = f"上传结果图片失败: {cos_result}"
                    return await handle_failure(err_msg, should_refund=False) # Don't refund if image generated but upload failed

            # --- Handle cases where no URL was found and no specific error occurred ---
            elif not error_yielded:
                logger.warning(f"Artwork {artwork_id}: Stream finished, but no result URL found and no specific failure message.")
                error_message = '处理完成，但结果不明确（未找到URL，无特定错误）。'
                if potential_error_fragments:
                     # Use set to remove duplicates and join
                     unique_fragments = "; ".join(list(set(potential_error_fragments)))
                     error_message = f"检测到潜在问题: {unique_fragments}"
                     logger.warning(f"Artwork {artwork_id}: Reporting potential fallback errors: {error_message}")

                return await handle_failure(error_message)

            # If we reach here, it means error_yielded was true, and handle_failure was already called.
            # We return the result from the initial handle_failure call.
            # The artwork status should already be FAILED in the DB.
            artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first() # Fetch final state
            final_msg = artwork.error_message if artwork else "处理失败，状态未知"
            logger.info(f"Artwork {artwork_id}: Process finished in error state: {final_msg}")
            return False, final_msg


        except httpx.TimeoutException:
            return await handle_failure("API 请求超时")
        except httpx.RequestError as e:
            # Network errors, DNS errors etc.
             return await handle_failure(f"API 请求失败: {e}")
        except Exception as e:
            # Catch any other unexpected errors during the process
            logger.error(f"Artwork {artwork_id}: An unexpected error occurred in _generate_styled_image_with_progress: {e}", exc_info=True)
            import traceback
            tb_str = traceback.format_exc()
            return await handle_failure(f"处理过程中发生意外错误: {e}\n{tb_str[:500]}...") # Limit traceback length

    @staticmethod
    def get_by_id(db: Session, artwork_id: int) -> Optional[Artwork]:
        """
        根据ID获取作品
        """
        return get_base_query(db, Artwork).options(joinedload(Artwork.style)).filter(Artwork.id == artwork_id).first()
    
    @staticmethod
    def get_all(db: Session, params: ArtworkListParams):
        """
        获取所有作品，带分页和过滤
        """
        query = get_base_query(db, Artwork).options(joinedload(Artwork.style))
        
        # 直接访问属性而不是使用.get()
        if params.status:
            query = query.filter(Artwork.status == params.status)
        
        if params.is_public is not None:
            query = query.filter(Artwork.is_public == params.is_public)
        
        if params.user_id:
            query = query.filter(Artwork.user_id == params.user_id)
        
        if params.style_id:
            query = query.filter(Artwork.style_id == params.style_id)
        
        # 排序
        if params.order_by:
            column = getattr(Artwork, params.order_by)
            if params.order_desc:
                column = column.desc()
            query = query.order_by(column)
        
        # 分页
        return query.offset(params.skip).limit(params.limit).all()
    
    @staticmethod
    def update(db: Session, artwork_id: int, artwork_update: ArtworkUpdate) -> Optional[Artwork]:
        """
        更新作品
        """
        db_artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
        if not db_artwork:
            return None
        
        for key, value in artwork_update.dict(exclude_unset=True).items():
            setattr(db_artwork, key, value)
        
        db.commit()
        db.refresh(db_artwork)
        return db_artwork
    
    @staticmethod
    def delete(db: Session, artwork_id: int) -> bool:
        """
        软删除作品
        """
        db_artwork = get_base_query(db, Artwork).filter(Artwork.id == artwork_id).first()
        if not db_artwork:
            return False
        
        # 软删除记录
        return soft_delete(db, db_artwork)
    
    @staticmethod
    def update_publish_settings(
        db: Session, 
        artwork_id: int, 
        is_public: bool, 
        public_scope: str = 'result_only'
    ) -> Optional[Artwork]:
        """
        更新作品的公开状态和范围
        """
        artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
        if not artwork:
            return None
        
        # 只有完成的作品才能设置为公开
        if is_public and artwork.status != ArtworkStatus.COMPLETED.value:
            logger.warning(f"尝试公开未完成的作品 (ID: {artwork_id}, Status: {artwork.status})")
            return None  # 或者可以抛出异常
        
        artwork.is_public = is_public
        # 如果设为公开，则更新公开范围；如果设为私密，可以将范围重置为默认或保持不变
        if is_public:
            if public_scope not in ['result_only', 'all']:
                 logger.warning(f"无效的 public_scope: {public_scope}，将使用默认值 'result_only'")
                 artwork.public_scope = 'result_only'
            else:
                artwork.public_scope = public_scope
        else:
            # 当设为私密时，重置 public_scope 为默认值，可选
            artwork.public_scope = 'result_only' 

        db.add(artwork)
        try:
            db.commit()
            db.refresh(artwork)
            return artwork
        except Exception as e:
            db.rollback()
            logger.error(f"更新作品公开状态时出错 (ID: {artwork_id}): {e}")
            return None
    
    @staticmethod
    def increment_view_count(db: Session, artwork_id: int) -> Optional[Artwork]:
        """
        增加作品的查看次数
        """
        db_artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
        if not db_artwork:
            return None
        
        db_artwork.views_count += 1
        db.commit()
        db.refresh(db_artwork)
        return db_artwork
    
    @staticmethod
    def count(
        db: Session, 
        status: Optional[ArtworkStatus] = None,
        is_public: Optional[bool] = None,
        user_id: Optional[int] = None,
        style_id: Optional[int] = None
    ) -> int:
        """
        计算作品总数
        """
        query = get_base_query(db, Artwork)
        
        if status:
            query = query.filter(Artwork.status == status)
        
        if is_public is not None:
            query = query.filter(Artwork.is_public == is_public)
        
        if user_id:
            query = query.filter(Artwork.user_id == user_id)
        
        if style_id:
            query = query.filter(Artwork.style_id == style_id)
            
        return query.with_entities(func.count(Artwork.id)).scalar()
    
    @staticmethod
    def get_artwork_progress(db: Session, artwork_id: int) -> dict:
        """
        获取作品的处理进度
        """
        artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
        
        if not artwork:
            return {
                "success": False,
                "error": "作品不存在"
            }
        
        result = {
            "success": True,
            "artwork_id": artwork.id,
            "status": artwork.status,
            "progress": artwork.progress,
        }
        
        # 如果已经完成，返回结果URL
        if artwork.status == ArtworkStatus.COMPLETED.value:
            result["result_image_url"] = artwork.result_image_url
        
        # 如果失败，返回错误信息
        if artwork.status == ArtworkStatus.FAILED.value:
            result["error_message"] = artwork.error_message
            
        return result 

    @staticmethod
    async def add_watermark_to_image(image_bytes, watermark_path=None):
        """
        给图片添加水印
        
        Args:
            image_bytes: 要添加水印的图片字节数据
            watermark_path: 水印图片路径，如果为None则使用默认水印
            
        Returns:
            添加水印后的图片base64字符串
        """
        try:
            # 打开原图
            img = Image.open(io.BytesIO(image_bytes))
            
            # 水印路径，如果没有指定则使用默认路径
            if not watermark_path:
                watermark_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'watermark.jpg')
                # 如果默认水印不存在，则记录错误并返回原图
                if not os.path.exists(watermark_path):
                    logger.error(f"水印图片不存在: {watermark_path}")
                    return base64.b64encode(image_bytes).decode("utf-8")
            
            # 打开水印图片
            watermark = Image.open(watermark_path)
            
            # 计算水印大小，设置为原图宽度的1/5
            watermark_width = img.width // 5
            watermark_height = int(watermark.height * watermark_width / watermark.width)
            watermark = watermark.resize((watermark_width, watermark_height))
            
            # 如果水印有透明通道，保留它
            if watermark.mode == 'RGBA':
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # 计算水印位置（右下角）
                position = (img.width - watermark_width - 10, img.height - watermark_height - 10)
                
                # 创建一个透明层
                transparent = Image.new('RGBA', img.size, (0,0,0,0))
                transparent.paste(watermark, position, watermark)
                
                # 合成图片
                result = Image.alpha_composite(img, transparent)
                
                # 如果原图不是RGBA格式，转回原始格式
                if img.mode != 'RGBA':
                    result = result.convert(img.mode)
            else:
                # 水印没有透明通道，直接粘贴
                # 计算水印位置（右下角）
                position = (img.width - watermark_width - 10, img.height - watermark_height - 10)
                
                # 复制原图，粘贴水印
                result = img.copy()
                result.paste(watermark, position)
            
            # 转回字节数据
            buffered = io.BytesIO()
            result.save(buffered, format=img.format or 'JPEG')
            img_bytes = buffered.getvalue()
            
            # 转为base64
            return base64.b64encode(img_bytes).decode("utf-8")
            
        except Exception as e:
            logger.error(f"添加水印时出错: {e}", exc_info=True)
            # 出错时返回原图
            return base64.b64encode(image_bytes).decode("utf-8") 