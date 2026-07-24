"""
Router para gestión de Recetas de Productos
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models import RecetaProducto, RecetaMaterial

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
async def nueva_receta_form(request: Request):
    """Formulario para crear receta"""
    return templates.TemplateResponse("recetas_form.html", {
        "request": request,
        "receta": None,
        "editando": False,
    })


@router.post("/crear")
async def crear_receta(
    request: Request,
    nombre: str = Form(...),
    categoria: str = Form(...),
    unidad_medida: str = Form("unidad"),
    precio_sugerido: float = Form(0),
    precio_minimo: float = Form(0),
    descripcion: str = Form(""),
    material_nombre: List[str] = Form([]),
    material_costo: List[float] = Form([]),
    db: AsyncSession = Depends(get_db)
):
    """Crear receta con costos directos"""
    receta = RecetaProducto(
        nombre=nombre,
        categoria=categoria,
        unidad_medida=unidad_medida,
        precio_sugerido=precio_sugerido,
        precio_minimo=precio_minimo,
        descripcion=descripcion,
    )
    db.add(receta)
    await db.flush()
    
    # Agregar materiales (costo directo por unidad)
    for i in range(len(material_nombre)):
        if material_nombre[i].strip():
            costo = material_costo[i] if i < len(material_costo) else 0
            material = RecetaMaterial(
                receta_id=receta.id,
                nombre_material=material_nombre[i].strip(),
                cantidad=1,  # Siempre 1 unidad
                unidad="unidad",
                costo_unitario=costo,
                costo_total=costo,
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
    """Formulario para editar receta"""
    result = await db.execute(
        select(RecetaProducto)
        .options(selectinload(RecetaProducto.materiales))
        .where(RecetaProducto.id == receta_id)
    )
    receta = result.scalar_one_or_none()
    
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    return templates.TemplateResponse("recetas_form.html", {
        "request": request,
        "receta": receta,
        "editando": True,
    })


@router.post("/actualizar/{receta_id}")
async def actualizar_receta(
    receta_id: int,
    nombre: str = Form(...),
    categoria: str = Form(...),
    unidad_medida: str = Form("unidad"),
    precio_sugerido: float = Form(0),
    precio_minimo: float = Form(0),
    descripcion: str = Form(""),
    material_nombre: List[str] = Form([]),
    material_costo: List[float] = Form([]),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(RecetaProducto).where(RecetaProducto.id == receta_id)
    )
    receta = result.scalar_one_or_none()
    
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    receta.nombre = nombre
    receta.categoria = categoria
    receta.unidad_medida = unidad_medida
    receta.precio_sugerido = precio_sugerido
    receta.precio_minimo = precio_minimo
    receta.descripcion = descripcion
    
    await db.execute(delete(RecetaMaterial).where(RecetaMaterial.receta_id == receta_id))
    
    for i in range(len(material_nombre)):
        if material_nombre[i].strip():
            costo = material_costo[i] if i < len(material_costo) else 0
            material = RecetaMaterial(
                receta_id=receta.id,
                nombre_material=material_nombre[i].strip(),
                cantidad=1,
                unidad="unidad",
                costo_unitario=costo,
                costo_total=costo,
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