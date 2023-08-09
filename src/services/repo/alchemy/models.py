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

tg_user = sa.Table(
    "tg_user",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("chat_id", sa.String, unique=True),
    sa.Column("username", sa.String, nullable=True),
    sa.Column("name", sa.String, nullable=True),
    sa.Column("surname", sa.String, nullable=True),
)

tg_user_state = sa.Table(
    "tg_user_state",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("chat_id", sa.String),
    sa.Column("state_map", sa.String),
    sa.Column("state", sa.String, nullable=True),
)

access_counter = sa.Table(
    "access_counter",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("user_id", sa.String),
    sa.Column("remain_per_day", sa.Integer, default=0),
    sa.Column("remain_per_all_time", sa.Integer, default=0),
)

out_tg_message = sa.Table(
    "out_tg_message",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("chat_id", sa.String, nullable=False),
    sa.Column("message_id", sa.String, nullable=False),
    sa.Column("text", sa.String),
    sa.Column("text_like", sa.String, default=""),
    sa.Column("not_pushed_to_delete", sa.Boolean, default=False),
    sa.Column("not_pushed_to_edit_text", sa.String, default=""),
    sa.Column("pushed", sa.Boolean, default=False),
)
