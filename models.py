"""
models.py - Pydantic Modelleri
AI Contract Analyzer için veri modelleri
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


# ─── Enum: Sözleşme Türleri ────────────────────────────────────────────────
class ContractType(str, Enum):
    KIRA = "kira"
    IS = "is"
    NDA = "nda"
    HIZMET = "hizmet"
    SATIS = "satis"
    DIGER = "diger"


CONTRACT_TYPE_LABELS = {
    ContractType.KIRA: "🏠 Kira Sözleşmesi",
    ContractType.IS: "💼 İş Sözleşmesi",
    ContractType.NDA: "🔒 Gizlilik Sözleşmesi (NDA)",
    ContractType.HIZMET: "🛠️ Hizmet Sözleşmesi",
    ContractType.SATIS: "🛒 Satış Sözleşmesi",
    ContractType.DIGER: "📄 Diğer",
}

# ─── Risk Severity ─────────────────────────────────────────────────────────
class RiskSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ─── Alt Modeller ──────────────────────────────────────────────────────────
class RiskItem(BaseModel):
    madde: str = Field(..., description="İlgili madde veya bölüm")
    aciklama: str = Field(..., description="Risk açıklaması")
    severity: RiskSeverity = Field(default=RiskSeverity.MEDIUM)
    oneri: Optional[str] = Field(None, description="Bu risk için öneri")


class OnemliMadde(BaseModel):
    baslik: str
    icerik: str
    kategori: Optional[str] = None


class TarafBilgisi(BaseModel):
    ad: Optional[str] = None
    unvan: Optional[str] = None
    adres: Optional[str] = None
    ek_bilgi: Optional[Dict[str, str]] = None


class FinansalDetay(BaseModel):
    miktar: Optional[str] = None
    para_birimi: Optional[str] = None
    odeme_kosullari: Optional[str] = None
    ek_bilgi: Optional[Dict[str, str]] = None


class SureTarih(BaseModel):
    baslangic: Optional[str] = None
    bitis: Optional[str] = None
    sure: Optional[str] = None
    yenileme_kosullari: Optional[str] = None


# ─── Ana Analiz Sonucu ─────────────────────────────────────────────────────
class AnalysisResult(BaseModel):
    ozet: str = Field(..., description="Sözleşmenin kısa özeti")
    sozlesme_turu: ContractType = Field(default=ContractType.DIGER)
    risk_skoru: int = Field(..., ge=0, le=100, description="Risk skoru (0=düşük, 100=kritik)")
    riskler: List[RiskItem] = Field(default_factory=list)
    onemli_maddeler: List[OnemliMadde] = Field(default_factory=list)
    tavsiyeler: List[str] = Field(default_factory=list)
    taraflar: Optional[Dict[str, Any]] = None
    sure_ve_tarihler: Optional[SureTarih] = None
    finansal_detaylar: Optional[FinansalDetay] = None
    genel_degerlendirme: Optional[str] = None
    analiz_tarihi: Optional[datetime] = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


# ─── API Request / Response Modelleri ─────────────────────────────────────
class AnalyzeTextRequest(BaseModel):
    metin: str = Field(..., min_length=50, description="Analiz edilecek sözleşme metni")
    sozlesme_turu: Optional[ContractType] = Field(
        None, description="Sözleşme türü (belirtilmezse otomatik tespit edilir)"
    )
    ai_provider: Optional[str] = Field("gemini", description="AI sağlayıcı: gemini veya groq")
    lang: Optional[str] = Field("tr", description="Language of analysis: tr or en")


class AnalyzeResponse(BaseModel):
    success: bool
    contract_id: Optional[int] = None
    analysis: Optional[AnalysisResult] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None


class ContractRecord(BaseModel):
    id: int
    dosya_adi: Optional[str] = None
    sozlesme_turu: Optional[str] = None
    metin_ozeti: Optional[str] = None
    risk_skoru: Optional[int] = None
    analiz_tarihi: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContractListResponse(BaseModel):
    total: int
    contracts: List[ContractRecord]


class HealthResponse(BaseModel):
    status: str
    gemini_available: bool
    groq_available: bool
    database: str
    version: str = "1.0.0"
