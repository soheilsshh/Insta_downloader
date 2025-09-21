import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
import asyncio
from config import BOT_TOKEN,DOWNLOAD_PATH, MAX_FILE_SIZE
from instagram_downloader import InstagramDownloader

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class InstagramDownloadBot:
    def __init__(self):
        self.downloader = InstagramDownloader()
        self.download_path = DOWNLOAD_PATH
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🤖 **ربات دانلودر اینستاگرام**

سلام! من می‌توانم محتوای عمومی اینستاگرام را برای شما دانلود کنم.

📋 **نحوه استفاده:**
• لینک پست، رییل، یا ویدیو اینستاگرام را ارسال کنید
• من محتوا را دانلود و برای شما ارسال می‌کنم

🔗 **لینک‌های پشتیبانی شده:**
• پست‌های عادی: `https://instagram.com/p/...`
• رییل‌ها: `https://instagram.com/reel/...`
• ویدیوهای IGTV: `https://instagram.com/tv/...`

✅ **ویژگی‌ها:**
• دانلود محتوای عمومی بدون نیاز به ورود
• پشتیبانی از عکس و ویدیو
• دانلود با کیفیت بالا
• حداکثر حجم فایل: 50 مگابایت

⚠️ **نکته مهم:**
• فقط پست‌های عمومی قابل دانلود هستند
• پست‌های خصوصی پشتیبانی نمی‌شوند

برای شروع، لینک اینستاگرام خود را ارسال کنید! 🚀
        """
        
        keyboard = [
            [InlineKeyboardButton("📖 راهنمای استفاده", callback_data="help")],
            [InlineKeyboardButton("ℹ️ درباره ربات", callback_data="about")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📖 **راهنمای استفاده از ربات**

**مراحل دانلود:**
1️⃣ لینک پست عمومی اینستاگرام را کپی کنید
2️⃣ لینک را در چت ارسال کنید
3️⃣ منتظر دانلود و دریافت فایل باشید

**نمونه لینک‌های معتبر:**
```
https://instagram.com/p/ABC123/
https://instagram.com/reel/XYZ789/
https://instagram.com/tv/DEF456/
```

**دستورات ربات:**
/start - شروع کار با ربات
/help - نمایش این راهنما
/about - اطلاعات ربات
/saved - نمایش پست‌های ذخیره شده

**نکات مهم:**
• فقط پست‌های عمومی قابل دانلود هستند
• فایل‌ها و اطلاعات ذخیره می‌شوند
• حداکثر حجم فایل: 2GB (بدون محدودیت زمانی)
• لینک باید کامل و صحیح باشد
• اتصال اینترنت خود را بررسی کنید
• پست‌های خصوصی پشتیبانی نمی‌شوند
        """
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /about command"""
        about_text = """
ℹ️ **درباره ربات دانلودر اینستاگرام**

**ویژگی‌ها:**
✅ دانلود پست‌های عمومی
✅ دانلود رییل‌ها
✅ دانلود ویدیوهای IGTV
✅ پشتیبانی از پست‌های چندرسانه‌ای
✅ دانلود با کیفیت بالا
✅ بدون نیاز به ورود
✅ ذخیره اطلاعات و فایل‌ها

**تکنولوژی:**
• Python Telegram Bot
• Instaloader
• Python 3.8+

**محدودیت‌ها:**
• حداکثر حجم فایل: 2GB (بدون محدودیت زمانی)
• فقط پست‌های عمومی
• استوری‌ها پشتیبانی نمی‌شوند

**توسعه‌دهنده:** ربات دانلودر اینستاگرام
**نسخه:** 3.0.0
        """
        await update.message.reply_text(about_text, parse_mode=ParseMode.MARKDOWN)
    
    async def saved_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /saved command - show saved posts"""
        try:
            import os
            import json
            
            saved_posts = []
            download_path = self.download_path
            
            if os.path.exists(download_path):
                for file in os.listdir(download_path):
                    if file.endswith('_metadata.json'):
                        try:
                            metadata_path = os.path.join(download_path, file)
                            with open(metadata_path, 'r', encoding='utf-8') as f:
                                post_info = json.load(f)
                            
                            # Check if files still exist
                            valid_files = []
                            for file_path in post_info.get('file_paths', []):
                                if os.path.exists(file_path):
                                    valid_files.append(file_path)
                            
                            if valid_files:
                                saved_posts.append({
                                    'shortcode': post_info.get('shortcode', 'Unknown'),
                                    'username': post_info.get('username', 'Unknown'),
                                    'date': post_info.get('date', 'Unknown'),
                                    'is_video': post_info.get('is_video', False),
                                    'file_count': len(valid_files)
                                })
                        except Exception as e:
                            logger.error(f"Error reading metadata file {file}: {e}")
            
            if saved_posts:
                text = "📁 **پست‌های ذخیره شده:**\n\n"
                for i, post in enumerate(saved_posts, 1):
                    media_type = "🎬 ویدیو" if post['is_video'] else "📸 عکس"
                    text += f"{i}. @{post['username']}\n"
                    text += f"   📅 {post['date']}\n"
                    text += f"   {media_type} ({post['file_count']} فایل)\n"
                    text += f"   🔗 https://instagram.com/p/{post['shortcode']}/\n\n"
                
                text += f"📊 **مجموع:** {len(saved_posts)} پست"
            else:
                text = "📁 هیچ پستی ذخیره نشده است"
            
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Error in saved command: {e}")
            await update.message.reply_text("❌ خطا در دریافت پست‌های ذخیره شده")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        message = update.message
        text = message.text
        
        # Check if message contains Instagram URL
        if "instagram.com" in text:
            await self.process_instagram_url(update, context, text)
        else:
            await message.reply_text(
                "❌ لطفاً لینک معتبر اینستاگرام ارسال کنید.\n\n"
                "برای راهنمایی /help را ارسال کنید."
            )
    
    async def process_instagram_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
        """Process Instagram URL and download content"""
        message = update.message
        
        # Send processing message
        processing_msg = await message.reply_text("🔄 در حال پردازش لینک...")
        
        try:
            # Extract shortcode first
            shortcode = self.downloader.extract_shortcode(url)
            if not shortcode:
                await processing_msg.edit_text("❌ نمی‌توان کد پست را استخراج کرد")
                return
            
            # Check if post is already downloaded
            success, load_msg, saved_info = self.downloader.load_saved_post(shortcode, self.download_path)
            
            if success:
                # Post already downloaded, show saved info
                await processing_msg.edit_text("📁 پست قبلاً دانلود شده است\n🔄 در حال بارگذاری...")
                
                info_text = f"""
📊 **اطلاعات پست (ذخیره شده):**
👤 کاربر: @{saved_info['username']}
❤️ لایک: {saved_info['likes']:,}
💬 کامنت: {saved_info['comments']:,}
📅 تاریخ: {saved_info['date']}
🎬 نوع: {'ویدیو' if saved_info['is_video'] else 'عکس'}
                """
                
                if saved_info['is_video'] and saved_info['video_view_count']:
                    info_text += f"👀 بازدید: {saved_info['video_view_count']:,}\n"
                
                if saved_info['caption']:
                    info_text += f"📝 کپشن: {saved_info['caption']}\n"
                
                await processing_msg.edit_text(info_text + "\n📁 ارسال فایل‌ها...")
                
                # Send saved files
                await self.send_downloaded_files(update, context, saved_info['file_paths'], load_msg)
                return
            
            # Get post info first
            success, info_msg, post_info = self.downloader.get_post_info(url)
            
            if not success:
                await processing_msg.edit_text(info_msg)
                return
            
            # Show post info
            info_text = f"""
📊 **اطلاعات پست:**
👤 کاربر: @{post_info['username']}
❤️ لایک: {post_info['likes']:,}
💬 کامنت: {post_info['comments']:,}
📅 تاریخ: {post_info['date']}
🎬 نوع: {'ویدیو' if post_info['is_video'] else 'عکس'}
            """
            
            if post_info['is_video'] and post_info['video_view_count']:
                info_text += f"👀 بازدید: {post_info['video_view_count']:,}\n"
            
            if post_info['caption']:
                info_text += f"📝 کپشن: {post_info['caption']}\n"
            
            await processing_msg.edit_text(info_text + "\n🔄 در حال دانلود...")
            
            # Download the post with metadata
            success, download_msg, file_paths, post_info = self.downloader.download_post(url, self.download_path)
            
            if not success:
                await processing_msg.edit_text(download_msg)
                return
            
            # Show final info with downloaded data
            final_info = f"""
📊 **پست دانلود شد:**
👤 کاربر: @{post_info['username']}
❤️ لایک: {post_info['likes']:,}
💬 کامنت: {post_info['comments']:,}
📅 تاریخ: {post_info['date']}
🎬 نوع: {'ویدیو' if post_info['is_video'] else 'عکس'}
📁 فایل‌ها: {len(file_paths)} عدد
            """
            
            if post_info['is_video'] and post_info['video_view_count']:
                final_info += f"👀 بازدید: {post_info['video_view_count']:,}\n"
            
            if post_info['caption']:
                final_info += f"📝 کپشن: {post_info['caption']}\n"
            
            await processing_msg.edit_text(final_info + "\n📁 ارسال فایل‌ها...")
            
            # Send files
            await self.send_downloaded_files(update, context, file_paths, download_msg)
            
        except Exception as e:
            logger.error(f"Error processing Instagram URL: {e}")
            await processing_msg.edit_text(f"❌ خطا در پردازش: {str(e)}")
    
    async def send_downloaded_files(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_paths: list, message: str):
        """Send downloaded files to user"""
        chat_id = update.effective_chat.id
        
        try:
            # Send message about download
            await context.bot.send_message(chat_id, message)
            
            # Send each file
            for file_path in file_paths:
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    
                    # Try to send file with appropriate method
                    await self._send_single_file(context, chat_id, file_path)
                    
        except Exception as e:
            logger.error(f"Error sending files: {e}")
            await context.bot.send_message(chat_id, f"❌ خطا در ارسال فایل: {str(e)}")
    
    async def _send_single_file(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int, file_path: str):
        """Send a single file with appropriate method"""
        try:
            # First try with send_document (most compatible)
            with open(file_path, 'rb') as f:
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=f,
                    caption=f"📁 {os.path.basename(file_path)}"
                )
            logger.info(f"Successfully sent file as document: {file_path}")
            return True
            
        except Exception as doc_error:
            logger.warning(f"send_document failed for {file_path}: {doc_error}")
            
            # Try with specific media type
            try:
                with open(file_path, 'rb') as f:
                    if file_path.lower().endswith(('.mp4', '.mov', '.avi')):
                        await context.bot.send_video(
                            chat_id=chat_id,
                            video=f,
                            caption=f"📹 {os.path.basename(file_path)}"
                        )
                        logger.info(f"Successfully sent as video: {file_path}")
                    elif file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                        await context.bot.send_photo(
                            chat_id=chat_id,
                            photo=f,
                            caption=f"📸 {os.path.basename(file_path)}"
                        )
                        logger.info(f"Successfully sent as photo: {file_path}")
                    else:
                        # Fallback to document for unknown types
                        await context.bot.send_document(
                            chat_id=chat_id,
                            document=f,
                            caption=f"📄 {os.path.basename(file_path)}"
                        )
                        logger.info(f"Successfully sent as document fallback: {file_path}")
                return True
                
            except Exception as media_error:
                logger.error(f"All methods failed for {file_path}: {media_error}")
                await context.bot.send_message(
                    chat_id, 
                    f"❌ خطا در ارسال فایل {os.path.basename(file_path)}: {str(media_error)}"
                )
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error sending {file_path}: {e}")
            await context.bot.send_message(
                chat_id, 
                f"❌ خطای غیرمنتظره در ارسال {os.path.basename(file_path)}: {str(e)}"
            )
            return False
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "help":
            await self.help_command(update, context)
        elif query.data == "about":
            await self.about_command(update, context)
    
    def run(self):
        """Run the bot"""
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN not found! Please set it in your environment variables.")
            return
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("about", self.about_command))
        application.add_handler(CommandHandler("saved", self.saved_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Start bot
        logger.info("Starting Instagram Download Bot...")
        logger.info(f"Max file size: {MAX_FILE_SIZE // (1024*1024)} MB")
        logger.info("Timeout restrictions removed for better performance")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Main function"""
    bot = InstagramDownloadBot()
    bot.run()

if __name__ == "__main__":
    main()
