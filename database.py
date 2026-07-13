"""
database.py - SQLite + SQLAlchemy Veritabanı Katmanı
Sözleşme kayıtlarını saklama ve yönetme
"""

import json
from datetime import datetime, date


class _DateTimeEncoder(json.JSONEncoder):
    """datetime ve date nesnelerini ISO formatına çevirir."""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)
from pathlib import Path
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
    event,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool

# ─── Veritabanı Ayarları ───────────────────────────────────────────────────
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR}/contract.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# WAL modu: daha iyi eşzamanlı erişim
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─── ORM Modeli ───────────────────────────────────────────────────────────
class ContractDB(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dosya_adi = Column(String(255), nullable=True)
    sozlesme_turu = Column(String(50), nullable=True)
    metin = Column(Text, nullable=True)          # Ham sözleşme metni
    metin_ozeti = Column(String(500), nullable=True)  # İlk 500 karakter
    analiz_json = Column(Text, nullable=True)    # JSON string olarak analiz
    risk_skoru = Column(Integer, nullable=True)
    ai_provider = Column(String(50), nullable=True)
    analiz_tarihi = Column(DateTime, default=datetime.utcnow)
    dosya_boyutu = Column(Integer, nullable=True)  # byte


# ─── Veritabanını Oluştur ─────────────────────────────────────────────────
def init_db():
    """Tabloları oluşturur (ilk çalıştırma)."""
    Base.metadata.create_all(bind=engine)


# ─── Bağlantı Yöneticisi ──────────────────────────────────────────────────
def get_db():
    """FastAPI dependency injection için."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── CRUD Fonksiyonları ───────────────────────────────────────────────────
def save_contract(
    db: Session,
    metin: str,
    analiz_dict: Dict[str, Any],
    dosya_adi: Optional[str] = None,
    ai_provider: str = "gemini",
) -> ContractDB:
    """Sözleşme ve analiz sonucunu kaydeder."""
    sozlesme_turu = analiz_dict.get("sozlesme_turu", "diger")
    risk_skoru = analiz_dict.get("risk_skoru", 0)
    ozet = analiz_dict.get("ozet", "")

    record = ContractDB(
        dosya_adi=dosya_adi or "Metin Girişi",
        sozlesme_turu=sozlesme_turu,
        metin=metin[:50000],           # Max 50KB metin
        metin_ozeti=ozet[:500],
        analiz_json=json.dumps(analiz_dict, ensure_ascii=False, cls=_DateTimeEncoder),
        risk_skoru=risk_skoru,
        ai_provider=ai_provider,
        analiz_tarihi=datetime.utcnow(),
        dosya_boyutu=len(metin.encode("utf-8")),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_all_contracts(
    db: Session, limit: int = 50, offset: int = 0
) -> List[ContractDB]:
    """Tüm sözleşmeleri tarih sırasına göre getirir."""
    return (
        db.query(ContractDB)
        .order_by(ContractDB.analiz_tarihi.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )


def get_contract_by_id(db: Session, contract_id: int) -> Optional[ContractDB]:
    """ID ile tek sözleşme getirir."""
    return db.query(ContractDB).filter(ContractDB.id == contract_id).first()


def delete_contract(db: Session, contract_id: int) -> bool:
    """Sözleşme kaydını siler."""
    record = get_contract_by_id(db, contract_id)
    if record:
        db.delete(record)
        db.commit()
        return True
    return False


def get_contract_count(db: Session) -> int:
    """Toplam sözleşme sayısı."""
    return db.query(ContractDB).count()


def get_analysis_dict(record: ContractDB) -> Optional[Dict[str, Any]]:
    """ORM kaydından analiz dict'ini döndürür."""
    if record and record.analiz_json:
        try:
            return json.loads(record.analiz_json)
        except json.JSONDecodeError:
            return None
    return None
