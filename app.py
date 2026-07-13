"""
app.py - Streamlit Arayüzü
AI Contract Analyzer - Yapay Zeka Destekli Sözleşme Analiz Sistemi
"""

import streamlit as st
import requests
import json
import time
import threading
from datetime import datetime
from pathlib import Path
import base64
import os
import urllib.request
import re
from fpdf import FPDF

# ─── Sayfa Ayarları ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Contract Analyzer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Sabitler ─────────────────────────────────────────────────────────────
API_BASE = "http://localhost:8000"

CONTRACT_TYPES = {
    "auto": "🤖 Otomatik Tespit",
    "kira": "🏠 Kira Sözleşmesi",
    "is": "💼 İş Sözleşmesi",
    "nda": "🔒 Gizlilik Sözleşmesi (NDA)",
    "hizmet": "🛠️ Hizmet Sözleşmesi",
    "satis": "🛒 Satış Sözleşmesi",
    "diger": "📄 Diğer",
}

SEVERITY_COLORS = {
    "low": "#22c55e",
    "medium": "#f59e0b",
    "high": "#ef4444",
    "critical": "#7c3aed",
}

SEVERITY_LABELS = {
    "low": "🟢 Düşük",
    "medium": "🟡 Orta",
    "high": "🔴 Yüksek",
    "critical": "🟣 Kritik",
}

RISK_LABELS = {
    (0, 25): ("Düşük Risk", "#22c55e", "✅"),
    (26, 50): ("Orta Risk", "#f59e0b", "⚠️"),
    (51, 75): ("Yüksek Risk", "#ef4444", "❌"),
    (76, 100): ("Kritik Risk", "#7c3aed", "🚨"),
}

# ─── CSS Stilleri ─────────────────────────────────────────────────────────
st.markdown(
    """
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global */
    * { font-family: 'Inter', sans-serif !important; }

    /* Ana arkaplan */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        min-height: 100vh;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(255,255,255,0.05) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255,255,255,0.1);
    }

    /* Başlıklar ve Genel Metinler */
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; }
    p, li, label, span, [data-testid="stMarkdownContainer"], [data-testid="stText"] { color: rgba(255,255,255,0.85) !important; }

    /* Kart bileşenleri */
    .metric-card {
        background: rgba(255,255,255,0.08);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.3);
    }

    /* Risk badge */
    .risk-badge {
        display: inline-block;
        padding: 6px 18px;
        border-radius: 50px;
        font-weight: 700;
        font-size: 1.1em;
        letter-spacing: 0.5px;
    }

    /* Risk maddesi kartı */
    .risk-card {
        background: rgba(255,255,255,0.06);
        border-left: 4px solid;
        border-radius: 0 12px 12px 0;
        padding: 16px 20px;
        margin: 10px 0;
        transition: background 0.2s;
    }
    .risk-card:hover { background: rgba(255,255,255,0.1); }

    /* Madde kartı */
    .clause-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
    }

    /* Tavsiye kartı */
    .advice-card {
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 10px;
        padding: 12px 16px;
        margin: 6px 0;
    }

    /* Progress bar override */
    .stProgress > div > div { border-radius: 10px !important; }

    /* Buton — tüm Streamlit buton varyantlarını yakala */
    .stButton > button,
    div[data-testid="stButton"] > button,
    div[data-testid="stBaseButton-secondary"],
    div[data-testid="stBaseButton-primary"],
    button[kind="secondary"],
    button[kind="primary"],
    .stButton button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        background-color: #6366f1 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 32px !important;
        font-weight: 700 !important;
        font-size: 1em !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.5) !important;
    }
    /* Buton içindeki tüm metin ve p elemanları */
    .stButton > button *,
    .stButton > button p,
    div[data-testid="stButton"] > button *,
    div[data-testid="stButton"] > button p {
        color: #ffffff !important;
        fill: #ffffff !important;
    }
    .stButton > button:hover,
    div[data-testid="stButton"] > button:hover {
        background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
        background-color: #4f46e5 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.7) !important;
    }

    /* ── Input & TextArea ── */
    .stTextArea textarea,
    .stTextArea textarea:focus,
    .stTextArea div textarea,
    [data-testid="stTextArea"] textarea,
    [data-testid="stTextArea"] textarea:focus,
    div[class*="stTextArea"] textarea {
        background: rgba(30, 27, 75, 0.85) !important;
        border: 1px solid rgba(139, 92, 246, 0.4) !important;
        border-radius: 12px !important;
        color: #f0f0ff !important;
        caret-color: #a78bfa !important;
        font-size: 0.97em !important;
        line-height: 1.7 !important;
    }
    .stTextArea textarea::placeholder,
    [data-testid="stTextArea"] textarea::placeholder {
        color: rgba(200, 190, 255, 0.45) !important;
    }
    /* Streamlit'in iç wrapper div'leri */
    .stTextArea > div,
    .stTextArea > div > div,
    [data-testid="stTextArea"] > div,
    [data-testid="stTextArea"] > div > div {
        background: transparent !important;
    }

    /* ── Selectbox: kutu görünümü ── */
    [data-baseweb="select"] > div:first-child {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.25) !important;
        border-radius: 12px !important;
    }
    /* Seçili değer metni */
    [data-baseweb="select"] [data-testid="stSelectbox"],
    [data-baseweb="select"] span,
    [data-baseweb="select"] div {
        color: rgba(255,255,255,0.85) !important;
    }
    /* Seçili değer yazısı (value container) */
    [data-baseweb="select"] .css-1jqq78o-placeholder,
    [data-baseweb="select"] .css-dvua67-singleValue,
    [data-baseweb="select"] [class*="singleValue"],
    [data-baseweb="select"] [class*="placeholder"] {
        color: white !important;
    }

    /* ── Dropdown açılır listesi (popup) ── */
    [data-baseweb="popover"],
    [data-baseweb="popover"] > div,
    [data-baseweb="popover"] > div > div,
    [data-baseweb="menu"],
    ul[data-baseweb="menu"],
    [data-baseweb="select"] [data-baseweb="popover"],
    [data-baseweb="select"] [data-baseweb="popover"] div,
    div[data-baseweb="popover"] > div,
    [role="listbox"],
    [role="listbox"] > div {
        background: #1e1b4b !important;
        background-color: #1e1b4b !important;
        border: 1px solid rgba(139, 92, 246, 0.4) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(20px);
        box-shadow: 0 20px 60px rgba(0,0,0,0.6) !important;
        overflow: hidden !important;
    }

    /* Liste öğeleri — geniş seçiciler */
    [data-baseweb="menu"] li,
    [data-baseweb="menu"] [role="option"],
    ul[data-baseweb="menu"] li,
    [role="listbox"] li,
    [role="listbox"] [role="option"],
    [role="option"],
    [data-baseweb="popover"] li,
    [data-baseweb="popover"] [role="option"] {
        background: transparent !important;
        background-color: transparent !important;
        color: #e2e8f0 !important;
        font-size: 0.95em !important;
        padding: 10px 16px !important;
        transition: background 0.15s ease !important;
    }

    /* Hover durumu */
    [data-baseweb="menu"] li:hover,
    [data-baseweb="menu"] [role="option"]:hover,
    [role="listbox"] li:hover,
    [role="listbox"] [role="option"]:hover,
    [role="option"]:hover,
    [data-baseweb="popover"] li:hover,
    [data-baseweb="menu"] [aria-selected="true"],
    [role="option"][aria-selected="true"] {
        background: rgba(99, 102, 241, 0.35) !important;
        background-color: rgba(99, 102, 241, 0.35) !important;
        color: white !important;
    }

    /* Seçili öğe */
    [data-baseweb="menu"] [aria-selected="true"],
    [role="listbox"] [aria-selected="true"],
    [role="option"][aria-selected="true"] {
        background: rgba(99, 102, 241, 0.5) !important;
        background-color: rgba(99, 102, 241, 0.5) !important;
        color: white !important;
        font-weight: 600 !important;
    }

    /* Dropdown ok ikonu */
    [data-baseweb="select"] svg {
        fill: rgba(255,255,255,0.7) !important;
    }

    /* Genel label renkleri */
    .stSelectbox label,
    .stTextArea label,
    .stFileUploader label {
        color: rgba(255,255,255,0.85) !important;
        font-weight: 500 !important;
    }

    /* Tab */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        color: rgba(255,255,255,0.7) !important;
        border-radius: 8px !important;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(99, 102, 241, 0.5) !important;
        color: white !important;
    }

    /* Divider */
    hr { border-color: rgba(255,255,255,0.1) !important; }

    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.05) !important;
        border-radius: 10px !important;
        color: white !important;
    }

    /* Alert kutuları */
    .stAlert {
        border-radius: 12px !important;
        backdrop-filter: blur(10px);
    }

    /* Header hero */
    .hero-header {
        text-align: center;
        padding: 40px 20px;
        background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.2));
        border-radius: 24px;
        border: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 30px;
    }
    .hero-title {
        font-size: 3em;
        font-weight: 800;
        color: #ffffff !important;
        text-shadow: 0 0 30px rgba(167,139,250,0.6);
        margin: 0;
        letter-spacing: -1px;
    }
    .hero-subtitle {
        color: rgba(255,255,255,0.85) !important;
        font-size: 1.15em;
        margin-top: 10px;
    }

    /* Score circle */
    .score-container {
        text-align: center;
        padding: 30px;
    }
    .score-circle {
        width: 140px;
        height: 140px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 15px;
        font-size: 2.5em;
        font-weight: 800;
        border: 6px solid;
        box-shadow: 0 0 30px rgba(0,0,0,0.4);
    }

    /* History item */
    .history-item {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 14px 18px;
        margin: 6px 0;
        cursor: pointer;
        transition: all 0.2s;
    }
    .history-item:hover {
        background: rgba(255,255,255,0.1);
        border-color: rgba(99,102,241,0.5);
    }

    /* ── File Uploader butonu — çift metin sorununu gider ── */
    [data-testid="stFileUploaderDropzone"] button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.9em !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: nowrap !important;
    }
    /* Streamlit'in iç span'ini gizle, sadece button metni görünsün */
    [data-testid="stFileUploaderDropzone"] button span {
        display: none !important;
    }
    [data-testid="stFileUploaderDropzone"] button::after {
        content: "Dosya Seç";
        color: white;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: rgba(255,255,255,0.04) !important;
        border: 2px dashed rgba(99,102,241,0.4) !important;
        border-radius: 14px !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ─── Yardımcı Fonksiyonlar ────────────────────────────────────────────────
@st.cache_resource
def get_fonts():
    """PDF için fontları indirir ve yollarını döner."""
    fonts_dir = "fonts"
    if not os.path.exists(fonts_dir):
        os.makedirs(fonts_dir)
    reg_path = os.path.join(fonts_dir, "Roboto-Regular.ttf")
    bold_path = os.path.join(fonts_dir, "Roboto-Bold.ttf")
    if not os.path.exists(reg_path):
        urllib.request.urlretrieve("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf", reg_path)
    if not os.path.exists(bold_path):
        urllib.request.urlretrieve("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf", bold_path)
    return reg_path, bold_path

def safe_text(txt):
    """Uzun boşluksuz metinleri böler, emojileri kaldırır (PDF uyumluluğu için)."""
    if not txt:
        return ""
    txt = str(txt).replace('\xa0', ' ')
    # Emoji ve özel unicode karakterleri kaldır (fpdf2 Unicode dışı fontlarda crash yapar)
    txt = re.sub(r'[^\x00-\x7F\u00C0-\u024F\u0100-\u017E]', '', txt)
    # 25 karakterden uzun boşluksuz kelimeleri böl
    return re.sub(r'(\S{25})', r'\1 ', txt)

def generate_pdf_report(result_dict: dict) -> bytes:
    """JSON analiz sonucunu PDF bytes dizisine çevirir."""
    analysis = result_dict.get("analysis", {})
    reg_path, bold_path = get_fonts()
    
    pdf = FPDF()
    pdf.set_margins(left=20, top=20, right=20)  # Yeterli margin
    pdf.add_page()
    pdf.add_font("Roboto", style="", fname=reg_path)
    pdf.add_font("Roboto", style="B", fname=bold_path)
    
    # Başlık
    pdf.set_font("Roboto", style="B", size=18)
    pdf.cell(0, 12, safe_text("Sozlesme Analiz Raporu"), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Roboto", style="", size=10)
    pdf.cell(0, 6, safe_text(f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}"), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    
    # Risk skoru ve tür
    pdf.set_font("Roboto", style="B", size=12)
    score = analysis.get("risk_skoru", 0)
    pdf.cell(0, 8, safe_text(f"Risk Skoru: {score} / 100"), new_x="LMARGIN", new_y="NEXT")
    
    turu_key = analysis.get("sozlesme_turu", "diger")
    # Emoji'siz tür adı
    turu_map = {
        "auto": "Otomatik Tespit", "kira": "Kira Sozlesmesi",
        "is": "Is Sozlesmesi", "nda": "Gizlilik Sozlesmesi (NDA)",
        "hizmet": "Hizmet Sozlesmesi", "satis": "Satis Sozlesmesi", "diger": "Diger"
    }
    turu = turu_map.get(turu_key, "Diger")
    pdf.cell(0, 8, safe_text(f"Sozlesme Turu: {turu}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Özet
    pdf.set_font("Roboto", style="B", size=14)
    pdf.cell(0, 10, safe_text("Ozet"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Roboto", style="", size=11)
    pdf.multi_cell(0, 6, safe_text(analysis.get("ozet", "Ozet bulunamadi.")))
    pdf.ln(5)
    
    # Genel Değerlendirme
    genel = analysis.get("genel_degerlendirme", "")
    if genel:
        pdf.set_font("Roboto", style="B", size=14)
        pdf.cell(0, 10, safe_text("Genel Degerlendirme"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Roboto", style="", size=11)
        pdf.multi_cell(0, 6, safe_text(genel))
        pdf.ln(5)
    
    # Riskler
    riskler = analysis.get("riskler", [])
    if riskler:
        pdf.set_font("Roboto", style="B", size=14)
        pdf.cell(0, 10, safe_text("Riskler"), new_x="LMARGIN", new_y="NEXT")
        for i, r in enumerate(riskler, 1):
            pdf.set_font("Roboto", style="B", size=11)
            pdf.multi_cell(0, 6, safe_text(f"{i}. Madde: {r.get('madde', '')} (Seviye: {r.get('severity', '')})"))
            pdf.set_font("Roboto", style="", size=11)
            pdf.multi_cell(0, 6, safe_text(f"Aciklama: {r.get('aciklama', '')}"))
            if r.get('oneri'):
                pdf.multi_cell(0, 6, safe_text(f"Oneri: {r.get('oneri', '')}"))
            pdf.ln(3)
    
    # Tavsiyeler
    tavsiyeler = analysis.get("tavsiyeler", [])
    if tavsiyeler:
        pdf.set_font("Roboto", style="B", size=14)
        pdf.cell(0, 10, safe_text("Tavsiyeler"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Roboto", style="", size=11)
        for i, t in enumerate(tavsiyeler, 1):
            pdf.multi_cell(0, 6, safe_text(f"{i}. {t}"))
            pdf.ln(2)

    return pdf.output()

def get_risk_info(score: int) -> tuple[str, str, str]:
    """Risk skoru için etiket, renk ve ikon döndürür."""
    for (lo, hi), (label, color, icon) in RISK_LABELS.items():
        if lo <= score <= hi:
            return label, color, icon
    return "Bilinmiyor", "#94a3b8", "❓"


def check_api_health() -> dict | None:
    """API sağlık durumunu kontrol eder."""
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def analyze_via_api(
    text: str,
    contract_type: str,
    ai_provider: str,
) -> dict | None:
    """API'ye metin gönderir, sonucu döndürür."""
    payload = {
        "metin": text,
        "sozlesme_turu": contract_type if contract_type != "auto" else None,
        "ai_provider": ai_provider,
    }
    try:
        resp = requests.post(
            f"{API_BASE}/analyze",
            json=payload,
            timeout=300,
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            try:
                err_msg = resp.json().get("detail", resp.text)
            except Exception:
                err_msg = resp.text
            st.error(f"⚠️ {err_msg}")
    except requests.exceptions.ConnectionError:
        st.error(
            "🔌 API'ye bağlanılamadı. Lütfen önce FastAPI sunucusunu başlatın:\n"
            "`uvicorn api:app --reload`"
        )
    except Exception as e:
        st.error(f"Bağlantı hatası: {e}")
    return None


def analyze_file_via_api(
    file_bytes: bytes,
    filename: str,
    contract_type: str,
    ai_provider: str,
) -> dict | None:
    """API'ye dosya gönderir."""
    try:
        files = {"file": (filename, file_bytes)}
        data = {
            "sozlesme_turu": contract_type if contract_type != "auto" else "",
            "ai_provider": ai_provider,
        }
        resp = requests.post(
            f"{API_BASE}/analyze/file",
            files=files,
            data=data,
            timeout=300,
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            try:
                err_msg = resp.json().get("detail", resp.text)
            except Exception:
                err_msg = resp.text
            st.error(f"⚠️ {err_msg}")
    except requests.exceptions.ConnectionError:
        st.error("🔌 API'ye bağlanılamadı.")
    except Exception as e:
        st.error(f"Hata: {e}")
    return None


def get_contracts_history() -> list:
    """Sözleşme geçmişini çeker."""
    try:
        resp = requests.get(f"{API_BASE}/contracts?limit=30", timeout=10)
        if resp.status_code == 200:
            return resp.json().get("contracts", [])
    except Exception:
        pass
    return []


def delete_contract_api(contract_id: int) -> bool:
    """Sözleşme siler."""
    try:
        resp = requests.delete(f"{API_BASE}/contracts/{contract_id}", timeout=10)
        return resp.status_code == 200
    except Exception:
        return False


def get_contract_detail(contract_id: int) -> dict | None:
    """Sözleşme detayını çeker."""
    try:
        resp = requests.get(f"{API_BASE}/contracts/{contract_id}", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


# ─── Analiz Sonuçlarını Göster ────────────────────────────────────────────
def render_analysis(analysis: dict, processing_time: float = 0):
    """Analiz sonuçlarını görsel olarak render eder."""

    risk_skoru = analysis.get("risk_skoru", 0)
    label, color, icon = get_risk_info(risk_skoru)
    sozlesme_turu = analysis.get("sozlesme_turu", "diger")
    turu_label = CONTRACT_TYPES.get(sozlesme_turu, sozlesme_turu)

    # ── Hero: Risk Skoru ──────────────────────────────────────────────────
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-size:3em;">{icon}</div>
                <div style="font-size:2.5em; font-weight:800; color:{color};">{risk_skoru}</div>
                <div style="color:rgba(255,255,255,0.7); font-size:0.9em;">Risk Skoru</div>
                <div class="risk-badge" style="background:{color}22; color:{color}; margin-top:8px;">{label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        riskler = analysis.get("riskler", [])
        kritik = sum(1 for r in riskler if r.get("severity") in ("high", "critical"))
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-size:3em;">⚠️</div>
                <div style="font-size:2.5em; font-weight:800; color:#f59e0b;">{len(riskler)}</div>
                <div style="color:rgba(255,255,255,0.7); font-size:0.9em;">Risk Maddesi</div>
                <div style="color:#ef4444; font-size:0.8em; margin-top:8px;">{kritik} kritik/yüksek</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-size:3em;">📄</div>
                <div style="font-size:1.6em; font-weight:700; color:#a78bfa;">{turu_label}</div>
                <div style="color:rgba(255,255,255,0.7); font-size:0.9em; margin-top:8px;">
                    ⏱️ {processing_time:.1f}s analiz süresi
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Risk Bar ──────────────────────────────────────────────────────────
    st.markdown(f"**Risk Göstergesi:** `{risk_skoru}/100`")
    st.progress(risk_skoru / 100)

    st.markdown("---")

    # ── Tab'lar ────────────────────────────────────────────────────────────
    tabs = st.tabs(["📋 Özet", "⚠️ Riskler", "📌 Önemli Maddeler", "💡 Tavsiyeler", "📊 Detaylar"])

    # TAB 1: Özet
    with tabs[0]:
        ozet = analysis.get("ozet", "")
        genel = analysis.get("genel_degerlendirme", "")
        if ozet:
            st.markdown(
                f"""<div class="clause-card">
                    <p style="font-size:1.05em; line-height:1.8; margin:0;">{ozet}</p>
                </div>""",
                unsafe_allow_html=True,
            )
        if genel:
            st.markdown("**⚖️ Genel Değerlendirme:**")
            st.info(genel)

    # TAB 2: Riskler
    with tabs[1]:
        riskler = analysis.get("riskler", [])
        if not riskler:
            st.success("✅ Önemli bir risk tespit edilmedi.")
        else:
            # Sıralama: critical → high → medium → low
            order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            sorted_risks = sorted(
                riskler, key=lambda r: order.get(r.get("severity", "low"), 3)
            )
            for risk in sorted_risks:
                sev = risk.get("severity", "medium")
                c = SEVERITY_COLORS.get(sev, "#94a3b8")
                sev_label = SEVERITY_LABELS.get(sev, sev)
                st.markdown(
                    f"""<div class="risk-card" style="border-left-color:{c};">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <strong style="color:{c}; font-size:1em;">📎 {risk.get('madde','')}</strong>
                            <span class="risk-badge" style="background:{c}22; color:{c}; font-size:0.8em;">{sev_label}</span>
                        </div>
                        <p style="margin:0 0 8px 0; color:rgba(255,255,255,0.85);">{risk.get('aciklama','')}</p>
                        {f'<p style="margin:0; color:#60a5fa; font-size:0.9em;">💡 {risk.get("oneri","")}</p>' if risk.get("oneri") else ""}
                    </div>""",
                    unsafe_allow_html=True,
                )

    # TAB 3: Önemli Maddeler
    with tabs[2]:
        maddeler = analysis.get("onemli_maddeler", [])
        if not maddeler:
            st.info("Önemli madde tespit edilemedi.")
        else:
            for madde in maddeler:
                with st.expander(f"📌 {madde.get('baslik', 'Madde')}  —  `{madde.get('kategori', '')}`"):
                    st.markdown(madde.get("icerik", ""))

    # TAB 4: Tavsiyeler
    with tabs[3]:
        tavsiyeler = analysis.get("tavsiyeler", [])
        if not tavsiyeler:
            st.info("Tavsiye bulunmuyor.")
        else:
            for i, t in enumerate(tavsiyeler, 1):
                st.markdown(
                    f"""<div class="advice-card">
                        <span style="color:#22c55e; font-weight:700;">✓ {i}.</span>
                        <span style="color:rgba(255,255,255,0.9);"> {t}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )

    # TAB 5: Detaylar
    with tabs[4]:
        col_a, col_b = st.columns(2)

        with col_a:
            taraflar = analysis.get("taraflar", {})
            if taraflar:
                st.markdown("#### 👥 Taraflar")
                for key, val in taraflar.items():
                    if isinstance(val, dict):
                        st.markdown(f"**{key}:**")
                        for k, v in val.items():
                            if v:
                                st.markdown(f"- {k}: `{v}`")
                    elif val:
                        st.markdown(f"- **{key}:** {val}")

        with col_b:
            sure = analysis.get("sure_ve_tarihler", {})
            fin = analysis.get("finansal_detaylar", {})

            if sure:
                st.markdown("#### 📅 Süre ve Tarihler")
                for k, v in sure.items():
                    if v and k != "ek_bilgi":
                        st.markdown(f"- **{k}:** {v}")

            if fin:
                st.markdown("#### 💰 Finansal Detaylar")
                for k, v in fin.items():
                    if v and k != "ek_bilgi":
                        st.markdown(f"- **{k}:** {v}")

        # Ham JSON
        with st.expander("🔍 Ham Analiz Verisi (JSON)"):
            st.json(analysis)


# ─── Sidebar ──────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown(
            """<div style='text-align:center; padding:20px 0;'>
                <div style='font-size:2.5em;'>⚖️</div>
                <div style='font-size:1.3em; font-weight:700; color:white;'>AI Contract</div>
                <div style='font-size:1.3em; font-weight:700; color:#a78bfa;'>Analyzer</div>
                <div style='color:rgba(255,255,255,0.5); font-size:0.75em; margin-top:5px;'>v1.0.0</div>
            </div>""",
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # API Durumu
        health = check_api_health()
        if health:
            st.markdown("**🟢 API Durumu:** Çevrimiçi")
            g_status = "✅ Aktif" if health.get("gemini_available") else "❌ Kapalı"
            r_status = "✅ Aktif" if health.get("groq_available") else "❌ Kapalı"
            st.markdown(f"- Gemini: {g_status}")
            st.markdown(f"- Groq: {r_status}")
            st.markdown(f"- `{health.get('database','')}`")
        else:
            st.markdown("**🔴 API Durumu:** Çevrimdışı")
            st.warning("Önce API'yi başlatın:\n```\nuvicorn api:app --reload\n```")

        st.markdown("---")

        # Navigasyon
        page = st.radio(
            "Navigasyon",
            ["🔍 Sözleşme Analizi", "📚 Geçmiş Analizler", "ℹ️ Hakkında"],
            label_visibility="collapsed",
        )

        st.markdown("---")

        # AI Provider
        st.markdown("**⚙️ AI Ayarları**")
        ai_provider = st.selectbox(
            "AI Sağlayıcı",
            ["gemini", "groq"],
            format_func=lambda x: "🤖 Google Gemini" if x == "gemini" else "⚡ Groq LLaMA",
        )

        return page, ai_provider


# ─── Sayfa: Analiz ────────────────────────────────────────────────────────
def render_analyze_page(ai_provider: str):
    st.markdown(
        """<div class="hero-header">
            <p class="hero-title">⚖️ AI Contract Analyzer</p>
            <p class="hero-subtitle">Sözleşmelerinizi yapay zeka ile analiz edin — riskler, önemli maddeler ve tavsiyeler</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── Giriş Modu ────────────────────────────────────────────────────────
    input_tab1, input_tab2 = st.tabs(["📝 Metin Yapıştır", "📁 Dosya Yükle"])

    contract_text = ""
    uploaded_file = None
    filename = None

    with input_tab1:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            contract_text = st.text_area(
                "Sözleşme Metni",
                height=300,
                placeholder="Sözleşme metninizi buraya yapıştırın...\n\nDesteklenen türler: Kira, İş, NDA, Hizmet, Satış",
                help="Minimum 50 karakter, maximum 200.000 karakter",
            )
        with col_right:
            if contract_text:
                words = len(contract_text.split())
                chars = len(contract_text)
                st.markdown(
                    f"""<div class="metric-card">
                        <div style="font-size:1.8em;">📊</div>
                        <div style="color:white; font-weight:700; font-size:1.1em;">{chars:,}</div>
                        <div style="color:rgba(255,255,255,0.6); font-size:0.8em;">karakter</div>
                        <hr style="border-color:rgba(255,255,255,0.1); margin:10px 0;">
                        <div style="color:white; font-weight:700; font-size:1.1em;">{words:,}</div>
                        <div style="color:rgba(255,255,255,0.6); font-size:0.8em;">kelime</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

    with input_tab2:
        col_l, col_r = st.columns([2, 1])
        with col_l:
            uploaded_file = st.file_uploader(
                "Dosya Yükle",
                type=["pdf", "docx", "doc", "txt"],
                help="Maksimum 10 MB. PDF, DOCX veya TXT",
            )
        with col_r:
            if uploaded_file:
                size_kb = len(uploaded_file.getvalue()) / 1024
                st.markdown(
                    f"""<div class="metric-card">
                        <div style="font-size:2em;">📁</div>
                        <div style="color:white; font-weight:600;">{uploaded_file.name}</div>
                        <div style="color:rgba(255,255,255,0.6); font-size:0.85em;">{size_kb:.1f} KB</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

    # ── Sözleşme Türü + Analiz Butonu ─────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_type, col_btn = st.columns([2, 1])

    with col_type:
        selected_type = st.selectbox(
            "Sözleşme Türü",
            list(CONTRACT_TYPES.keys()),
            format_func=lambda x: CONTRACT_TYPES[x],
            help="'Otomatik Tespit' seçilirse AI türü kendisi belirler",
        )

    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_clicked = st.button("🔍 Sözleşmeyi Analiz Et", help="Girilen metni ya da yüklenen dosyayı analiz eder", use_container_width=True)

    # ── Analiz ────────────────────────────────────────────────────────────
    if analyze_clicked:
        has_text = bool(contract_text and contract_text.strip())
        has_file = bool(uploaded_file)

        if not has_text and not has_file:
            st.warning("⚠️ Lütfen sözleşme metni girin veya dosya yükleyin.")
            return

        with st.spinner("🤖 Yapay zeka analiz ediyor... Bu işlem 15-60 saniye sürebilir."):
            progress_bar = st.progress(0)
            for i in range(0, 80, 10):
                time.sleep(0.3)
                progress_bar.progress(i)

            if has_file:
                result = analyze_file_via_api(
                    uploaded_file.getvalue(),
                    uploaded_file.name,
                    selected_type,
                    ai_provider,
                )
            else:
                result = analyze_via_api(contract_text, selected_type, ai_provider)

            progress_bar.progress(100)

        if result and result.get("success"):
            st.success("✅ Analiz tamamlandı!")
            st.markdown("---")
            analysis = result.get("analysis", {})
            proc_time = result.get("processing_time", 0)
            render_analysis(analysis, proc_time)

            # İndirme butonu
            try:
                pdf_bytes = generate_pdf_report(result)
                st.download_button(
                    "⬇️ Analiz Raporunu İndir (PDF)",
                    data=bytes(pdf_bytes),
                    file_name=f"analiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"PDF oluşturulurken bir hata oluştu: {e}")
                # Hata durumunda JSON'a geri dön
                json_str = json.dumps(result, ensure_ascii=False, indent=2)
                st.download_button(
                    "⬇️ Analiz Raporunu İndir (JSON)",
                    data=json_str,
                    file_name=f"analiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True,
                )
        else:
            progress_bar.empty()


# ─── Sayfa: Geçmiş ────────────────────────────────────────────────────────
def render_history_page():
    st.markdown("## 📚 Geçmiş Analizler")
    contracts = get_contracts_history()

    if not contracts:
        st.info("Henüz analiz yapılmamış. İlk sözleşmenizi analiz edin!")
        return

    st.markdown(f"**Toplam {len(contracts)} sözleşme bulundu.**")

    for c in contracts:
        score = c.get("risk_skoru", 0) or 0
        label, color, icon = get_risk_info(score)
        turu = CONTRACT_TYPES.get(c.get("sozlesme_turu", "diger"), "📄 Diğer")
        tarih = c.get("analiz_tarihi", "")
        if tarih:
            try:
                tarih = datetime.fromisoformat(tarih).strftime("%d.%m.%Y %H:%M")
            except Exception:
                pass

        col1, col2 = st.columns([6, 1])
        with col1:
            st.markdown(
                f"""<div class="history-item">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-weight:700; color:white;">#{c['id']} — {c.get('dosya_adi','Sözleşme')}</span>
                            <span style="margin-left:10px; color:rgba(255,255,255,0.6); font-size:0.85em;">{turu}</span>
                        </div>
                        <div>
                            <span class="risk-badge" style="background:{color}22; color:{color}; font-size:0.85em;">{icon} {score}/100</span>
                        </div>
                    </div>
                    <div style="color:rgba(255,255,255,0.5); font-size:0.82em; margin-top:5px;">
                        📅 {tarih}
                    </div>
                    <div style="color:rgba(255,255,255,0.7); font-size:0.9em; margin-top:6px;">
                        {c.get('metin_ozeti','')[:120]}...
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

        with col2:
            if st.button("🗑️", key=f"del_{c['id']}", help="Sil"):
                if delete_contract_api(c["id"]):
                    st.success("Silindi!")
                    st.rerun()

        # Detay görüntüleme
        state_key = f"view_state_{c['id']}"
        if state_key not in st.session_state:
            st.session_state[state_key] = False

        btn_label = "❌ Detayları Kapat" if st.session_state[state_key] else "📋 Detayları Gör"
        if st.button(btn_label, key=f"view_btn_{c['id']}", use_container_width=True):
            st.session_state[state_key] = not st.session_state[state_key]
            st.rerun()

        if st.session_state[state_key]:
            detail = get_contract_detail(c["id"])
            if detail and detail.get("analiz"):
                st.markdown("---")
                st.markdown(f"### 📄 Analiz Detayı #{c['id']} — {c.get('dosya_adi','')}")
                with st.container():
                    stats = detail.get("metin_istatistikleri", {})
                    s1, s2, s3 = st.columns(3)
                    s1.metric("Kelime", stats.get("kelime_sayisi", "-"))
                    s2.metric("Karakter", stats.get("karakter_sayisi", "-"))
                    s3.metric("Okuma Süresi", stats.get("tahmini_okuma_suresi", "-"))
                    render_analysis(detail["analiz"])


# ─── Sayfa: Hakkında ──────────────────────────────────────────────────────
def render_about_page():
    st.markdown("## ℹ️ Hakkında")

    st.markdown(
        "<div style='background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.12); "
        "border-radius:16px; padding:24px 28px; margin-bottom:20px;'>"
        "<h3 style='color:#a78bfa; margin-top:0;'>⚖️ AI Contract Analyzer</h3>"
        "<p style='color:rgba(255,255,255,0.85); font-size:1.02em; line-height:1.8; margin:0;'>"
        "Yapay zeka destekli sözleşme analiz sistemi. Hukuki belgelerinizi saniyeler içinde analiz eder, "
        "riskleri tespit eder ve tavsiyeler sunar."
        "</p></div>",
        unsafe_allow_html=True,
    )

    # ── Teknoloji Stack ──────────────────────────────────────────────────
    st.markdown("### 🛠️ Teknoloji Stack")
    st.markdown("""
| Katman | Teknoloji |
|--------|-----------|
| 🖥️ Frontend | Streamlit |
| ⚙️ Backend | FastAPI |
| 🤖 AI | Gemini 1.5 Flash / Groq LLaMA |
| 🗄️ Veritabanı | SQLite + SQLAlchemy |
| ✅ Doğrulama | Pydantic v2 |
| 📄 PDF Okuma | PyMuPDF (fitz) |
| 📝 DOCX Okuma | python-docx |
""")

    st.markdown("---")

    # ── Desteklenen Türler ───────────────────────────────────────────────
    st.markdown("### 📋 Desteklenen Sözleşme Türleri")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("- 🏠 Kira Sözleşmesi")
        st.markdown("- 💼 İş Sözleşmesi")
        st.markdown("- 🔒 Gizlilik Sözleşmesi (NDA)")
    with col2:
        st.markdown("- 🛠️ Hizmet Sözleşmesi")
        st.markdown("- 🛒 Satış Sözleşmesi")
        st.markdown("- 🤖 Otomatik Tespit")

    st.markdown("---")

    # ── Yasal Uyarı ─────────────────────────────────────────────────────
    st.markdown("### ⚠️ Yasal Uyarı")
    st.warning(
        "Bu araç **bilgilendirme amaçlıdır**. Hukuki tavsiye niteliği taşımaz. "
        "Önemli kararlar için bir avukattan profesyonel destek alınız."
    )

    st.markdown("---")

    # ── Öneri ve Geri Bildirim ──────────────────────────────────────────────────
    st.markdown("### 💡 Öneri ve Geri Bildirim")
    st.info(
        "Sistemle ilgili önerileriniz, hata bildirimleriniz ve geri bildirimleriniz için "
        "benimle iletişime geçebilirsiniz:\n\n"
        "📧 **[betulaltinkaynakdemirel@gmail.com](https://mail.google.com/mail/?view=cm&fs=1&to=betulaltinkaynakdemirel@gmail.com)**"
    )

    st.markdown("---")

    # ── Geliştirici ─────────────────────────────────────────────────────
    st.markdown(
        "<div style='text-align:center; padding:20px; "
        "background:linear-gradient(135deg,rgba(99,102,241,0.15),rgba(139,92,246,0.15)); "
        "border:1px solid rgba(139,92,246,0.4); border-radius:14px;'>"
        "<div style='color:rgba(255,255,255,0.6); font-size:0.9em; margin-bottom:6px;'>👩‍💻 Proje Geliştiricisi</div>"
        "<div style='color:#a78bfa; font-weight:700; font-size:1.2em; letter-spacing:0.5px;'>"
        "Betül Altınkaynak Demirel</div>"
        "</div>",
        unsafe_allow_html=True,
    )


@st.cache_resource
def get_api_lock():
    return threading.Lock()

def start_api_if_offline():
    """
    FastAPI sunucusunu Streamlit ile aynı process içinde
    daemon thread olarak başlatır. Her sayfa yüklemesinde API'nin
    çevrimiçi olup olmadığını kontrol eder.
    """
    if check_api_health():
        return  # Zaten çalışıyor

    lock = get_api_lock()
    with lock:
        # Kilit alındıktan sonra tekrar kontrol et (race condition önleme)
        if check_api_health():
            return

        def _run_server():
            import uvicorn
            # Zaten port kullanımdaysa exception fırlatır, thread kapanır
            try:
                uvicorn.run(
                    "api:app",
                    host="localhost",
                    port=8000,
                    log_level="error",
                )
            except Exception as e:
                print(f"API baslatilamadi: {e}")

        thread = threading.Thread(target=_run_server, daemon=True, name="fastapi-server")
        thread.start()

        # API'nin ayağa kalkmasını bekle (en fazla 20 saniye)
        with st.spinner("API sunucusu başlatılıyor, lütfen bekleyin..."):
            for _ in range(20):
                time.sleep(1)
                if check_api_health():
                    break


# ─── Ana Uygulama ─────────────────────────────────────────────────────────
def main():
    start_api_if_offline()
    page, ai_provider = render_sidebar()

    if page == "🔍 Sözleşme Analizi":
        render_analyze_page(ai_provider)
    elif page == "📚 Geçmiş Analizler":
        render_history_page()
    elif page == "ℹ️ Hakkında":
        render_about_page()


if __name__ == "__main__":
    main()
