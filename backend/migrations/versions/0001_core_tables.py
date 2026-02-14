from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql


revision = "0001_core_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "sites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("hostname", sa.String(length=255)),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filter_mode", sa.String(length=20), nullable=False, server_default="disabled"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
    )
    op.create_index("ix_sites_hostname", "sites", ["hostname"], unique=True)

    op.create_table(
        "site_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_site_users_site_id", "site_users", ["site_id"], unique=False)
    op.create_index("ix_site_users_user_id", "site_users", ["user_id"], unique=False)

    op.create_table(
        "geofences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255)),
        sa.Column("polygon", Geometry("POLYGON", srid=4326)),
        sa.Column("center", Geometry("POINT", srid=4326)),
        sa.Column("radius_meters", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"]),
    )
    op.create_index(
        "ix_geofences_polygon",
        "geofences",
        ["polygon"],
        postgresql_using="gist",
    )
    op.create_index(
        "ix_geofences_center",
        "geofences",
        ["center"],
        postgresql_using="gist",
    )

    op.create_table(
        "ip_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cidr", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"]),
    )
    op.create_index("ix_ip_rules_site_id", "ip_rules", ["site_id"], unique=False)

    op.create_table(
        "artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"]),
    )
    op.create_index("ix_artifacts_site_id", "artifacts", ["site_id"], unique=False)

    op.create_table(
        "access_audit",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("client_ip", sa.String(length=50)),
        sa.Column("ip_geo_lat", sa.Float()),
        sa.Column("ip_geo_lng", sa.Float()),
        sa.Column("ip_geo_country", sa.String(length=10)),
        sa.Column("client_gps", Geometry("POINT", srid=4326)),
        sa.Column("decision", sa.String(length=20)),
        sa.Column("reason", sa.Text()),
        sa.Column("artifact_path", sa.String(length=500)),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"]),
    )
    op.create_index("ix_access_audit_site_id", "access_audit", ["site_id"], unique=False)
    op.create_index("ix_access_audit_timestamp", "access_audit", ["timestamp"], unique=False)
    op.create_index(
        "ix_access_audit_client_gps",
        "access_audit",
        ["client_gps"],
        postgresql_using="gist",
    )

    op.create_table(
        "ip_geo_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("ip_address", postgresql.INET(), nullable=False),
        sa.Column("country_code", sa.String(length=10)),
        sa.Column("location", Geometry("POINT", srid=4326)),
        sa.Column("raw", postgresql.JSONB()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_ip_geo_cache_ip_address", "ip_geo_cache", ["ip_address"], unique=True)
    op.create_index(
        "ix_ip_geo_cache_location",
        "ip_geo_cache",
        ["location"],
        postgresql_using="gist",
    )


def downgrade() -> None:
    op.drop_index("ix_ip_geo_cache_location", table_name="ip_geo_cache")
    op.drop_index("ix_ip_geo_cache_ip_address", table_name="ip_geo_cache")
    op.drop_table("ip_geo_cache")

    op.drop_index("ix_access_audit_client_gps", table_name="access_audit")
    op.drop_index("ix_access_audit_timestamp", table_name="access_audit")
    op.drop_index("ix_access_audit_site_id", table_name="access_audit")
    op.drop_table("access_audit")

    op.drop_index("ix_artifacts_site_id", table_name="artifacts")
    op.drop_table("artifacts")

    op.drop_index("ix_ip_rules_site_id", table_name="ip_rules")
    op.drop_table("ip_rules")

    op.drop_index("ix_geofences_center", table_name="geofences")
    op.drop_index("ix_geofences_polygon", table_name="geofences")
    op.drop_table("geofences")

    op.drop_index("ix_site_users_user_id", table_name="site_users")
    op.drop_index("ix_site_users_site_id", table_name="site_users")
    op.drop_table("site_users")

    op.drop_index("ix_sites_hostname", table_name="sites")
    op.drop_table("sites")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
