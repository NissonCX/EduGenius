"""
邮件发送工具模块

支持密码重置邮件等邮件发送功能
"""
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class EmailService:
    """邮件服务类"""

    def __init__(self):
        """初始化邮件服务"""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_from = settings.SMTP_FROM
        self.smtp_from_name = settings.SMTP_FROM_NAME
        self.use_tls = settings.SMTP_USE_TLS

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        发送邮件

        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            html_content: HTML 格式内容
            text_content: 纯文本内容（备用）

        Returns:
            bool: 是否发送成功
        """
        if not self.smtp_user:
            logger.warning("⚠️ 邮件服务未配置，跳过发送")
            return False

        try:
            # 创建邮件
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.smtp_from_name} <{self.smtp_from}>"
            message["To"] = to_email

            # 添加纯文本部分
            if text_content:
                part1 = MIMEText(text_content, "plain", "utf-8")
                message.attach(part1)

            # 添加 HTML 部分
            part2 = MIMEText(html_content, "html", "utf-8")
            message.attach(part2)

            # 连接 SMTP 服务器
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)
                server.quit()

            logger.info(f"✅ 邮件已发送至: {to_email}")
            return True

        except Exception as e:
            logger.error(f"❌ 邮件发送失败: {e}")
            return False

    def generate_reset_token(self) -> str:
        """
        生成安全的重置令牌

        Returns:
            str: 64字符的十六进制令牌
        """
        return secrets.token_hex(32)

    async def send_password_reset_email(
        self,
        email: str,
        reset_token: str
    ) -> bool:
        """
        发送密码重置邮件

        Args:
            email: 用户邮箱
            reset_token: 重置令牌

        Returns:
            bool: 是否发送成功
        """
        # 构建重置链接
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

        # 邮件内容
        subject = "重置您的 EduGenius 密码"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background: #f9f9f9;
                    padding: 40px;
                    border-radius: 12px;
                    text-align: center;
                }}
                .logo {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #000;
                    margin-bottom: 20px;
                }}
                .title {{
                    font-size: 20px;
                    margin-bottom: 10px;
                }}
                .content {{
                    background: #fff;
                    padding: 30px;
                    border-radius: 8px;
                    margin: 20px 0;
                    text-align: left;
                }}
                .button {{
                    display: inline-block;
                    background: #000;
                    color: #fff !important;
                    text-decoration: none;
                    padding: 12px 30px;
                    border-radius: 6px;
                    margin: 20px 0;
                    font-weight: 500;
                }}
                .footer {{
                    font-size: 12px;
                    color: #666;
                    margin-top: 30px;
                }}
                .warning {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">🎓 EduGenius</div>
                <h1 class="title">重置您的密码</h1>

                <div class="content">
                    <p>您好，</p>
                    <p>我们收到了重置您账户密码的请求。</p>
                    <p>如果这是您发起的操作，请点击下方按钮重置密码：</p>

                    <a href="{reset_link}" class="button">重置密码</a>

                    <p>或者复制以下链接到浏览器地址栏：</p>
                    <p style="word-break: break-all; color: #666; font-size: 12px;">{reset_link}</p>

                    <div class="warning">
                        ⚠️ 此链接将在 1 小时后失效
                    </div>

                    <p>如果您没有请求重置密码，请忽略此邮件，您的账户安全。</p>
                </div>

                <div class="footer">
                    <p>此邮件由系统自动发送，请勿回复。</p>
                    <p>© {datetime.now().year} EduGenius. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
重置您的 EduGenius 密码

我们收到了重置您账户密码的请求。

如果这是您发起的操作，请访问以下链接重置密码：
{reset_link}

此链接将在 1 小时后失效。

如果您没有请求重置密码，请忽略此邮件，您的账户安全。

© {datetime.now().year} EduGenius. All rights reserved.
        """

        return await self.send_email(email, subject, html_content, text_content)


# 全局邮件服务实例
email_service = EmailService()


async def get_email_service() -> EmailService:
    """
    获取邮件服务实例

    Returns:
        EmailService: 邮件服务实例
    """
    return email_service
