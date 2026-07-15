"""
api.py - FastAPI Backend
Sözleşme analizi için RESTful API endpoint'leri
"""

import time
import logging
import json
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from models import (
    AnalyzeTextRequest,
    AnalyzeResponse,
    ContractListResponse,
    ContractRecord,
    HealthResponse,
    ContractType,
)
from database import (
    get_db,
    init_db,
    save_contract,
    get_all_contracts,
    get_contract_by_id,
    delete_contract,
    get_contract_count,
    get_analysis_dict,
)
from ai_service import ai_service
from contract_service import (
    extract_text_from_file,
    validate_contract_text,
    save_uploaded_file,
    get_text_stats,
)

# ─── Loglama ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── FastAPI Uygulaması ──────────────────────────────────────────────────
app = FastAPI(
    title="AI Contract Analyzer API",
    description="Yapay Zeka Destekli Sözleşme Analiz Sistemi",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Başlangıç ────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    init_db()
    logger.info("Veritabanı başlatıldı.")
    logger.info(f"Gemini: {'✓' if ai_service.gemini_available else '✗'}")
    logger.info(f"Groq:   {'✓' if ai_service.groq_available else '✗'}")


# ─── ENDPOINT: Sağlık Kontrolü ────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["Sistem"])
async def health_check(db: Session = Depends(get_db)):
    """API'nin durumunu ve AI sağlayıcılarını kontrol eder."""
    count = get_contract_count(db)
    return HealthResponse(
        status="ok",
        gemini_available=ai_service.gemini_available,
        groq_available=ai_service.groq_available,
        database=f"SQLite - {count} sözleşme kayıtlı",
    )


# ─── ENDPOINT: Metin Analizi ──────────────────────────────────────────────
@app.post("/analyze", response_model=AnalyzeResponse, tags=["Analiz"])
async def analyze_text(
    request: AnalyzeTextRequest,
    db: Session = Depends(get_db),
):
    """
    Sözleşme metnini analiz eder.
    Body: { metin, sozlesme_turu (opsiyonel), ai_provider (opsiyonel) }
    """
    start_time = time.time()

    # Doğrulama
    valid, err = validate_contract_text(request.metin)
    if not valid:
        raise HTTPException(status_code=422, detail=err)

    try:
        contract_type = request.sozlesme_turu.value if request.sozlesme_turu else "auto"
        result, used_provider = ai_service.analyze_contract(
            text=request.metin,
            contract_type=contract_type,
            preferred_provider=request.ai_provider or "gemini",
            lang=request.lang or "tr",
        )

        # Veritabanına kaydet
        record = save_contract(
            db=db,
            metin=request.metin,
            analiz_dict=result.dict(),
            dosya_adi="Metin Girişi",
            ai_provider=used_provider,
        )

        elapsed = round(time.time() - start_time, 2)
        logger.info(f"Analiz tamamlandı: ID={record.id}, süre={elapsed}s, provider={used_provider}")

        return AnalyzeResponse(
            success=True,
            contract_id=record.id,
            analysis=result,
            processing_time=elapsed,
        )

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Analiz hatası")
        raise HTTPException(status_code=500, detail=f"Analiz başarısız: {str(e)}")


# ─── ENDPOINT: Dosya Analizi ──────────────────────────────────────────────
@app.post("/analyze/file", response_model=AnalyzeResponse, tags=["Analiz"])
async def analyze_file(
    file: UploadFile = File(...),
    sozlesme_turu: Optional[str] = Form(None),
    ai_provider: Optional[str] = Form("gemini"),
    lang: Optional[str] = Form("tr"),
    db: Session = Depends(get_db),
):
    """
    PDF, DOCX veya TXT dosyası yükleyerek analiz eder.
    """
    start_time = time.time()

    # Dosya kontrolü
    allowed = {".pdf", ".docx", ".doc", ".txt"}
    import pathlib
    suffix = pathlib.Path(file.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(
            status_code=415,
            detail=f"Desteklenmeyen dosya türü: {suffix}. Kabul edilenler: {', '.join(allowed)}",
        )

    # Dosyayı oku
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=413, detail="Dosya 10 MB'dan büyük olamaz.")

    try:
        # Metin çıkar
        text = extract_text_from_file(content, file.filename or "dosya")

        # Doğrula
        valid, err = validate_contract_text(text)
        if not valid:
            raise HTTPException(status_code=422, detail=err)

        # Dosyayı kaydet
        save_uploaded_file(content, file.filename or "dosya")

        # AI analizi
        result, used_provider = ai_service.analyze_contract(
            text=text,
            contract_type=sozlesme_turu or "auto",
            preferred_provider=ai_provider or "gemini",
            lang=lang or "tr",
        )

        # DB kaydı
        record = save_contract(
            db=db,
            metin=text,
            analiz_dict=result.dict(),
            dosya_adi=file.filename,
            ai_provider=used_provider,
        )

        elapsed = round(time.time() - start_time, 2)
        return AnalyzeResponse(
            success=True,
            contract_id=record.id,
            analysis=result,
            processing_time=elapsed,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Dosya analiz hatası")
        raise HTTPException(status_code=500, detail=str(e))


# ─── ENDPOINT: Tüm Sözleşmeler ───────────────────────────────────────────
@app.get("/contracts", response_model=ContractListResponse, tags=["Sözleşmeler"])
async def list_contracts(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Kayıtlı tüm sözleşmeleri listeler."""
    records = get_all_contracts(db, limit=limit, offset=offset)
    total = get_contract_count(db)

    contracts = [
        ContractRecord(
            id=r.id,
            dosya_adi=r.dosya_adi,
            sozlesme_turu=r.sozlesme_turu,
            metin_ozeti=r.metin_ozeti,
            risk_skoru=r.risk_skoru,
            analiz_tarihi=r.analiz_tarihi,
        )
        for r in records
    ]

    return ContractListResponse(total=total, contracts=contracts)


# ─── ENDPOINT: Tek Sözleşme ───────────────────────────────────────────────
@app.get("/contracts/{contract_id}", tags=["Sözleşmeler"])
async def get_contract(contract_id: int, db: Session = Depends(get_db)):
    """ID ile sözleşme detayını getirir."""
    record = get_contract_by_id(db, contract_id)
    if not record:
        raise HTTPException(status_code=404, detail="Sözleşme bulunamadı.")

    analysis = get_analysis_dict(record)
    stats = get_text_stats(record.metin or "")

    return {
        "id": record.id,
        "dosya_adi": record.dosya_adi,
        "sozlesme_turu": record.sozlesme_turu,
        "ai_provider": record.ai_provider,
        "analiz_tarihi": record.analiz_tarihi,
        "metin_istatistikleri": stats,
        "analiz": analysis,
    }


# ─── ENDPOINT: Sözleşme Sil ───────────────────────────────────────────────
@app.delete("/contracts/{contract_id}", tags=["Sözleşmeler"])
async def remove_contract(contract_id: int, db: Session = Depends(get_db)):
    """Sözleşme kaydını siler."""
    success = delete_contract(db, contract_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sözleşme bulunamadı.")
    return {"success": True, "message": f"Sözleşme #{contract_id} silindi."}


# ─── ENDPOINT: Kök ────────────────────────────────────────────────────────
@app.get("/", tags=["Sistem"])
async def root():
    return {
        "name": "AI Contract Analyzer API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
