"""Seed initial LKM data sources

Revision ID: 002
Revises: 001
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None

SOURCES = [
    # Patents
    {"name": "EPO EspaceNet", "url_pattern": "https://worldwide.espacenet.com/patent/search?q={query}", "source_type": "patents", "parsing_strategy": "ai", "schedule": "0 4 * * *"},
    {"name": "Google Patents", "url_pattern": "https://patents.google.com/?q={query}&before=priority:{date}", "source_type": "patents", "parsing_strategy": "ai", "schedule": "0 4 * * *"},
    {"name": "ФИПС (Россия)", "url_pattern": "https://new.fips.ru/registers-doc-view/fips_servlet?DB=RUPAT&rn=1&TypeFile=html", "source_type": "patents", "parsing_strategy": "ai", "schedule": "0 5 * * 1"},
    {"name": "USPTO Patent Search", "url_pattern": "https://ppubs.uspto.gov/pubwebapp/external.html?q={query}", "source_type": "patents", "parsing_strategy": "ai", "schedule": "0 4 * * 1"},
    # Scientific
    {"name": "Google Scholar", "url_pattern": "https://scholar.google.com/scholar?q={query}&as_ylo={year}", "source_type": "scientific", "parsing_strategy": "ai", "schedule": "0 6 * * 1,4"},
    {"name": "arXiv Chemistry", "url_pattern": "https://arxiv.org/search/?query={query}&searchtype=all&start=0", "source_type": "scientific", "parsing_strategy": "ai", "schedule": "0 7 * * 1,4"},
    {"name": "ChemRxiv", "url_pattern": "https://chemrxiv.org/engage/chemrxiv/search-results?text={query}", "source_type": "scientific", "parsing_strategy": "ai", "schedule": "0 7 * * 1,4"},
    {"name": "PubMed", "url_pattern": "https://pubmed.ncbi.nlm.nih.gov/?term={query}", "source_type": "scientific", "parsing_strategy": "ai", "schedule": "0 7 * * 1,4"},
    {"name": "Scopus (stub)", "url_pattern": None, "source_type": "scientific", "parsing_strategy": "api", "schedule": "0 6 * * *", "is_active": False},
    # News
    {"name": "Coatings World", "url_pattern": "https://www.coatingsworld.com/search/{query}", "source_type": "news", "parsing_strategy": "ai", "schedule": "0 8 * * *"},
    {"name": "European Coatings", "url_pattern": "https://www.european-coatings.com/search?q={query}", "source_type": "news", "parsing_strategy": "ai", "schedule": "0 8 * * *"},
    {"name": "Paint & Coatings Industry", "url_pattern": "https://www.pcimag.com/search?q={query}", "source_type": "news", "parsing_strategy": "ai", "schedule": "0 8 * * *"},
    {"name": "ЛКМ-портал (ru)", "url_pattern": "https://lakokraska.ru/search?q={query}", "source_type": "news", "parsing_strategy": "ai", "schedule": "0 9 * * *"},
    # Raw Materials
    {"name": "Trading Economics Chemicals", "url_pattern": "https://tradingeconomics.com/commodities", "source_type": "raw_materials", "parsing_strategy": "ai", "schedule": "0 10 * * 1,3,5"},
    {"name": "ICIS (stub)", "url_pattern": None, "source_type": "raw_materials", "parsing_strategy": "api", "schedule": "0 */4 * * *", "is_active": False},
    # Competitors
    {"name": "PPG Industries", "url_pattern": "https://www.ppg.com/en-US/news", "source_type": "competitors", "parsing_strategy": "ai", "schedule": "0 6 * * 1"},
    {"name": "AkzoNobel", "url_pattern": "https://www.akzonobel.com/en/media/media-releases", "source_type": "competitors", "parsing_strategy": "ai", "schedule": "0 6 * * 1"},
    {"name": "Sherwin-Williams", "url_pattern": "https://investors.sherwin-williams.com/news", "source_type": "competitors", "parsing_strategy": "ai", "schedule": "0 6 * * 1"},
    {"name": "BASF Coatings", "url_pattern": "https://www.basf.com/global/en/media/news-releases/coatings.html", "source_type": "competitors", "parsing_strategy": "ai", "schedule": "0 6 * * 1"},
    {"name": "Эмпилс (ru)", "url_pattern": "https://empils.ru/news/", "source_type": "competitors", "parsing_strategy": "ai", "schedule": "0 7 * * 1"},
    # Standards
    {"name": "ISO TC 35 (Paints & Varnishes)", "url_pattern": "https://www.iso.org/committee/47980.html", "source_type": "standards", "parsing_strategy": "ai", "schedule": "0 0 1 * *"},
    {"name": "ECHA REACH", "url_pattern": "https://echa.europa.eu/new-substances", "source_type": "standards", "parsing_strategy": "ai", "schedule": "0 0 1 * *"},
    # Trends
    {"name": "Google Trends", "url_pattern": None, "source_type": "trends", "parsing_strategy": "api", "schedule": "0 8 * * 1"},
]


def upgrade() -> None:
    conn = op.get_bind()
    for src in SOURCES:
        conn.execute(
            sa.text("""
                INSERT INTO sources (id, name, url_pattern, source_type, domain, parsing_strategy,
                    schedule, is_active, created_at, updated_at)
                VALUES (:id, :name, :url_pattern, :source_type, 'lkm', :parsing_strategy,
                    :schedule, :is_active, now(), now())
                ON CONFLICT DO NOTHING
            """),
            {
                "id": str(uuid.uuid4()),
                "name": src["name"],
                "url_pattern": src.get("url_pattern"),
                "source_type": src["source_type"],
                "parsing_strategy": src.get("parsing_strategy", "ai"),
                "schedule": src.get("schedule", "0 */6 * * *"),
                "is_active": src.get("is_active", True),
            },
        )


def downgrade() -> None:
    op.execute("DELETE FROM sources WHERE domain = 'lkm'")
