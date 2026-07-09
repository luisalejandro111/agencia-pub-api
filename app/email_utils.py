# app/email_utils.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
import logging

logger = logging.getLogger(__name__)

async def send_reset_email(to_email: str, reset_url: str, nombre: str) -> bool:
    """
    Envía email para restablecer contraseña
    
    Args:
        to_email: Email del destinatario
        reset_url: URL para restablecer la contraseña
        nombre: Nombre del usuario
    
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        # Configuración SMTP
        smtp_server = settings.SMTP_SERVER
        smtp_port = settings.SMTP_PORT
        smtp_user = settings.SMTP_USER
        smtp_password = settings.SMTP_PASSWORD
        smtp_from = settings.SMTP_FROM
        
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = smtp_from
        msg['To'] = to_email
        msg['Subject'] = "Recuperación de contraseña - SGOAP"

        # Diseño del email
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: #f4f7fc; }}
                .container {{ max-width: 600px; margin: 40px auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
                .header {{ background: linear-gradient(135deg, #0d1b3e 0%, #1e293b 100%); padding: 30px 40px; text-align: center; }}
                .header h1 {{ color: #00D4FF; margin: 10px 0 0 0; font-size: 24px; }}
                .content {{ padding: 40px; }}
                .content p {{ color: #475569; line-height: 1.6; font-size: 16px; }}
                .btn {{ display: inline-block; background: #0d1b3e; color: white !important; padding: 14px 40px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #94a3b8; font-size: 12px; border-top: 1px solid #e2e8f0; }}
                .warning {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px 16px; margin: 20px 0; border-radius: 4px; }}
                .warning p {{ margin: 0; color: #78350f; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 SGOAP</h1>
                    <p style="color: rgba(255,255,255,0.7); margin: 5px 0 0 0;">Sistema de Gestión Operativa</p>
                </div>
                <div class="content">
                    <h2 style="color: #0d1b3e; margin-top: 0;">Hola {nombre} 👋</h2>
                    <p>Hemos recibido una solicitud para restablecer tu contraseña en <strong>SGOAP</strong>.</p>
                    
                    <div class="warning">
                        <p>🔔 Este enlace expirará en <strong>15 minutos</strong>.</p>
                    </div>
                    
                    <p>Haz clic en el botón para crear una nueva contraseña:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="btn">Restablecer Contraseña</a>
                    </div>
                    
                    <p style="font-size: 14px; color: #64748b; margin-top: 20px;">
                        Si no solicitaste este cambio, puedes ignorar este email.
                    </p>
                    <p style="font-size: 14px; color: #64748b;">
                        Si el botón no funciona, copia y pega este enlace en tu navegador:
                        <br>
                        <span style="color: #0d1b3e; word-break: break-all; font-size: 12px;">{reset_url}</span>
                    </p>
                </div>
                <div class="footer">
                    <p>SGOAP © 2026 • Conectando cada área de tu agencia.</p>
                    <p style="margin-top: 5px;">Este es un mensaje automático, por favor no responder.</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        # Conectar y enviar
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✅ Email enviado exitosamente a {to_email}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"❌ Error de autenticación SMTP: {e}")
        logger.error("⚠️ Verifica tu email y contraseña de aplicación en .env")
        return False
        
    except smtplib.SMTPException as e:
        logger.error(f"❌ Error SMTP: {e}")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error inesperado enviando email: {e}")
        return False