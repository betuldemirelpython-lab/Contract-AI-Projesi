"""
ai_service.py - Gemini / Groq AI Entegrasyon Servisi
Sözleşme analizi için yapay zeka API çağrıları
"""

import json
import os
import time
import logging
from typing import Optional, Dict, Any

from dotenv import load_dotenv

from models import AnalysisResult, ContractType
from prompts import get_analysis_prompt, get_detection_prompt

load_dotenv()

logger = logging.getLogger(__name__)

# ─── Yapılandırma ──────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

MAX_RETRIES = 3
RETRY_DELAY = 2  # saniye


# ─── Yardımcı: JSON Temizleme ─────────────────────────────────────────────
def _clean_json_response(text: str) -> str:
    """AI'dan gelen metindeki JSON'u temizler."""
    text = text.strip()
    # Code block varsa kaldır
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    return text.strip()


def _parse_analysis_response(raw_text: str, contract_type: str) -> Dict[str, Any]:
    """AI yanıtını dict'e çevirir, hata durumunda varsayılan döndürür."""
    try:
        cleaned = _clean_json_response(raw_text)
        data = json.loads(cleaned)
        
        # İngilizce (EN) JSON anahtarları geldiyse, Türkçe (TR) model formatına dönüştür.
        if "summary" in data: data["ozet"] = data.pop("summary")
        if "contract_type" in data: data["sozlesme_turu"] = data.pop("contract_type")
        if "risk_score" in data: data["risk_skoru"] = data.pop("risk_score")
        if "general_evaluation" in data: data["genel_degerlendirme"] = data.pop("general_evaluation")
        if "recommendations" in data: data["tavsiyeler"] = data.pop("recommendations")
        
        if "risks" in data:
            for r in data["risks"]:
                if "clause" in r: r["madde"] = r.pop("clause")
                if "description" in r: r["aciklama"] = r.pop("description")
                if "recommendation" in r: r["oneri"] = r.pop("recommendation")
            data["riskler"] = data.pop("risks")
            
        if "key_clauses" in data:
            for k in data["key_clauses"]:
                if "title" in k: k["baslik"] = k.pop("title")
                if "content" in k: k["icerik"] = k.pop("content")
                if "category" in k: k["kategori"] = k.pop("category")
            data["onemli_maddeler"] = data.pop("key_clauses")
            
        if "parties" in data:
            parties = data.pop("parties")
            for p_v in parties.values():
                if isinstance(p_v, dict):
                    if "name" in p_v: p_v["ad"] = p_v.pop("name")
                    if "title" in p_v: p_v["unvan"] = p_v.pop("title")
                    if "address" in p_v: p_v["adres"] = p_v.pop("address")
                    if "additional_info" in p_v: p_v["ek_bilgi"] = p_v.pop("additional_info")
            data["taraflar"] = parties

        if "duration_and_dates" in data:
            dd = data.pop("duration_and_dates")
            if "start" in dd: dd["baslangic"] = dd.pop("start")
            if "end" in dd: dd["bitis"] = dd.pop("end")
            if "duration" in dd: dd["sure"] = dd.pop("duration")
            if "renewal_conditions" in dd: dd["yenileme_kosullari"] = dd.pop("renewal_conditions")
            data["sure_ve_tarihler"] = dd

        if "financial_details" in data:
            fd = data.pop("financial_details")
            if "amount" in fd: fd["miktar"] = fd.pop("amount")
            if "currency" in fd: fd["para_birimi"] = fd.pop("currency")
            if "payment_terms" in fd: fd["odeme_kosullari"] = fd.pop("payment_terms")
            if "additional_info" in fd: fd["ek_bilgi"] = fd.pop("additional_info")
            data["finansal_detaylar"] = fd

        return data
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"JSON parse hatası: {e}. Ham yanıt: {raw_text[:200]}")
        # Varsayılan sonuç
        return {
            "ozet": "Analiz sırasında bir sorun oluştu. Lütfen tekrar deneyin.",
            "sozlesme_turu": contract_type,
            "risk_skoru": 50,
            "riskler": [],
            "onemli_maddeler": [],
            "tavsiyeler": ["Analiz tekrar yapılmalı."],
            "genel_degerlendirme": "Analiz tamamlanamadı.",
        }


# ─── Gemini Servisi ────────────────────────────────────────────────────────
class GeminiService:
    def __init__(self):
        self.available = False
        self.client = None
        self._init()

    def _init(self):
        if not GEMINI_API_KEY:
            logger.info("GEMINI_API_KEY bulunamadı.")
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            self.client = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.95,
                    "max_output_tokens": 4096,
                },
            )
            self.available = True
            logger.info(f"Gemini servisi hazır: {GEMINI_MODEL}")
        except Exception as e:
            logger.error(f"Gemini başlatma hatası: {e}")

    def analyze(self, system_prompt: str, user_prompt: str) -> str:
        """Gemini ile analiz yapar."""
        if not self.available:
            raise RuntimeError("Gemini servisi kullanılamıyor.")

        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.client.generate_content(full_prompt)
                return response.text
            except Exception as e:
                logger.warning(f"Gemini deneme {attempt}/{MAX_RETRIES} başarısız: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * attempt)
                else:
                    raise


# ─── Groq Servisi ─────────────────────────────────────────────────────────
class GroqService:
    def __init__(self):
        self.available = False
        self.client = None
        self._init()

    def _init(self):
        if not GROQ_API_KEY:
            logger.info("GROQ_API_KEY bulunamadı.")
            return
        try:
            from groq import Groq
            self.client = Groq(api_key=GROQ_API_KEY)
            self.available = True
            logger.info(f"Groq servisi hazır: {GROQ_MODEL}")
        except Exception as e:
            logger.error(f"Groq başlatma hatası: {e}")

    def analyze(self, system_prompt: str, user_prompt: str) -> str:
        """Groq ile analiz yapar."""
        if not self.available:
            raise RuntimeError("Groq servisi kullanılamıyor.")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.1,
                    max_tokens=4096,
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"Groq deneme {attempt}/{MAX_RETRIES} başarısız: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * attempt)
                else:
                    raise


# ─── Ana AI Servis Sınıfı ─────────────────────────────────────────────────
class AIService:
    def __init__(self):
        self.gemini = GeminiService()
        self.groq = GroqService()

    def _get_provider(self, preferred: str = "gemini"):
        """Tercih edilen sağlayıcıyı döndürür, yoksa alternatife geçer."""
        if preferred == "gemini" and self.gemini.available:
            return self.gemini, "gemini"
        elif preferred == "groq" and self.groq.available:
            return self.groq, "groq"
        elif self.gemini.available:
            return self.gemini, "gemini"
        elif self.groq.available:
            return self.groq, "groq"
        else:
            raise RuntimeError(
                "Hiçbir AI sağlayıcısı kullanılamıyor. "
                "Lütfen .env dosyasında GEMINI_API_KEY veya GROQ_API_KEY tanımlayın."
            )

    def detect_contract_type(
        self, text: str, preferred_provider: str = "gemini", lang: str = "tr"
    ) -> str:
        """Sözleşme türünü otomatik tespit eder. Hata durumunda diğer sağlayıcıya geçer."""
        sys_p, usr_p = get_detection_prompt(text, lang=lang)
        try:
            provider, _ = self._get_provider(preferred_provider)
            raw = provider.analyze(sys_p, usr_p)
        except Exception as e:
            logger.warning(f"Tür tespiti (ilk tercih) hatası: {e}. Alternatife geçiliyor.")
            try:
                alt_provider_name = "groq" if preferred_provider == "gemini" else "gemini"
                alt_provider, _ = self._get_provider(alt_provider_name)
                raw = alt_provider.analyze(sys_p, usr_p)
            except Exception as e2:
                logger.error(f"Tür tespiti (alternatif) de başarısız: {e2}")
                return "diger"
                
        try:
            data = _parse_analysis_response(raw, "diger")
            return data.get("sozlesme_turu", "diger")
        except Exception:
            return "diger"

    def analyze_contract(
        self,
        text: str,
        contract_type: Optional[str] = None,
        preferred_provider: str = "gemini",
        lang: str = "tr",
    ) -> tuple[AnalysisResult, str]:
        """
        Sözleşmeyi analiz eder. Hata durumunda otomatik olarak diğer AI modeline düşer.
        Returns: (AnalysisResult, kullanılan_provider)
        """
        # Tür belirleme
        if not contract_type or contract_type == "auto":
            contract_type = self.detect_contract_type(text, preferred_provider, lang=lang)

        # Promptları oluştur
        sys_p, usr_p = get_analysis_prompt(contract_type, text, lang=lang)

        # AI çağrısı ve Fallback (Yedekleme) Mantığı
        try:
            provider, used_provider = self._get_provider(preferred_provider)
            raw_response = provider.analyze(sys_p, usr_p)
        except Exception as e:
            logger.warning(f"Analiz hatası ({preferred_provider}): {e}. Alternatif deneniyor...")
            alt_provider_name = "groq" if preferred_provider == "gemini" else "gemini"
            try:
                alt_provider, used_provider = self._get_provider(alt_provider_name)
                raw_response = alt_provider.analyze(sys_p, usr_p)
            except Exception as e2:
                logger.error(f"Alternatif AI ({alt_provider_name}) da hata verdi: {e2}")
                raise RuntimeError(f"Tüm AI modelleri başarısız oldu (Örn: Kota aşımı). Hata: {str(e)} / {str(e2)}")

        # Parse
        analysis_dict = _parse_analysis_response(raw_response, contract_type)

        # AnalysisResult modeline dönüştür
        try:
            result = AnalysisResult(**analysis_dict)
        except Exception as e:
            logger.error(f"AnalysisResult oluşturma hatası: {e}")
            # Hata durumunda minimum model
            result = AnalysisResult(
                ozet=analysis_dict.get("ozet", "Analiz tamamlanamadı"),
                sozlesme_turu=ContractType(contract_type) if contract_type in [c.value for c in ContractType] else ContractType.DIGER,
                risk_skoru=analysis_dict.get("risk_skoru", 50),
                riskler=[],
                onemli_maddeler=[],
                tavsiyeler=[],
            )

        return result, used_provider

    @property
    def gemini_available(self) -> bool:
        return self.gemini.available

    @property
    def groq_available(self) -> bool:
        return self.groq.available


# Singleton instance
ai_service = AIService()
