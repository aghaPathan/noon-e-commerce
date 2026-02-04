"""
SQLAlchemy Database Models for Noon-E-Commerce
User authentication and SKU tracking
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Boolean, Float, DateTime, ForeignKey,
    Index, Text, create_engine
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """User model for authentication"""
    __tablename__ = 'users'
    __table_args__ = {'schema': 'noon'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    skus = relationship("SKU", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class SKU(Base):
    """SKU model for product tracking"""
    __tablename__ = 'skus'
    __table_args__ = (
        Index('ix_skus_user_sku', 'user_id', 'sku_code'),
        {'schema': 'noon'}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('noon.users.id', ondelete='CASCADE'), nullable=False, index=True)
    sku_code = Column(String(50), nullable=False, index=True)
    product_name = Column(String(500))
    product_url = Column(Text)
    current_price = Column(Float)
    original_price = Column(Float)
    target_price = Column(Float)  # For price alerts
    seller = Column(String(255))
    in_stock = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    last_checked_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="skus")
    price_history = relationship("PriceHistory", back_populates="sku", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SKU {self.sku_code}>"


class PriceHistory(Base):
    """Price history for SKUs"""
    __tablename__ = 'price_history'
    __table_args__ = (
        Index('ix_price_history_sku_recorded', 'sku_id', 'recorded_at'),
        {'schema': 'noon'}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku_id = Column(UUID(as_uuid=True), ForeignKey('noon.skus.id', ondelete='CASCADE'), nullable=False, index=True)
    price = Column(Float, nullable=False)
    original_price = Column(Float)
    seller = Column(String(255))
    in_stock = Column(Boolean, default=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    sku = relationship("SKU", back_populates="price_history")

    def __repr__(self):
        return f"<PriceHistory {self.sku_id} @ {self.price}>"


# Database connection helper
def get_engine(database_url: str):
    """Create SQLAlchemy engine"""
    return create_engine(database_url, pool_pre_ping=True)


def get_session(engine):
    """Create database session"""
    Session = sessionmaker(bind=engine)
    return Session()


def init_db(engine):
    """Initialize database tables"""
    Base.metadata.create_all(engine)
