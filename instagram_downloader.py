import os
import re
import requests
import instaloader
from typing import Optional, Tuple
from urllib.parse import urlparse
import logging
import time

logger = logging.getLogger(__name__)

class InstagramDownloader:
    def __init__(self):
        """
        Initialize Instagram downloader for public content only
        """
        self.loader = instaloader.Instaloader(
            download_pictures=True,
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False
        )
        
        # Set user agent to avoid detection
        self.loader.context._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        logger.info("Instagram downloader initialized for public content")
    
    def is_valid_instagram_url(self, url: str) -> bool:
        """
        Check if the URL is a valid Instagram post/story URL
        """
        instagram_patterns = [
            r'https?://(?:www\.)?instagram\.com/p/[A-Za-z0-9_-]+/?',
            r'https?://(?:www\.)?instagram\.com/reel/[A-Za-z0-9_-]+/?',
            r'https?://(?:www\.)?instagram\.com/tv/[A-Za-z0-9_-]+/?',
            r'https?://(?:www\.)?instagram\.com/stories/[A-Za-z0-9_.]+/[0-9]+/?'
        ]
        
        for pattern in instagram_patterns:
            if re.match(pattern, url):
                return True
        return False
    
    def extract_shortcode(self, url: str) -> Optional[str]:
        """
        Extract shortcode from Instagram URL
        """
        patterns = [
            r'/p/([A-Za-z0-9_-]+)',
            r'/reel/([A-Za-z0-9_-]+)',
            r'/tv/([A-Za-z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def download_post(self, url: str, download_path: str = "downloads") -> Tuple[bool, str, list, dict]:
        """
        Download Instagram post content with caption metadata
        
        Returns:
            (success, message, file_paths, post_info)
        """
        try:
            if not self.is_valid_instagram_url(url):
                return False, "❌ لینک اینستاگرام نامعتبر است", [], {}
            
            shortcode = self.extract_shortcode(url)
            if not shortcode:
                return False, "❌ نمی‌توان کد پست را استخراج کرد", [], {}
            
            # Create unique download directory for this post
            target_dir = os.path.normpath(os.path.join(download_path, shortcode))
            os.makedirs(target_dir, exist_ok=True)
            
            # Get post
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            
            # Download post to target_dir (ensure no subdirectories are created)
            self.loader.dirname_pattern = target_dir
            self.loader.filename_pattern = "{shortcode}"
            self.loader.download_post(post, target=target_dir)
            
            # Get downloaded files
            file_paths = []
            for file in os.listdir(target_dir):
                full_path = os.path.normpath(os.path.join(target_dir, file))
                if os.path.isfile(full_path) and file.endswith(('.jpg', '.jpeg', '.png', '.mp4', '.mov')):
                    file_paths.append(full_path)
                    logger.info(f"Found file: {full_path}")
            
            # Save metadata (only caption)
            post_info = {
                'shortcode': shortcode,
                'username': post.owner_username,
                'caption': post.caption,
                'likes': post.likes,
                'comments': post.comments,
                'is_video': post.is_video,
                'video_view_count': post.video_view_count if post.is_video else 0,
                'date': post.date_utc.strftime("%Y-%m-%d %H:%M:%S"),
                'file_paths': file_paths
            }
            
            # Save metadata to JSON file
            import json
            metadata_path = os.path.normpath(os.path.join(target_dir, f"{shortcode}_metadata.json"))
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(post_info, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved metadata: {metadata_path}")
            
            if file_paths:
                return True, f"✅ پست با موفقیت دانلود شد\n📁 {len(file_paths)} فایل", file_paths, post_info
            else:
                logger.error(f"No files found in {target_dir} after download.")
                return False, "❌ هیچ فایلی دانلود نشد", [], {}
                
        except instaloader.exceptions.InstaloaderException as e:
            logger.error(f"Instaloader error: {e}")
            if "Login required" in str(e):
                return False, "❌ این پست خصوصی است و نیاز به ورود دارد", [], {}
            elif "Not found" in str(e):
                return False, "❌ پست یافت نشد یا حذف شده است", [], {}
            else:
                return False, f"❌ خطا در دانلود: {str(e)}", [], {}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False, f"❌ خطای غیرمنتظره: {str(e)}", [], {}

    def get_post_info(self, url: str) -> Tuple[bool, str, dict]:
        """
        Get post information without downloading
        """
        try:
            if not self.is_valid_instagram_url(url):
                return False, "❌ لینک اینستاگرام نامعتبر است", {}
            
            shortcode = self.extract_shortcode(url)
            if not shortcode:
                return False, "❌ نمی‌توان کد پست را استخراج کرد", {}
            
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            
            info = {
                'shortcode': shortcode,
                'username': post.owner_username,
                'caption': post.caption[:100] + "..." if post.caption and len(post.caption) > 100 else post.caption,
                'likes': post.likes,
                'comments': post.comments,
                'is_video': post.is_video,
                'video_view_count': post.video_view_count if post.is_video else 0,
                'date': post.date_utc.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return True, "✅ اطلاعات پست دریافت شد", info
            
        except Exception as e:
            return False, f"❌ خطا در دریافت اطلاعات: {str(e)}", {}
    
    def load_saved_post(self, shortcode: str, download_path: str = "downloads") -> Tuple[bool, str, dict]:
        """
        Load previously saved post data
        
        Returns:
            (success, message, post_info)
        """
        try:
            metadata_path = os.path.join(download_path, f"{shortcode}_metadata.json")
            
            if not os.path.exists(metadata_path):
                return False, "❌ اطلاعات پست ذخیره نشده است", {}
            
            import json
            with open(metadata_path, 'r', encoding='utf-8') as f:
                post_info = json.load(f)
            
            # Verify files still exist
            verified_files = []
            for file_path in post_info.get('file_paths', []):
                if os.path.exists(file_path):
                    verified_files.append(file_path)
                else:
                    logger.warning(f"File not found: {file_path}")
            
            post_info['file_paths'] = verified_files
            
            if verified_files:
                return True, f"✅ اطلاعات پست بارگذاری شد\n📁 {len(verified_files)} فایل", post_info
            else:
                return False, "❌ فایل‌های پست یافت نشد", {}
                
        except Exception as e:
            logger.error(f"Error loading saved post: {e}")
            return False, f"❌ خطا در بارگذاری اطلاعات: {str(e)}", {}
