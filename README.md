# ⚖️ AI Contract Analyzer
### Yapay Zeka Destekli Sözleşme Analiz Sistemi
**Proje Geliştiricisi:** Betül Altınkaynak Demirel
<div align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" />
  <img src="https://img.shields.io/badge/FastAPI-0.110+-green?logo=fastapi" />
  <img src="https://img.shields.io/badge/Streamlit-1.35+-red?logo=streamlit" />
  <img src="https://img.shields.io/badge/Gemini-1.5_Flash-orange?logo=google" />
  <img src="https://img.shields.io/badge/SQLite-Database-lightblue?logo=sqlite" />
</div>

---

## 🌟 Özellikler

- **🤖 AI Destekli Analiz** — Google Gemini 1.5 Flash veya Groq LLaMA ile derin analiz
- **📄 Çoklu Format** — PDF, DOCX ve TXT dosyaları veya metin yapıştırma
- **🏷️ 5 Sözleşme Türü** — Kira, İş, NDA, Hizmet, Satış
- **⚠️ Risk Değerlendirmesi** — 0–100 arası risk skoru ve detaylı risk listesi
- **📌 Önemli Maddeler** — Kritik hükümlerin tespiti
- **💡 Tavsiyeler** — Hukuki öneriler ve iyileştirmeler
- **📚 Geçmiş** — Tüm analizler SQLite'ta saklanır
- **⬇️ Export** — Analiz raporunu JSON olarak indir

---

## 🗂️ Proje Yapısı

```
AI-Contract-Analyzer/
│
├── app.py                  # Streamlit Arayüzü
├── api.py                  # FastAPI Backend
├── ai_service.py           # Gemini / Groq Servisi
├── database.py             # SQLite + SQLAlchemy
├── models.py               # Pydantic Modelleri
├── contract_service.py     # PDF/DOCX İşleme
├── prompts.py              # AI System Promptları
├── requirements.txt
├── .env                    # API Anahtarları (bu dosyayı paylaşmayın!)
├── .gitignore
│
├── uploads/                # Yüklenen dosyalar (otomatik oluşur)
│
├── data/
│     └── contract.db       # SQLite veritabanı (otomatik oluşur)
│
└── README.md
```

---

## 🚀 Kurulum

### 1. Depoyu Klonla
```bash
git clone https://github.com/kullanici/ai-contract-analyzer.git
cd ai-contract-analyzer
```

### 2. Sanal Ortam Oluştur (Önerilen)
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
```

### 3. Bağımlılıkları Yükle
```bash
pip install -r requirements.txt
```

### 4. API Anahtarlarını Ayarla
`.env` dosyasını düzenle:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here   # Opsiyonel
```

> **Gemini API Key:** https://aistudio.google.com/app/apikey  
> **Groq API Key:** https://console.groq.com/keys

---

## ▶️ Çalıştırma

### Terminal 1 — FastAPI Backend
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

API dökümantasyonu: http://localhost:8000/docs

### Terminal 2 — Streamlit Frontend
```bash
streamlit run app.py
```

Arayüz: http://localhost:8501

---

## 🔌 API Endpoint'leri

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/health` | API sağlık durumu |
| POST | `/analyze` | Metin analizi |
| POST | `/analyze/file` | Dosya yükleme ve analiz |
| GET | `/contracts` | Tüm sözleşmeler |
| GET | `/contracts/{id}` | Tek sözleşme detayı |
| DELETE | `/contracts/{id}` | Sözleşme sil |

---

## 📋 Desteklenen Sözleşme Türleri

| Tür | Emoji | Anahtar |
|-----|-------|---------|
| Kira Sözleşmesi | 🏠 | `kira` |
| İş Sözleşmesi | 💼 | `is` |
| Gizlilik Sözleşmesi (NDA) | 🔒 | `nda` |
| Hizmet Sözleşmesi | 🛠️ | `hizmet` |
| Satış Sözleşmesi | 🛒 | `satis` |

---

## 🛠️ Teknoloji Stack

| Katman | Teknoloji |
|--------|-----------|
| Frontend | Streamlit |
| Backend | FastAPI |
| AI | Gemini 1.5 Flash / Groq LLaMA 3.3 |
| Veritabanı | SQLite |
| ORM | SQLAlchemy |
| Doğrulama | Pydantic v2 |
| PDF Okuma | PyMuPDF (fitz) |
| DOCX Okuma | python-docx |
| Environment | python-dotenv |

---

## ⚠️ Yasal Uyarı

Bu araç **bilgilendirme amaçlıdır**. Hukuki tavsiye niteliği taşımaz.  
Önemli hukuki kararlar için bir avukattan profesyonel destek alınız.

---

## 📄 Lisans

MIT License — Detaylar için `LICENSE` dosyasına bakın.
