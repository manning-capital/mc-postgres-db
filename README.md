# MC Postgres DB

A Python package containing ORM models for a PostgreSQL database that powers a personal quantitative trading and investment analysis platform.

## Overview

This package provides SQLAlchemy ORM models and database utilities for managing financial data, trading strategies, portfolio analytics, and market research. The database serves as the backbone for a personal "quant hedge fund" project, storing everything from market data and content data.

## Features

- **Asset Models**: `AssetType` and `Asset` tables for categorizing and managing financial instruments and various fiat and digital currencies
- **Provider Models**: `ProviderType` and `Provider` tables for handling data sources and exchanges
- **Market Data Models**: `ProviderAssetMarket` table for storing OHLCV and bid/ask price data
- **Order Models**: `ProviderAssetOrder` table for tracking trading orders between assets
- **Content Models**: `ContentType`, `ProviderContent`, and `AssetContent` tables for managing news articles and social content
- **Relation Models**: `ProviderAsset` table for mapping relationships between providers and assets

## Installation

### From PyPI

```bash
pip install mc-postgres-db
```

### From Source

```bash
# Clone the repository
git clone <repository-url>
cd mc-postgres-db

# Install using uv (recommended)
uv sync
```

## Database Setup

1. **PostgreSQL Setup**: Ensure PostgreSQL is installed and running
2. **Environment Variables**: Set up your database connection string
   ```bash
   export SQLALCHEMY_DATABASE_URL="postgresql://username:password@localhost:5432/mc_trading_db"
   ```

## Usage

```python
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from mcpdb.tables import Asset, Provider, ProviderAssetMarket

# Create database connection
url = "postgresql://username:password@localhost:5432/mc_trading_db"
engine = create_engine(url)

# Query assets
with Session(engine) as session:
    stmt = select(Asset).where(Asset.is_active)
    assets = session.scalars(stmt).all()
    asset_pairs = {asset.id: asset.name for asset in assets}
    print("Available assets:")
    for asset_id, asset_name in asset_pairs.items():
        print(f"{asset_id}: {asset_name}")

# Query market data
with Session(engine) as session:
    stmt = (
        select(ProviderAssetMarket)
        .where(
            ProviderAssetMarket.asset_id == 1,  # Bitcoin for example
            ProviderAssetMarket.provider_id == 2,  # Binance for example
        )
        .order_by(ProviderAssetMarket.timestamp.desc())
        .limit(10)
    )
    market_data = session.scalars(stmt).all()
    for data in market_data:
        print(f"Timestamp: {data.timestamp}, Close: {data.close}, Volume: {data.volume}")

# Get assets from a provider
with Session(engine) as session:
    stmt = select(Provider).where(Provider.id == 1)
    provider = session.scalars(stmt).one()
    provider_assets = provider.get_all_assets(engine)
    print(f"Assets available from {provider.name}:")
    for provider_asset in provider_assets:
        print(f"Asset code: {provider_asset.asset_code}")
```

## Models Overview

### Core Models

- **AssetType**: Categorizes assets (e.g., stocks, bonds, cryptocurrencies) with names and descriptions
- **Asset**: Represents financial instruments with references to asset types, symbols, and optional underlying assets
- **ProviderType**: Categorizes data providers (e.g., exchanges, news services) with names and descriptions
- **Provider**: Represents data sources with references to provider types and optional underlying providers
- **ProviderAsset**: Maps the relationship between providers and assets with asset codes and active status
- **ProviderAssetOrder**: Tracks orders for assets from providers including timestamp, price, and volume
- **ProviderAssetMarket**: Stores OHLCV (Open, High, Low, Close, Volume) market data and bid/ask prices
- **ContentType**: Categorizes content (e.g., news articles, social media posts) with names and descriptions
- **ProviderContent**: Stores content from providers with timestamps, titles, descriptions, and full content
- **AssetContent**: Maps the relationship between content and assets

### Database Schema Features

- **Inheritance Support**: Assets and providers can reference underlying entities for hierarchical relationships
- **Timestamped Records**: All tables include creation and update timestamps
- **Soft Delete Pattern**: Uses is_active flags to mark records as inactive without deletion
- **Time Series Data**: Market data is organized by timestamp for efficient time-series operations
- **Cross-Reference Tables**: Enables many-to-many relationships between assets, providers, and content

## Development

### Setting up Development Environment

```bash
# Install development dependencies using uv
uv sync --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check src/mcpdb/
uv run ruff format src/mcpdb/
```

### Database Migrations

```bash
# Generate new migration
uv run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1
```

## Project Structure

```
mc-postgres-db/
├── src/                 # Source code directory
│   └── mcpdb/           # Package directory
│       └── tables.py    # SQLAlchemy ORM models
├── tests/               # Unit and integration tests
├── scripts/             # Database maintenance scripts
├── pyproject.toml       # Project configuration and dependencies
├── uv.lock             # Locked dependency versions
└── README.md           # Project documentation
```

## Data Sources

This database integrates with various financial data providers:

- Market data APIs (Alpha Vantage, IEX Cloud, etc.)
- Fundamental data providers
- Alternative data sources
- Custom scraped data

## Security & Compliance

- Database connections use SSL encryption
- Sensitive data is encrypted at rest
- Access controls and audit logging implemented
- Regular backups and disaster recovery procedures

## Performance Considerations

- Optimized indexes for common query patterns
- Partitioned tables for large time-series data
- Connection pooling for high-throughput operations
- Caching layer for frequently accessed data

## Contributing

This is a personal project, but suggestions and improvements are welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

This project is for personal use and learning purposes.

## Disclaimer

This software is for educational and personal use only. It is not intended for production trading or investment advice. Use at your own risk.
