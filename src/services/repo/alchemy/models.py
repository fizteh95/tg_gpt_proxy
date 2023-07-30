import sqlalchemy as sa

sa_metadata = sa.MetaData()
in_command = sa.Table(
    "in_command",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("outer_id", sa.String, unique=True),  # id_
    sa.Column("text_command", sa.String, nullable=True),
)
