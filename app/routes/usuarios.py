# app/routes/usuarios.py - VERSIÓN COMPLETA CON VALIDACIONES
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Usuario, Empleado
from app.auth import hash_password
import re

# 🔥 IMPORTAR LA FUNCIÓN CORRECTA DESDE AUTH.PY
from app.auth import get_current_user_from_session

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

# 🔥 ALIAS para mantener compatibilidad con el código existente
get_current_user = get_current_user_from_session


# ============================================================
# ENDPOINT PARA VERIFICAR USERNAME (VALIDACIÓN EN TIEMPO REAL)
# ============================================================
@router.get("/verificar-username")
async def verificar_username(username: str, db: AsyncSession = Depends(get_db)):
    """Verifica si un username ya existe (para validación en tiempo real)"""
    result = await db.execute(select(Usuario).where(Usuario.username == username))
    existe = result.scalar_one_or_none() is not None
    return {"exists": existe}


# ============================================================
# ENDPOINT PARA OBTENER EMPLEADOS ACTIVOS
# ============================================================
@router.get("/api/empleados/activos")
async def get_empleados_activos(db: AsyncSession = Depends(get_db)):
    """Obtiene empleados activos para el selector"""
    result = await db.execute(
        select(Empleado).where(Empleado.activo == True).order_by(Empleado.nombre_completo)
    )
    empleados = result.scalars().all()
    return [
        {
            "id": e.id,
            "nombre_completo": e.nombre_completo,
            "tipo_contrato": e.tipo_contrato
        }
        for e in empleados
    ]


# ============================================================
# LISTAR USUARIOS
# ============================================================
@router.get("/", response_class=HTMLResponse)
async def listar_usuarios(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user or user.rol != "administrador":
        return RedirectResponse(url="/dashboard", status_code=303)
    
    # Obtener todos los usuarios
    result = await db.execute(select(Usuario))
    usuarios = result.scalars().all()
    
    # Obtener todos los empleados para el selector
    result_emp = await db.execute(select(Empleado))
    empleados = result_emp.scalars().all()
    
    html = """<!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gestión de Usuarios</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    </head>
    <body class="bg-gray-50">
        <div class="container mx-auto px-4 py-8">
            <div class="flex justify-between items-center mb-8">
                <h1 class="text-2xl font-bold text-gray-800">Gestion de Usuarios</h1>
                <button id="btnNuevoUsuario" class="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition duration-200 flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Nuevo Usuario
                </button>
            </div>

            <!-- Tabla de usuarios -->
            <div class="bg-white shadow-md rounded-lg overflow-hidden">
                <div class="px-6 py-4 border-b border-gray-200">
                    <div class="flex flex-col md:flex-row md:items-center md:justify-between">
                        <div class="mb-3 md:mb-0">
                            <h2 class="text-lg font-semibold text-gray-700">Lista de Usuarios</h2>
                        </div>
                        <div class="relative">
                            <input type="text" id="searchUsuarios" placeholder="Buscar usuarios..." 
                                   class="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400 absolute left-3 top-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                        </div>
                    </div>
                </div>
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Username</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rol</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Empleado</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                            </tr>
                        </thead>
                        <tbody id="tablaUsuarios" class="bg-white divide-y divide-gray-200">"""
    
    for u in usuarios:
        # Buscar empleado asociado
        empleado_nombre = "Externo"
        if u.empleado_id:
            emp = next((e for e in empleados if e.id == u.empleado_id), None)
            empleado_nombre = emp.nombre_completo if emp else "No encontrado"
        
        rol_label = "Administrador" if u.rol == "administrador" else "Operativo"
        estado_label = "Activo" if u.activo else "Inactivo"
        estado_color = "text-green-600" if u.activo else "text-red-600"
        
        html += f"""
                            <tr>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{u.nombre}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{u.username}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{u.email or '-'}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    <span class="px-2 py-1 rounded-full text-xs {'bg-purple-100 text-purple-800' if u.rol == 'administrador' else 'bg-blue-100 text-blue-800'}">
                                        {rol_label}
                                    </span>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{empleado_nombre}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    <span class="{estado_color}">{estado_label}</span>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <a href="/usuarios/{u.id}/editar" class="text-blue-600 hover:text-blue-900 mr-2" title="Editar">
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                        </svg>
                                    </a>
                                    <button class="btn-reset-password text-yellow-600 hover:text-yellow-900 mr-2" data-id="{u.id}" title="Restablecer contraseña">
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                                        </svg>
                                    </button>
                                    <form action="/usuarios/{u.id}/eliminar" method="post" class="inline" onsubmit="return confirm('¿Estas seguro de eliminar este usuario?')">
                                        <button type="submit" class="text-red-600 hover:text-red-900" title="Eliminar">
                                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                            </svg>
                                        </button>
                                    </form>
                                </td>
                            </tr>"""
    
    html += """
                        </tbody>
                    </table>
                </div>
                <div class="px-6 py-4 bg-gray-50 border-t border-gray-200">
                    <div class="flex items-center justify-between">
                        <p class="text-sm text-gray-700">
                            Mostrando todos los usuarios
                        </p>
                    </div>
                </div>
            </div>
            <div class="mt-6">
                <a href="/dashboard" class="text-indigo-600 hover:underline">← Volver al Dashboard</a>
            </div>
        </div>

        <!-- Modal para crear usuario -->
        <div id="modalUsuario" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full hidden z-50">
            <div class="relative top-20 mx-auto p-5 border w-11/12 md:w-3/5 lg:w-1/2 shadow-lg rounded-md bg-white">
                <div class="mt-3 text-center">
                    <h3 id="tituloModal" class="text-lg font-medium text-gray-900 mb-4">Crear Nuevo Usuario</h3>
                    <div class="mt-2 px-7 py-3">
                        <form id="formUsuario" action="/usuarios/crear" method="post" class="space-y-4">
                            <input type="hidden" id="usuarioId" name="usuario_id">
                            
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <!-- SELECTOR DE EMPLEADOS -->
                                <div class="md:col-span-2">
                                    <label for="empleadoId" class="block text-left text-sm font-medium text-gray-700">Empleado Asociado</label>
                                    <select id="empleadoId" name="empleado_id"
                                            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500">
                                        <option value="">Ninguno (usuario externo)</option>"""
    
    # Agregar empleados al selector
    for emp in empleados:
        html += f'                                        <option value="{emp.id}">{emp.nombre_completo} - {emp.tipo_contrato}</option>\n'
    
    html += """
                                    </select>
                                    <p class="mt-1 text-xs text-gray-500">Seleccione un empleado si el usuario pertenece a la empresa</p>
                                </div>
                                
                                <div>
                                    <label for="nombre" class="block text-left text-sm font-medium text-gray-700">Nombre Completo</label>
                                    <input type="text" id="nombre" name="nombre" required
                                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500">
                                </div>
                                
                                <div>
                                    <label for="username" class="block text-left text-sm font-medium text-gray-700">Username</label>
                                    <input type="text" id="username" name="username" required
                                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500">
                                </div>
                                
                                <div>
                                    <label for="email" class="block text-left text-sm font-medium text-gray-700">Email</label>
                                    <input type="email" id="email" name="email"
                                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500">
                                    <p class="mt-1 text-xs text-gray-500">Opcional</p>
                                </div>
                                
                                <div>
                                    <label for="rol" class="block text-left text-sm font-medium text-gray-700">Rol</label>
                                    <select id="rol" name="rol" required
                                            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500">
                                        <option value="administrador">Administrador</option>
                                        <option value="operativo" selected>Operativo</option>
                                        <option value="contable">Contable</option>
                                    </select>
                                </div>
                                
                                <div>
                                    <label for="password" class="block text-left text-sm font-medium text-gray-700">Contraseña</label>
                                    <input type="password" id="password" name="password" required
                                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500">
                                    <p class="mt-1 text-xs text-gray-500">Minimo 6 caracteres</p>
                                </div>
                                
                                <div>
                                    <label for="activo" class="block text-left text-sm font-medium text-gray-700">Estado</label>
                                    <select id="activo" name="activo"
                                            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500">
                                        <option value="1">Activo</option>
                                        <option value="0">Inactivo</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="mt-5 sm:mt-6 flex justify-end space-x-3">
                                <button type="button" id="btnCancelar" 
                                        class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none">
                                    Cancelar
                                </button>
                                <button type="submit" id="btnGuardar" 
                                        class="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none">
                                    Guardar Usuario
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal para resetear contraseña -->
        <div id="modalResetPassword" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full hidden z-50">
            <div class="relative top-20 mx-auto p-5 border w-11/12 md:w-2/5 lg:w-1/3 shadow-lg rounded-md bg-white">
                <div class="mt-3">
                    <h3 class="text-lg font-medium text-gray-900 mb-4 text-center">Restablecer Contraseña</h3>
                    <div class="mt-2 px-7 py-3">
                        <form id="formResetPassword" action="/usuarios/reset-password" method="post" class="space-y-4">
                            <input type="hidden" id="resetUsuarioId" name="usuario_id">
                            
                            <div class="text-center">
                                <p class="text-sm text-gray-600 mb-4">
                                    ¿Estas seguro de restablecer la contraseña del usuario?
                                </p>
                                <p id="resetNombreUsuario" class="text-sm font-medium text-gray-800 mb-4"></p>
                            </div>
                            
                            <div>
                                <label for="nuevaPassword" class="block text-left text-sm font-medium text-gray-700">Nueva Contraseña</label>
                                <input type="password" id="nuevaPassword" name="nueva_password" required
                                       class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                                       placeholder="Ingrese nueva contraseña (minimo 6 caracteres)">
                            </div>
                            
                            <div>
                                <label for="confirmarPassword" class="block text-left text-sm font-medium text-gray-700">Confirmar Contraseña</label>
                                <input type="password" id="confirmarPassword" name="confirmar_password" required
                                       class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                                       placeholder="Confirme la nueva contraseña">
                            </div>
                            
                            <div class="mt-5 sm:mt-6 flex justify-end space-x-3">
                                <button type="button" id="btnCancelarReset" 
                                        class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none">
                                    Cancelar
                                </button>
                                <button type="submit" id="btnGuardarReset" 
                                        class="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-yellow-600 hover:bg-yellow-700 focus:outline-none">
                                    Restablecer Contraseña
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>

        <script>
            document.addEventListener('DOMContentLoaded', function() {
                // Elementos del DOM
                const modalUsuario = document.getElementById('modalUsuario');
                const modalResetPassword = document.getElementById('modalResetPassword');
                const btnNuevoUsuario = document.getElementById('btnNuevoUsuario');
                const btnCancelar = document.getElementById('btnCancelar');
                const btnCancelarReset = document.getElementById('btnCancelarReset');
                const formUsuario = document.getElementById('formUsuario');
                
                // Función para abrir modal de nuevo usuario
                btnNuevoUsuario.addEventListener('click', function() {
                    document.getElementById('tituloModal').textContent = 'Crear Nuevo Usuario';
                    document.getElementById('btnGuardar').textContent = 'Crear Usuario';
                    document.getElementById('usuarioId').value = '';
                    document.getElementById('password').required = true;
                    document.getElementById('password').placeholder = 'Ingrese contraseña';
                    document.getElementById('password').value = '';
                    formUsuario.reset();
                    modalUsuario.classList.remove('hidden');
                    document.getElementById('nombre').focus();
                });
                
                // Función para cerrar modal
                function cerrarModal() {
                    modalUsuario.classList.add('hidden');
                }
                
                function cerrarModalReset() {
                    modalResetPassword.classList.add('hidden');
                }
                
                btnCancelar.addEventListener('click', cerrarModal);
                btnCancelarReset.addEventListener('click', cerrarModalReset);
                
                // Cerrar modales al hacer clic fuera
                modalUsuario.addEventListener('click', function(e) {
                    if (e.target === this) cerrarModal();
                });
                
                modalResetPassword.addEventListener('click', function(e) {
                    if (e.target === this) cerrarModalReset();
                });
                
                // Autocompletar al seleccionar empleado
                document.getElementById('empleadoId').addEventListener('change', function() {
                    const nombreInput = document.getElementById('nombre');
                    const usernameInput = document.getElementById('username');
                    const emailInput = document.getElementById('email');
                    
                    if (this.value) {
                        const option = this.options[this.selectedIndex];
                        const texto = option.textContent;
                        const nombre = texto.split(' - ')[0];
                        if (nombre && !nombreInput.value) {
                            nombreInput.value = nombre;
                            const username = nombre.toLowerCase()
                                .normalize('NFD')
                                .replace(/[\u0300-\u036f]/g, '')
                                .replace(/ñ/g, 'n')
                                .replace(/[^a-z0-9]/g, '.')
                                .replace(/\.+/g, '.')
                                .replace(/^\.|\.$/g, '');
                            usernameInput.value = username;
                            // Disparar evento para validar
                            usernameInput.dispatchEvent(new Event('input'));
                            if (!emailInput.value) {
                                emailInput.value = username + '@empresa.com';
                            }
                        }
                    }
                });
                
                // 🔥 VALIDACIÓN DE USERNAME EN TIEMPO REAL
                const usernameInput = document.getElementById('username');
                const usernameStatus = document.createElement('div');
                usernameStatus.id = 'username-status';
                usernameStatus.className = 'text-xs mt-1 hidden';
                usernameInput.parentNode.parentNode.appendChild(usernameStatus);
                
                usernameInput.addEventListener('input', function() {
                    const username = this.value;
                    const statusDiv = document.getElementById('username-status');
                    
                    if (username.length === 0) {
                        statusDiv.className = 'text-xs mt-1 hidden';
                        this.classList.remove('error', 'success');
                        return;
                    }
                    
                    // Validar caracteres permitidos
                    const validPattern = /^[a-zA-Z0-9_.-]+$/;
                    if (!validPattern.test(username)) {
                        statusDiv.className = 'text-xs mt-1 text-red-600';
                        statusDiv.innerHTML = '<i class="fas fa-times-circle"></i> Solo letras, números, puntos, guiones y guiones bajos';
                        this.classList.add('error');
                        this.classList.remove('success');
                        return;
                    }
                    
                    // Verificar si el username ya existe
                    checkUsernameExists(username);
                });
                
                async function checkUsernameExists(username) {
                    const statusDiv = document.getElementById('username-status');
                    const input = document.getElementById('username');
                    
                    try {
                        const response = await fetch(`/usuarios/verificar-username?username=${encodeURIComponent(username)}`);
                        const data = await response.json();
                        
                        if (data.exists) {
                            statusDiv.className = 'text-xs mt-1 text-red-600';
                            statusDiv.innerHTML = '<i class="fas fa-times-circle"></i> Este username ya está en uso';
                            input.classList.add('error');
                            input.classList.remove('success');
                        } else {
                            statusDiv.className = 'text-xs mt-1 text-green-600';
                            statusDiv.innerHTML = '<i class="fas fa-check-circle"></i> Username disponible';
                            input.classList.remove('error');
                            input.classList.add('success');
                        }
                    } catch (error) {
                        console.error('Error verificando username:', error);
                    }
                }
                
                // 🔥 VALIDACIÓN DE EMAIL
                const emailInput = document.getElementById('email');
                const emailError = document.createElement('div');
                emailError.id = 'email-error';
                emailError.className = 'field-error text-red-600 text-xs mt-1 hidden';
                emailInput.parentNode.parentNode.appendChild(emailError);
                
                emailInput.addEventListener('blur', function() {
                    const email = this.value;
                    const errorDiv = document.getElementById('email-error');
                    
                    if (email.length === 0) {
                        errorDiv.classList.add('hidden');
                        this.classList.remove('error', 'success');
                        return;
                    }
                    
                    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailPattern.test(email)) {
                        errorDiv.classList.remove('hidden');
                        errorDiv.innerHTML = '<i class="fas fa-times-circle"></i> Email inválido';
                        this.classList.add('error');
                        this.classList.remove('success');
                    } else {
                        errorDiv.classList.add('hidden');
                        this.classList.remove('error');
                        this.classList.add('success');
                    }
                });
                
                // 🔥 VALIDACIÓN DE CONTRASEÑA
                const passwordInput = document.getElementById('password');
                const passwordError = document.createElement('div');
                passwordError.id = 'password-error';
                passwordError.className = 'field-error text-red-600 text-xs mt-1 hidden';
                passwordInput.parentNode.parentNode.appendChild(passwordError);
                
                passwordInput.addEventListener('input', function() {
                    const password = this.value;
                    const errorDiv = document.getElementById('password-error');
                    
                    if (password.length > 0 && password.length < 6) {
                        errorDiv.classList.remove('hidden');
                        errorDiv.innerHTML = '<i class="fas fa-times-circle"></i> La contraseña debe tener al menos 6 caracteres';
                        this.classList.add('error');
                    } else {
                        errorDiv.classList.add('hidden');
                        this.classList.remove('error');
                        if (password.length >= 6) {
                            this.classList.add('success');
                        }
                    }
                });
                
                // 🔥 VALIDACIÓN DE CONFIRMACIÓN DE CONTRASEÑA
                const confirmInput = document.getElementById('confirmarPassword');
                const confirmError = document.createElement('div');
                confirmError.id = 'confirmar-error';
                confirmError.className = 'field-error text-red-600 text-xs mt-1 hidden';
                confirmInput.parentNode.parentNode.appendChild(confirmError);
                
                confirmInput.addEventListener('input', function() {
                    const password = document.getElementById('password').value;
                    const confirmar = this.value;
                    const errorDiv = document.getElementById('confirmar-error');
                    
                    if (confirmar.length === 0) {
                        errorDiv.classList.add('hidden');
                        this.classList.remove('error', 'success');
                        return;
                    }
                    
                    if (password !== confirmar) {
                        errorDiv.classList.remove('hidden');
                        errorDiv.innerHTML = '<i class="fas fa-times-circle"></i> Las contraseñas no coinciden';
                        this.classList.add('error');
                        this.classList.remove('success');
                    } else {
                        errorDiv.classList.add('hidden');
                        this.classList.remove('error');
                        this.classList.add('success');
                    }
                });
                
                // Botones de reset password
                document.querySelectorAll('.btn-reset-password').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const id = this.dataset.id;
                        document.getElementById('resetUsuarioId').value = id;
                        const row = this.closest('tr');
                        const nombre = row.querySelector('td:first-child').textContent;
                        document.getElementById('resetNombreUsuario').textContent = 'Usuario: ' + nombre;
                        modalResetPassword.classList.remove('hidden');
                        document.getElementById('nuevaPassword').focus();
                    });
                });
                
                // Buscar usuarios
                const searchInput = document.getElementById('searchUsuarios');
                searchInput.addEventListener('input', function() {
                    const filter = this.value.toLowerCase();
                    const rows = document.querySelectorAll('#tablaUsuarios tr');
                    rows.forEach(row => {
                        const text = row.textContent.toLowerCase();
                        row.style.display = text.includes(filter) ? '' : 'none';
                    });
                });
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)


# ============================================================
# FORMULARIO CREAR USUARIO (PÁGINA INDEPENDIENTE)
# ============================================================
@router.get("/nuevo", response_class=HTMLResponse)
async def formulario_crear(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user or user.rol != "administrador":
        return RedirectResponse(url="/dashboard", status_code=303)
    
    # Obtener empleados para el selector
    result_emp = await db.execute(select(Empleado))
    empleados = result_emp.scalars().all()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Crear Usuario</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    </head>
    <body class="bg-gray-100">
        <div class="max-w-md mx-auto mt-20 bg-white p-8 rounded-xl shadow-lg">
            <h1 class="text-2xl font-bold text-indigo-600 mb-6">Crear Usuario</h1>
            <form action="/usuarios/crear" method="post">
                <div class="mb-4">
                    <label class="block font-bold mb-2">Empleado Asociado</label>
                    <select name="empleado_id" class="w-full px-3 py-2 border rounded-lg">
                        <option value="">Ninguno (usuario externo)</option>"""
    
    for emp in empleados:
        html += f'                        <option value="{emp.id}">{emp.nombre_completo}</option>\n'
    
    html += """
                    </select>
                </div>
                <div class="mb-4">
                    <label class="block font-bold mb-2">Nombre</label>
                    <input type="text" name="nombre" required class="w-full px-3 py-2 border rounded-lg">
                </div>
                <div class="mb-4">
                    <label class="block font-bold mb-2">Usuario</label>
                    <input type="text" name="username" required class="w-full px-3 py-2 border rounded-lg">
                </div>
                <div class="mb-4">
                    <label class="block font-bold mb-2">Email</label>
                    <input type="email" name="email" class="w-full px-3 py-2 border rounded-lg">
                    <p class="text-xs text-gray-500 mt-1">Opcional</p>
                </div>
                <div class="mb-4">
                    <label class="block font-bold mb-2">Contraseña</label>
                    <input type="password" name="password" required class="w-full px-3 py-2 border rounded-lg">
                    <p class="text-xs text-gray-500 mt-1">Minimo 6 caracteres</p>
                </div>
                <div class="mb-6">
                    <label class="block font-bold mb-2">Rol</label>
                    <select name="rol" class="w-full px-3 py-2 border rounded-lg">
                        <option value="operativo">Operativo</option>
                        <option value="contable">Contable</option>
                        <option value="administrador">Administrador</option>
                    </select>
                </div>
                <button type="submit" class="w-full bg-indigo-600 text-white py-2 rounded-lg font-bold">Crear</button>
            </form>
            <a href="/usuarios" class="block text-center text-indigo-600 mt-4">← Volver</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(html)


# ============================================================
# CREAR USUARIO
# ============================================================
@router.post("/crear")
async def crear_usuario(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user or user.rol != "administrador":
        return RedirectResponse(url="/dashboard", status_code=303)
    
    form = await request.form()
    
    # ============================================================
    # 1. VALIDAR NOMBRE
    # ============================================================
    nombre = form.get("nombre", "").strip()
    if not nombre:
        return RedirectResponse(url="/usuarios/nuevo?error=El nombre es requerido", status_code=303)
    
    # ============================================================
    # 2. VALIDAR USERNAME
    # ============================================================
    username = form.get("username", "").strip()
    if not username:
        return RedirectResponse(url="/usuarios/nuevo?error=El username es requerido", status_code=303)
    
    # Validar caracteres permitidos
    if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
        return RedirectResponse(
            url="/usuarios/nuevo?error=Username solo puede contener letras, números, puntos, guiones y guiones bajos",
            status_code=303
        )
    
    # Verificar si el username ya existe
    result = await db.execute(select(Usuario).where(Usuario.username == username))
    if result.scalar_one_or_none():
        return RedirectResponse(url="/usuarios/nuevo?error=Username ya existe", status_code=303)
    
    # ============================================================
    # 3. VALIDAR EMAIL (si se proporcionó)
    # ============================================================
    email = form.get("email", "").strip()
    if email:
        # Validar formato email
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            return RedirectResponse(url="/usuarios/nuevo?error=Email inválido", status_code=303)
        
        # Verificar si el email ya existe
        result = await db.execute(select(Usuario).where(Usuario.email == email))
        if result.scalar_one_or_none():
            return RedirectResponse(url="/usuarios/nuevo?error=Email ya existe", status_code=303)
    else:
        email = None
    
    # ============================================================
    # 4. VALIDAR CONTRASEÑA
    # ============================================================
    password = form.get("password", "").strip()
    if not password:
        return RedirectResponse(url="/usuarios/nuevo?error=La contraseña es requerida", status_code=303)
    
    if len(password) < 6:
        return RedirectResponse(url="/usuarios/nuevo?error=La contraseña debe tener al menos 6 caracteres", status_code=303)
    
    # ============================================================
    # 5. OBTENER EMPLEADO_ID (opcional)
    # ============================================================
    empleado_id = form.get("empleado_id")
    if empleado_id:
        try:
            empleado_id = int(empleado_id)
            # Verificar que el empleado existe
            result = await db.execute(select(Empleado).where(Empleado.id == empleado_id))
            if not result.scalar_one_or_none():
                return RedirectResponse(url="/usuarios/nuevo?error=Empleado no encontrado", status_code=303)
        except ValueError:
            empleado_id = None
    else:
        empleado_id = None
    
    # ============================================================
    # 6. CREAR USUARIO
    # ============================================================
    nuevo = Usuario(
        nombre=nombre,
        username=username,
        email=email,
        hashed_password=hash_password(password),
        rol=form.get("rol", "operativo"),
        activo=True if form.get("activo") == "1" else False,
        empleado_id=empleado_id
    )
    db.add(nuevo)
    await db.commit()
    
    return RedirectResponse(url="/usuarios?success=Usuario creado correctamente", status_code=303)


# ============================================================
# EDITAR USUARIO
# ============================================================
@router.get("/{usuario_id}/editar", response_class=HTMLResponse)
async def editar_usuario(usuario_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user or user.rol != "administrador":
        return RedirectResponse(url="/dashboard", status_code=303)
    
    # Obtener el usuario
    result = await db.execute(select(Usuario).where(Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()
    
    if not usuario:
        return RedirectResponse(url="/usuarios?error=Usuario no encontrado", status_code=303)
    
    # Obtener empleados para el selector
    result_emp = await db.execute(select(Empleado))
    empleados = result_emp.scalars().all()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Editar Usuario</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    </head>
    <body class="bg-gray-100">
        <div class="max-w-md mx-auto mt-20 bg-white p-8 rounded-xl shadow-lg">
            <h1 class="text-2xl font-bold text-indigo-600 mb-6">Editar Usuario</h1>
            <form action="/usuarios/{usuario_id}/actualizar" method="post">
                <div class="mb-4">
                    <label class="block font-bold mb-2">Empleado Asociado</label>
                    <select name="empleado_id" class="w-full px-3 py-2 border rounded-lg">
                        <option value="">Ninguno (usuario externo)</option>"""
    
    for emp in empleados:
        selected = "selected" if usuario.empleado_id == emp.id else ""
        html += f'                        <option value="{emp.id}" {selected}>{emp.nombre_completo}</option>\n'
    
    html += f"""
                    </select>
                </div>
                <div class="mb-4">
                    <label class="block font-bold mb-2">Nombre</label>
                    <input type="text" name="nombre" value="{usuario.nombre}" required class="w-full px-3 py-2 border rounded-lg">
                </div>
                <div class="mb-4">
                    <label class="block font-bold mb-2">Usuario</label>
                    <input type="text" name="username" value="{usuario.username}" required class="w-full px-3 py-2 border rounded-lg">
                </div>
                <div class="mb-4">
                    <label class="block font-bold mb-2">Email</label>
                    <input type="email" name="email" value="{usuario.email or ''}" class="w-full px-3 py-2 border rounded-lg">
                    <p class="text-xs text-gray-500 mt-1">Opcional</p>
                </div>
                <div class="mb-4">
                    <label class="block font-bold mb-2">Contraseña</label>
                    <input type="password" name="password" placeholder="Dejar en blanco para mantener" class="w-full px-3 py-2 border rounded-lg">
                    <p class="text-xs text-gray-500 mt-1">Minimo 6 caracteres si se cambia</p>
                </div>
                <div class="mb-4">
                    <label class="block font-bold mb-2">Rol</label>
                    <select name="rol" class="w-full px-3 py-2 border rounded-lg">
                        <option value="operativo" {"selected" if usuario.rol == "operativo" else ""}>Operativo</option>
                        <option value="contable" {"selected" if usuario.rol == "contable" else ""}>Contable</option>
                        <option value="administrador" {"selected" if usuario.rol == "administrador" else ""}>Administrador</option>
                    </select>
                </div>
                <div class="mb-6">
                    <label class="block font-bold mb-2">Estado</label>
                    <select name="activo" class="w-full px-3 py-2 border rounded-lg">
                        <option value="1" {"selected" if usuario.activo else ""}>Activo</option>
                        <option value="0" {"selected" if not usuario.activo else ""}>Inactivo</option>
                    </select>
                </div>
                <button type="submit" class="w-full bg-indigo-600 text-white py-2 rounded-lg font-bold">Actualizar</button>
            </form>
            <a href="/usuarios" class="block text-center text-indigo-600 mt-4">← Volver</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(html)


# ============================================================
# ACTUALIZAR USUARIO
# ============================================================
@router.post("/{usuario_id}/actualizar")
async def actualizar_usuario(usuario_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user or user.rol != "administrador":
        return RedirectResponse(url="/dashboard", status_code=303)
    
    form = await request.form()
    
    # Obtener el usuario
    result = await db.execute(select(Usuario).where(Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()
    
    if not usuario:
        return RedirectResponse(url="/usuarios?error=Usuario no encontrado", status_code=303)
    
    # ============================================================
    # VALIDAR NOMBRE
    # ============================================================
    nombre = form.get("nombre", "").strip()
    if not nombre:
        return RedirectResponse(
            url=f"/usuarios/{usuario_id}/editar?error=El nombre es requerido",
            status_code=303
        )
    
    # ============================================================
    # VALIDAR USERNAME
    # ============================================================
    username = form.get("username", "").strip()
    if not username:
        return RedirectResponse(
            url=f"/usuarios/{usuario_id}/editar?error=El username es requerido",
            status_code=303
        )
    
    # Validar caracteres permitidos
    if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
        return RedirectResponse(
            url=f"/usuarios/{usuario_id}/editar?error=Username solo puede contener letras, números, puntos, guiones y guiones bajos",
            status_code=303
        )
    
    # Verificar username único (excepto el mismo usuario)
    result_check = await db.execute(
        select(Usuario).where(Usuario.username == username, Usuario.id != usuario_id)
    )
    if result_check.scalar_one_or_none():
        return RedirectResponse(
            url=f"/usuarios/{usuario_id}/editar?error=Username ya existe",
            status_code=303
        )
    
    # ============================================================
    # VALIDAR EMAIL (si se proporcionó)
    # ============================================================
    email = form.get("email", "").strip()
    if email:
        # Validar formato email
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            return RedirectResponse(
                url=f"/usuarios/{usuario_id}/editar?error=Email inválido",
                status_code=303
            )
        
        # Verificar email único (excepto el mismo usuario)
        result_check = await db.execute(
            select(Usuario).where(Usuario.email == email, Usuario.id != usuario_id)
        )
        if result_check.scalar_one_or_none():
            return RedirectResponse(
                url=f"/usuarios/{usuario_id}/editar?error=Email ya existe",
                status_code=303
            )
    else:
        email = None
    
    # ============================================================
    # VALIDAR CONTRASEÑA (si se cambia)
    # ============================================================
    nueva_password = form.get("password", "").strip()
    if nueva_password and len(nueva_password) < 6:
        return RedirectResponse(
            url=f"/usuarios/{usuario_id}/editar?error=La contraseña debe tener al menos 6 caracteres",
            status_code=303
        )
    
    # ============================================================
    # ACTUALIZAR USUARIO
    # ============================================================
    usuario.nombre = nombre
    usuario.username = username
    usuario.email = email
    usuario.rol = form.get("rol", usuario.rol)
    usuario.activo = True if form.get("activo") == "1" else False
    
    # Actualizar empleado_id (si viene vacío, se pone NULL)
    empleado_id = form.get("empleado_id")
    usuario.empleado_id = int(empleado_id) if empleado_id else None
    
    # Actualizar contraseña solo si se proporcionó
    if nueva_password:
        usuario.hashed_password = hash_password(nueva_password)
    
    await db.commit()
    return RedirectResponse(url="/usuarios?success=Usuario actualizado correctamente", status_code=303)


# ============================================================
# ELIMINAR USUARIO
# ============================================================
@router.post("/{usuario_id}/eliminar")
async def eliminar_usuario(usuario_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user or user.rol != "administrador":
        return RedirectResponse(url="/dashboard", status_code=303)
    
    result = await db.execute(select(Usuario).where(Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()
    
    if usuario and usuario.id != user.id:
        await db.delete(usuario)
        await db.commit()
        return RedirectResponse(url="/usuarios?success=Usuario eliminado correctamente", status_code=303)
    elif usuario and usuario.id == user.id:
        return RedirectResponse(url="/usuarios?error=No puedes eliminar tu propio usuario", status_code=303)
    else:
        return RedirectResponse(url="/usuarios?error=Usuario no encontrado", status_code=303)


# ============================================================
# RESTABLECER CONTRASEÑA
# ============================================================
@router.post("/reset-password")
async def reset_password(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user or user.rol != "administrador":
        return RedirectResponse(url="/dashboard", status_code=303)
    
    form = await request.form()
    usuario_id = form.get("usuario_id")
    nueva_password = form.get("nueva_password")
    
    if not usuario_id or not nueva_password or len(nueva_password) < 6:
        return RedirectResponse(url="/usuarios?error=Contraseña inválida (mínimo 6 caracteres)", status_code=303)
    
    result = await db.execute(select(Usuario).where(Usuario.id == int(usuario_id)))
    usuario = result.scalar_one_or_none()
    
    if usuario:
        usuario.hashed_password = hash_password(nueva_password)
        await db.commit()
        return RedirectResponse(url="/usuarios?success=Contraseña actualizada correctamente", status_code=303)
    else:
        return RedirectResponse(url="/usuarios?error=Usuario no encontrado", status_code=303)
