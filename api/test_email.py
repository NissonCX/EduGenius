#!/usr/bin/env python3
"""
邮件服务测试脚本

用于测试 SMTP 配置是否正确，邮件是否能正常发送
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
api_dir = Path(__file__).parent
sys.path.insert(0, str(api_dir))

from app.core.email import email_service
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def print_header(text: str):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_success(text: str):
    """打印成功消息"""
    print(f"✅ {text}")


def print_error(text: str):
    """打印错误消息"""
    print(f"❌ {text}")


def print_info(text: str):
    """打印信息"""
    print(f"ℹ️  {text}")


def print_warning(text: str):
    """打印警告"""
    print(f"⚠️  {text}")


async def check_configuration():
    """检查邮件配置"""
    print_header("1️⃣  检查邮件配置")

    config_checks = [
        ("SMTP 主机", email_service.smtp_host),
        ("SMTP 端口", email_service.smtp_port),
        ("SMTP 用户", email_service.smtp_user),
        ("SMTP 密码", "****" if email_service.smtp_password else "未设置"),
        ("发件人", email_service.smtp_from),
        ("发件人名称", email_service.smtp_from_name),
        ("使用 TLS", email_service.use_tls),
    ]

    all_configured = True
    for name, value in config_checks:
        if value and value != "未设置":
            print_success(f"{name}: {value}")
        else:
            print_error(f"{name}: 未设置")
            all_configured = False

    if not all_configured:
        print_warning("\n⚠️  邮件配置不完整，请检查 api/.env 文件")
        return False

    print_success("\n邮件配置完整！")
    return True


async def test_send_test_email():
    """发送测试邮件"""
    print_header("2️⃣  发送测试邮件")

    # 检查配置
    if not email_service.smtp_user:
        print_error("邮件服务未配置（SMTP_USER 为空）")
        print_info("请参考 EMAIL_SETUP_GUIDE.md 配置邮件服务")
        return False

    # 获取测试邮箱
    test_email = input("\n请输入测试邮箱地址（留空跳过）: ").strip()

    if not test_email:
        print_warning("跳过发送测试邮件")
        return True

    print_info(f"正在发送测试邮件到: {test_email}...")

    # 发送测试邮件
    subject = "EduGenius 邮件服务测试"
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .success { background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 测试成功！</h1>
            <p>如果您看到这封邮件，说明 EduGenius 邮件服务配置正确！</p>
            <div class="success">
                <p><strong>测试项目：</strong></p>
                <ul>
                    <li>✅ SMTP 连接正常</li>
                    <li>✅ 身份验证成功</li>
                    <li>✅ 邮件发送成功</li>
                </ul>
            </div>
            <p>您现在可以使用密码重置功能了。</p>
        </div>
    </body>
    </html>
    """

    text_content = """
    测试成功！

    如果您看到这封邮件，说明 EduGenius 邮件服务配置正确！

    测试项目：
    - SMTP 连接正常
    - 身份验证成功
    - 邮件发送成功
    """

    try:
        result = await email_service.send_email(
            to_email=test_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

        if result:
            print_success(f"测试邮件已成功发送到: {test_email}")
            print_info("请检查收件箱（包括垃圾邮件文件夹）")
            return True
        else:
            print_error("测试邮件发送失败")
            print_info("请检查 SMTP 配置和网络连接")
            return False

    except Exception as e:
        print_error(f"发送测试邮件时出错: {e}")
        return False


async def test_password_reset_email():
    """测试密码重置邮件"""
    print_header("3️⃣  测试密码重置邮件")

    if not email_service.smtp_user:
        print_warning("邮件服务未配置，跳过密码重置邮件测试")
        return True

    test_email = input("\n请输入测试邮箱地址（留空跳过）: ").strip()

    if not test_email:
        print_warning("跳过密码重置邮件测试")
        return True

    print_info(f"正在发送密码重置邮件到: {test_email}...")

    # 生成测试 token
    test_token = "test_" + email_service.generate_reset_token()[:16]

    try:
        result = await email_service.send_password_reset_email(
            email=test_email,
            reset_token=test_token
        )

        if result:
            print_success(f"密码重置邮件已成功发送到: {test_email}")
            print_info("请检查收件箱（包括垃圾邮件文件夹）")
            print_info(f"测试 Token: {test_token}")
            return True
        else:
            print_error("密码重置邮件发送失败")
            return False

    except Exception as e:
        print_error(f"发送密码重置邮件时出错: {e}")
        return False


async def main():
    """主测试流程"""
    print_header("🔧 EduGenius 邮件服务测试")

    # 1. 检查配置
    config_ok = await check_configuration()

    if not config_ok:
        print_info("\n您可以：")
        print("  1. 参考 EMAIL_SETUP_GUIDE.md 配置邮件服务")
        print("  2. 在 api/.env 文件中添加 SMTP 配置")
        print("  3. 重新运行此测试脚本")
        return

    # 询问是否继续
    print("\n" + "-" * 60)
    choice = input("配置检查通过，是否继续发送测试邮件？(y/n): ").strip().lower()

    if choice not in ['y', 'yes', '是']:
        print_info("测试已取消")
        return

    # 2. 发送测试邮件
    test_email_ok = await test_send_test_email()

    # 3. 测试密码重置邮件
    if test_email_ok:
        print("\n" + "-" * 60)
        choice = input("是否测试密码重置邮件？(y/n): ").strip().lower()
        if choice in ['y', 'yes', '是']:
            await test_password_reset_email()

    # 总结
    print_header("✨ 测试完成")

    if config_ok and test_email_ok:
        print_success("所有测试通过！邮件服务配置正确")
        print_info("您现在可以在前端使用密码重置功能了")
    else:
        print_warning("部分测试未通过")
        print_info("请根据上述提示检查配置")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print_error(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
