from db.db import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    Boolean,
    ForeignKey,
    DateTime
)
from sqlalchemy.orm import relationship
from datetime import datetime


# =========================
# 👤 USER
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    reset_token = Column(String(255), nullable=True, index=True)
    reset_token_expires = Column(DateTime, nullable=True)

    rooms = relationship("Room", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email
        }


# =========================
# 🏠 ROOM
# =========================
class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True)

    image_url = Column(String(500), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    user = relationship("User", back_populates="rooms")

    recommendations = relationship(
        "Recommendation",
        back_populates="room",
        cascade="all, delete-orphan"
    )

    conversations = relationship(
        "Conversation",
        back_populates="room",
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "image_url": self.image_url,
            "created_at": self.created_at
        }


# =========================
# 🪑 TABLE
# =========================
class Table(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True)

    name = Column(String(150), nullable=False)

    style = Column(String(100))
    material = Column(String(100))
    color = Column(String(100))
    shape = Column(String(100))

    width = Column(Float)
    depth = Column(Float)
    height = Column(Float)
    diameter = Column(Float)  # 👈 nuevo: solo aplica para mesas redondas

    price = Column(Float)

    description = Column(Text)

    image_url = Column(String(500), nullable=False)

    is_active = Column(Boolean, default=True)

    recommendations = relationship(
        "Recommendation",
        back_populates="table"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "style": self.style,
            "material": self.material,
            "color": self.color,
            "shape": self.shape,
            "width": self.width,
            "depth": self.depth,
            "height": self.height,
            "diameter": self.diameter,
            "price": self.price,
            "description": self.description,
            "image_url": self.image_url,
            "is_active": self.is_active
        }


# =========================
# 🤖 RECOMMENDATION
# =========================
class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True)

    room_id = Column(
        Integer,
        ForeignKey("rooms.id"),
        nullable=False
    )

    table_id = Column(
        Integer,
        ForeignKey("tables.id"),
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    score = Column(Float)

    explanation = Column(Text)

    generated_image = Column(String(500))

    created_at = Column(DateTime, default=datetime.utcnow)

    room = relationship("Room", back_populates="recommendations")

    table = relationship("Table", back_populates="recommendations")

    user = relationship("User", back_populates="recommendations")

    def to_dict(self):
        return {
            "id": self.id,
            "score": self.score,
            "explanation": self.explanation,
            "generated_image": self.generated_image,
            "table": self.table.name if self.table else None,
            "room": self.room.id if self.room else None,
            "created_at": self.created_at
        }


# =========================
# 💬 CONVERSATION
# =========================
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)

    room_id = Column(
        Integer,
        ForeignKey("rooms.id"),
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    created_at = Column(DateTime, default=datetime.utcnow)

    room = relationship("Room", back_populates="conversations")

    user = relationship("User", back_populates="conversations")

    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "room_id": self.room_id,
            "created_at": self.created_at,
            "messages": [m.to_dict() for m in self.messages]
        }


# =========================
# 📩 MESSAGE
# =========================
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)

    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id"),
        nullable=False
    )

    role = Column(String(20), nullable=False)  # "user" o "assistant"

    content = Column(Text, nullable=False)

    # Si el bot cambió de mesa o regeneró la imagen en este mensaje
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=True)
    generated_image = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

    table = relationship("Table")

    def to_dict(self):
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "table": self.table.to_dict() if self.table else None,
            "generated_image": self.generated_image,
            "created_at": self.created_at
        }