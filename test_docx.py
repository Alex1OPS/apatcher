import docx as dd
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import Pt

# переменные текста
p_1_pr_str = "Устанавливаются обновления, полученные __data_d___ от сотрудника отдела внедрения ООО \"ПОТОК\" "
p_1_pr_str_1 = "__author_name__ в виде архива(директории) __dir_name__ ."
p_2_pr_str = "Дата и время установки выполнения обновлений"
p_2_pr_str_1 = " __________________________."

# работа с документом
document = dd.Document()
style = document.styles['Normal']
font = style.font
font.name = 'Calibri'
font.size = Pt(12)

# C Т И Л И
# для заголовка
obj_styles = document.styles
obj_charstyle = obj_styles.add_style('TitleStyle1', WD_STYLE_TYPE.CHARACTER)
obj_font = obj_charstyle.font
obj_font.size = Pt(14)
obj_font.name = 'Times New Roman'
# основной
obj_styles = document.styles
obj_charstyle = obj_styles.add_style('BodyStyle1', WD_STYLE_TYPE.CHARACTER)
obj_font = obj_charstyle.font
obj_font.size = Pt(12)
obj_font.name = 'Times New Roman'

# шапка
p_begin = document.add_paragraph()
p_begin.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_begin.add_run("Журнал установки обновлений", style='TitleStyle1').bold = True

# 1 блок
p_1 = document.add_paragraph()
p_1.add_run(p_1_pr_str + p_1_pr_str_1, style='BodyStyle1')

# 2 блок
p_2 = document.add_paragraph()
p_2.add_run(p_2_pr_str + p_2_pr_str_1, style='BodyStyle1')

# document.add_picture('monty-truth.png', width=Inches(1.25))

table = document.add_table(rows=1, cols=3)
table.style = 'Table Grid'
hdr_cells = table.rows[0].cells
hdr_cells[0].text = 'Qty'
hdr_cells[1].text = 'Id'
hdr_cells[2].text = 'Desc'
run = hdr_cells[0].paragraphs[0].runs[0]
run.font.bold = True
for item in range(1, 10):
    row_cells = table.add_row().cells
    row_cells[0].text = str(item)
    row_cells[1].text = str(item)
    row_cells[2].text = str('New line')

document.save('tmp//demo.docx')
