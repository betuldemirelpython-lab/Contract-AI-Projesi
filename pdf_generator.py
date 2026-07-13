import os
import requests
from fpdf import FPDF
from pathlib import Path
from datetime import datetime

FONT_DIR = Path(__file__).parent / "assets" / "fonts"
FONT_URL = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf"
FONT_BOLD_URL = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
FONT_PATH = FONT_DIR / "Roboto-Regular.ttf"
FONT_BOLD_PATH = FONT_DIR / "Roboto-Bold.ttf"

def ensure_fonts():
    """Gerekli font dosyalarını indirir (Türkçe karakter desteği için)."""
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    
    if not FONT_PATH.exists():
        resp = requests.get(FONT_URL)
        if resp.status_code == 200:
            FONT_PATH.write_bytes(resp.content)
            
    if not FONT_BOLD_PATH.exists():
        resp = requests.get(FONT_BOLD_URL)
        if resp.status_code == 200:
            FONT_BOLD_PATH.write_bytes(resp.content)

class ReportPDF(FPDF):
    def header(self):
        self.set_font("Roboto", "B", 16)
        self.cell(0, 10, "Sözleşme Analiz Raporu", 0, 1, "C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Roboto", "", 8)
        self.cell(0, 10, f"Sayfa {self.page_no()}", 0, 0, "C")

def create_analysis_pdf(analysis_data: dict) -> bytes:
    ensure_fonts()
    
    pdf = ReportPDF()
    pdf.add_page()
    
    # Fontları kaydet
    pdf.add_font("Roboto", "", str(FONT_PATH), uni=True)
    pdf.add_font("Roboto", "B", str(FONT_BOLD_PATH), uni=True)
    
    # 1. Genel Bilgiler
    pdf.set_font("Roboto", "B", 14)
    pdf.cell(0, 10, "1. Genel Değerlendirme", 0, 1, "L")
    
    pdf.set_font("Roboto", "B", 12)
    risk_skoru = analysis_data.get("risk_skoru", 0)
    pdf.cell(0, 8, f"Risk Skoru: {risk_skoru} / 100", 0, 1, "L")
    
    pdf.set_font("Roboto", "", 11)
    ozet = analysis_data.get("ozet", "")
    genel = analysis_data.get("genel_degerlendirme", "")
    if ozet:
        pdf.multi_cell(0, 6, f"Özet: {ozet}")
        pdf.ln(2)
    if genel:
        pdf.multi_cell(0, 6, f"Değerlendirme: {genel}")
        pdf.ln(5)
        
    # 2. Riskler
    riskler = analysis_data.get("riskler", [])
    if riskler:
        pdf.set_font("Roboto", "B", 14)
        pdf.cell(0, 10, "2. Tespit Edilen Riskler", 0, 1, "L")
        
        for i, risk in enumerate(riskler, 1):
            pdf.set_font("Roboto", "B", 12)
            sev = risk.get('severity', 'medium').upper()
            pdf.cell(0, 8, f"{i}. {risk.get('madde', 'Risk')} [{sev}]", 0, 1, "L")
            
            pdf.set_font("Roboto", "", 11)
            pdf.multi_cell(0, 6, f"Açıklama: {risk.get('aciklama', '')}")
            
            oneri = risk.get('oneri', '')
            if oneri:
                pdf.set_text_color(0, 100, 0)
                pdf.multi_cell(0, 6, f"Öneri: {oneri}")
                pdf.set_text_color(0, 0, 0)
            pdf.ln(3)
            
    # 3. Önemli Maddeler
    maddeler = analysis_data.get("onemli_maddeler", [])
    if maddeler:
        pdf.set_font("Roboto", "B", 14)
        pdf.cell(0, 10, "3. Önemli Maddeler", 0, 1, "L")
        
        for madde in maddeler:
            pdf.set_font("Roboto", "B", 11)
            pdf.cell(0, 8, f"- {madde.get('baslik', '')} ({madde.get('kategori', '')})", 0, 1, "L")
            
            pdf.set_font("Roboto", "", 10)
            pdf.multi_cell(0, 6, f"{madde.get('icerik', '')}")
            pdf.ln(2)
            
    # 4. Tavsiyeler
    tavsiyeler = analysis_data.get("tavsiyeler", [])
    if tavsiyeler:
        pdf.set_font("Roboto", "B", 14)
        pdf.cell(0, 10, "4. Sonuç ve Tavsiyeler", 0, 1, "L")
        
        pdf.set_font("Roboto", "", 11)
        for i, tavsiye in enumerate(tavsiyeler, 1):
            pdf.multi_cell(0, 6, f"{i}. {tavsiye}")
            pdf.ln(1)
            
    # Çıktıyı byte array olarak döndür
    return pdf.output(dest='S').encode('latin1')  # fpdf2 outputs latin1 string when dest='S', so we encode it to get bytes.

