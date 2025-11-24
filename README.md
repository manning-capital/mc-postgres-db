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

### Testing Dependencies

For testing, you'll also need Docker installed and running:

```bash
# Install Docker (if not already installed)
# On macOS with Homebrew:
brew install --cask docker

# On Ubuntu/Debian:
sudo apt-get update
sudo apt-get install docker.io

# Start Docker daemon
# On macOS: Start Docker Desktop
# On Linux: sudo systemctl start docker
```

## Database Setup

1. **PostgreSQL Setup**: Ensure PostgreSQL is installed and running
2. **Environment Variables**: Set up your database connection string
   ```bash
   export SQLALCHEMY_DATABASE_URL="postgresql://username:password@localhost:5432/mc_trading_db"
   ```

## Usage

### Basic Queries

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

### Efficient Relationship Loading with `joinedload`

The ORM models are optimized for efficient querying using SQLAlchemy's `joinedload` functionality. All relationships are unidirectional (singular) to avoid N+1 query problems and enable efficient eager loading:

```python
from sqlalchemy.orm import Session, joinedload
from mc_postgres_db.models import (
    Asset, Provider, ProviderAssetMarket, ProviderAssetOrder,
    ProviderAssetGroup, ProviderAssetGroupMember, ProviderAssetGroupAttribute
)

# Load Asset with its AssetType (no additional queries)
with Session(engine) as session:
    asset = session.query(Asset).options(
        joinedload(Asset.asset_type)
    ).filter_by(id=1).first()
    
    print(f"Asset: {asset.name} ({asset.asset_type.name})")
    # No additional query needed - asset_type is already loaded

# Load ProviderAssetOrder with all related objects
with Session(engine) as session:
    order = session.query(ProviderAssetOrder).options(
        joinedload(ProviderAssetOrder.provider),
        joinedload(ProviderAssetOrder.from_asset),
        joinedload(ProviderAssetOrder.to_asset)
    ).filter_by(id=1).first()
    
    print(f"Order: {order.from_asset.name} -> {order.to_asset.name}")
    print(f"Provider: {order.provider.name}")
    # All relationships loaded in a single query

# Load ProviderAssetGroup with members and attributes
with Session(engine) as session:
    group = session.query(ProviderAssetGroup).options(
        joinedload(ProviderAssetGroup.asset_group_type),
        joinedload(ProviderAssetGroup.members)
    ).filter_by(id=1).first()
    
    print(f"Group: {group.name}")
    print(f"Type: {group.asset_group_type.name}")
    print(f"Members ({len(group.members)}):")
    for member in group.members:
        print(f"  - {member.from_asset.name} -> {member.to_asset.name} (order: {member.order})")

# Load ProviderAssetGroupAttribute with related group
with Session(engine) as session:
    attribute = session.query(ProviderAssetGroupAttribute).options(
        joinedload(ProviderAssetGroupAttribute.provider_asset_group)
    ).filter_by(
        provider_asset_group_id=1,
        lookback_window_seconds=86400
    ).first()
    
    print(f"Group: {attribute.provider_asset_group.name}")
    print(f"Cointegration p-value: {attribute.cointegration_pvalue}")
    print(f"OU Process - mu: {attribute.ou_mu}, theta: {attribute.ou_theta}, sigma: {attribute.ou_sigma}")
```

### Asset Group Management

```python
# Create a new asset group for pairs trading
with Session(engine) as session:
    # Create asset group type
    asset_group_type = AssetGroupType(
        name="Pairs Trading",
        description="Groups for pairs trading strategies",
        is_active=True
    )
    session.add(asset_group_type)
    session.flush()
    
    # Create the asset group
    asset_group = ProviderAssetGroup(
        provider_id=1,
        asset_group_type_id=asset_group_type.id,
        name="BTC-ETH Pairs",
        description="Bitcoin and Ethereum pairs for mean reversion",
        is_active=True
    )
    session.add(asset_group)
    session.flush()
    
    # Add members to the group
    member1 = ProviderAssetGroupMember(
        provider_id=1,
        provider_asset_group_id=asset_group.id,
        from_asset_id=1,  # Bitcoin
        to_asset_id=2,    # USD
        order=1
    )
    member2 = ProviderAssetGroupMember(
        provider_id=1,
        provider_asset_group_id=asset_group.id,
        from_asset_id=3,  # Ethereum
        to_asset_id=2,    # USD
        order=2
    )
    session.add_all([member1, member2])
    session.commit()
    
    print(f"Created asset group: {asset_group.name}")
    print(f"Members: {len(asset_group.members)}")
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
- **AssetGroupType**: Categorizes asset group types (e.g., "Pairs Trading", "Mean Reversion") for organizing statistical groups
- **ProviderAssetGroup**: Groups provider assets for calculating aggregated statistical values between members. Each group contains provider asset pairs that share statistical relationships for cointegration analysis, mean reversion modeling, and linear regression calculations.
- **ProviderAssetGroupMember**: Maps provider asset pairs to statistical groups for aggregated calculations. Each record represents a pair of assets (from_asset_id, to_asset_id) from a specific provider that belong to a statistical group. The order field allows sequencing within groups for hierarchical analysis.
- **ProviderAssetGroupAttribute**: Stores aggregated statistical calculations for provider asset groups across multiple time windows. Contains cointegration analysis results, Ornstein-Uhlenbeck process parameters for mean reversion modeling, and comprehensive linear regression statistics including coefficients, fit measures, and significance tests.

### Database Schema Features

- **Inheritance Support**: Assets and providers can reference underlying entities for hierarchical relationships
- **Timestamped Records**: All tables include creation and update timestamps
- **Soft Delete Pattern**: Uses is_active flags to mark records as inactive without deletion
- **Time Series Data**: Market data is organized by timestamp for efficient time-series operations
- **Cross-Reference Tables**: Enables many-to-many relationships between assets, providers, and content
- **Statistical Group Support**: Specialized tables for grouping provider assets and calculating aggregated statistical measures across multiple time windows
- **Composite Primary Keys**: Ensures uniqueness across multiple dimensions (timestamp, provider, asset group, lookback window)
- **Optimized Relationships**: Unidirectional relationships designed for efficient `joinedload` operations, eliminating N+1 query problems
- **Asset Group Management**: Comprehensive support for pairs trading and statistical analysis with ordered member sequences

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
│   ├── with_prefect/        # Tests that use Prefect
│   ├── no_prefect/          # Tests that don't use Prefect
│   └── utils.py             # Shared test utilities
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

This package provides a robust testing harness for database-related tests, allowing you to run your tests against a temporary PostgreSQL database running in Docker. This is especially useful for testing Prefect flows and tasks that interact with the database, without requiring a live PostgreSQL instance or extensive mocking.

### Prerequisites

The testing harness requires Docker to be installed and running on your system:

```bash
# Check if Docker is installed and running
docker --version
docker ps
```

If Docker is not available, you may need to install Docker Desktop or start the Docker daemon.

### `postgres_test_harness`

The `postgres_test_harness` context manager (found in `mc_postgres_db.testing.utilities`) creates a temporary PostgreSQL database using Docker and initializes all ORM models. It can optionally integrate with Prefect to set up database secrets, or be used independently without Prefect.

**Key benefits:**
- No need to change or mock every Prefect flow or task that uses the database engine (when using Prefect mode).
- All Prefect tasks that call `get_engine` (sync or async) will automatically use the temporary PostgreSQL database (when using Prefect mode).
- Can be used independently of Prefect for direct database testing.
- The database is created fresh for each test session or function (depending on fixture scope), ensuring isolation and repeatability.
- Uses ephemeral storage (no volume mounting) for complete isolation between test runs.
- Comprehensive safety checks to prevent accidental connection to production databases.
- At the end of the test, the Docker container and all tables are cleaned up.
- Prefect imports are lazy-loaded, so Prefect is only required when `use_prefect=True`.

**Safety Features:**
- Validates that the database connection is to localhost only
- Ensures the database uses test credentials (`testuser`/`testpass`/`testdb`)
- Checks database size to prevent accidental connection to production databases
- Verifies Docker container environment variables match expected test configuration

**Configuration:**
- PostgreSQL version can be controlled via the `POSTGRES_VERSION` environment variable (defaults to `latest`)
- Test database uses ephemeral storage for complete isolation
- Automatic port selection to avoid conflicts
- `use_prefect`: Boolean flag to enable/disable Prefect integration (default: `True`)
- `prefect_server_startup_timeout`: Timeout in seconds for Prefect server startup (only used when `use_prefect=True`, default: `30`)

### Usage with Prefect (Default)

When `use_prefect=True` (the default), the harness initializes Prefect's test harness and sets up the database URL as a Prefect secret. This ensures that all Prefect tasks which retrieve the database engine (both sync and async) will use this temporary PostgreSQL database during your tests.

You can use the harness as a fixture in your tests:

```python
import pytest
from mc_postgres_db.testing.utilities import postgres_test_harness

@pytest.fixture(scope="function", autouse=True)
def postgres_harness():
    with postgres_test_harness():
        yield

def test_my_flow():
    # Any Prefect task that calls get_engine() will use the PostgreSQL test DB
    ...
```

For session-scoped tests with Prefect flows:

```python
import pytest
from mc_postgres_db.testing.utilities import postgres_test_harness

@pytest.fixture(scope="session", autouse=True)
def postgres_harness():
    with postgres_test_harness(prefect_server_startup_timeout=45):
        yield
```

### Usage without Prefect

When `use_prefect=False`, the harness skips Prefect initialization and yields the SQLAlchemy engine directly. This is useful for tests that don't use Prefect or when you want to test database functionality independently.

**As a context manager:**

```python
from mc_postgres_db.testing.utilities import postgres_test_harness
from sqlalchemy import text
from sqlalchemy.orm import Session
from mc_postgres_db.models import AssetType

# Use the harness without Prefect
with postgres_test_harness(use_prefect=False) as engine:
    # Use the engine directly
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.fetchone()[0] == 1
    
    # Or use with SQLAlchemy sessions
    with Session(engine) as session:
        asset_type = AssetType(name="Test Asset")
        session.add(asset_type)
        session.commit()
```

**As a pytest fixture:**

You can also use the harness as a pytest fixture, which allows you to pass the engine as a parameter to your test functions:

```python
import pytest
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session
from mc_postgres_db.testing.utilities import postgres_test_harness
from mc_postgres_db.models import AssetType

@pytest.fixture
def db_engine():
    """Fixture that provides a database engine without Prefect."""
    with postgres_test_harness(use_prefect=False) as engine:
        yield engine

def test_database_connection(db_engine: Engine):
    """Test that we can connect to the database."""
    with db_engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.fetchone()[0] == 1

def test_create_asset_type(db_engine: Engine):
    """Test creating an asset type using the engine fixture."""
    with Session(db_engine) as session:
        asset_type = AssetType(
            name="Test Asset Type",
            description="Test Description"
        )
        session.add(asset_type)
        session.commit()
        
        # Verify it was created
        assert asset_type.id is not None
        assert asset_type.is_active is True
```

**Note:** When `use_prefect=False`, the harness yields the engine. When `use_prefect=True` (default), it yields `None` (Prefect is initialized and the database URL is available as a secret).

### Test Organization

The test suite is organized into two directories to isolate Prefect-dependent and Prefect-independent tests:

- **`tests/with_prefect/`**: Tests that use Prefect. These tests have a `conftest.py` that sets up the Prefect test harness automatically.
- **`tests/no_prefect/`**: Tests that don't use Prefect. These tests can use `postgres_test_harness(use_prefect=False)` without conflicts.

This organization ensures that:
- Tests that need Prefect have it available via the session fixture
- Tests that don't need Prefect can run without Prefect dependencies
- No namespace conflicts occur between test directories and the Prefect package

### Additional Testing Utilities

The package also provides a `clear_database` function for manually clearing test databases:

```python
from mc_postgres_db.testing.utilities import clear_database
from sqlalchemy import create_engine

# Clear a test database (with safety checks)
engine = create_engine("postgresql://testuser:testpass@localhost:5432/testdb")
clear_database(engine)  # Drops and recreates all tables
```

**Note:** The `clear_database` function includes comprehensive safety checks to prevent accidental clearing of production databases.

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
