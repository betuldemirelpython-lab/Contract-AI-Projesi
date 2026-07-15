"""
app.py - Streamlit Arayüzü
AI Contract Analyzer - Yapay Zeka Destekli Sözleşme Analiz Sistemi (Türkçe ve İngilizce Destekli)
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

CONTRACT_TYPES_TR = {
    "auto": "🤖 Otomatik Tespit",
    "kira": "🏠 Kira Sözleşmesi",
    "is": "💼 İş Sözleşmesi",
    "nda": "🔒 Gizlilik Sözleşmesi (NDA)",
    "hizmet": "🛠️ Hizmet Sözleşmesi",
    "satis": "🛒 Satış Sözleşmesi",
    "diger": "📄 Diğer",
}

CONTRACT_TYPES_EN = {
    "auto": "🤖 Automatic Detection",
    "kira": "🏠 Lease Agreement",
    "is": "💼 Employment Contract",
    "nda": "🔒 Nondisclosure Agreement (NDA)",
    "hizmet": "🛠️ Service Agreement",
    "satis": "🛒 Sales Contract",
    "diger": "📄 Other",
}

SEVERITY_COLORS = {
    "low": "#22c55e",
    "medium": "#f59e0b",
    "high": "#ef4444",
    "critical": "#7c3aed",
}

SEVERITY_LABELS_TR = {
    "low": "🟢 Düşük",
    "medium": "🟡 Orta",
    "high": "🔴 Yüksek",
    "critical": "🟣 Kritik",
}

SEVERITY_LABELS_EN = {
    "low": "🟢 Low",
    "medium": "🟡 Medium",
    "high": "🔴 High",
    "critical": "🟣 Critical",
}

RISK_LABELS_TR = {
    (0, 25): ("Düşük Risk", "#22c55e", "✅"),
    (26, 50): ("Orta Risk", "#f59e0b", "⚠️"),
    (51, 75): ("Yüksek Risk", "#ef4444", "❌"),
    (76, 100): ("Kritik Risk", "#7c3aed", "🚨"),
}

RISK_LABELS_EN = {
    (0, 25): ("Low Risk", "#22c55e", "✅"),
    (26, 50): ("Medium Risk", "#f59e0b", "⚠️"),
    (51, 75): ("High Risk", "#ef4444", "❌"),
    (76, 100): ("Critical Risk", "#7c3aed", "🚨"),
}

# ─── Çeviriler (Translations) ─────────────────────────────────────────────
T = {
    "tr": {
        "page_title": "AI Contract Analyzer",
        "nav_analyze": "🔍 Sözleşme Analizi",
        "nav_history": "📚 Geçmiş Analizler",
        "nav_about": "ℹ️ Hakkında",
        "api_online": "🟢 API Durumu: Çevrimiçi",
        "api_offline": "🔴 API Durumu: Çevrimdışı",
        "api_warn": "Önce API'yi başlatın:\n```\nuvicorn api:app --reload\n```",
        "ai_settings": "⚙️ AI Ayarları",
        "ai_provider": "AI Sağlayıcı",
        "hero_title": "⚖️ AI Contract Analyzer",
        "hero_subtitle": "Sözleşmelerinizi yapay zeka ile analiz edin — riskler, önemli maddeler ve tavsiyeler",
        "tab_paste": "📝 Metin Yapıştır",
        "tab_upload": "📁 Dosya Yükle",
        "text_area_label": "Sözleşme Metni",
        "text_area_placeholder": "Sözleşme metninizi buraya yapıştırın...\n\nDesteklenen türler: Kira, İş, NDA, Hizmet, Satış",
        "text_area_help": "Minimum 50 karakter, maximum 200.000 karakter",
        "char_count": "karakter",
        "word_count": "kelime",
        "file_uploader_label": "Dosya Yükle",
        "file_uploader_help": "Maksimum 10 MB. PDF, DOCX veya TXT",
        "file_uploaded_name": "Yüklenen Dosya",
        "contract_type": "Sözleşme Türü",
        "contract_type_help": "'Otomatik Tespit' seçilirse AI türü kendisi belirler",
        "analyze_btn": "🔍 Sözleşmeyi Analiz Et",
        "analyze_btn_help": "Girilen metni ya da yüklenen dosyayı analiz eder",
        "warning_empty": "⚠️ Lütfen sözleşme metni girin veya dosya yükleyin.",
        "spinner_analyzing": "🤖 Yapay zeka analiz ediyor... Bu işlem 15-60 saniye sürebilir.",
        "success_done": "✅ Analiz tamamlandı!",
        "risk_score": "Risk Skoru",
        "risk_items": "Risk Maddesi",
        "risk_crit_high": "kritik/yüksek",
        "processing_time": "analiz süresi",
        "risk_indicator": "Risk Göstergesi",
        "tab_summary": "📋 Özet",
        "tab_risks": "⚠️ Riskler",
        "tab_clauses": "📌 Önemli Maddeler",
        "tab_advice": "💡 Tavsiyeler",
        "tab_details": "📊 Detaylar",
        "general_evaluation": "⚖️ Genel Değerlendirme:",
        "no_risks": "✅ Önemli bir risk tespit edilmedi.",
        "no_advice": "Tavsiye bulunmuyor.",
        "no_clauses": "Önemli madde tespit edilemedi.",
        "parties": "👥 Taraflar",
        "duration_dates": "📅 Süre ve Tarihler",
        "financial_details": "💰 Finansal Detaylar",
        "raw_json": "🔍 Ham Analiz Verisi (JSON)",
        "download_pdf": "⬇️ Analiz Raporunu İndir (PDF)",
        "download_json": "⬇️ Analiz Raporunu İndir (JSON)",
        "pdf_error": "PDF oluşturulurken bir hata oluştu: {e}",
        "history_title": "📚 Geçmiş Analizler",
        "history_empty": "Henüz analiz yapılmamış. İlk sözleşmenizi analiz edin!",
        "history_total": "Toplam {count} sözleşme bulundu.",
        "history_deleted": "Silindi!",
        "history_view_detail": "📋 Detayları Gör",
        "history_close_detail": "❌ Detayları Kapat",
        "history_detail_title": "📄 Analiz Detayı #{id} — {filename}",
        "history_word": "Kelime",
        "history_char": "Karakter",
        "history_reading_time": "Okuma Süresi",
        "about_title": "ℹ️ Hakkında",
        "about_desc": "Yapay zeka destekli sözleşme analiz sistemi. Hukuki belgelerinizi saniyeler içinde analiz eder, riskleri tespit eder ve tavsiyeler sunar.",
        "about_tech_title": "🛠️ Teknoloji Stack",
        "about_types_title": "📋 Desteklenen Sözleşme Türleri",
        "about_warning_title": "⚠️ Yasal Uyarı",
        "about_warning_body": "Bu araç **bilgilendirme amaçlıdır**. Hukuki tavsiye niteliği taşımaz. Önemli kararlar için bir avukattan profesyonel destek alınız.",
        "about_feedback_title": "💡 Öneri ve Geri Bildirim",
        "about_feedback_body": "Sistemle ilgili önerileriniz, hata bildirimleriniz ve geri bildirimleriniz için benimle iletişime geçebilirsiniz:\n\n📧 **[betulaltinkaynakdemirel@gmail.com](https://mail.google.com/mail/?view=cm&fs=1&to=betulaltinkaynakdemirel@gmail.com)**",
        "about_dev_title": "👩‍💻 Proje Geliştiricisi",
        "about_dev_name": "Betül Altınkaynak Demirel",
        "api_starting": "API sunucusu başlatılıyor, lütfen bekleyin...",
        "api_err_not_connected": "🔌 API'ye bağlanılamadı. Lütfen önce FastAPI sunucusunu başlatın:\n`uvicorn api:app --reload`",
        "api_err_generic": "Bağlantı hatası: {e}",
        "file_btn_text": "Dosya Seç",
    },
    "en": {
        "page_title": "AI Contract Analyzer",
        "nav_analyze": "🔍 Contract Analysis",
        "nav_history": "📚 Analysis History",
        "nav_about": "ℹ️ About",
        "api_online": "🟢 API Status: Online",
        "api_offline": "🔴 API Status: Offline",
        "api_warn": "Please start the API first:\n```\nuvicorn api:app --reload\n```",
        "ai_settings": "⚙️ AI Settings",
        "ai_provider": "AI Provider",
        "hero_title": "⚖️ AI Contract Analyzer",
        "hero_subtitle": "Analyze your contracts with artificial intelligence — risks, key clauses, and recommendations",
        "tab_paste": "📝 Paste Text",
        "tab_upload": "📁 Upload File",
        "text_area_label": "Contract Text",
        "text_area_placeholder": "Paste your contract text here...\n\nSupported types: Lease, Employment, NDA, Service, Sales",
        "text_area_help": "Minimum 50 characters, maximum 200,000 characters",
        "char_count": "characters",
        "word_count": "words",
        "file_uploader_label": "Upload File",
        "file_uploader_help": "Maximum 10 MB. PDF, DOCX or TXT",
        "file_uploaded_name": "Uploaded File",
        "contract_type": "Contract Type",
        "contract_type_help": "If 'Automatic Detection' is selected, AI will determine the type itself",
        "analyze_btn": "🔍 Analyze Contract",
        "analyze_btn_help": "Analyzes the pasted text or uploaded file",
        "warning_empty": "⚠️ Please enter contract text or upload a file.",
        "spinner_analyzing": "🤖 AI is analyzing... This process may take 15-60 seconds.",
        "success_done": "✅ Analysis completed!",
        "risk_score": "Risk Score",
        "risk_items": "Risk Clauses",
        "risk_crit_high": "critical/high",
        "processing_time": "analysis time",
        "risk_indicator": "Risk Indicator",
        "tab_summary": "📋 Summary",
        "tab_risks": "⚠️ Risks",
        "tab_clauses": "📌 Key Clauses",
        "tab_advice": "💡 Recommendations",
        "tab_details": "📊 Details",
        "general_evaluation": "⚖️ General Evaluation:",
        "no_risks": "✅ No significant risks detected.",
        "no_advice": "No recommendations found.",
        "no_clauses": "No key clauses detected.",
        "parties": "👥 Parties",
        "duration_dates": "📅 Duration and Dates",
        "financial_details": "💰 Financial Details",
        "raw_json": "🔍 Raw Analysis Data (JSON)",
        "download_pdf": "⬇️ Download Analysis Report (PDF)",
        "download_json": "⬇️ Download Analysis Report (JSON)",
        "pdf_error": "An error occurred while generating PDF: {e}",
        "history_title": "📚 Analysis History",
        "history_empty": "No analysis done yet. Analyze your first contract!",
        "history_total": "Total {count} contracts found.",
        "history_deleted": "Deleted!",
        "history_view_detail": "📋 View Details",
        "history_close_detail": "❌ Close Details",
        "history_detail_title": "📄 Analysis Detail #{id} — {filename}",
        "history_word": "Words",
        "history_char": "Characters",
        "history_reading_time": "Reading Time",
        "about_title": "ℹ️ About",
        "about_desc": "AI-powered contract analysis system. Analyzes your legal documents in seconds, detects risks and provides recommendations.",
        "about_tech_title": "🛠️ Technology Stack",
        "about_types_title": "📋 Supported Contract Types",
        "about_warning_title": "⚠️ Disclaimer",
        "about_warning_body": "This tool is for **information purposes only**. It does not constitute legal advice. For important decisions, please obtain professional support from a lawyer.",
        "about_feedback_title": "💡 Suggestions & Feedback",
        "about_feedback_body": "For suggestions, bug reports, and feedback, you can contact me at:\n\n📧 **[betulaltinkaynakdemirel@gmail.com](https://mail.google.com/mail/?view=cm&fs=1&to=betulaltinkaynakdemirel@gmail.com)**",
        "about_dev_title": "👩‍💻 Project Developer",
        "about_dev_name": "Betül Altınkaynak Demirel",
        "api_starting": "API server is starting, please wait...",
        "api_err_not_connected": "🔌 Could not connect to API. Please start FastAPI server first:\n`uvicorn api:app --reload`",
        "api_err_generic": "Connection error: {e}",
        "file_btn_text": "Select File",
    }
}

# ─── CSS Stilleri ─────────────────────────────────────────────────────────
CSS_STYLE = """
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Ana Font (Güvenli atama, ikonları bozmaz) */
    html, body, p, h1, h2, h3, h4, h5, h6, label {
        font-family: 'Inter', sans-serif;
    }

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
        content: "__FILE_BTN_TEXT__";
        color: white;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: rgba(255,255,255,0.04) !important;
        border: 2px dashed rgba(99,102,241,0.4) !important;
        border-radius: 14px !important;
    }
</style>
"""


# ─── Yardımcı Fonksiyonlar ────────────────────────────────────────────────
@st.cache_resource
def get_fonts():
    """PDF için fontları indirir ve yollarını döner."""
    fonts_dir = "fonts"
    if not os.path.exists(fonts_dir):
        os.makedirs(fonts_dir)
    reg_path = os.path.join(fonts_dir, "Roboto-Regular.ttf")
    bold_path = os.path.join(fonts_dir, "Roboto-Bold.ttf")
    
    try:
        if not os.path.exists(reg_path):
            r = requests.get("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf", timeout=15)
            r.raise_for_status()
            with open(reg_path, "wb") as f:
                f.write(r.content)
        if not os.path.exists(bold_path):
            r = requests.get("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf", timeout=15)
            r.raise_for_status()
            with open(bold_path, "wb") as f:
                f.write(r.content)
    except Exception as e:
        print(f"Font indirme hatası: {e}")
        raise RuntimeError(f"Font dosyaları indirilemedi: {e}")

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


def generate_pdf_report(result_dict: dict, lang: str = "tr") -> bytes:
    """JSON analiz sonucunu PDF bytes dizisine çevirir."""
    analysis = result_dict.get("analysis", {})
    reg_path, bold_path = get_fonts()
    
    pdf = FPDF()
    pdf.set_margins(left=20, top=20, right=20)  # Yeterli margin
    pdf.add_page()
    pdf.add_font("Roboto", style="", fname=reg_path)
    pdf.add_font("Roboto", style="B", fname=bold_path)
    
    pdf_t = {
        "tr": {
            "title": "Sozlesme Analiz Raporu",
            "date": "Tarih",
            "risk_score": "Risk Skoru",
            "type": "Sozlesme Turu",
            "summary": "Ozet",
            "no_summary": "Ozet bulunamadi.",
            "evaluation": "Genel Degerlendirme",
            "risks": "Riskler",
            "clause": "Madde",
            "level": "Seviye",
            "description": "Aciklama",
            "suggestion": "Oneri",
            "recommendations": "Tavsiyeler",
        },
        "en": {
            "title": "Contract Analysis Report",
            "date": "Date",
            "risk_score": "Risk Score",
            "type": "Contract Type",
            "summary": "Summary",
            "no_summary": "Summary not found.",
            "evaluation": "General Evaluation",
            "risks": "Risks",
            "clause": "Clause",
            "level": "Level",
            "description": "Description",
            "suggestion": "Recommendation",
            "recommendations": "Recommendations",
        }
    }[lang]

    # Başlık
    pdf.set_font("Roboto", style="B", size=18)
    pdf.set_x(pdf.l_margin)
    pdf.cell(pdf.epw, 12, safe_text(pdf_t["title"]), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Roboto", style="", size=10)
    pdf.set_x(pdf.l_margin)
    pdf.cell(pdf.epw, 6, safe_text(f"{pdf_t['date']}: {datetime.now().strftime('%d.%m.%Y %H:%M')}"), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    
    # Risk skoru ve tür
    pdf.set_font("Roboto", style="B", size=12)
    score = analysis.get("risk_skoru", 0)
    pdf.set_x(pdf.l_margin)
    pdf.cell(pdf.epw, 8, safe_text(f"{pdf_t['risk_score']}: {score} / 100"), new_x="LMARGIN", new_y="NEXT")
    
    turu_key = analysis.get("sozlesme_turu", "diger")
    turu_map_tr = {
        "auto": "Otomatik Tespit", "kira": "Kira Sozlesmesi",
        "is": "Is Sozlesmesi", "nda": "Gizlilik Sozlesmesi (NDA)",
        "hizmet": "Hizmet Sozlesmesi", "satis": "Satis Sozlesmesi", "diger": "Diger"
    }
    turu_map_en = {
        "auto": "Automatic Detection", "kira": "Lease Agreement",
        "is": "Employment Contract", "nda": "NDA",
        "hizmet": "Service Agreement", "satis": "Sales Contract", "diger": "Other"
    }
    turu_map = turu_map_tr if lang == "tr" else turu_map_en
    turu = turu_map.get(turu_key, "Diger" if lang == "tr" else "Other")
    pdf.set_x(pdf.l_margin)
    pdf.cell(pdf.epw, 8, safe_text(f"{pdf_t['type']}: {turu}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Özet
    pdf.set_font("Roboto", style="B", size=14)
    pdf.set_x(pdf.l_margin)
    pdf.cell(pdf.epw, 10, safe_text(pdf_t["summary"]), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Roboto", style="", size=11)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, 6, safe_text(analysis.get("ozet", pdf_t["no_summary"])))
    pdf.ln(5)
    
    # Genel Değerlendirme
    genel = analysis.get("genel_degerlendirme", "")
    if genel:
        pdf.set_font("Roboto", style="B", size=14)
        pdf.set_x(pdf.l_margin)
        pdf.cell(pdf.epw, 10, safe_text(pdf_t["evaluation"]), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Roboto", style="", size=11)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pdf.epw, 6, safe_text(genel))
        pdf.ln(5)
    
    # Riskler
    riskler = analysis.get("riskler", [])
    if riskler:
        pdf.set_font("Roboto", style="B", size=14)
        pdf.set_x(pdf.l_margin)
        pdf.cell(pdf.epw, 10, safe_text(pdf_t["risks"]), new_x="LMARGIN", new_y="NEXT")
        
        severity_map = {
            "tr": {"low": "Dusuk", "medium": "Orta", "high": "Yuksek", "critical": "Kritik"},
            "en": {"low": "Low", "medium": "Medium", "high": "High", "critical": "Critical"}
        }[lang]
        
        for i, r in enumerate(riskler, 1):
            pdf.set_font("Roboto", style="B", size=11)
            pdf.set_x(pdf.l_margin)
            sev = r.get("severity", "medium")
            sev_val = severity_map.get(sev, sev)
            pdf.multi_cell(pdf.epw, 6, safe_text(f"{i}. {pdf_t['clause']}: {r.get('madde', '')} ({pdf_t['level']}: {sev_val})"))
            pdf.set_font("Roboto", style="", size=11)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 6, safe_text(f"{pdf_t['description']}: {r.get('aciklama', '')}"))
            if r.get('oneri'):
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(pdf.epw, 6, safe_text(f"{pdf_t['suggestion']}: {r.get('oneri', '')}"))
            pdf.ln(3)
    
    # Tavsiyeler
    tavsiyeler = analysis.get("tavsiyeler", [])
    if tavsiyeler:
        pdf.set_font("Roboto", style="B", size=14)
        pdf.set_x(pdf.l_margin)
        pdf.cell(pdf.epw, 10, safe_text(pdf_t["recommendations"]), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Roboto", style="", size=11)
        for i, t in enumerate(tavsiyeler, 1):
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 6, safe_text(f"{i}. {t}"))
            pdf.ln(2)

    return pdf.output()


def get_risk_info(score: int, lang: str = "tr") -> tuple[str, str, str]:
    """Risk skoru için etiket, renk ve ikon döndürür."""
    labels = RISK_LABELS_TR if lang == "tr" else RISK_LABELS_EN
    for (lo, hi), (label, color, icon) in labels.items():
        if lo <= score <= hi:
            return label, color, icon
    return ("Bilinmiyor" if lang == "tr" else "Unknown"), "#94a3b8", "❓"


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
    lang: str = "tr",
) -> dict | None:
    """API'ye metin gönderir, sonucu döndürür."""
    payload = {
        "metin": text,
        "sozlesme_turu": contract_type if contract_type != "auto" else None,
        "ai_provider": ai_provider,
        "lang": lang,
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
        st.error(T[lang]["api_err_not_connected"])
    except Exception as e:
        st.error(T[lang]["api_err_generic"].format(e=e))
    return None


def analyze_file_via_api(
    file_bytes: bytes,
    filename: str,
    contract_type: str,
    ai_provider: str,
    lang: str = "tr",
) -> dict | None:
    """API'ye dosya gönderir."""
    try:
        files = {"file": (filename, file_bytes)}
        data = {
            "sozlesme_turu": contract_type if contract_type != "auto" else "",
            "ai_provider": ai_provider,
            "lang": lang,
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
        st.error("🔌 API'ye bağlanılamadı." if lang == "tr" else "🔌 Could not connect to API.")
    except Exception as e:
        st.error(f"Hata: {e}" if lang == "tr" else f"Error: {e}")
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
def render_analysis(analysis: dict, processing_time: float = 0, lang: str = "tr"):
    """Analiz sonuçlarını görsel olarak render eder."""
    t = T[lang]
    risk_skoru = analysis.get("risk_skoru", 0)
    label, color, icon = get_risk_info(risk_skoru, lang=lang)
    sozlesme_turu = analysis.get("sozlesme_turu", "diger")
    
    contract_types = CONTRACT_TYPES_TR if lang == "tr" else CONTRACT_TYPES_EN
    turu_label = contract_types.get(sozlesme_turu, sozlesme_turu)

    # ── Hero: Risk Skoru ──────────────────────────────────────────────────
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-size:3em;">{icon}</div>
                <div style="font-size:2.5em; font-weight:800; color:{color};">{risk_skoru}</div>
                <div style="color:rgba(255,255,255,0.7); font-size:0.9em;">{t["risk_score"]}</div>
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
                <div style="color:rgba(255,255,255,0.7); font-size:0.9em;">{t["risk_items"]}</div>
                <div style="color:#ef4444; font-size:0.8em; margin-top:8px;">{kritik} {t["risk_crit_high"]}</div>
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
                    ⏱️ {processing_time:.1f}s {t["processing_time"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Risk Bar ──────────────────────────────────────────────────────────
    st.markdown(f"**{t['risk_indicator']}:** `{risk_skoru}/100`")
    st.progress(risk_skoru / 100)

    st.markdown("---")

    # ── Tab'lar ────────────────────────────────────────────────────────────
    tabs = st.tabs([t["tab_summary"], t["tab_risks"], t["tab_clauses"], t["tab_advice"], t["tab_details"]])

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
            st.markdown(f"**{t['general_evaluation']}**")
            st.info(genel)

    # TAB 2: Riskler
    with tabs[1]:
        riskler = analysis.get("riskler", [])
        if not riskler:
            st.success(t["no_risks"])
        else:
            # Sıralama: critical → high → medium → low
            order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            sorted_risks = sorted(
                riskler, key=lambda r: order.get(r.get("severity", "low"), 3)
            )
            
            severity_labels = SEVERITY_LABELS_TR if lang == "tr" else SEVERITY_LABELS_EN
            
            for risk in sorted_risks:
                sev = risk.get("severity", "medium")
                c = SEVERITY_COLORS.get(sev, "#94a3b8")
                sev_label = severity_labels.get(sev, sev)
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
            st.info(t["no_clauses"])
        else:
            for madde in maddeler:
                with st.expander(f"📌 {madde.get('baslik', 'Madde')}  —  `{madde.get('kategori', '')}`"):
                    st.markdown(madde.get("icerik", ""))

    # TAB 4: Tavsiyeler
    with tabs[3]:
        tavsiyeler = analysis.get("tavsiyeler", [])
        if not tavsiyeler:
            st.info(t["no_advice"])
        else:
            for i, t_val in enumerate(tavsiyeler, 1):
                st.markdown(
                    f"""<div class="advice-card">
                        <span style="color:#22c55e; font-weight:700;">✓ {i}.</span>
                        <span style="color:rgba(255,255,255,0.9);"> {t_val}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )

    # TAB 5: Detaylar
    with tabs[4]:
        col_a, col_b = st.columns(2)

        with col_a:
            taraflar = analysis.get("taraflar", {})
            if taraflar:
                st.markdown(f"#### {t['parties']}")
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
                st.markdown(f"#### {t['duration_dates']}")
                for k, v in sure.items():
                    if v and k != "ek_bilgi":
                        st.markdown(f"- **{k}:** {v}")

            if fin:
                st.markdown(f"#### {t['financial_details']}")
                for k, v in fin.items():
                    if v and k != "ek_bilgi":
                        st.markdown(f"- **{k}:** {v}")

        # Ham JSON
        with st.expander(t["raw_json"]):
            st.json(analysis)


# ─── Sidebar ──────────────────────────────────────────────────────────────
def render_sidebar():
    if "lang" not in st.session_state:
        st.session_state["lang"] = "tr"

    lang_code = st.session_state["lang"]
    t = T[lang_code]

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

        # Dil Seçimi
        lang_options = ["tr", "en"]
        selected_lang = st.selectbox(
            "🌐 Dil / Language",
            lang_options,
            format_func=lambda x: "🇹🇷 Türkçe" if x == "tr" else "🇺🇸 English",
            index=lang_options.index(lang_code),
            key="lang_selector"
        )
        if selected_lang != lang_code:
            st.session_state["lang"] = selected_lang
            st.rerun()

        st.markdown("---")

        # API Durumu
        health = check_api_health()
        if health:
            st.markdown(f"**{t['api_online']}**")
            g_status = "✅ Aktif" if health.get("gemini_available") else "❌ Kapalı"
            r_status = "✅ Aktif" if health.get("groq_available") else "❌ Kapalı"
            st.markdown(f"- Gemini: {g_status}")
            st.markdown(f"- Groq: {r_status}")
            
            db_status = health.get('database','')
            if lang_code == "en":
                db_status = db_status.replace("sözleşme kayıtlı", "contracts registered")
            st.markdown(f"- `{db_status}`")
        else:
            st.markdown(f"**{t['api_offline']}**")
            st.warning(t["api_warn"])

        st.markdown("---")

        # Navigasyon
        page = st.radio(
            "Navigasyon",
            [t["nav_analyze"], t["nav_history"], t["nav_about"]],
            label_visibility="collapsed",
        )

        st.markdown("---")

        # AI Provider
        st.markdown(f"**{t['ai_settings']}**")
        ai_provider = st.selectbox(
            t["ai_provider"],
            ["gemini", "groq"],
            format_func=lambda x: "🤖 Google Gemini" if x == "gemini" else "⚡ Groq LLaMA",
        )

        return page, ai_provider


# ─── Sayfa: Analiz ────────────────────────────────────────────────────────
def render_analyze_page(ai_provider: str):
    lang_code = st.session_state.get("lang", "tr")
    t = T[lang_code]
    contract_types = CONTRACT_TYPES_TR if lang_code == "tr" else CONTRACT_TYPES_EN

    st.markdown(
        f"""<div class="hero-header">
            <p class="hero-title">{t['hero_title']}</p>
            <p class="hero-subtitle">{t['hero_subtitle']}</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── Giriş Modu ────────────────────────────────────────────────────────
    input_tab1, input_tab2 = st.tabs([t["tab_paste"], t["tab_upload"]])

    contract_text = ""
    uploaded_file = None

    with input_tab1:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            contract_text = st.text_area(
                t["text_area_label"],
                height=300,
                placeholder=t["text_area_placeholder"],
                help=t["text_area_help"],
            )
        with col_right:
            if contract_text:
                words = len(contract_text.split())
                chars = len(contract_text)
                st.markdown(
                    f"""<div class="metric-card">
                        <div style="font-size:1.8em;">📊</div>
                        <div style="color:white; font-weight:700; font-size:1.1em;">{chars:,}</div>
                        <div style="color:rgba(255,255,255,0.6); font-size:0.8em;">{t['char_count']}</div>
                        <hr style="border-color:rgba(255,255,255,0.1); margin:10px 0;">
                        <div style="color:white; font-weight:700; font-size:1.1em;">{words:,}</div>
                        <div style="color:rgba(255,255,255,0.6); font-size:0.8em;">{t['word_count']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

    with input_tab2:
        col_l, col_r = st.columns([2, 1])
        with col_l:
            uploaded_file = st.file_uploader(
                t["file_uploader_label"],
                type=["pdf", "docx", "doc", "txt"],
                help=t["file_uploader_help"],
            )
        with col_r:
            if uploaded_file:
                size_kb = len(uploaded_file.getvalue()) / 1024
                st.markdown(
                    f"""<div class="metric-card" style="overflow: hidden; padding: 15px; width: 100%; box-sizing: border-box;">
                        <div style="font-size:2em;">📁</div>
                        <div style="color:white; font-weight:600; word-break: break-all; white-space: normal; line-height: 1.4; margin-bottom: 5px;">{uploaded_file.name}</div>
                        <div style="color:rgba(255,255,255,0.6); font-size:0.85em;">{size_kb:.1f} KB</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

    # ── Sözleşme Türü + Analiz Butonu ─────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_type, col_btn = st.columns([2, 1])

    with col_type:
        selected_type = st.selectbox(
            t["contract_type"],
            list(contract_types.keys()),
            format_func=lambda x: contract_types[x],
            help=t["contract_type_help"],
        )

    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_clicked = st.button(t["analyze_btn"], help=t["analyze_btn_help"], use_container_width=True)

    # ── Analiz ────────────────────────────────────────────────────────────
    if analyze_clicked:
        has_text = bool(contract_text and contract_text.strip())
        has_file = bool(uploaded_file)

        if not has_text and not has_file:
            st.warning(t["warning_empty"])
            return

        with st.spinner(t["spinner_analyzing"]):
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
                    lang=lang_code,
                )
            else:
                result = analyze_via_api(contract_text, selected_type, ai_provider, lang=lang_code)

            progress_bar.progress(100)

        if result and result.get("success"):
            st.success(t["success_done"])
            st.markdown("---")
            analysis = result.get("analysis", {})
            proc_time = result.get("processing_time", 0)
            render_analysis(analysis, proc_time, lang=lang_code)

            # İndirme butonu
            try:
                pdf_bytes = generate_pdf_report(result, lang=lang_code)
                st.download_button(
                    t["download_pdf"],
                    data=bytes(pdf_bytes),
                    file_name=f"analiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(t["pdf_error"].format(e=e))
                # Hata durumunda JSON'a geri dön
                json_str = json.dumps(result, ensure_ascii=False, indent=2)
                st.download_button(
                    t["download_json"],
                    data=json_str,
                    file_name=f"analiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True,
                )
        else:
            progress_bar.empty()


# ─── Sayfa: Geçmiş ────────────────────────────────────────────────────────
def render_history_page():
    lang_code = st.session_state.get("lang", "tr")
    t = T[lang_code]
    contract_types = CONTRACT_TYPES_TR if lang_code == "tr" else CONTRACT_TYPES_EN

    st.markdown(f"## {t['history_title']}")
    contracts = get_contracts_history()

    if not contracts:
        st.info(t["history_empty"])
        return

    st.markdown(t["history_total"].format(count=len(contracts)))

    for c in contracts:
        score = c.get("risk_skoru", 0) or 0
        label, color, icon = get_risk_info(score, lang=lang_code)
        turu_key = c.get("sozlesme_turu", "diger")
        turu = contract_types.get(turu_key, "📄 Diğer" if lang_code == "tr" else "📄 Other")
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
                            <span style="font-weight:700; color:white;">#{c['id']} — {c.get('dosya_adi','Sözleşme' if lang_code == 'tr' else 'Contract')}</span>
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
            if st.button("🗑️", key=f"del_{c['id']}", help="Sil" if lang_code == "tr" else "Delete"):
                if delete_contract_api(c["id"]):
                    st.success(t["history_deleted"])
                    st.rerun()

        # Detay görüntüleme
        state_key = f"view_state_{c['id']}"
        if state_key not in st.session_state:
            st.session_state[state_key] = False

        btn_label = t["history_close_detail"] if st.session_state[state_key] else t["history_view_detail"]
        if st.button(btn_label, key=f"view_btn_{c['id']}", use_container_width=True):
            st.session_state[state_key] = not st.session_state[state_key]
            st.rerun()

        if st.session_state[state_key]:
            detail = get_contract_detail(c["id"])
            if detail and detail.get("analiz"):
                st.markdown("---")
                st.markdown(f"### {t['history_detail_title'].format(id=c['id'], filename=c.get('dosya_adi',''))}")
                with st.container():
                    stats = detail.get("metin_istatistikleri", {})
                    s1, s2, s3 = st.columns(3)
                    s1.metric(t["history_word"], stats.get("kelime_sayisi", "-"))
                    s2.metric(t["history_char"], stats.get("karakter_sayisi", "-"))
                    s3.metric(t["history_reading_time"], stats.get("tahmini_okuma_suresi", "-"))
                    render_analysis(detail["analiz"], lang=lang_code)


# ─── Sayfa: Hakkında ──────────────────────────────────────────────────────
def render_about_page():
    lang_code = st.session_state.get("lang", "tr")
    t = T[lang_code]

    st.markdown(f"## {t['about_title']}")

    st.markdown(
        f"<div style='background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.12); "
        "border-radius:16px; padding:24px 28px; margin-bottom:20px;'>"
        f"<h3 style='color:#a78bfa; margin-top:0;'>{t['hero_title']}</h3>"
        f"<p style='color:rgba(255,255,255,0.85); font-size:1.02em; line-height:1.8; margin:0;'>"
        f"{t['about_desc']}"
        "</p></div>",
        unsafe_allow_html=True,
    )

    # ── Teknoloji Stack ──────────────────────────────────────────────────
    st.markdown(f"### {t['about_tech_title']}")
    if lang_code == "tr":
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
    else:
        st.markdown("""
| Layer | Technology |
|-------|------------|
| 🖥️ Frontend | Streamlit |
| ⚙️ Backend | FastAPI |
| 🤖 AI | Gemini 1.5 Flash / Groq LLaMA |
| 🗄️ Database | SQLite + SQLAlchemy |
| ✅ Validation | Pydantic v2 |
| 📄 PDF Reading | PyMuPDF (fitz) |
| 📝 DOCX Reading | python-docx |
""")

    st.markdown("---")

    # ── Desteklenen Türler ───────────────────────────────────────────────
    st.markdown(f"### {t['about_types_title']}")
    col1, col2 = st.columns(2)
    contract_types = CONTRACT_TYPES_TR if lang_code == "tr" else CONTRACT_TYPES_EN
    
    with col1:
        st.markdown(f"- {contract_types['kira']}")
        st.markdown(f"- {contract_types['is']}")
        st.markdown(f"- {contract_types['nda']}")
    with col2:
        st.markdown(f"- {contract_types['hizmet']}")
        st.markdown(f"- {contract_types['satis']}")
        st.markdown(f"- {contract_types['auto']}")

    st.markdown("---")

    # ── Yasal Uyarı ─────────────────────────────────────────────────────
    st.markdown(f"### {t['about_warning_title']}")
    st.warning(t["about_warning_body"])

    st.markdown("---")

    # ── Öneri ve Geri Bildirim ──────────────────────────────────────────────────
    st.markdown(f"### {t['about_feedback_title']}")
    st.info(t["about_feedback_body"])

    st.markdown("---")

    # ── Geliştirici ─────────────────────────────────────────────────────
    st.markdown(
        f"<div style='text-align:center; padding:20px; "
        "background:linear-gradient(135deg,rgba(99,102,241,0.15),rgba(139,92,246,0.15)); "
        "border:1px solid rgba(139,92,246,0.4); border-radius:14px;'>"
        f"<div style='color:rgba(255,255,255,0.6); font-size:0.9em; margin-bottom:6px;'>{t['about_dev_title']}</div>"
        "<div style='color:#a78bfa; font-weight:700; font-size:1.2em; letter-spacing:0.5px;'>"
        f"{t['about_dev_name']}</div>"
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

        import subprocess
        import sys
        
        try:
            # Thread yerine ayrı bir process olarak başlat (Streamlit Cloud'da çökmemesi için)
            subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            print(f"API baslatilamadi: {e}")

        # API'nin ayağa kalkmasını bekle (en fazla 20 saniye)
        lang_code = st.session_state.get("lang", "tr")
        t = T[lang_code]
        with st.spinner(t["api_starting"]):
            for _ in range(20):
                time.sleep(1)
                if check_api_health():
                    break


# ─── Ana Uygulama ─────────────────────────────────────────────────────────
def main():
    if "lang" not in st.session_state:
        st.session_state["lang"] = "tr"

    start_api_if_offline()
    page, ai_provider = render_sidebar()

    lang_code = st.session_state["lang"]
    t = T[lang_code]
    st.markdown(CSS_STYLE.replace("__FILE_BTN_TEXT__", t["file_btn_text"]), unsafe_allow_html=True)

    if page == t["nav_analyze"]:
        render_analyze_page(ai_provider)
    elif page == t["nav_history"]:
        render_history_page()
    elif page == t["nav_about"]:
        render_about_page()


if __name__ == "__main__":
    main()
