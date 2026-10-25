# app/migrar_sedes.py
import asyncio
import os
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from datetime import datetime

# ⚠️ CAMBIA ESTO por tu connection string de Neon
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://usuario:password@ep-xxx-xxx.region.aws.neon.tech/neondb?sslmode=require")

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def migrar_a_sedes():
    """
    Script de migración para Neon PostgreSQL.
    ⚠️ EJECUTAR SOLO UNA VEZ Y CON BACKUP PREVIO.
    """
    async with async_session() as db:
        try:
            print("=" * 60)
            print("🚀 INICIANDO MIGRACIÓN A SEDES (Neon PostgreSQL)")
            print("=" * 60)

            # 1️⃣ Crear sede principal si no existe
            result = await db.execute(text("SELECT id FROM sedes WHERE codigo = 'PRINCIPAL'"))
            row = result.fetchone()

            if row:
                sede_principal_id = row[0]
                print(f"ℹ️  Sede principal ya existe: ID {sede_principal_id}")
            else:
                await db.execute(text("""
                    INSERT INTO sedes (nombre, codigo, direccion, encargado, activa)
                    VALUES ('Sede Principal', 'PRINCIPAL', 'Dirección principal', 'Administrador', TRUE)
                    RETURNING id
                """))
                result = await db.execute(text("SELECT id FROM sedes WHERE codigo = 'PRINCIPAL'"))
                sede_principal_id = result.fetchone()[0]
                print(f"✅ Sede principal creada: ID {sede_principal_id}")

            # 2️⃣ Asignar usuarios sin sede a la sede principal
            result = await db.execute(text("""
                UPDATE usuarios 
                SET sede_id = :sede_id 
                WHERE sede_id IS NULL
                RETURNING id, username, rol
            """), {"sede_id": sede_principal_id})
            usuarios_actualizados = result.fetchall()
            print(f"✅ {len(usuarios_actualizados)} usuarios asignados a sede principal")

            # Marcar primer administrador como superadmin
            result = await db.execute(text("""
                UPDATE usuarios 
                SET es_superadmin = TRUE 
                WHERE rol = 'administrador' AND es_superadmin = FALSE
                ORDER BY id ASC 
                LIMIT 1
                RETURNING id, username, email
            """))
            admin = result.fetchone()
            if admin:
                print(f"👑 Superadmin asignado: {admin[1]} ({admin[2]})")

            # 3️⃣ Migrar stock de materiales a StockSede
            result = await db.execute(text("""
                SELECT id, stock_actual, stock_minimo, tallas, ubicacion
                FROM material_inventario
                WHERE (stock_actual > 0 OR tallas IS NOT NULL)
            """))
            materiales = result.fetchall()
            contador_migrados = 0

            for mat in materiales:
                mat_id, stock_actual, stock_minimo, tallas, ubicacion = mat

                # Verificar si ya existe en stock_sede
                existe = await db.execute(text("""
                    SELECT id FROM stock_sede 
                    WHERE sede_id = :sede_id AND material_id = :mat_id
                """), {"sede_id": sede_principal_id, "mat_id": mat_id})

                if not existe.fetchone():
                    await db.execute(text("""
                        INSERT INTO stock_sede (sede_id, material_id, stock_actual, stock_minimo, tallas, ubicacion)
                        VALUES (:sede_id, :mat_id, :stock_actual, :stock_minimo, :tallas, :ubicacion)
                    """), {
                        "sede_id": sede_principal_id,
                        "mat_id": mat_id,
                        "stock_actual": stock_actual or 0.0,
                        "stock_minimo": stock_minimo or 0.0,
                        "tallas": tallas,
                        "ubicacion": ubicacion
                    })
                    contador_migrados += 1

            print(f"✅ {contador_migrados} materiales migrados a StockSede")

            # 4️⃣ Asignar entradas existentes a sede principal
            result = await db.execute(text("""
                UPDATE entrada_inventario SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Entradas asignadas a sede principal")

            # 5️⃣ Asignar salidas existentes a sede principal
            result = await db.execute(text("""
                UPDATE salida_material SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Salidas asignadas a sede principal")

            # 6️⃣ Asignar movimientos existentes a sede principal
            result = await db.execute(text("""
                UPDATE movimiento_inventario SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Movimientos asignados a sede principal")

            # 7️⃣ Asignar empleados a sede principal
            result = await db.execute(text("""
                UPDATE empleado SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Empleados asignados a sede principal")

            # 8️⃣ Asignar trabajos a sede principal
            result = await db.execute(text("""
                UPDATE trabajo SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Trabajos asignados a sede principal")

            # 9️⃣ Asignar clientes a sede principal
            result = await db.execute(text("""
                UPDATE clientes SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Clientes asignados a sede principal")

            # 🔟 Asignar presupuestos a sede principal
            result = await db.execute(text("""
                UPDATE presupuestos SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Presupuestos asignados a sede principal")

            # 1️⃣1️⃣ Asignar gastos a sede principal
            result = await db.execute(text("""
                UPDATE gasto_diario SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Gastos asignados a sede principal")

            # 1️⃣2️⃣ Asignar ingresos a sede principal
            result = await db.execute(text("""
                UPDATE ingreso_diario SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Ingresos asignados a sede principal")

            # 1️⃣3️⃣ Asignar cierres de caja a sede principal
            result = await db.execute(text("""
                UPDATE cierre_caja SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Cierres de caja asignados a sede principal")

            # 1️⃣4️⃣ Asignar préstamos a sede principal
            result = await db.execute(text("""
                UPDATE prestamo SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Préstamos asignados a sede principal")

            # 1️⃣5️⃣ Asignar deducciones a sede principal
            result = await db.execute(text("""
                UPDATE deduccion_empleado SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Deducciones asignadas a sede principal")

            # 1️⃣6️⃣ Asignar pagos semanales a sede principal
            result = await db.execute(text("""
                UPDATE pago_semanal SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Pagos semanales asignados a sede principal")

            # 1️⃣7️⃣ Asignar compras empleado a sede principal
            result = await db.execute(text("""
                UPDATE compras_empleado SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Compras empleado asignadas a sede principal")

            # 1️⃣8️⃣ Asignar asistencias a sede principal
            result = await db.execute(text("""
                UPDATE asistencia SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Asistencias asignadas a sede principal")

            # 1️⃣9️⃣ Asignar reportes semanales a sede principal
            result = await db.execute(text("""
                UPDATE reporte_semanal SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Reportes semanales asignados a sede principal")

            # 2️⃣0️⃣ Asignar activos fijos a sede principal
            result = await db.execute(text("""
                UPDATE activo_fijo SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Activos fijos asignados a sede principal")

            # 2️⃣1️⃣ Asignar movimientos de activo fijo a sede principal
            result = await db.execute(text("""
                UPDATE movimiento_activo_fijo SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Movimientos de activo fijo asignados a sede principal")

            # 2️⃣2️⃣ Asignar deudas manuales a sede principal
            result = await db.execute(text("""
                UPDATE deudas_manuales SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Deudas manuales asignadas a sede principal")

            # 2️⃣3️⃣ Asignar pagos_trabajo a sede principal
            result = await db.execute(text("""
                UPDATE pagos_trabajo SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Pagos de trabajo asignados a sede principal")

            # 2️⃣4️⃣ Asignar servicios_externos a sede principal
            result = await db.execute(text("""
                UPDATE servicios_externos SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Servicios externos asignados a sede principal")

            # 2️⃣5️⃣ Asignar material_usado a sede principal
            result = await db.execute(text("""
                UPDATE material_usado SET sede_id = :sede_id WHERE sede_id IS NULL
            """), {"sede_id": sede_principal_id})
            print(f"✅ Material usado asignado a sede principal")

            # COMMIT FINAL
            await db.commit()

            print("=" * 60)
            print("🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
            print("=" * 60)
            print(f"📍 Sede principal ID: {sede_principal_id}")
            print("⚠️  Verifica los datos en Neon Dashboard antes de continuar")

        except Exception as e:
            await db.rollback()
            print(f"❌ ERROR EN MIGRACIÓN: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrar_a_sedes())