from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    JSON,
    BigInteger,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    pass


class RepoStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    SANITIZING = "SANITIZING"
    INDEXING = "INDEXING"
    PARSING = "PARSING"
    GRAPHING = "GRAPHING"
    EMBEDDING = "EMBEDDING"
    SUMMARIZING = "SUMMARIZING"
    READY = "READY"
    FAILED = "FAILED"
    STALE = "STALE"


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Repo(Base):
    __tablename__ = "repos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(1024))
    branch: Mapped[str] = mapped_column(String(255), default="main")
    commit_hash: Mapped[Optional[str]] = mapped_column(String(64))
    status: Mapped[RepoStatus] = mapped_column(
        SAEnum(RepoStatus), default=RepoStatus.QUEUED
    )
    local_path: Mapped[Optional[str]] = mapped_column(String(1024))
    file_count: Mapped[int] = mapped_column(Integer, default=0)
    total_loc: Mapped[int] = mapped_column(BigInteger, default=0)
    languages: Mapped[Optional[dict]] = mapped_column(JSON)  # {"python": 42, ...}
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    files: Mapped[List["File"]] = relationship(back_populates="repo", cascade="all, delete-orphan")
    jobs: Mapped[List["Job"]] = relationship(back_populates="repo", cascade="all, delete-orphan")
    summaries: Mapped[List["Summary"]] = relationship(back_populates="repo", cascade="all, delete-orphan")
    events: Mapped[List["Event"]] = relationship(back_populates="repo", cascade="all, delete-orphan")


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repo_id: Mapped[int] = mapped_column(ForeignKey("repos.id"), nullable=False)
    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    language: Mapped[Optional[str]] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    loc: Mapped[int] = mapped_column(Integer, default=0)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64))
    is_entry_point: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    repo: Mapped["Repo"] = relationship(back_populates="files")
    functions: Mapped[List["Function"]] = relationship(back_populates="file", cascade="all, delete-orphan")
    imports: Mapped[List["Import"]] = relationship(back_populates="file", cascade="all, delete-orphan")


class Function(Base):
    __tablename__ = "functions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id"), nullable=False)
    repo_id: Mapped[int] = mapped_column(ForeignKey("repos.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    class_name: Mapped[Optional[str]] = mapped_column(String(512))
    start_line: Mapped[int] = mapped_column(Integer, default=0)
    end_line: Mapped[int] = mapped_column(Integer, default=0)
    body: Mapped[Optional[str]] = mapped_column(Text)
    docstring: Mapped[Optional[str]] = mapped_column(Text)
    parameters: Mapped[Optional[list]] = mapped_column(JSON)
    return_type: Mapped[Optional[str]] = mapped_column(String(256))
    is_async: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    file: Mapped["File"] = relationship(back_populates="functions")


class Import(Base):
    __tablename__ = "imports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id"), nullable=False)
    repo_id: Mapped[int] = mapped_column(ForeignKey("repos.id"), nullable=False)
    module: Mapped[str] = mapped_column(String(512), nullable=False)
    names: Mapped[Optional[list]] = mapped_column(JSON)  # ["func1", "Class1"]
    is_relative: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    file: Mapped["File"] = relationship(back_populates="imports")


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repo_id: Mapped[int] = mapped_column(ForeignKey("repos.id"), nullable=False)
    scope: Mapped[str] = mapped_column(String(64))  # "file" | "module" | "folder" | "project"
    path: Mapped[Optional[str]] = mapped_column(String(1024))  # file or folder path
    content: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(64))  # ollama | gemini | none
    model: Mapped[Optional[str]] = mapped_column(String(128))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    repo: Mapped["Repo"] = relationship(back_populates="summaries")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repo_id: Mapped[int] = mapped_column(ForeignKey("repos.id"), nullable=False)
    job_type: Mapped[str] = mapped_column(String(64))  # "index" | "reindex" | "embed"
    status: Mapped[JobStatus] = mapped_column(SAEnum(JobStatus), default=JobStatus.PENDING)
    stage: Mapped[Optional[str]] = mapped_column(String(64))  # current pipeline stage
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    repo: Mapped["Repo"] = relationship(back_populates="jobs")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repo_id: Mapped[Optional[int]] = mapped_column(ForeignKey("repos.id"))
    event_type: Mapped[str] = mapped_column(String(128))  # "repo_uploaded", "repo_indexed", etc.
    data: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    repo: Mapped[Optional["Repo"]] = relationship(back_populates="events")


class TokenUsage(Base):
    __tablename__ = "token_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repo_id: Mapped[Optional[int]] = mapped_column(ForeignKey("repos.id"))
    provider: Mapped[str] = mapped_column(String(64))
    request_type: Mapped[str] = mapped_column(String(64))  # "summary" | "answer" | "embed"
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
