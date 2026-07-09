# app/routes/install.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Usuario
from app.auth import hash_password
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/install", tags=["Install"])

@router.get("/", response_class=HTMLResponse)
async def install_form(request: Request, db: AsyncSession = Depends(get_db)):
    # Verificar si ya hay usuarios
    result = await db.execute(select(Usuario))
    usuarios = result.scalars().all()
    
    if len(usuarios) > 0:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sistema ya instalado - SGOAP</title>
            <link rel="icon" type="image/x-icon" href="/static/logo2.ico">
            <link rel="shortcut icon" href="/static/logo2.ico">
            <script src="https://cdn.tailwindcss.com"></script>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
        </head>
        <body class="bg-gray-100" style="background: linear-gradient(135deg, #0d1b3e 0%, #1e293b 100%); min-height: 100vh;">
            <div class="min-h-screen flex items-center justify-center p-4">
                <div class="bg-white rounded-2xl shadow-2xl p-8 border border-gray-100 max-w-md w-full text-center">
                    <div class="flex items-center justify-center mx-auto mb-4">
                        <img src="/static/logo2.png" alt="Logo" class="h-20 w-auto object-contain">
                    </div>
                    <div class="text-6xl mb-4">✅</div>
                    <h1 class="text-2xl font-bold text-primary" style="color: #0d1b3e;">Sistema ya instalado</h1>
                    <p class="text-gray-600 mt-2">El sistema ya tiene usuarios registrados.</p>
                    <div class="mt-6">
                        <a href="/login" class="bg-slate-900 hover:bg-cyan-600 text-white font-bold py-3 px-6 rounded-lg transition duration-300 inline-block">
                            <i class="fas fa-sign-in-alt"></i> Ir al Login
                        </a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """)
    
    # Mostrar mensajes de error si existen
    error = request.query_params.get("error", "")
    success = request.query_params.get("success", "")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Instalación - SGOAP</title>
        <link rel="icon" type="image/x-icon" href="/static/logo2.ico">
        <link rel="shortcut icon" href="/static/logo2.ico">
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    </head>
    <body class="bg-gray-100" style="background: linear-gradient(135deg, #0d1b3e 0%, #1e293b 100%); min-height: 100vh;">
        <div class="min-h-screen flex items-center justify-center p-4">
            <div class="bg-white rounded-2xl shadow-2xl p-8 border border-gray-100 max-w-md w-full">
                <div class="text-center mb-6">
                    <div class="flex items-center justify-center mx-auto mb-4">
                        <img src="/static/logo2.png" alt="Logo" class="h-20 w-auto object-contain">
                    </div>
                    <h1 class="text-2xl font-bold text-primary" style="color: #0d1b3e;">🚀 Instalación</h1>
                    <p class="text-gray-600 text-sm mt-1">Crea el usuario administrador</p>
                </div>
                
                <div id="mensajeContainer">
    """
    
    if error:
        html += f'<div class="mb-4 p-3 bg-red-100 text-red-700 rounded-lg border border-red-200">❌ {error}</div>'
    if success:
        html += f'<div class="mb-4 p-3 bg-green-100 text-green-700 rounded-lg border border-green-200">✅ {success}</div>'
    
    html += """
                </div>
                
                <form method="POST" action="/install/crear-admin" class="space-y-4">
                    <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-2 tracking-wider">
                            <span class="text-red-500">*</span> Username
                        </label>
                        <div class="relative">
                            <span class="absolute top-1/2 left-3 -translate-y-1/2 text-slate-400">
                                <i class="fas fa-user"></i>
                            </span>
                            <input type="text" name="username" required 
                                   class="w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition duration-200"
                                   placeholder="admin">
                        </div>
                        <p class="text-xs text-gray-500 mt-1"><i class="fas fa-info-circle"></i> Nombre de usuario para iniciar sesión</p>
                    </div>
                    
                    <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-2 tracking-wider">
                            <span class="text-red-500">*</span> Nombre Completo
                        </label>
                        <div class="relative">
                            <span class="absolute top-1/2 left-3 -translate-y-1/2 text-slate-400">
                                <i class="fas fa-id-card"></i>
                            </span>
                            <input type="text" name="nombre" required 
                                   class="w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition duration-200"
                                   placeholder="Administrador del Sistema">
                        </div>
                    </div>
                    
                    <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-2 tracking-wider">Email (Opcional)</label>
                        <div class="relative">
                            <span class="absolute top-1/2 left-3 -translate-y-1/2 text-slate-400">
                                <i class="fas fa-envelope"></i>
                            </span>
                            <input type="email" name="email" 
                                   class="w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition duration-200"
                                   placeholder="admin@agencia.com">
                        </div>
                        <p class="text-xs text-gray-500 mt-1"><i class="fas fa-info-circle"></i> Opcional, necesario para recuperar contraseña</p>
                    </div>
                    
                    <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-2 tracking-wider">
                            <span class="text-red-500">*</span> Contraseña
                        </label>
                        <div class="relative">
                            <span class="absolute top-1/2 left-3 -translate-y-1/2 text-slate-400">
                                <i class="fas fa-lock"></i>
                            </span>
                            <input type="password" name="password" required minlength="6"
                                   class="w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition duration-200"
                                   placeholder="Mínimo 6 caracteres">
                        </div>
                        <p class="text-xs text-gray-500 mt-1"><i class="fas fa-info-circle"></i> Mínimo 6 caracteres</p>
                    </div>
                    
                    <button type="submit" 
                            class="w-full bg-slate-900 hover:bg-cyan-600 text-white font-bold py-3 rounded-lg transition duration-300 shadow-lg flex items-center justify-center gap-2">
                        <i class="fas fa-user-plus"></i> Crear Administrador
                    </button>
                </form>
                
                <div class="mt-4 text-center">
                    <p class="text-xs text-slate-400">
                        <i class="fas fa-shield-alt"></i> El primer usuario será el administrador del sistema
                    </p>
                </div>
            </div>
        </div>
        
        <script>
            document.querySelector('form').addEventListener('submit', function(e) {
                const password = document.querySelector('input[name="password"]').value;
                const container = document.getElementById('mensajeContainer');
                
                container.innerHTML = '';
                
                if (password.length < 6) {
                    e.preventDefault();
                    container.innerHTML = '<div class="mb-4 p-3 bg-red-100 text-red-700 rounded-lg border border-red-200">❌ La contraseña debe tener al menos 6 caracteres</div>';
                    document.querySelector('input[name="password"]').focus();
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

@router.post("/crear-admin")
async def crear_admin_install(
    request: Request,
    username: str = Form(...),
    nombre: str = Form(...),
    email: str = Form(None),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # Verificar si ya hay usuarios (seguridad)
    result = await db.execute(select(Usuario))
    usuarios = result.scalars().all()
    
    if len(usuarios) > 0:
        return RedirectResponse(url="/login", status_code=303)
    
    # Validar username
    username = username.strip().lower()
    if not username:
        return RedirectResponse(url="/install?error=El username es requerido", status_code=303)
    
    # Validar contraseña
    if len(password) < 6:
        return RedirectResponse(url="/install?error=La contraseña debe tener al menos 6 caracteres", status_code=303)
    
    # Verificar username único
    result = await db.execute(select(Usuario).where(Usuario.username == username))
    if result.scalar_one_or_none():
        return RedirectResponse(url="/install?error=El username ya existe", status_code=303)
    
    # Verificar email único (si se proporcionó)
    if email and email.strip():
        email = email.strip().lower()
        result = await db.execute(select(Usuario).where(Usuario.email == email))
        if result.scalar_one_or_none():
            return RedirectResponse(url="/install?error=El email ya existe", status_code=303)
    else:
        email = None
    
    try:
        # Crear administrador
        admin = Usuario(
            nombre=nombre.strip(),
            username=username,
            email=email,
            hashed_password=hash_password(password),
            rol="administrador",
            activo=True
        )
        db.add(admin)
        await db.commit()
        
        logger.info(f"✅ Administrador creado: {username}")
        
        mensaje = "Administrador creado exitosamente. Inicia sesión."
        if not email:
            mensaje += " (Recuerda que el email es opcional, usa el username para login)"
        
        return RedirectResponse(
            url=f"/login?success={mensaje}",
            status_code=303
        )
        
    except Exception as e:
        logger.error(f"Error creando administrador: {e}")
        return RedirectResponse(
            url=f"/install?error=Error al crear administrador: {str(e)}",
            status_code=303
        )