from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from datetime import datetime

class FacturaPDFGenerator:
    def __init__(self, factura):
        self.factura = factura
        self.buffer = BytesIO()
        
    def generar(self):
        # Crear el documento PDF
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        titulo_style = ParagraphStyle(
            'Titulo',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        # Contenido
        elementos = []
        
        # Título
        elementos.append(Paragraph("FACTURA", titulo_style))
        
        # Información de la factura
        elementos.append(self._crear_encabezado())
        elementos.append(Spacer(1, 20))
        
        # Información del cliente
        elementos.append(self._crear_info_cliente())
        elementos.append(Spacer(1, 20))
        
        # Tabla de items
        elementos.append(self._crear_tabla_items())
        elementos.append(Spacer(1, 20))
        
        # Totales
        elementos.append(self._crear_totales())
        elementos.append(Spacer(1, 20))
        
        # Observaciones
        if self.factura.observaciones:
            elementos.append(self._crear_observaciones())
        
        # Construir PDF
        doc.build(elementos)
        
        # Retornar el PDF como bytes
        self.buffer.seek(0)
        return self.buffer.getvalue()
    
    def _crear_encabezado(self):
        data = [
            ['N° Factura:', self.factura.numero_factura],
            ['Fecha Emisión:', self.factura.fecha_emision.strftime('%d/%m/%Y')],
            ['Método de Pago:', self.factura.metodo_pago or 'No especificado']
        ]
        
        table = Table(data, colWidths=[4*cm, 8*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#111827')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        return table
    
    def _crear_info_cliente(self):
        styles = getSampleStyleSheet()
        cliente_style = ParagraphStyle(
            'Cliente',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=5
        )
        
        cliente_text = f"""
        <b>DATOS DEL CLIENTE</b><br/>
        {self.factura.cliente.nombre_razon_social}<br/>
        RIF/Cédula: {self.factura.cliente.rif or self.factura.cliente.cedula or 'N/A'}<br/>
        Teléfono: {self.factura.cliente.telefono or 'N/A'}<br/>
        Email: {self.factura.cliente.email or 'N/A'}<br/>
        Dirección: {self.factura.cliente.direccion or 'N/A'}
        """
        
        return Paragraph(cliente_text, cliente_style)
    
    def _crear_tabla_items(self):
        # Cabecera de la tabla
        data = [['Descripción', 'Cantidad', 'Precio Unit.', 'Desc. %', 'Subtotal']]
        
        # Agregar items
        for item in self.factura.items:
            data.append([
                item.descripcion,
                f"{item.cantidad:.2f}",
                f"${item.precio_unitario:.2f}",
                f"{item.descuento_porcentaje:.2f}%",
                f"${item.subtotal_linea:.2f}"
            ])
        
        # Crear tabla
        table = Table(data, colWidths=[7*cm, 2*cm, 2.5*cm, 2*cm, 2.5*cm])
        
        # Estilos de la tabla
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ])
        
        table.setStyle(style)
        return table
    
    def _crear_totales(self):
        styles = getSampleStyleSheet()
        
        data = [
            ['Subtotal:', f"${self.factura.subtotal:.2f}"],
            [f"IVA ({self.factura.iva_porcentaje:.2f}%):", f"${self.factura.iva_monto:.2f}"],
            ['', ''],
            ['TOTAL (USD):', f"${self.factura.total:.2f}"]
        ]
        
        if self.factura.tasa_cambio:
            data.extend([
                ['', ''],
                ['Tasa de Cambio:', f"{self.factura.tasa_cambio:.2f} Bs/USD"],
                ['Subtotal (Bs):', f"Bs {self.factura.subtotal_bs:.2f}"],
                ['IVA (Bs):', f"Bs {self.factura.iva_monto_bs:.2f}"],
                ['TOTAL (Bs):', f"Bs {self.factura.total_bs:.2f}"]
            ])
        
        table = Table(data, colWidths=[8*cm, 4*cm])
        
        style = TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#111827')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ])
        
        # Estilo especial para el total
        style.add('FONTNAME', (0, 3), (1, 3), 'Helvetica-Bold')
        style.add('FONTSIZE', (0, 3), (1, 3), 12)
        style.add('TEXTCOLOR', (0, 3), (1, 3), colors.HexColor('#059669'))
        
        if self.factura.tasa_cambio:
            style.add('FONTNAME', (0, 8), (1, 8), 'Helvetica-Bold')
            style.add('FONTSIZE', (0, 8), (1, 8), 11)
            style.add('TEXTCOLOR', (0, 8), (1, 8), colors.HexColor('#059669'))
        
        table.setStyle(style)
        return table
    
    def _crear_observaciones(self):
        styles = getSampleStyleSheet()
        obs_style = ParagraphStyle(
            'Observaciones',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6b7280'),
            alignment=TA_LEFT,
            spaceBefore=10
        )
        
        return Paragraph(f"<b>Observaciones:</b><br/>{self.factura.observaciones}", obs_style)