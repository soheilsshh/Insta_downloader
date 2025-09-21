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
        Download Instagram post content with metadata
        
        Returns:
            (success, message, file_paths, post_info)
        """
        try:
            if not self.is_valid_instagram_url(url):
                return False, "❌ لینک اینستاگرام نامعتبر است", [], {}
            
            shortcode = self.extract_shortcode(url)
            if not shortcode:
                return False, "❌ نمی‌توان کد پست را استخراج کرد", [], {}
            
            # Create download directory
            os.makedirs(download_path, exist_ok=True)
            
            # Get post
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            
            # Step 1: Download media content first
            logger.info(f"Step 1: Downloading media content for {shortcode}")
            file_paths = []
            
            # Download media files directly
            if post.is_video:
                # Download video
                video_url = post.video_url
                if video_url:
                    video_path = os.path.join(download_path, f"{shortcode}_video.mp4")
                    if self._download_file(video_url, video_path):
                        file_paths.append(video_path)
                        logger.info(f"Downloaded video: {video_path}")
            else:
                # Download images
                for i, media_url in enumerate(post.get_isvideos()):
                    if media_url:
                        image_path = os.path.join(download_path, f"{shortcode}_image_{i}.jpg")
                        if self._download_file(media_url, image_path):
                            file_paths.append(image_path)
                            logger.info(f"Downloaded image: {image_path}")
            
            # Step 2: Download and save metadata
            logger.info(f"Step 2: Saving metadata for {shortcode}")
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
            metadata_path = os.path.join(download_path, f"{shortcode}_metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(post_info, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved metadata: {metadata_path}")
            
            # Step 3: Verify all files exist
            logger.info(f"Step 3: Verifying downloaded files")
            verified_files = []
            for file_path in file_paths:
                if os.path.exists(file_path):
                    verified_files.append(file_path)
                    logger.info(f"Verified file: {file_path}")
                else:
                    logger.warning(f"File not found: {file_path}")
            
            if verified_files:
                return True, f"✅ پست با موفقیت دانلود شد\n📁 {len(verified_files)} فایل", verified_files, post_info
            else:
                return False, "❌ هیچ فایلی دانلود نشد", [], {}
                
        except instaloader.exceptions.InstaloaderException as e:
            if "Login required" in str(e):
                return False, "❌ این پست خصوصی است و نیاز به ورود دارد", [], {}
            elif "Not found" in str(e):
                return False, "❌ پست یافت نشد یا حذف شده است", [], {}
            else:
                return False, f"❌ خطا در دانلود: {str(e)}", [], {}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False, f"❌ خطای غیرمنتظره: {str(e)}", [], {}
    
    def download_post_direct(self, url: str, download_path: str = "downloads") -> Tuple[bool, str, list]:
        """
        Direct download method using post URLs
        """
        try:
            if not self.is_valid_instagram_url(url):
                return False, "❌ لینک اینستاگرام نامعتبر است", []
            
            shortcode = self.extract_shortcode(url)
            if not shortcode:
                return False, "❌ نمی‌توان کد پست را استخراج کرد", []
            
            # Create download directory
            os.makedirs(download_path, exist_ok=True)
            
            # Get post
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            
            file_paths = []
            
            # Download media files directly
            if post.is_video:
                # Download video
                video_url = post.video_url
                if video_url:
                    video_path = os.path.join(download_path, f"{shortcode}_video.mp4")
                    self._download_file(video_url, video_path)
                    if os.path.exists(video_path):
                        file_paths.append(video_path)
                        logger.info(f"Downloaded video: {video_path}")
            else:
                # Download images
                for i, url in enumerate(post.get_isvideos()):
                    if url:
                        file_path = os.path.join(download_path, f"{shortcode}_image_{i}.jpg")
                        self._download_file(url, file_path)
                        if os.path.exists(file_path):
                            file_paths.append(file_path)
                            logger.info(f"Downloaded image: {file_path}")
            
            if file_paths:
                return True, f"✅ پست با موفقیت دانلود شد\n📁 {len(file_paths)} فایل", file_paths
            else:
                return False, "❌ هیچ فایلی دانلود نشد", []
                
        except Exception as e:
            logger.error(f"Direct download error: {e}")
            return False, f"❌ خطا در دانلود مستقیم: {str(e)}", []
    
    def _download_file(self, url: str, file_path: str) -> bool:
        """
        Download a single file from URL
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download file from {url}: {e}")
            return False
        
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
