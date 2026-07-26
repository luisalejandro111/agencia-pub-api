"""
Router para gestión de Recetas de Productos
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models import RecetaProducto, RecetaMaterial, MaterialInventario

router = APIRouter(prefix="/recetas", tags=["Recetas"])
templates = Jinja2Templates(directory="app/templates")


# ============================================
# API ENDPOINTS (para autocompletar en Presupuestos y Trabajos)
# ============================================

@router.get("/api/listar")
async def api_listar_recetas(
    categoria: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """API para obtener recetas (usada por Presupuestos y Trabajos)"""
    query = (
        select(RecetaProducto)
        .options(selectinload(RecetaProducto.materiales))
        .where(RecetaProducto.activo == True)
    )
    
    if categoria:
        query = query.where(RecetaProducto.categoria == categoria)
    
    query = query.order_by(RecetaProducto.categoria, RecetaProducto.nombre)
    result = await db.execute(query)
    recetas = result.scalars().all()
    
    return [
        {
            "id": r.id,
            "nombre": r.nombre,
            "categoria": r.categoria,
            "unidad_medida": r.unidad_medida,
            "precio_sugerido": r.precio_sugerido,
            "precio_minimo": r.precio_minimo,
            "costo_total": r.costo_total,
            "materiales": [
                {
                    "nombre": m.nombre_material,
                    "cantidad": m.cantidad,
                    "unidad": m.unidad,
                    "costo_total": m.costo_total,
                }
                for m in r.materiales
            ],
        }
        for r in recetas
    ]


@router.get("/api/buscar")
async def api_buscar_receta(
    nombre: str,
    db: AsyncSession = Depends(get_db)
):
    """API para que TRABAJOS obtenga el precio de una receta por nombre"""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models import RecetaProducto
    
    result = await db.execute(
        select(RecetaProducto)
        .where(RecetaProducto.nombre.ilike(f"%{nombre}%"))
    )
    receta = result.scalars().first()
    
    if not receta:
        return {"encontrada": False, "precio": 0}
    
    return {
        "encontrada": True,
        "id": receta.id,
        "nombre": receta.nombre,
        "precio": float(receta.precio_sugerido or 0),
    }

@router.get("/api/{receta_id}")
async def api_obtener_receta(
    receta_id: int,
    db: AsyncSession = Depends(get_db)
):
    """API para obtener una receta específica"""
    result = await db.execute(
        select(RecetaProducto)
        .options(selectinload(RecetaProducto.materiales))
        .where(RecetaProducto.id == receta_id)
    )
    receta = result.scalar_one_or_none()
    
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    return {
        "id": receta.id,
        "nombre": receta.nombre,
        "categoria": receta.categoria,
        "unidad_medida": receta.unidad_medida,
        "precio_sugerido": receta.precio_sugerido,
        "precio_minimo": receta.precio_minimo,
        "costo_total": receta.costo_total,
        "ganancia_esperada": receta.ganancia_esperada,
        "margen_porcentaje": receta.margen_porcentaje,
        "materiales": [
            {
                "nombre": m.nombre_material,
                "cantidad": m.cantidad,
                "unidad": m.unidad,
                "costo_unitario": m.costo_unitario,
                "costo_total": m.costo_total,
            }
            for m in receta.materiales
        ],
    }


# ============================================
# VISTAS HTML
# ============================================

@router.get("/", response_class=HTMLResponse)
async def listar_recetas(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Listado de todas las recetas"""
    result = await db.execute(
        select(RecetaProducto)
        .options(selectinload(RecetaProducto.materiales))
        .where(RecetaProducto.activo == True)
        .order_by(RecetaProducto.categoria, RecetaProducto.nombre)
    )
    recetas = result.scalars().all()
    
    # Agrupar por categoría
    categorias = {}
    for r in recetas:
        if r.categoria not in categorias:
            categorias[r.categoria] = []
        categorias[r.categoria].append(r)
    
    return templates.TemplateResponse("recetas_listado.html", {
        "request": request,
        "recetas": recetas,
        "categorias": categorias,
        "total": len(recetas),
    })


@router.get("/nuevo", response_class=HTMLResponse)
async def nueva_receta_form(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Formulario para crear receta con materiales del inventario"""
    # Obtener materiales del inventario activos
    result = await db.execute(
        select(MaterialInventario)
        .where(MaterialInventario.activo == True)
        .order_by(MaterialInventario.nombre)
    )
    materiales_inventario = result.scalars().all()
    
    return templates.TemplateResponse("recetas_form.html", {
        "request": request,
        "receta": None,
        "editando": False,
        "materiales_inventario": materiales_inventario,
    })


@router.post("/crear")
async def crear_receta(
    request: Request,
    nombre: str = Form(...),
    unidad_medida: str = Form("unidad"),
    precio_sugerido: float = Form(0),
    descripcion: str = Form(""),
    material_inventario_id: List[int] = Form([]),
    material_cantidad: List[float] = Form([]),
    db: AsyncSession = Depends(get_db)
):
    """Crear receta BOM (Bill of Materials) vinculada al inventario"""
    
    # Validar nombre único
    existe = await db.execute(
        select(RecetaProducto).where(
            func.lower(RecetaProducto.nombre) == func.lower(nombre.strip()),
            RecetaProducto.activo == True
        )
    )
    if existe.scalar_one_or_none():
        return RedirectResponse(
            url=f"/recetas/nuevo?error=Ya+existe+una+receta+con+el+nombre+{nombre}",
            status_code=303
        )
    
    receta = RecetaProducto(
        nombre=nombre.strip(),
        categoria=None,  # Ya no usamos categoría
        unidad_medida=unidad_medida,
        precio_sugerido=precio_sugerido,
        precio_minimo=0,  # Legacy
        descripcion=descripcion,
    )
    db.add(receta)
    await db.flush()
    
    # Agregar materiales vinculados al inventario
    for i in range(len(material_inventario_id)):
        if material_inventario_id[i] and material_inventario_id[i] > 0:
            # Obtener el material del inventario
            mat_result = await db.execute(
                select(MaterialInventario).where(MaterialInventario.id == material_inventario_id[i])
            )
            mat_inv = mat_result.scalar_one_or_none()
            
            if mat_inv:
                cantidad = float(material_cantidad[i]) if i < len(material_cantidad) and material_cantidad[i] else 0
                
                material = RecetaMaterial(
                    receta_id=receta.id,
                    material_inventario_id=mat_inv.id,
                    nombre_material=mat_inv.nombre,  # Copiar nombre para compatibilidad
                    cantidad=cantidad,
                    unidad=mat_inv.unidad_medida,  # Usar unidad del inventario
                    costo_unitario=0,  # Legacy
                    costo_total=0,  # Legacy
                )
                db.add(material)
    
    await db.commit()
    return RedirectResponse(url="/recetas?success=creada", status_code=303)


@router.get("/editar/{receta_id}", response_class=HTMLResponse)
async def editar_receta_form(
    receta_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Formulario para editar receta con materiales del inventario"""
    result = await db.execute(
        select(RecetaProducto)
        .options(selectinload(RecetaProducto.materiales))
        .where(RecetaProducto.id == receta_id)
    )
    receta = result.scalar_one_or_none()
    
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    # Obtener materiales del inventario activos
    mat_result = await db.execute(
        select(MaterialInventario)
        .where(MaterialInventario.activo == True)
        .order_by(MaterialInventario.nombre)
    )
    materiales_inventario = mat_result.scalars().all()
    
    return templates.TemplateResponse("recetas_form.html", {
        "request": request,
        "receta": receta,
        "editando": True,
        "materiales_inventario": materiales_inventario,
    })


@router.post("/actualizar/{receta_id}")
async def actualizar_receta(
    receta_id: int,
    nombre: str = Form(...),
    unidad_medida: str = Form("unidad"),
    precio_sugerido: float = Form(0),
    descripcion: str = Form(""),
    material_inventario_id: List[int] = Form([]),
    material_cantidad: List[float] = Form([]),
    db: AsyncSession = Depends(get_db)
):
    """Actualizar receta BOM (Bill of Materials)"""
    result = await db.execute(
        select(RecetaProducto).where(RecetaProducto.id == receta_id)
    )
    receta = result.scalar_one_or_none()
    
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    # Validar nombre único (excepto esta misma receta)
    existe = await db.execute(
        select(RecetaProducto).where(
            func.lower(RecetaProducto.nombre) == func.lower(nombre.strip()),
            RecetaProducto.activo == True,
            RecetaProducto.id != receta_id
        )
    )
    if existe.scalar_one_or_none():
        return RedirectResponse(
            url=f"/recetas/editar/{receta_id}?error=Ya+existe+otra+receta+con+ese+nombre",
            status_code=303
        )
    
    receta.nombre = nombre.strip()
    receta.categoria = None  # Legacy
    receta.unidad_medida = unidad_medida
    receta.precio_sugerido = precio_sugerido
    receta.precio_minimo = 0  # Legacy
    receta.descripcion = descripcion
    
    # Eliminar materiales viejos
    await db.execute(delete(RecetaMaterial).where(RecetaMaterial.receta_id == receta_id))
    
    # Agregar nuevos materiales vinculados al inventario
    for i in range(len(material_inventario_id)):
        if material_inventario_id[i] and material_inventario_id[i] > 0:
            mat_result = await db.execute(
                select(MaterialInventario).where(MaterialInventario.id == material_inventario_id[i])
            )
            mat_inv = mat_result.scalar_one_or_none()
            
            if mat_inv:
                cantidad = float(material_cantidad[i]) if i < len(material_cantidad) and material_cantidad[i] else 0
                
                material = RecetaMaterial(
                    receta_id=receta.id,
                    material_inventario_id=mat_inv.id,
                    nombre_material=mat_inv.nombre,
                    cantidad=cantidad,
                    unidad=mat_inv.unidad_medida,
                    costo_unitario=0,
                    costo_total=0,
                )
                db.add(material)
    
    await db.commit()
    return RedirectResponse(url="/recetas?success=actualizada", status_code=303)


@router.post("/eliminar/{receta_id}")
async def eliminar_receta(
    receta_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Eliminar (soft delete) una receta"""
    result = await db.execute(
        select(RecetaProducto).where(RecetaProducto.id == receta_id)
    )
    receta = result.scalar_one_or_none()
    
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    receta.activo = False
    await db.commit()
    return RedirectResponse(url="/recetas?success=eliminada", status_code=303)


# ============================================
# FUNCIÓN AUXILIAR
# ============================================

def calcular_costo_normalizado(cantidad: float, unidad: str, costo_unitario: float) -> float:
    """
    Calcula el costo total normalizando las unidades.
    Ejemplo: 200g a $8/kg → 0.2 kg × $8 = $1.60
    """
    # Conversiones comunes
    if unidad in ["g", "gr", "gramo", "gramos"]:
        # Si el costo es por kg, convertir gramos a kg
        return (cantidad / 1000) * costo_unitario
    elif unidad in ["ml"]:
        # Si el costo es por litro, convertir ml a L
        return (cantidad / 1000) * costo_unitario
    elif unidad in ["cm"]:
        # Si el costo es por metro, convertir cm a m
        return (cantidad / 100) * costo_unitario
    else:
        # m2, m, L, kg, unidad - sin conversión
        return cantidad * costo_unitario


# ============================================
# 🔥 API: BUSCAR RECETA POR NOMBRE (para trabajos)
# ============================================
