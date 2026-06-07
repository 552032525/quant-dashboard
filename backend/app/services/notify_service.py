'''通知服务 — 邮件发送'''
import smtplib
import asyncio
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from app.core.config import settings

logger = logging.getLogger("notify")

async def send_email(to_email: str, subject: str, body: str) -> bool:
    '''发送邮件通知'''
    if not settings.notification_enabled:
        logger.info("邮件通知未启用，跳过")
        return False
    
    if not settings.smtp_host:
        logger.warning("SMTP 未配置")
        return False
    
    def _send():
        msg = MIMEMultipart()
        msg["From"] = f"{Header(settings.smtp_from_name, 'utf-8').encode()} <{settings.smtp_from_email}>"
        msg["To"] = to_email
        msg["Subject"] = Header(subject, "utf-8").encode()
        msg.attach(MIMEText(body, "html", "utf-8"))
        
        try:
            if settings.smtp_port == 465:
                server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10, local_hostname="localhost")
            else:
                server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10, local_hostname="localhost")
                server.ehlo("localhost")
                server.starttls()
                server.ehlo("localhost")
            
            server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.smtp_from_email, to_email, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
    
    return await asyncio.to_thread(_send)


async def send_alert_notification(alerts: list[dict], to_email: str = "") -> bool:
    '''发送预警触发通知
    
    Args:
        alerts: 触发的预警列表 [{"code": "...", "name": "...", "message": "..."}]
        to_email: 接收邮箱，默认使用配置中的 from_email
    '''
    if not alerts:
        return False
    
    recipient = to_email or settings.smtp_from_email
    if not recipient:
        return False
    
    # 构建 HTML 邮件
    items_html = ""
    for a in alerts:
        items_html += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #eee;">{a['name']} ({a['code']})</td>
            <td style="padding:8px;border-bottom:1px solid #eee;color:#cf202f;">⚠ {a['message']}</td>
        </tr>"""
    
    body = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
        <h2 style="color:#1a1a2e;">📊 Quant Dashboard 预警通知</h2>
        <p>以下预警已触发：</p>
        <table style="width:100%;border-collapse:collapse;">
            <thead><tr style="background:#f5f5f5;">
                <th style="padding:8px;text-align:left;">股票</th>
                <th style="padding:8px;text-align:left;">预警信息</th>
            </tr></thead>
            <tbody>{items_html}</tbody>
        </table>
        <p style="color:#999;font-size:12px;margin-top:20px;">
            此邮件由 Quant Dashboard 自动发送，请勿回复。
        </p>
    </body></html>"""
    
    subject = f"Quant Dashboard 预警 - {len(alerts)} 条触发"
    return await send_email(recipient, subject, body)
