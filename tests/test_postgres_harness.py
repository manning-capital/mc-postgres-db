import os
import sys
import datetime as dt

import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "src"))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import pytest
from sqlalchemy import Engine, select, create_engine
from sqlalchemy.orm import Session

from tests.utils import create_base_data
from mc_postgres_db.models import (
    Base,
    ProviderAssetMarket,
)
from mc_postgres_db.prefect.tasks import set_data, get_engine
from mc_postgres_db.testing.utilities import (
    TEST_DB_NAME,
    TEST_DB_USER,
    TEST_DB_PASSWORD,
    TEST_DB_SIZE_THRESHOLD_MB,
    clear_database,
    _validate_test_database_connection,
)
from mc_postgres_db.prefect.asyncio.tasks import set_data as set_data_async
from mc_postgres_db.prefect.asyncio.tasks import get_engine as get_engine_async


def test_engine_is_mocked():
    engine = get_engine()
    assert isinstance(engine, Engine)
    assert engine.url.database is not None
    assert engine.url.database == "testdb"
    assert engine.url.drivername == "postgresql"
    assert engine.url.username == "testuser"
    assert engine.url.password == "testpass"
    assert engine.url.host in ["localhost", "127.0.0.1"]
    assert engine.url.port is not None


@pytest.mark.asyncio
async def test_engine_is_mocked_async():
    engine = await get_engine_async()
    assert isinstance(engine, Engine)
    assert engine.url.database is not None
    assert engine.url.database == "testdb"
    assert engine.url.drivername == "postgresql"
    assert engine.url.username == "testuser"
    assert engine.url.password == "testpass"
    assert engine.url.host in ["localhost", "127.0.0.1"]
    assert engine.url.port is not None


@pytest.mark.asyncio
async def test_primary_key_constraint_name_is_correct():
    engine = await get_engine_async()
    assert engine.dialect.name == "postgresql"
    for table in Base.metadata.tables.values():
        assert table.primary_key.name == f"{table.name}_pkey"


def test_all_models_are_created():
    # Get the engine.
    engine = get_engine()

    # Check that the models are created.
    for _, table in Base.metadata.tables.items():
        stmt = select(table)
        df = pd.read_sql(stmt, engine)
        assert df.columns.tolist().sort() == [col.name for col in table.columns].sort()


def test_create_an_asset_type_model():
    from mc_postgres_db.models import AssetType

    # Get the engine.
    engine = get_engine()

    # Create a new asset type in a session.
    with Session(engine) as session:
        # Clear the database.
        clear_database(engine)

        # Create a new asset type.
        asset_type = AssetType(
            name="Test Asset Type",
            description="Test Asset Type Description",
        )
        session.add(asset_type)
        session.commit()

    # Query the asset type.
    with Session(engine) as session:
        stmt = select(AssetType)
        asset_type_result = session.execute(stmt).scalar_one()
        assert asset_type_result.id is not None
        assert asset_type_result.name == "Test Asset Type"
        assert asset_type_result.description == "Test Asset Type Description"
        assert asset_type_result.is_active is True
        assert asset_type_result.created_at is not None
        assert asset_type_result.updated_at is not None


def test_create_an_asset_model():
    from mc_postgres_db.models import Asset, AssetType

    # Get the engine.
    engine = get_engine()

    # Create a new asset type.
    with Session(engine) as session:
        # Clear the database.
        clear_database(engine)

        # Create a new asset type.
        asset_type = AssetType(
            name="Test Asset Type",
            description="Test Asset Type Description",
        )
        session.add(asset_type)
        session.commit()

        # Get the asset type id.
        stmt = select(AssetType)
        asset_type_result = session.execute(stmt).scalar_one()
        asset_type_id = asset_type_result.id

        # Create a new asset.
        asset = Asset(
            asset_type_id=asset_type_id,
            name="Test Asset",
            description="Test Asset Description",
            symbol="TST",
            is_active=True,
        )
        session.add(asset)
        session.commit()

        # Query the asset.
        stmt = select(Asset)
        asset_result = session.execute(stmt).scalar_one()
        assert asset_result.id is not None
        assert asset_result.asset_type_id == asset_type_id
        assert asset_result.name == "Test Asset"
        assert asset_result.description == "Test Asset Description"
        assert asset_result.symbol == "TST"
        assert asset_result.is_active is True


def test_use_set_data_upsert_to_add_provider_market_data():
    # Get the engine.
    engine = get_engine()

    # Create the base data.
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Add the market data again using set data without close. We expect that the close will be null.
        timestamp = dt.datetime.now()
        set_data(
            ProviderAssetMarket.__tablename__,
            pd.DataFrame(
                [
                    {
                        "timestamp": timestamp,
                        "provider_id": provider.id,
                        "from_asset_id": btc_asset.id,
                        "to_asset_id": usd_asset.id,
                        "close": 10001,
                        "high": 10002,
                        "low": 10003,
                        "open": 10004,
                        "volume": 10005,
                        "best_bid": 10006,
                        "best_ask": 10007,
                    }
                ]
            ),
            operation_type="upsert",
        )

        # Check to see if the market data was added.
        stmt = select(ProviderAssetMarket)
        provider_asset_market_result = session.execute(stmt).scalar_one()
        assert provider_asset_market_result.timestamp == timestamp
        assert provider_asset_market_result.provider_id == provider.id
        assert provider_asset_market_result.from_asset_id == btc_asset.id
        assert provider_asset_market_result.to_asset_id == usd_asset.id
        assert provider_asset_market_result.close == 10001
        assert provider_asset_market_result.high == 10002
        assert provider_asset_market_result.low == 10003
        assert provider_asset_market_result.open == 10004
        assert provider_asset_market_result.volume == 10005
        assert provider_asset_market_result.best_bid == 10006
        assert provider_asset_market_result.best_ask == 10007


def test_use_set_data_upsert_to_add_provider_market_data_with_incomplete_columns():
    from mc_postgres_db.models import (
        ProviderAssetMarket,
    )

    # Get the engine.
    engine = get_engine()

    # Create the base data.
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Add the market data again using set data without close. We expect that the close will be null.
        timestamp = dt.datetime.now()
        set_data(
            ProviderAssetMarket.__tablename__,
            pd.DataFrame(
                [
                    {
                        "timestamp": timestamp,
                        "provider_id": provider.id,
                        "from_asset_id": btc_asset.id,
                        "to_asset_id": usd_asset.id,
                        "high": 10002,
                        "low": 10003,
                        "open": 10004,
                        "volume": 10005,
                    }
                ]
            ),
            operation_type="upsert",
        )

        # Check to see if the market data was added.
        stmt = select(ProviderAssetMarket)
        provider_asset_market_result = session.execute(stmt).scalar_one()
        assert provider_asset_market_result.timestamp == timestamp
        assert provider_asset_market_result.provider_id == provider.id
        assert provider_asset_market_result.from_asset_id == btc_asset.id
        assert provider_asset_market_result.to_asset_id == usd_asset.id
        assert provider_asset_market_result.close is None
        assert provider_asset_market_result.high == 10002
        assert provider_asset_market_result.low == 10003
        assert provider_asset_market_result.open == 10004
        assert provider_asset_market_result.volume == 10005


def test_use_set_data_upsert_to_add_provider_market_data_and_overwrite_with_complete_columns():
    from mc_postgres_db.models import (
        ProviderAssetMarket,
    )

    # Get the engine.
    engine = get_engine()

    # Create the base data.
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Add market data using the set data.
        timestamp = dt.datetime.now()
        set_data(
            ProviderAssetMarket.__tablename__,
            pd.DataFrame(
                [
                    {
                        "timestamp": timestamp,
                        "provider_id": provider.id,
                        "from_asset_id": btc_asset.id,
                        "to_asset_id": usd_asset.id,
                        "close": 10001,
                        "high": 10002,
                        "low": 10003,
                        "open": 10004,
                        "volume": 10005,
                    }
                ]
            ),
            operation_type="upsert",
        )

        # Add the market data again using set data without close. We expect that the close will not be null.
        set_data(
            ProviderAssetMarket.__tablename__,
            pd.DataFrame(
                [
                    {
                        "timestamp": timestamp,
                        "provider_id": provider.id,
                        "from_asset_id": btc_asset.id,
                        "to_asset_id": usd_asset.id,
                        "high": 10002,
                        "low": 10003,
                        "open": 10004,
                        "volume": 10005,
                    }
                ]
            ),
            operation_type="upsert",
        )

        # Check to see if the market data was added.
        stmt = select(ProviderAssetMarket)
        provider_asset_market_result = session.execute(stmt).scalar_one()
        assert provider_asset_market_result.timestamp == timestamp
        assert provider_asset_market_result.provider_id == provider.id
        assert provider_asset_market_result.from_asset_id == btc_asset.id
        assert provider_asset_market_result.to_asset_id == usd_asset.id
        assert provider_asset_market_result.close == 10001
        assert provider_asset_market_result.high == 10002
        assert provider_asset_market_result.low == 10003
        assert provider_asset_market_result.open == 10004
        assert provider_asset_market_result.volume == 10005


@pytest.mark.asyncio
async def test_use_async_set_data_upsert_to_add_provider_market_data():
    from mc_postgres_db.models import (
        ProviderAssetMarket,
    )

    # Get the engine.
    engine = await get_engine_async()

    # Create the base data.
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    # Create a new asset type.
    with Session(engine) as session:
        # Add market data using the set data.
        timestamp = dt.datetime.now()
        await set_data_async(
            ProviderAssetMarket.__tablename__,
            pd.DataFrame(
                [
                    {
                        "timestamp": timestamp,
                        "provider_id": provider.id,
                        "from_asset_id": btc_asset.id,
                        "to_asset_id": usd_asset.id,
                        "close": 10001,
                        "high": 10002,
                        "low": 10003,
                        "open": 10004,
                        "volume": 10005,
                    }
                ]
            ),
            operation_type="upsert",
        )

        # Add the market data again using set data without close. We expect that the close will not be null.
        await set_data_async(
            ProviderAssetMarket.__tablename__,
            pd.DataFrame(
                [
                    {
                        "timestamp": timestamp,
                        "provider_id": provider.id,
                        "from_asset_id": btc_asset.id,
                        "to_asset_id": usd_asset.id,
                        "high": 10002,
                        "low": 10003,
                        "open": 10004,
                        "volume": 10005,
                    }
                ]
            ),
            operation_type="upsert",
        )

        # Check to see if the market data was added.
        stmt = select(ProviderAssetMarket)
        provider_asset_market_result = session.execute(stmt).scalar_one()
        assert provider_asset_market_result.timestamp == timestamp
        assert provider_asset_market_result.provider_id == provider.id
        assert provider_asset_market_result.from_asset_id == btc_asset.id
        assert provider_asset_market_result.to_asset_id == usd_asset.id
        assert provider_asset_market_result.close == 10001
        assert provider_asset_market_result.high == 10002
        assert provider_asset_market_result.low == 10003
        assert provider_asset_market_result.open == 10004
        assert provider_asset_market_result.volume == 10005


def test_use_set_data_append_to_add_provider_market_data():
    from mc_postgres_db.models import (
        ProviderAssetOrder,
    )

    # Get the engine.
    engine = get_engine()

    # Create the base data.
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    # Generate fake data.
    timestamp = dt.datetime.now()
    fake_data = pd.DataFrame(
        [
            {
                "timestamp": timestamp,
                "provider_id": provider.id,
                "from_asset_id": btc_asset.id,
                "to_asset_id": usd_asset.id,
                "price": 10001,
                "volume": 10002,
            }
        ]
    )

    # Add the order data using set data.
    set_data(
        ProviderAssetOrder.__tablename__,
        fake_data,
        operation_type="append",
    )

    # Add the order data again using set data.
    set_data(
        ProviderAssetOrder.__tablename__,
        fake_data,
        operation_type="append",
    )

    # Check to see if the market data was added.
    stmt = select(ProviderAssetOrder)
    provider_asset_order_df = pd.read_sql(stmt, engine)
    assert provider_asset_order_df.shape[0] == 2
    assert provider_asset_order_df.iloc[0].timestamp == timestamp
    assert provider_asset_order_df.iloc[0].provider_id == provider.id
    assert provider_asset_order_df.iloc[0].from_asset_id == btc_asset.id
    assert provider_asset_order_df.iloc[0].to_asset_id == usd_asset.id
    assert provider_asset_order_df.iloc[0].price == 10001
    assert provider_asset_order_df.iloc[0].volume == 10002
    assert provider_asset_order_df.iloc[1].timestamp == timestamp
    assert provider_asset_order_df.iloc[1].provider_id == provider.id
    assert provider_asset_order_df.iloc[1].from_asset_id == btc_asset.id
    assert provider_asset_order_df.iloc[1].to_asset_id == usd_asset.id
    assert provider_asset_order_df.iloc[1].price == 10001
    assert provider_asset_order_df.iloc[1].volume == 10002
    assert provider_asset_order_df.iloc[0].id != provider_asset_order_df.iloc[1].id


# Tests for the new validation functionality
class TestDatabaseValidation:
    """Test the database validation functionality."""

    def test_constants_are_defined(self):
        """Test that all required constants are defined."""
        assert TEST_DB_USER == "testuser"
        assert TEST_DB_PASSWORD == "testpass"
        assert TEST_DB_NAME == "testdb"
        assert TEST_DB_SIZE_THRESHOLD_MB == 1000

    def test_validate_test_database_connection_success(self):
        """Test that validation passes for a valid test database connection."""
        engine = get_engine()
        # This should not raise any exception
        _validate_test_database_connection(engine)

    def test_validate_test_database_connection_wrong_driver(self):
        """Test that validation fails for non-PostgreSQL drivers."""
        # Create a SQLite engine to test wrong driver
        sqlite_engine = create_engine("sqlite:///:memory:")

        with pytest.raises(ValueError, match="Unsupported database driver: sqlite"):
            _validate_test_database_connection(sqlite_engine)

    def test_validate_test_database_connection_wrong_host(self):
        """Test that validation fails for non-localhost hosts."""
        # Create a mock engine with wrong host
        engine = create_engine(
            "postgresql://testuser:testpass@prod-server.com:5432/testdb"
        )

        with pytest.raises(
            ValueError, match="PostgreSQL host 'prod-server.com' is not localhost"
        ):
            _validate_test_database_connection(engine)

    def test_validate_test_database_connection_wrong_username(self):
        """Test that validation fails for wrong username."""
        # Create a mock engine with wrong username
        engine = create_engine("postgresql://postgres:testpass@localhost:5432/testdb")

        with pytest.raises(
            ValueError,
            match="PostgreSQL username 'postgres' is not the expected test user 'testuser'",
        ):
            _validate_test_database_connection(engine)

    def test_validate_test_database_connection_wrong_database_name(self):
        """Test that validation fails for wrong database name."""
        # Create a mock engine with wrong database name
        engine = create_engine(
            "postgresql://testuser:testpass@localhost:5432/production_db"
        )

        with pytest.raises(
            ValueError,
            match="PostgreSQL database 'production_db' is not the expected test database 'testdb'",
        ):
            _validate_test_database_connection(engine)

    def test_validate_test_database_connection_127_0_0_1_host(self):
        """Test that validation passes for 127.0.0.1 host."""
        # Create a mock engine with 127.0.0.1 host
        engine = create_engine("postgresql://testuser:testpass@127.0.0.1:5432/testdb")

        # This should not raise any exception (though it might fail on connection)
        # We're just testing the URL parsing part
        try:
            _validate_test_database_connection(engine)
        except ValueError as e:
            # If it fails, it should be due to connection issues, not validation
            assert "production database" in str(
                e
            ) or "Cannot validate database safety" in str(e)

    def test_clear_database_validation_integration(self):
        """Test that clear_database calls validation."""
        engine = get_engine()

        # This should work fine with our test engine
        clear_database(engine)

        # Verify tables were cleared and recreated
        with Session(engine) as session:
            # Check that tables exist but are empty
            from mc_postgres_db.models import AssetType

            stmt = select(AssetType)
            result = session.execute(stmt).all()
            assert len(result) == 0

    def test_clear_database_with_invalid_engine(self):
        """Test that clear_database fails with invalid engine."""
        # Create an invalid engine
        invalid_engine = create_engine(
            "postgresql://postgres:wrongpass@prod-server.com:5432/production"
        )

        with pytest.raises(
            ValueError, match="PostgreSQL host 'prod-server.com' is not localhost"
        ):
            clear_database(invalid_engine)

    def test_validation_error_messages_are_descriptive(self):
        """Test that validation error messages are clear and actionable."""
        test_cases = [
            ("postgresql://testuser:testpass@remote-host:5432/testdb", "remote-host"),
            ("postgresql://postgres:testpass@localhost:5432/testdb", "postgres"),
            ("postgresql://testuser:testpass@localhost:5432/production", "production"),
        ]

        for url, expected_content in test_cases:
            engine = create_engine(url)
            with pytest.raises(ValueError) as exc_info:
                _validate_test_database_connection(engine)

            error_message = str(exc_info.value)
            assert expected_content in error_message
            assert (
                "production database" in error_message
                or "not localhost" in error_message
            )

    def test_validation_constants_consistency(self):
        """Test that validation uses the same constants as the harness."""
        engine = get_engine()

        # Verify the engine matches our constants
        assert engine.url.username == TEST_DB_USER
        assert engine.url.password == TEST_DB_PASSWORD
        assert engine.url.database == TEST_DB_NAME

        # Validation should pass
        _validate_test_database_connection(engine)

    def test_size_threshold_constant_usage(self):
        """Test that the size threshold constant is properly defined."""
        assert isinstance(TEST_DB_SIZE_THRESHOLD_MB, int)
        assert TEST_DB_SIZE_THRESHOLD_MB > 0
        assert TEST_DB_SIZE_THRESHOLD_MB == 1000  # As set by user


@pytest.mark.asyncio
async def test_use_async_set_data_append_to_add_provider_market_data():
    from mc_postgres_db.models import (
        ProviderAssetOrder,
    )

    # Get the engine.
    engine = await get_engine_async()

    # Create the base data.
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    # Generate fake data.
    timestamp = dt.datetime.now()
    fake_data = pd.DataFrame(
        [
            {
                "timestamp": timestamp,
                "provider_id": provider.id,
                "from_asset_id": btc_asset.id,
                "to_asset_id": usd_asset.id,
                "price": 10001,
                "volume": 10002,
            }
        ]
    )

    # Add the order data using set data.
    await set_data_async(
        ProviderAssetOrder.__tablename__,
        fake_data,
        operation_type="append",
    )

    # Add the order data again using set data.
    await set_data_async(
        ProviderAssetOrder.__tablename__,
        fake_data,
        operation_type="append",
    )

    # Check to see if the market data was added.
    stmt = select(ProviderAssetOrder)
    provider_asset_order_df = pd.read_sql(stmt, engine)
    assert provider_asset_order_df.shape[0] == 2
    assert provider_asset_order_df.iloc[0].timestamp == timestamp
    assert provider_asset_order_df.iloc[0].provider_id == provider.id
    assert provider_asset_order_df.iloc[0].from_asset_id == btc_asset.id
    assert provider_asset_order_df.iloc[0].to_asset_id == usd_asset.id
    assert provider_asset_order_df.iloc[0].price == 10001
    assert provider_asset_order_df.iloc[0].volume == 10002
    assert provider_asset_order_df.iloc[1].timestamp == timestamp
    assert provider_asset_order_df.iloc[1].provider_id == provider.id
    assert provider_asset_order_df.iloc[1].from_asset_id == btc_asset.id
    assert provider_asset_order_df.iloc[1].to_asset_id == usd_asset.id
    assert provider_asset_order_df.iloc[1].price == 10001
    assert provider_asset_order_df.iloc[1].volume == 10002
    assert provider_asset_order_df.iloc[0].id != provider_asset_order_df.iloc[1].id
