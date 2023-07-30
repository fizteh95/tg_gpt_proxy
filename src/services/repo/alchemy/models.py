import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

sa_metadata = sa.MetaData()
user_context = sa.Table(
    "user_context",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("user_id", sa.String, unique=True),
    sa.Column("context", JSON, nullable=True),
)
