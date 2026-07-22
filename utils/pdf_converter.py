import io
import os
import tempfile
from docx2pdf import convert

def docx_to_pdf(docx_bytes):
    """将Word字节流转换为PDF字节流
    注意：Windows环境需安装Microsoft Office；Linux环境需安装LibreOffice
    """
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_docx:
        tmp_docx.write(docx_bytes.getvalue())
        tmp_docx_path = tmp_docx.name
    
    pdf_path = tmp_docx_path.replace('.docx', '.pdf')
    
    try:
        convert(tmp_docx_path, pdf_path)
        
        with open(pdf_path, 'rb') as f:
            pdf_bytes = io.BytesIO(f.read())
        
        return pdf_bytes
    finally:
        if os.path.exists(tmp_docx_path):
            os.remove(tmp_docx_path)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
