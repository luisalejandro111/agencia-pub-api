from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario

async def get_current_user_from_session(
    request: Request,
    db: Session = Depends(get_db)
):
    """Obtiene el usuario actual desde la sesión"""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    return user



from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Usuario
from app.auth import hash_password
import secrets
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["Auth"])

# Almacenamiento temporal para tokens de recuperación
reset_tokens = {}

@router.get("/olvide-contrasena", response_class=HTMLResponse)
async def olvide_contrasena(request: Request):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Recuperar Contraseña</title>
        <link rel="icon" type="image/x-icon" href="/static/logo2.ico">
        <link rel="shortcut icon" href="/static/logo2.ico">
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    </head>
    <body class="bg-gray-100" style="background: linear-gradient(135deg, #0d1b3e 0%, #1e293b 100%);">
        <div class="min-h-screen flex items-center justify-center p-4">
            <div class="max-w-md w-full bg-white rounded-2xl shadow-2xl p-8 border border-gray-100">
                <div class="text-center mb-6">
                    <div class="flex items-center justify-center mx-auto mb-4">
                        <img src="/static/logo2.png" alt="Logo" class="h-20 w-auto object-contain">
                    </div>
                    <h1 class="text-2xl font-bold text-primary">Recuperar Contraseña</h1>
                    <p class="text-gray-600 mt-2 text-sm">Ingresa tu email y te enviaremos un enlace para restablecer tu contraseña</p>
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
                                   class="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                                   placeholder="tu@email.com">
                        </div>
                    </div>
                    
                    <button type="submit" 
                            class="w-full bg-slate-900 hover:bg-cyan-600 text-white font-bold py-3 rounded-lg transition duration-300 shadow-lg">
                        Enviar enlace de recuperación
                    </button>
                </form>
                
                <div class="mt-4 text-center">
                    <a href="/login" class="text-sm text-indigo-600 hover:underline">← Volver al inicio de sesión</a>
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
                    container.innerHTML = `<div class="mb-4 p-3 bg-green-100 text-green-700 rounded-lg">✅ ${success}</div>`;
                } else if (error) {
                    container.innerHTML = `<div class="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">❌ ${error}</div>`;
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

@router.post("/solicitar-recuperacion")
async def solicitar_recuperacion(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    email = form.get("email")
    
    if not email:
        return RedirectResponse(url="/auth/olvide-contrasena?error=Email es requerido", status_code=303)
    
    # Buscar usuario por email
    result = await db.execute(select(Usuario).where(Usuario.email == email))
    usuario = result.scalar_one_or_none()
    
    if not usuario:
        return RedirectResponse(
            url="/auth/olvide-contrasena?success=Si el email existe, recibirás un enlace para recuperar tu contraseña",
            status_code=303
        )
    
    # Generar token único
    token = secrets.token_urlsafe(32)
    
    # Guardar token con expiración (15 minutos)
    reset_tokens[token] = {
        "usuario_id": usuario.id,
        "expira": datetime.now() + timedelta(minutes=15)
    }
    
    # En desarrollo, mostrar en consola
    reset_url = f"http://localhost:8000/auth/restablecer-contrasena?token={token}"
    print(f"\n🔑 ENLACE DE RECUPERACIÓN PARA {usuario.nombre}:")
    print(f"{reset_url}\n")
    
    return RedirectResponse(
        url=f"/auth/olvide-contrasena?success=Se ha enviado un enlace de recuperación a tu email",
        status_code=303
    )

@router.get("/restablecer-contrasena", response_class=HTMLResponse)
async def restablecer_contrasena(request: Request, token: str = None):
    if not token or token not in reset_tokens:
        return RedirectResponse(url="/auth/olvide-contrasena?error=Token inválido o expirado", status_code=303)
    
    token_data = reset_tokens[token]
    if datetime.now() > token_data["expira"]:
        del reset_tokens[token]
        return RedirectResponse(url="/auth/olvide-contrasena?error=El enlace ha expirado", status_code=303)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Restablecer Contraseña</title>
        <link rel="icon" type="image/x-icon" href="/static/logo2.ico">
        <link rel="shortcut icon" href="/static/logo2.ico">
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    </head>
    <body class="bg-gray-100" style="background: linear-gradient(135deg, #0d1b3e 0%, #1e293b 100%);">
        <div class="min-h-screen flex items-center justify-center p-4">
            <div class="max-w-md w-full bg-white rounded-2xl shadow-2xl p-8 border border-gray-100">
                <div class="text-center mb-6">
                    <div class="flex items-center justify-center mx-auto mb-4">
                        <img src="/static/logo2.png" alt="Logo" class="h-20 w-auto object-contain">
                    </div>
                    <h1 class="text-2xl font-bold text-primary">Nueva Contraseña</h1>
                    <p class="text-gray-600 mt-2 text-sm">Ingresa tu nueva contraseña</p>
                </div>
                
                <div id="mensajeContainer"></div>
                
                <form action="/auth/restablecer-contrasena" method="post" class="space-y-4">
                    <input type="hidden" name="token" value="{token}">
                    
                    <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-2 tracking-wider">Nueva Contraseña</label>
                        <div class="relative">
                            <span class="absolute top-1/2 left-3 -translate-y-1/2 text-slate-400">
                                <i class="fas fa-lock"></i>
                            </span>
                            <input type="password" id="password" name="password" required 
                                   class="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                                   placeholder="Mínimo 6 caracteres" minlength="6">
                        </div>
                    </div>
                    
                    <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-2 tracking-wider">Confirmar Contraseña</label>
                        <div class="relative">
                            <span class="absolute top-1/2 left-3 -translate-y-1/2 text-slate-400">
                                <i class="fas fa-check-circle"></i>
                            </span>
                            <input type="password" id="confirm_password" name="confirm_password" required 
                                   class="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                                   placeholder="Repite la contraseña" minlength="6">
                        </div>
                    </div>
                    
                    <button type="submit" 
                            class="w-full bg-slate-900 hover:bg-cyan-600 text-white font-bold py-3 rounded-lg transition duration-300 shadow-lg">
                        Restablecer Contraseña
                    </button>
                </form>
                
                <div class="mt-4 text-center">
                    <a href="/login" class="text-sm text-indigo-600 hover:underline">← Volver al inicio de sesión</a>
                </div>
            </div>
        </div>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const urlParams = new URLSearchParams(window.location.search);
                const error = urlParams.get('error');
                const container = document.getElementById('mensajeContainer');
                
                if (error) {{
                    container.innerHTML = `<div class="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">❌ ${{error}}</div>`;
                }}
            }});
            
            document.querySelector('form').addEventListener('submit', function(e) {{
                const password = document.getElementById('password').value;
                const confirm = document.getElementById('confirm_password').value;
                const container = document.getElementById('mensajeContainer');
                
                if (password.length < 6) {{
                    e.preventDefault();
                    container.innerHTML = `<div class="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">❌ La contraseña debe tener al menos 6 caracteres</div>`;
                    return;
                }}
                
                if (password !== confirm) {{
                    e.preventDefault();
                    container.innerHTML = `<div class="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">❌ Las contraseñas no coinciden</div>`;
                    return;
                }}
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

@router.post("/restablecer-contrasena")
async def actualizar_contrasena(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    token = form.get("token")
    password = form.get("password")
    confirm_password = form.get("confirm_password")
    
    if not token or token not in reset_tokens:
        return RedirectResponse(url="/auth/olvide-contrasena?error=Token inválido", status_code=303)
    
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
    
    token_data = reset_tokens[token]
    if datetime.now() > token_data["expira"]:
        del reset_tokens[token]
        return RedirectResponse(url="/auth/olvide-contrasena?error=El enlace ha expirado", status_code=303)
    
    result = await db.execute(select(Usuario).where(Usuario.id == token_data["usuario_id"]))
    usuario = result.scalar_one_or_none()
    
    if usuario:
        usuario.hashed_password = hash_password(password)
        await db.commit()
        del reset_tokens[token]
        return RedirectResponse(url="/login?success=Contraseña actualizada correctamente", status_code=303)
    else:
        return RedirectResponse(url="/auth/olvide-contrasena?error=Usuario no encontrado", status_code=303)