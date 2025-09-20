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
- **Sentiment Models**: `SentimentType` and `ProviderContentSentiment` tables for analyzing content sentiment
- **Asset Group Models**: `ProviderAssetGroup`, `ProviderAssetGroupMember`, and `ProviderAssetGroupAttribute` tables for grouping provider assets and calculating aggregated statistical values
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
from mc_postgres_db.models import Asset, Provider, ProviderAssetMarket

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
            ProviderAssetMarket.from_asset_id == 1,  # Bitcoin for example
            ProviderAssetMarket.to_asset_id == 2,    # USD for example
            ProviderAssetMarket.provider_id == 3,    # Binance for example
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
- **ProviderAssetMarket**: Stores OHLCV (Open, High, Low, Close, Volume) market data and bid/ask prices for asset pairs
- **ContentType**: Categorizes content (e.g., news articles, social media posts) with names and descriptions
- **ProviderContent**: Stores content from providers with timestamps, titles, descriptions, and full content
- **AssetContent**: Maps the relationship between content and assets
- **SentimentType**: Categorizes sentiment analysis methods (e.g., PROVIDER, NLTK, VADER) with names and descriptions
- **ProviderContentSentiment**: Stores sentiment analysis results for content with positive, negative, neutral, and overall sentiment scores
- **ProviderAssetGroup**: Groups provider assets for calculating aggregated statistical values between members. Each group contains provider asset pairs that share statistical relationships for cointegration analysis, mean reversion modeling, and linear regression calculations.
- **ProviderAssetGroupMember**: Maps provider asset pairs to statistical groups for aggregated calculations. Each record represents a pair of assets (from_asset_id, to_asset_id) from a specific provider that belong to a statistical group. Optional order field allows sequencing within groups for hierarchical analysis.
- **ProviderAssetGroupAttribute**: Stores aggregated statistical calculations for provider asset groups across multiple time windows. Contains cointegration analysis results, Ornstein-Uhlenbeck process parameters for mean reversion modeling, and comprehensive linear regression statistics including coefficients, fit measures, and significance tests.

### Database Schema Features

- **Inheritance Support**: Assets and providers can reference underlying entities for hierarchical relationships
- **Timestamped Records**: All tables include creation and update timestamps
- **Soft Delete Pattern**: Uses is_active flags to mark records as inactive without deletion
- **Time Series Data**: Market data is organized by timestamp for efficient time-series operations
- **Cross-Reference Tables**: Enables many-to-many relationships between assets, providers, and content
- **Statistical Group Support**: Specialized tables for grouping provider assets and calculating aggregated statistical measures across multiple time windows
- **Composite Primary Keys**: Ensures uniqueness across multiple dimensions (timestamp, provider, asset group, lookback window)

## Development

### Setting up Development Environment

```bash
# Install development dependencies using uv
uv sync --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check
uv run ruff format
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
├── src/                       # Source code directory
│   └── mc_postgres_db/        # Main package directory
│       ├── __init__.py
│       ├── models.py
│       ├── operations.py
│       ├── prefect/
│       │   ├── __init__.py
│       │   ├── tasks.py
│       │   └── asyncio/
│       │       ├── __init__.py
│       │       └── tasks.py
│       └── testing/
│           ├── __init__.py
│           └── utilities.py
├── tests/                    # Unit and integration tests
├── alembic/                  # Database migrations
├── pyproject.toml            # Project configuration and dependencies
├── uv.lock                   # Locked dependency versions
└── README.md                 # Project documentation
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

## Testing Utilities

This package provides a robust testing harness for database-related tests, allowing you to run your tests against a temporary SQLite database that mirrors your PostgreSQL schema. This is especially useful for testing Prefect flows and tasks that interact with the database, without requiring a live PostgreSQL instance or extensive mocking.

### `postgres_test_harness`

The `postgres_test_harness` context manager (found in `mc_postgres_db.testing.utilities`) creates a temporary SQLite database file, initializes all ORM models, and **patches the Prefect tasks used to obtain the SQLAlchemy engine** (both sync and async) so that all database operations in your flows and tasks are transparently redirected to this SQLite database.

**Key benefits:**
- No need to change or mock every Prefect flow or task that uses the database engine.
- All Prefect tasks that call `get_engine` (sync or async) will automatically use the temporary SQLite database.
- The database is created fresh for each test session or function (depending on fixture scope), ensuring isolation and repeatability.
- At the end of the test, the database and all tables are cleaned up.

### Usage with Pytest

You can use the harness as a fixture in your tests. For example:

```python
import pytest
from mc_postgres_db.testing.utilities import postgres_test_harness

@pytest.fixture(scope="function", autouse=True)
def postgres_harness():
    with postgres_test_harness():
        yield

def test_my_flow():
    # Any Prefect task that calls get_engine() will use the SQLite test DB
    ...
```

If you are also testing Prefect flows, the postgres harness will already use Prefect's harness to ensure isolation:

```python
import pytest
from mc_postgres_db.testing.utilities import postgres_test_harness

@pytest.fixture(scope="session", autouse=True)
def postgres_harness():
    with postgres_test_harness(prefect_server_startup_timeout=45):
        yield
```

Now, all your tests (including those that run Prefect flows) will use the temporary SQLite database, and you don't need to modify your flows or tasks to support testing.

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
