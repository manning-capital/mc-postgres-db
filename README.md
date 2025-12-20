# Postgres Database - Manning Capital

A Python package containing SQLAlchemy ORM models for a PostgreSQL database that powers a personal quantitative trading and investment analysis platform.

## Overview

This package provides SQLAlchemy ORM models and database utilities for managing financial data, trading strategies, portfolio analytics, and market research. The database serves as the backbone for a personal "quant hedge fund" project, storing everything from market data and content data.

All models are defined in `src/mc_postgres_db/models.py`. See the model definitions for detailed field descriptions and relationships.

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
# Check if Docker is installed and running
docker --version
docker ps
```

## Database Setup

1. **PostgreSQL Setup**: Ensure PostgreSQL is installed and running
2. **Environment Variables**: Set up your database connection string
   ```bash
   export SQLALCHEMY_DATABASE_URL="postgresql://username:password@localhost:5432/mc_trading_db"
   ```

## Usage Examples

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
    for asset in assets:
        print(f"{asset.id}: {asset.name}")

# Query market data
with Session(engine) as session:
    stmt = (
        select(ProviderAssetMarket)
        .where(
            ProviderAssetMarket.from_asset_id == 1,
            ProviderAssetMarket.to_asset_id == 2,
            ProviderAssetMarket.provider_id == 3,
        )
        .order_by(ProviderAssetMarket.timestamp.desc())
        .limit(10)
    )
    market_data = session.scalars(stmt).all()
    for data in market_data:
        print(f"Timestamp: {data.timestamp}, Close: {data.close}, Volume: {data.volume}")
```

### Efficient Relationship Loading

The ORM models are optimized for efficient querying using SQLAlchemy's `joinedload`:

```python
from sqlalchemy.orm import Session, joinedload
from mc_postgres_db.models import PortfolioTransaction, TransactionStatus

with Session(engine) as session:
    transaction = session.query(PortfolioTransaction).options(
        joinedload(PortfolioTransaction.transaction_type),
        joinedload(PortfolioTransaction.portfolio),
        joinedload(PortfolioTransaction.statuses).joinedload(TransactionStatus.transaction_status_type)
    ).filter_by(id=1).first()
    
    print(f"Transaction: {transaction.transaction_type.name}")
    print(f"Portfolio: {transaction.portfolio.name}")
    print("Status History:")
    for status in transaction.statuses:
        print(f"  {status.timestamp}: {status.transaction_status_type.name}")
```

### Creating Records

```python
from sqlalchemy.orm import Session
from mc_postgres_db.models import Portfolio, TransactionType, PortfolioTransaction
from datetime import datetime

with Session(engine) as session:
    # Create a portfolio
    portfolio = Portfolio(
        name="Main Trading Portfolio",
        description="Primary portfolio for active trading strategies",
        is_active=True
    )
    session.add(portfolio)
    session.flush()
    
    # Create transaction type
    buy_type = TransactionType(
        symbol="BUY",
        name="Buy",
        description="Purchase of an asset",
        is_active=True
    )
    session.add(buy_type)
    session.flush()
    
    # Create a transaction
    transaction = PortfolioTransaction(
        timestamp=datetime.now(),
        transaction_type_id=buy_type.id,
        portfolio_id=portfolio.id,
        from_asset_id=2,  # USD (cash)
        to_asset_id=1,    # Bitcoin
        quantity=0.5,
        price=50000.0
    )
    session.add(transaction)
    session.commit()
```

## Testing Utilities

This package provides a robust testing harness for database-related tests using a temporary PostgreSQL database in Docker.

### Using `postgres_test_harness`

The `postgres_test_harness` context manager creates a temporary PostgreSQL database and initializes all ORM models. It can integrate with Prefect or be used independently.

**Key features:**
- Creates a fresh database for each test (ephemeral storage)
- Integrates with Prefect (optional) - all `get_engine()` calls use the test DB
- Comprehensive safety checks to prevent accidental connection to production
- Automatic cleanup after tests

### Usage with Prefect

```python
import pytest
from mc_postgres_db.testing.utilities import postgres_test_harness

@pytest.fixture(scope="function", autouse=True)
def postgres_harness():
    with postgres_test_harness():
        yield

def test_my_prefect_flow():
    # Any Prefect task that calls get_engine() will use the PostgreSQL test DB
    ...
```

### Usage without Prefect

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

def test_create_asset_type(db_engine: Engine):
    """Test creating an asset type."""
    with Session(db_engine) as session:
        asset_type = AssetType(
            name="Test Asset Type",
            description="Test Description"
        )
        session.add(asset_type)
        session.commit()
        
        assert asset_type.id is not None
        assert asset_type.is_active is True
```

### Test Organization

Tests are organized into two directories:
- **`tests/with_prefect/`**: Tests that use Prefect
- **`tests/no_prefect/`**: Tests that don't use Prefect

## Development

### Setting up Development Environment

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check
uv run ruff format
```

### Database Migrations

This project uses Alembic for database migrations.

**Creating a new migration:**

```bash
# Generate new migration from model changes
uv run alembic revision --autogenerate -m "Description of changes"

# Or create an empty migration
uv run alembic revision -m "Description of changes"
```

**Applying migrations:**

```bash
# Apply all pending migrations
uv run alembic upgrade head

# Apply migrations one at a time
uv run alembic upgrade +1

# Rollback one migration
uv run alembic downgrade -1

# Rollback to a specific revision
uv run alembic downgrade <revision_id>
```

**Best practices:**
- Always review auto-generated migrations before committing
- Test migrations on a copy of production data when possible
- Include both `upgrade()` and `downgrade()` functions
- Add descriptive comments to migration files

## Contributing

This is a personal project, but suggestions and improvements are welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure migrations are properly created and tested
5. Submit a pull request

## License

This project is for personal use and learning purposes.

## Disclaimer

This software is for educational and personal use only. It is not intended for production trading or investment advice. Use at your own risk.
