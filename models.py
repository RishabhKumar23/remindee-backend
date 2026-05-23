from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4

from sqlmodel import Field, SQLModel, Relationship

def _uuid() -> str:
    return str(uuid4())

def _now() -> datetime:
    return datetime.now(timezone.utc)

##ANCHOR - For Image
class Image(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    job_id: str = Field(foreign_key="job.id")
    style_name: str = Field(default="")
    imagekit_url: Optional[str] = Field(default=None)
    status: str = Field(default="pending")
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_now)

    job: Optional["Job"] = Relationship(back_populates="Images")

##ANCHOR - For Job -> job is nothing but the task to create Images
class Job(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    prompt: str = Field(default="")
    num_Images: int = Field(default=1, ge=1, le=3)
    headshot_url: str = Field(default="")
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=_now)

    Images: List[Image] = Relationship(back_populates="job")