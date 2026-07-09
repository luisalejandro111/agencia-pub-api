# app/routes/auth.py
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Usuario
from app.auth import hash_password
from app.config import settings
import secrets
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])

# Almacenamiento temporal para tokens
reset_tokens = {}

# ============================================================
# PÁGINA: OLVIDÉ CONTRASEÑA
# ============================================================
@router.get("/olvide-contrasena", response_class=HTMLResponse)
async def olvide_contrasena(request: Request):
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Recuperar Contraseña - SGOAP</title>
        <link rel="icon" type="image/x-icon" href="/static/logo2.ico">
        <link rel="shortcut icon" href="/static/logo2.ico">
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
        <style>
            body {
                background: linear-gradient(135deg, #0d1b3e 0%, #1e293b 100%);
                min-height: 100vh;
            }
            .alert {
                padding: 0.75rem 1rem;
                border-radius: 0.5rem;
                font-size: 0.875rem;
                margin-bottom: 1rem;
                display: none;
            }
            .alert-success {
                background-color: #d1fae5;
                color: #065f46;
                border: 1px solid #a7f3d0;
                display: block;
                word-break: break-all;
            }
            .alert-error {
                background-color: #fee2e2;
                color: #991b1b;
                border: 1px solid #fca5a5;
                display: block;
            }
            .alert-info {
                background-color: #dbeafe;
                color: #1e40af;
                border: 1px solid #93c5fd;
                display: block;
            }
            .link-box {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 0.5rem;
                padding: 0.75rem;
                margin: 0.5rem 0;
                word-break: break-all;
                font-size: 0.875rem;
                color: #2563eb;
            }
            .link-box a {
                color: #2563eb;
                text-decoration: none;
            }
            .link-box a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="min-h-screen flex items-center justify-center p-4">
            <div class="max-w-md w-full bg-white rounded-2xl shadow-2xl p-8 border border-gray-100">
                <div class="text-center mb-6">
                    <div class="flex items-center justify-center mx-auto mb-4">
                        <img src="/static/logo2.png" alt="Logo" class="h-20 w-auto object-contain">
                    </div>
                    <h1 class="text-2xl font-bold text-primary" style="color: #0d1b3e;">Recuperar Contraseña</h1>
                    <p class="text-gray-600 mt-2 text-sm">Ingresa tu email para recibir tu enlace</p>
                </div>
                
                <div id="mensajeContainer"></div>
                
                <form action="/auth/solicitar-recuperacion" method="post" class="space-y-4">
                    <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-2 tracking-wider">Email</label>
                        <div class="relative">
                            <span class="absolute top-1/2 left-3 -translate-y-1/2 text-slate-400">
                                <i class="fas fa-envelope"></i>
                            </span>
                            <input type="email" name="email" required 
                                   class="w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition duration-200"
                                   placeholder="tu@email.com">
                        </div>
                    </div>
                    
                    <button type="submit" 
                            class="w-full bg-slate-900 hover:bg-cyan-600 text-white font-bold py-3 rounded-lg transition duration-300 shadow-lg flex items-center justify-center gap-2">
                        <i class="fas fa-paper-plane"></i> Generar enlace
                    </button>
                </form>
                
                <div class="mt-4 text-center">
                    <a href="/login" class="text-sm text-indigo-600 hover:underline transition duration-200">
                        <i class="fas fa-arrow-left"></i> Volver al inicio de sesión
                    </a>
                </div>
            </div>
        </div>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const urlParams = new URLSearchParams(window.location.search);
                const success = urlParams.get('success');
                const error = urlParams.get('error');
                const container = document.getElementById('mensajeContainer');
                
                if (success) {
                    // Si el mensaje contiene un enlace, mostrarlo bonito
                    const msg = decodeURIComponent(success);
                    if (msg.includes('http')) {
                        container.innerHTML = `
                            <div class="alert alert-success">
                                <p class="font-medium mb-2">✅ Enlace de recuperación generado:</p>
                                <div class="link-box">
                                    <a href="${msg}" target="_blank">${msg}</a>
                                </div>
                                <p class="text-xs text-gray-500 mt-2">
                                    <i class="fas fa-clock"></i> Este enlace expirará en 15 minutos
                                </p>
                                <p class="text-xs text-gray-500 mt-1">
                                    <i class="fas fa-info-circle"></i> Haz clic en el enlace para restablecer tu contraseña
                                </p>
                            </div>
                        `;
                    } else {
                        container.innerHTML = `<div class="alert alert-success">✅ ${msg}</div>`;
                    }
                } else if (error) {
                    container.innerHTML = `<div class="alert alert-error">❌ ${decodeURIComponent(error)}</div>`;
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

# ============================================================
# POST: SOLICITAR RECUPERACIÓN (MUESTRA EL ENLACE EN LA PÁGINA)
# ============================================================
@router.post("/solicitar-recuperacion")
async def solicitar_recuperacion(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    email = form.get("email")
    
    print(f"📧 Solicitud de recuperación para: {email}")
    
    if not email:
        return RedirectResponse(
            url="/auth/olvide-contrasena?error=Email es requerido", 
            status_code=303
        )
    
    # Buscar usuario por email
    result = await db.execute(select(Usuario).where(Usuario.email == email))
    usuario = result.scalar_one_or_none()
    
    if not usuario:
        print(f"⚠️ Email no registrado: {email}")
        return RedirectResponse(
            url="/auth/olvide-contrasena?error=Email no registrado",
            status_code=303
        )
    
    # Generar token
    token = secrets.token_urlsafe(32)
    reset_tokens[token] = {
        "usuario_id": usuario.id,
        "expira": datetime.now() + timedelta(minutes=15)
    }
    
    # Construir URL de recuperación
    reset_url = f"{settings.BASE_URL}/auth/restablecer-contrasena?token={token}"
    
    print(f"🔑 Enlace generado para {usuario.nombre}: {reset_url}")
    
    # 🔥 REDIRIGIR CON EL ENLACE EN EL MENSAJE
    return RedirectResponse(
        url=f"/auth/olvide-contrasena?success={reset_url}",
        status_code=303
    )

# ============================================================
# GET: RESTABLECER CONTRASEÑA (mostrar formulario)
# ============================================================
@router.get("/restablecer-contrasena", response_class=HTMLResponse)
async def restablecer_contrasena(request: Request, token: str = None):
    print(f"🔍 Token recibido: {token}")
    
    if not token or token not in reset_tokens:
        return RedirectResponse(
            url="/auth/olvide-contrasena?error=Token inválido o expirado", 
            status_code=303
        )
    
    token_data = reset_tokens[token]
    if datetime.now() > token_data["expira"]:
        del reset_tokens[token]
        return RedirectResponse(
            url="/auth/olvide-contrasena?error=El enlace ha expirado", 
            status_code=303
        )
    
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Nueva Contraseña - SGOAP</title>
        <link rel="icon" type="image/x-icon" href="/static/logo2.ico">
        <link rel="shortcut icon" href="/static/logo2.ico">
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
        <style>
            body {{
                background: linear-gradient(135deg, #0d1b3e 0%, #1e293b 100%);
                min-height: 100vh;
            }}
            .alert {{
                padding: 0.75rem 1rem;
                border-radius: 0.5rem;
                font-size: 0.875rem;
                margin-bottom: 1rem;
                display: none;
            }}
            .alert-error {{
                background-color: #fee2e2;
                color: #991b1b;
                border: 1px solid #fca5a5;
                display: block;
            }}
            .password-strength {{
                height: 4px;
                margin-top: 0.5rem;
                border-radius: 4px;
                background: #e5e7eb;
                overflow: hidden;
            }}
            .password-strength-bar {{
                height: 100%;
                width: 0%;
                border-radius: 4px;
                transition: width 0.3s ease;
            }}
            input.error {{
                border-color: #dc2626 !important;
            }}
            input.success {{
                border-color: #16a34a !important;
            }}
        </style>
    </head>
    <body>
        <div class="min-h-screen flex items-center justify-center p-4">
            <div class="max-w-md w-full bg-white rounded-2xl shadow-2xl p-8 border border-gray-100">
                <div class="text-center mb-6">
                    <div class="flex items-center justify-center mx-auto mb-4">
                        <img src="/static/logo2.png" alt="Logo" class="h-20 w-auto object-contain">
                    </div>
                    <h1 class="text-2xl font-bold text-primary" style="color: #0d1b3e;">Nueva Contraseña</h1>
                    <p class="text-gray-600 mt-2 text-sm">Ingresa tu nueva contraseña</p>
                </div>
                
                <div id="mensajeContainer"></div>
                
                <form id="formRestablecer" action="/auth/restablecer-contrasena" method="post" class="space-y-4">
                    <input type="hidden" name="token" value="{token}">
                    
                    <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-2 tracking-wider">Nueva Contraseña</label>
                        <div class="relative">
                            <span class="absolute top-1/2 left-3 -translate-y-1/2 text-slate-400">
                                <i class="fas fa-lock"></i>
                            </span>
                            <input type="password" id="password" name="password" required 
                                   class="w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition duration-200"
                                   placeholder="Mínimo 6 caracteres" minlength="6">
                        </div>
                        <div class="password-strength">
                            <div id="password-strength-bar" class="password-strength-bar"></div>
                        </div>
                        <div id="password-error" class="text-red-600 text-xs mt-1 hidden">
                            <i class="fas fa-times-circle"></i> La contraseña debe tener al menos 6 caracteres
                        </div>
                    </div>
                    
                    <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-2 tracking-wider">Confirmar Contraseña</label>
                        <div class="relative">
                            <span class="absolute top-1/2 left-3 -translate-y-1/2 text-slate-400">
                                <i class="fas fa-check-circle"></i>
                            </span>
                            <input type="password" id="confirm_password" name="confirm_password" required 
                                   class="w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition duration-200"
                                   placeholder="Repite la contraseña" minlength="6">
                        </div>
                        <div id="confirm-error" class="text-red-600 text-xs mt-1 hidden">
                            <i class="fas fa-times-circle"></i> Las contraseñas no coinciden
                        </div>
                    </div>
                    
                    <button type="submit" 
                            class="w-full bg-slate-900 hover:bg-cyan-600 text-white font-bold py-3 rounded-lg transition duration-300 shadow-lg flex items-center justify-center gap-2">
                        <i class="fas fa-save"></i> Restablecer Contraseña
                    </button>
                </form>
                
                <div class="mt-4 text-center">
                    <a href="/login" class="text-sm text-indigo-600 hover:underline transition duration-200">
                        <i class="fas fa-arrow-left"></i> Volver al inicio de sesión
                    </a>
                </div>
            </div>
        </div>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const urlParams = new URLSearchParams(window.location.search);
                const error = urlParams.get('error');
                const container = document.getElementById('mensajeContainer');
                
                if (error) {{
                    container.innerHTML = `<div class="alert alert-error">❌ ${{decodeURIComponent(error)}}</div>`;
                }}
                
                // 🔥 Validación de contraseña en tiempo real
                const passwordInput = document.getElementById('password');
                const confirmInput = document.getElementById('confirm_password');
                const strengthBar = document.getElementById('password-strength-bar');
                const passwordError = document.getElementById('password-error');
                const confirmError = document.getElementById('confirm-error');
                
                passwordInput.addEventListener('input', function() {{
                    const password = this.value;
                    
                    // Validar mínimo 6 caracteres
                    if (password.length > 0 && password.length < 6) {{
                        passwordError.classList.remove('hidden');
                        this.classList.add('error');
                    }} else {{
                        passwordError.classList.add('hidden');
                        this.classList.remove('error');
                    }}
                    
                    // Calcular fuerza
                    let strength = 0;
                    if (password.length >= 6) strength += 20;
                    if (password.length >= 10) strength += 20;
                    if (/[a-z]/.test(password)) strength += 20;
                    if (/[A-Z]/.test(password)) strength += 20;
                    if (/[0-9]/.test(password)) strength += 10;
                    if (/[^a-zA-Z0-9]/.test(password)) strength += 10;
                    strength = Math.min(strength, 100);
                    
                    let color = '#e5e7eb';
                    if (strength < 30) color = '#dc2626';
                    else if (strength < 50) color = '#f59e0b';
                    else if (strength < 70) color = '#3b82f6';
                    else color = '#16a34a';
                    
                    strengthBar.style.width = strength + '%';
                    strengthBar.style.background = color;
                    
                    // Verificar confirmación
                    if (confirmInput.value.length > 0) {{
                        checkConfirm();
                    }}
                }});
                
                function checkConfirm() {{
                    const password = document.getElementById('password').value;
                    const confirm = document.getElementById('confirm_password').value;
                    
                    if (confirm.length === 0) {{
                        confirmError.classList.add('hidden');
                        return;
                    }}
                    
                    if (password !== confirm) {{
                        confirmError.classList.remove('hidden');
                        confirmInput.classList.add('error');
                    }} else {{
                        confirmError.classList.add('hidden');
                        confirmInput.classList.remove('error');
                        confirmInput.classList.add('success');
                    }}
                }}
                
                confirmInput.addEventListener('input', checkConfirm);
                
                // 🔥 Validación final antes de enviar
                document.getElementById('formRestablecer').addEventListener('submit', function(e) {{
                    const password = document.getElementById('password').value;
                    const confirm = document.getElementById('confirm_password').value;
                    const container = document.getElementById('mensajeContainer');
                    container.innerHTML = '';
                    
                    if (password.length < 6) {{
                        e.preventDefault();
                        container.innerHTML = `<div class="alert alert-error">❌ La contraseña debe tener al menos 6 caracteres</div>`;
                        document.getElementById('password').focus();
                        return;
                    }}
                    
                    if (password !== confirm) {{
                        e.preventDefault();
                        container.innerHTML = `<div class="alert alert-error">❌ Las contraseñas no coinciden</div>`;
                        document.getElementById('confirm_password').focus();
                        return;
                    }}
                }});
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

# ============================================================
# POST: RESTABLECER CONTRASEÑA (actualizar)
# ============================================================
@router.post("/restablecer-contrasena")
async def actualizar_contrasena(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    token = form.get("token")
    password = form.get("password")
    confirm_password = form.get("confirm_password")
    
    print(f"🔄 Intentando restablecer contraseña...")
    
    # Validar token
    if not token or token not in reset_tokens:
        return RedirectResponse(
            url="/auth/olvide-contrasena?error=Token inválido", 
            status_code=303
        )
    
    # Validar contraseña
    if not password or len(password) < 6:
        return RedirectResponse(
            url=f"/auth/restablecer-contrasena?token={token}&error=La contraseña debe tener al menos 6 caracteres",
            status_code=303
        )
    
    if password != confirm_password:
        return RedirectResponse(
            url=f"/auth/restablecer-contrasena?token={token}&error=Las contraseñas no coinciden",
            status_code=303
        )
    
    # Verificar expiración
    token_data = reset_tokens[token]
    if datetime.now() > token_data["expira"]:
        del reset_tokens[token]
        return RedirectResponse(
            url="/auth/olvide-contrasena?error=El enlace ha expirado", 
            status_code=303
        )
    
    # Actualizar contraseña
    result = await db.execute(select(Usuario).where(Usuario.id == token_data["usuario_id"]))
    usuario = result.scalar_one_or_none()
    
    if not usuario:
        return RedirectResponse(
            url="/auth/olvide-contrasena?error=Usuario no encontrado", 
            status_code=303
        )
    
    # Hashear y guardar nueva contraseña
    usuario.hashed_password = hash_password(password)
    await db.commit()
    
    # Eliminar token usado
    del reset_tokens[token]
    
    print(f"✅ Contraseña actualizada para: {usuario.email}")
    
    return RedirectResponse(
        url="/login?success=Contraseña actualizada correctamente", 
        status_code=303
    )
    