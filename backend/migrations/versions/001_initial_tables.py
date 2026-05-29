"""Initial tables

Revision ID: 001
Revises:
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "repos",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(1024)),
        sa.Column("branch", sa.String(255), default="main"),
        sa.Column("commit_hash", sa.String(64)),
        sa.Column(
            "status",
            sa.Enum(
                "QUEUED", "SANITIZING", "INDEXING", "PARSING",
                "GRAPHING", "EMBEDDING", "SUMMARIZING", "READY", "FAILED", "STALE",
                name="repostatus",
            ),
            default="QUEUED",
        ),
        sa.Column("local_path", sa.String(1024)),
        sa.Column("file_count", sa.Integer, default=0),
        sa.Column("total_loc", sa.BigInteger, default=0),
        sa.Column("languages", sa.JSON),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        "files",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("repo_id", sa.Integer, sa.ForeignKey("repos.id"), nullable=False),
        sa.Column("path", sa.String(1024), nullable=False),
        sa.Column("language", sa.String(64)),
        sa.Column("size_bytes", sa.Integer, default=0),
        sa.Column("loc", sa.Integer, default=0),
        sa.Column("file_hash", sa.String(64)),
        sa.Column("is_entry_point", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_files_repo_id", "files", ["repo_id"])
    op.create_index("ix_files_path", "files", ["path"])

    op.create_table(
        "functions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("file_id", sa.Integer, sa.ForeignKey("files.id"), nullable=False),
        sa.Column("repo_id", sa.Integer, sa.ForeignKey("repos.id"), nullable=False),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("class_name", sa.String(512)),
        sa.Column("start_line", sa.Integer, default=0),
        sa.Column("end_line", sa.Integer, default=0),
        sa.Column("body", sa.Text),
        sa.Column("docstring", sa.Text),
        sa.Column("parameters", sa.JSON),
        sa.Column("return_type", sa.String(256)),
        sa.Column("is_async", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_functions_repo_id", "functions", ["repo_id"])
    op.create_index("ix_functions_name", "functions", ["name"])

    op.create_table(
        "imports",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("file_id", sa.Integer, sa.ForeignKey("files.id"), nullable=False),
        sa.Column("repo_id", sa.Integer, sa.ForeignKey("repos.id"), nullable=False),
        sa.Column("module", sa.String(512), nullable=False),
        sa.Column("names", sa.JSON),
        sa.Column("is_relative", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_imports_repo_id", "imports", ["repo_id"])

    op.create_table(
        "summaries",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("repo_id", sa.Integer, sa.ForeignKey("repos.id"), nullable=False),
        sa.Column("scope", sa.String(64)),
        sa.Column("path", sa.String(1024)),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("provider", sa.String(64)),
        sa.Column("model", sa.String(128)),
        sa.Column("input_tokens", sa.Integer, default=0),
        sa.Column("output_tokens", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_summaries_repo_id", "summaries", ["repo_id"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("repo_id", sa.Integer, sa.ForeignKey("repos.id"), nullable=False),
        sa.Column("job_type", sa.String(64)),
        sa.Column(
            "status",
            sa.Enum("PENDING", "RUNNING", "DONE", "FAILED", "CANCELLED", name="jobstatus"),
            default="PENDING",
        ),
        sa.Column("stage", sa.String(64)),
        sa.Column("progress", sa.Integer, default=0),
        sa.Column("error_message", sa.Text),
        sa.Column("started_at", sa.DateTime),
        sa.Column("ended_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_jobs_repo_id", "jobs", ["repo_id"])

    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("repo_id", sa.Integer, sa.ForeignKey("repos.id")),
        sa.Column("event_type", sa.String(128)),
        sa.Column("data", sa.JSON),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "token_usage",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("repo_id", sa.Integer, sa.ForeignKey("repos.id")),
        sa.Column("provider", sa.String(64)),
        sa.Column("request_type", sa.String(64)),
        sa.Column("input_tokens", sa.Integer, default=0),
        sa.Column("output_tokens", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("token_usage")
    op.drop_table("events")
    op.drop_table("jobs")
    op.drop_table("summaries")
    op.drop_table("imports")
    op.drop_table("functions")
    op.drop_table("files")
    op.drop_table("repos")
