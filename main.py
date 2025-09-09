# Instalar dependências (rodar apenas uma vez)
# !pip install streamlit reportlab --quiet

import streamlit as st
import zipfile
import json
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable, PageBreak

# -----------------------------
# Função para processar PBIT
# -----------------------------
def process_pbit(file_bytes, filename):
    # Ler DataModelSchema
    with zipfile.ZipFile(BytesIO(file_bytes), 'r') as pbit_zip:
        if 'DataModelSchema' not in pbit_zip.namelist():
            st.error("DataModelSchema não encontrado no arquivo PBIT.")
            return None
        with pbit_zip.open('DataModelSchema') as f:
            data_model_json = json.load(f)
    
    # Extrair tabelas simplificadas
    simplified_model = {"tables": [], "relationships": []}
    for table in data_model_json.get("model", {}).get("tables", []):
        table_source = ""
        partitions = table.get("partitions", [])
        if partitions:
            first_partition = partitions[0]
            source_info = first_partition.get("source", {})
            if "expression" in source_info and source_info["expression"]:
                table_source = "Fonte: " + " ".join(source_info["expression"][:2]) + "..."
            elif "type" in source_info:
                table_source = f"Fonte tipo: {source_info['type']}"
        simplified_table = {
            "name": table.get("name"),
            "description": table.get("description",""),
            "source": table_source,
            "columns": [{"name": c.get("name"), "dataType": c.get("dataType"), "description": c.get("description","")} for c in table.get("columns", [])],
            "measures": [{"name": m.get("name"), "expression": m.get("expression"), "description": m.get("description","")} for m in table.get("measures", [])]
        }
        simplified_model["tables"].append(simplified_table)

    for rel in data_model_json.get("model", {}).get("relationships", []):
        simplified_model["relationships"].append({
            "fromTable": rel.get("fromTable"),
            "fromColumn": rel.get("fromColumn"),
            "toTable": rel.get("toTable"),
            "toColumn": rel.get("toColumn")
        })

    # -----------------------------
    # Criar PDF em memória
    # -----------------------------
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Estilos
    title_style = ParagraphStyle('title', parent=styles['Heading1'], fontSize=24, spaceAfter=14, alignment=1, textColor=colors.HexColor('#0B5394'))
    subtitle_style = ParagraphStyle('subtitle', parent=styles['Heading2'], fontSize=18, spaceAfter=10, textColor=colors.HexColor('#1155CC'))
    normal_style = styles['Normal']
    measure_style = ParagraphStyle('measure', parent=styles['Normal'], backColor=colors.HexColor('#EDEDED'), borderPadding=6, spaceAfter=8, fontSize=10)
    source_style = ParagraphStyle('source', parent=normal_style, fontSize=10, textColor=colors.HexColor('#666666'))

    # -----------------------------
    # Índice
    # -----------------------------
    story.append(Paragraph("Documentação Power BI - ERD Final", title_style))
    story.append(Spacer(1,16))
    story.append(Paragraph("Índice", subtitle_style))
    table_destinations = {}
    for idx, table in enumerate(simplified_model["tables"]):
        dest_name = f"table_{idx}"
        table_destinations[table["name"]] = dest_name
        story.append(Paragraph(f'<link href="#{dest_name}">{table["name"]}</link>', ParagraphStyle('index', parent=styles['Normal'], fontSize=14, spaceAfter=6, textColor=colors.HexColor('#1155CC'))))
    story.append(PageBreak())

    # -----------------------------
    # Tabelas detalhadas
    # -----------------------------
    table_colors = [colors.HexColor('#D9EAD3'), colors.HexColor('#CFE2F3'), colors.HexColor('#FCE5CD'), colors.HexColor('#F4CCCC')]
    for idx, table in enumerate(simplified_model["tables"]):
        color = table_colors[idx % len(table_colors)]
        dest_name = table_destinations[table["name"]]
        story.append(Paragraph(f'<a name="{dest_name}"/>Tabela: {table["name"]}',
                               ParagraphStyle('table_title', parent=subtitle_style, backColor=color, fontSize=18, spaceAfter=8)))
        # Descrição
        if table.get("description"):
            story.append(Paragraph(f"Descrição: {table['description']}", normal_style))
            story.append(Spacer(1, 8))
        # Fonte
        if table.get("source"):
            story.append(Paragraph(table['source'], source_style))
            story.append(Spacer(1, 8))
        # Colunas
        col_data = [["Coluna", "Tipo", "Descrição"]]
        for col in table["columns"]:
            col_data.append([col["name"], col["dataType"], col.get("description","")])
        t = Table(col_data, colWidths=[150,100,250])
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0), color),
            ('GRID',(0,0),(-1,-1),0.5, colors.black),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('VALIGN',(0,0),(-1,-1),'TOP')
        ]))
        story.append(t)
        story.append(Spacer(1,12))
        # Medidas
        for measure in table["measures"]:
            story.append(Paragraph(f"Medida: {measure['name']}", ParagraphStyle('measure_title', parent=measure_style, backColor=colors.HexColor('#D9D2E9'), fontSize=11)))
            story.append(Paragraph(str(measure.get("expression","")), measure_style))
            if measure.get("description"):
                story.append(Paragraph(f"Descrição: {measure['description']}", normal_style))
            story.append(Spacer(1,8))
        story.append(PageBreak())

    # -----------------------------
    # Diagrama ERD avançado com círculos
    # -----------------------------
    class ERDAutoDiagram(Flowable):
        def __init__(self, tables, relationships, destinations, width=500, height=500, colors_list=None):
            Flowable.__init__(self)
            self.tables = tables
            self.relationships = relationships
            self.destinations = destinations
            self.width = width
            self.height = height
            self.colors_list = colors_list or [colors.HexColor('#D9EAD3'), colors.HexColor('#CFE2F3'),
                                               colors.HexColor('#FCE5CD'), colors.HexColor('#F4CCCC')]

        def draw_cardinality_arrow(self, c, x, y, orientation='end', size=12):
            if orientation == 'end':
                points = [(x, y), (x-size, y+size/2), (x-size, y-size/2)]
            else:
                points = [(x, y), (x+size, y+size/2), (x+size, y-size/2)]
            path = c.beginPath()
            path.moveTo(*points[0])
            path.lineTo(*points[1])
            path.lineTo(*points[2])
            path.close()
            c.setFillColor(colors.black)
            c.setStrokeColor(colors.black)
            c.drawPath(path, fill=1, stroke=1)

        def draw(self):
            c = self.canv
            n = len(self.tables)
            padding = 30
            cols = min(3, n)
            rows = (n + cols - 1) // cols
            box_width = (self.width - padding*2)/cols - 20
            box_height = (self.height - padding*2)/rows - 20
            table_positions = {}
            idx = 0
            for r in range(rows):
                for col in range(cols):
                    if idx >= n: break
                    table = self.tables[idx]
                    x = padding + col*(box_width + 20)
                    y = self.height - padding - (r+1)*(box_height + 20) + 20
                    color = self.colors_list[idx % len(self.colors_list)]
                    c.setFillColor(color)
                    c.rect(x, y, box_width, box_height, fill=1)
                    c.setFillColor(colors.black)
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(x+5, y+box_height-12, table["name"])
                    y_offset = y + box_height - 24
                    for colm in table["columns"][:5]:
                        c.setFont("Helvetica", 8)
                        c.drawString(x+5, y_offset, f"{colm['name']}")
                        y_offset -= 10
                    for measure in table["measures"][:3]:
                        c.drawString(x+5, y_offset, f"m:{measure['name']}")
                        y_offset -= 10
                    table_positions[table["name"]] = (x, y, box_width, box_height)
                    c.linkRect('', self.destinations[table["name"]], (x, y, x+box_width, y+box_height), relative=1)
                    idx += 1

            # Linhas curvas com círculo na origem
            rel_pairs = {}
            for rel in self.relationships:
                pair = tuple(sorted([rel["fromTable"], rel["toTable"]]))
                if pair not in rel_pairs:
                    rel_pairs[pair] = 0
                count = rel_pairs[pair]
                rel_pairs[pair] += 1
                offset_step = 20
                offset = count * offset_step
                start = table_positions.get(rel["fromTable"])
                end = table_positions.get(rel["toTable"])
                if start and end:
                    x1, y1, w1, h1 = start
                    x2, y2, w2, h2 = end
                    x1c = x1 + w1/2
                    y1c = y1 + h1/2 + offset
                    x2c = x2 + w2/2
                    y2c = y2 + h2/2 + offset
                    # círculo origem
                    c.setFillColor(colors.HexColor('#1155CC'))
                    c.circle(x1c, y1c, 6, fill=1, stroke=0)
                    # curva
                    c.setStrokeColor(colors.black)
                    c.setLineWidth(1)
                    ctrl_x = (x1c + x2c)/2
                    ctrl_y1 = y1c
                    ctrl_y2 = y2c
                    path = c.beginPath()
                    path.moveTo(x1c, y1c)
                    path.curveTo(ctrl_x, ctrl_y1, ctrl_x, ctrl_y2, x2c, y2c)
                    c.drawPath(path)
                    # seta
                    self.draw_cardinality_arrow(c, x2c, y2c, orientation='end')

    story.append(Paragraph("Diagrama ERD Avançado", subtitle_style))
    story.append(Spacer(1,12))
    diagram = ERDAutoDiagram(simplified_model["tables"], simplified_model["relationships"], table_destinations, width=500, height=500)
    story.append(diagram)
    story.append(PageBreak())

    # Relacionamentos detalhados
    story.append(Paragraph("Relacionamentos Detalhados", subtitle_style))
    story.append(Spacer(1,12))
    for table in simplified_model["tables"]:
        story.append(Paragraph(f"Relacionamentos da Tabela: {table['name']}", ParagraphStyle('table_title', parent=subtitle_style, fontSize=16, spaceAfter=6, backColor=colors.HexColor('#D9D9D9'))))
        rels = [r for r in simplified_model["relationships"] if r["fromTable"]==table["name"] or r["toTable"]==table["name"]]
        if not rels:
            story.append(Paragraph("Nenhum relacionamento.", normal_style))
            story.append(Spacer(1,8))
            continue
        rel_data = [["Coluna Origem", "Tabela Origem", "Coluna Destino", "Tabela Destino"]]
        for r in rels:
            rel_data.append([r["fromColumn"], r["fromTable"], r["toColumn"], r["toTable"]])
        t = Table(rel_data, colWidths=[120,120,120,120])
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0), colors.HexColor('#CFE2F3')),
            ('GRID',(0,0),(-1,-1),0.5, colors.black),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('FONTSIZE',(0,0),(-1,-1),9),
        ]))
        story.append(t)
        story.append(Spacer(1,12))

    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer

# -----------------------------
# Streamlit UI
# -----------------------------
# st.title("Gerador de Documentação Power BI (ERD)")
# uploaded_file = st.file_uploader("Escolha um arquivo .pbit", type=["pbit"])

# if uploaded_file:
#     with st.spinner("Processando PBIT e gerando PDF..."):
#         pdf_bytes = process_pbit(uploaded_file.read(), uploaded_file.name)
#         if pdf_bytes:
#             st.success("PDF gerado com sucesso!")
#             st.download_button(
#                 label="Baixar PDF",
#                 data=pdf_bytes,
#                 file_name=uploaded_file.name.replace(".pbit","_erd_final.pdf"),
#                 mime="application/pdf"
#             )