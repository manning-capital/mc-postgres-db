import os
import sys
import pandas as pd
import datetime as dt

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "src"))

import pytest
from mc_postgres_db.testing.utilities import postgres_test_harness
from prefect.testing.utilities import prefect_test_harness
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session


@pytest.fixture(scope="session", autouse=True)
def prefect_harness():
    with prefect_test_harness():
        yield


@pytest.fixture(scope="function", autouse=True)
def postgres_harness():
    with postgres_test_harness():
        yield


def test_engine_is_mocked():
    from mc_postgres_db.prefect.tasks import get_engine

    engine = get_engine()
    assert isinstance(engine, Engine)
    assert engine.url.database is not None
    assert engine.url.database.endswith(".db")
    assert engine.url.drivername == "sqlite"
    assert engine.url.username is None
    assert engine.url.password is None
    assert engine.url.host is None
    assert engine.url.port is None


@pytest.mark.asyncio
async def test_engine_is_mocked_async():
    from mc_postgres_db.prefect.asyncio.tasks import get_engine

    engine = await get_engine()
    assert isinstance(engine, Engine)
    assert engine.url.database is not None
    assert engine.url.database.endswith(".db")
    assert engine.url.drivername == "sqlite"
    assert engine.url.username is None
    assert engine.url.password is None
    assert engine.url.host is None
    assert engine.url.port is None


def test_all_models_are_created():
    from mc_postgres_db.models import Base
    from mc_postgres_db.prefect.tasks import get_engine

    # Get the engine.
    engine = get_engine()

    # Check that the models are created.
    for _, table in Base.metadata.tables.items():
        stmt = select(table)
        df = pd.read_sql(stmt, engine)
        assert df.columns.tolist().sort() == [col.name for col in table.columns].sort()


def test_create_an_asset_type_model():
    from mc_postgres_db.models import AssetType
    from mc_postgres_db.prefect.tasks import get_engine

    # Get the engine.
    engine = get_engine()

    # Create a new asset type in a session.
    with Session(engine) as session:
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
    from mc_postgres_db.prefect.tasks import get_engine

    # Get the engine.
    engine = get_engine()

    # Create a new asset type.
    with Session(engine) as session:
        asset_type = AssetType(
            name="Test Asset Type",
            description="Test Asset Type Description",
        )
        session.add(asset_type)
        session.commit()

    # Get the asset type id.
    with Session(engine) as session:
        stmt = select(AssetType)
        asset_type_result = session.execute(stmt).scalar_one()
        asset_type_id = asset_type_result.id

    # Create a new asset.
    with Session(engine) as session:
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
    with Session(engine) as session:
        stmt = select(Asset)
        asset_result = session.execute(stmt).scalar_one()
        assert asset_result.id is not None
        assert asset_result.asset_type_id == asset_type_id
        assert asset_result.name == "Test Asset"
        assert asset_result.description == "Test Asset Description"
        assert asset_result.symbol == "TST"
        assert asset_result.is_active is True


def test_use_set_data_upsert_to_add_provider_market_data():
    from mc_postgres_db.models import (
        Asset,
        AssetType,
        ProviderType,
        Provider,
        ProviderAssetMarket,
    )
    from mc_postgres_db.prefect.tasks import get_engine, set_data

    # Get the engine.
    engine = get_engine()

    # Create a new asset type.
    with Session(engine) as session:
        # Create a new asset type.
        asset_type = AssetType(
            name="CryptoCurrency",
            description="CryptoCurrency Asset Type",
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
            name="Bitcoin",
            description="Bitcoin Asset",
            symbol="BTC",
            is_active=True,
        )
        session.add(asset)
        session.commit()

        # Get the asset id.
        stmt = select(Asset)
        asset_result = session.execute(stmt).scalar_one()
        asset_id = asset_result.id

        # Create a new provider type.
        provider_type = ProviderType(
            name="CryptoCurrencyExchange",
            description="CryptoCurrency Exchange Provider Type",
        )
        session.add(provider_type)
        session.commit()

        # Get the provider type id.
        stmt = select(ProviderType)
        provider_type_result = session.execute(stmt).scalar_one()
        provider_type_id = provider_type_result.id

        # Create a new provider.
        provider = Provider(
            provider_type_id=provider_type_id,
            name="Kraken",
            description="Kraken CryptoCurrency Exchange Provider",
        )
        session.add(provider)
        session.commit()

        # Get the provider id.
        stmt = select(Provider)
        provider_result = session.execute(stmt).scalar_one()
        provider_id = provider_result.id

        # Add the market data again using set data without close. We expect that the close will be null.
        timestamp = dt.datetime.now()
        set_data(
            ProviderAssetMarket.__tablename__,
            pd.DataFrame(
                [
                    {
                        "timestamp": timestamp,
                        "provider_id": provider_id,
                        "asset_id": asset_id,
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
        assert provider_asset_market_result.provider_id == provider_id
        assert provider_asset_market_result.asset_id == asset_id
        assert provider_asset_market_result.close == 10001
        assert provider_asset_market_result.high == 10002
        assert provider_asset_market_result.low == 10003
        assert provider_asset_market_result.open == 10004
        assert provider_asset_market_result.volume == 10005
        assert provider_asset_market_result.best_bid == 10006
        assert provider_asset_market_result.best_ask == 10007


def test_use_set_data_upsert_to_add_provider_market_data_with_incomplete_columns():
    from mc_postgres_db.models import (
        Asset,
        AssetType,
        ProviderType,
        Provider,
        ProviderAssetMarket,
    )
    from mc_postgres_db.prefect.tasks import get_engine, set_data

    # Get the engine.
    engine = get_engine()

    # Create a new asset type.
    with Session(engine) as session:
        # Create a new asset type.
        asset_type = AssetType(
            name="CryptoCurrency",
            description="CryptoCurrency Asset Type",
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
            name="Bitcoin",
            description="Bitcoin Asset",
            symbol="BTC",
            is_active=True,
        )
        session.add(asset)
        session.commit()

        # Get the asset id.
        stmt = select(Asset)
        asset_result = session.execute(stmt).scalar_one()
        asset_id = asset_result.id

        # Create a new provider type.
        provider_type = ProviderType(
            name="CryptoCurrencyExchange",
            description="CryptoCurrency Exchange Provider Type",
        )
        session.add(provider_type)
        session.commit()

        # Get the provider type id.
        stmt = select(ProviderType)
        provider_type_result = session.execute(stmt).scalar_one()
        provider_type_id = provider_type_result.id

        # Create a new provider.
        provider = Provider(
            provider_type_id=provider_type_id,
            name="Kraken",
            description="Kraken CryptoCurrency Exchange Provider",
        )
        session.add(provider)
        session.commit()

        # Get the provider id.
        stmt = select(Provider)
        provider_result = session.execute(stmt).scalar_one()
        provider_id = provider_result.id

        # Add the market data again using set data without close. We expect that the close will be null.
        timestamp = dt.datetime.now()
        set_data(
            ProviderAssetMarket.__tablename__,
            pd.DataFrame(
                [
                    {
                        "timestamp": timestamp,
                        "provider_id": provider_id,
                        "asset_id": asset_id,
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
        assert provider_asset_market_result.provider_id == provider_id
        assert provider_asset_market_result.asset_id == asset_id
        assert provider_asset_market_result.close is None
        assert provider_asset_market_result.high == 10002
        assert provider_asset_market_result.low == 10003
        assert provider_asset_market_result.open == 10004
        assert provider_asset_market_result.volume == 10005


def test_use_set_data_upsert_to_add_provider_market_data_and_overwrite_with_complete_columns():
    from mc_postgres_db.models import (
        Asset,
        AssetType,
        ProviderType,
        Provider,
        ProviderAssetMarket,
    )
    from mc_postgres_db.prefect.tasks import get_engine, set_data

    # Get the engine.
    engine = get_engine()

    # Create a new asset type.
    with Session(engine) as session:
        # Create a new asset type.
        asset_type = AssetType(
            name="CryptoCurrency",
            description="CryptoCurrency Asset Type",
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
            name="Bitcoin",
            description="Bitcoin Asset",
            symbol="BTC",
            is_active=True,
        )
        session.add(asset)
        session.commit()

        # Get the asset id.
        stmt = select(Asset)
        asset_result = session.execute(stmt).scalar_one()
        asset_id = asset_result.id

        # Create a new provider type.
        provider_type = ProviderType(
            name="CryptoCurrencyExchange",
            description="CryptoCurrency Exchange Provider Type",
        )
        session.add(provider_type)
        session.commit()

        # Get the provider type id.
        stmt = select(ProviderType)
        provider_type_result = session.execute(stmt).scalar_one()
        provider_type_id = provider_type_result.id

        # Create a new provider.
        provider = Provider(
            provider_type_id=provider_type_id,
            name="Kraken",
            description="Kraken CryptoCurrency Exchange Provider",
        )
        session.add(provider)
        session.commit()

        # Get the provider id.
        stmt = select(Provider)
        provider_result = session.execute(stmt).scalar_one()
        provider_id = provider_result.id

        # Add market data using the set data.
        timestamp = dt.datetime.now()
        set_data(
            ProviderAssetMarket.__tablename__,
            pd.DataFrame(
                [
                    {
                        "timestamp": timestamp,
                        "provider_id": provider_id,
                        "asset_id": asset_id,
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
                        "provider_id": provider_id,
                        "asset_id": asset_id,
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
        assert provider_asset_market_result.provider_id == provider_id
        assert provider_asset_market_result.asset_id == asset_id
        assert provider_asset_market_result.close == 10001
        assert provider_asset_market_result.high == 10002
        assert provider_asset_market_result.low == 10003
        assert provider_asset_market_result.open == 10004
        assert provider_asset_market_result.volume == 10005


@pytest.mark.asyncio
async def test_use_async_set_data_upsert_to_add_provider_market_data():
    from mc_postgres_db.models import (
        Asset,
        AssetType,
        ProviderType,
        Provider,
        ProviderAssetMarket,
    )
    from mc_postgres_db.prefect.asyncio.tasks import get_engine, set_data

    # Get the engine.
    engine = await get_engine()

    # Create a new asset type.
    with Session(engine) as session:
        # Create a new asset type.
        asset_type = AssetType(
            name="CryptoCurrency",
            description="CryptoCurrency Asset Type",
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
            name="Bitcoin",
            description="Bitcoin Asset",
            symbol="BTC",
            is_active=True,
        )
        session.add(asset)
        session.commit()

        # Get the asset id.
        stmt = select(Asset)
        asset_result = session.execute(stmt).scalar_one()
        asset_id = asset_result.id

        # Create a new provider type.
        provider_type = ProviderType(
            name="CryptoCurrencyExchange",
            description="CryptoCurrency Exchange Provider Type",
        )
        session.add(provider_type)
        session.commit()

        # Get the provider type id.
        stmt = select(ProviderType)
        provider_type_result = session.execute(stmt).scalar_one()
        provider_type_id = provider_type_result.id

        # Create a new provider.
        provider = Provider(
            provider_type_id=provider_type_id,
            name="Kraken",
            description="Kraken CryptoCurrency Exchange Provider",
        )
        session.add(provider)
        session.commit()

        # Get the provider id.
        stmt = select(Provider)
        provider_result = session.execute(stmt).scalar_one()
        provider_id = provider_result.id

        # Add market data using the set data.
        timestamp = dt.datetime.now()
        await set_data(
            ProviderAssetMarket.__tablename__,
            pd.DataFrame(
                [
                    {
                        "timestamp": timestamp,
                        "provider_id": provider_id,
                        "asset_id": asset_id,
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
        await set_data(
            ProviderAssetMarket.__tablename__,
            pd.DataFrame(
                [
                    {
                        "timestamp": timestamp,
                        "provider_id": provider_id,
                        "asset_id": asset_id,
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
        assert provider_asset_market_result.provider_id == provider_id
        assert provider_asset_market_result.asset_id == asset_id
        assert provider_asset_market_result.close == 10001
        assert provider_asset_market_result.high == 10002
        assert provider_asset_market_result.low == 10003
        assert provider_asset_market_result.open == 10004
        assert provider_asset_market_result.volume == 10005


def test_use_set_data_append_to_add_provider_market_data():
    from mc_postgres_db.models import (
        Asset,
        AssetType,
        ProviderType,
        Provider,
        ProviderAssetOrder,
    )
    from mc_postgres_db.prefect.tasks import get_engine, set_data

    # Get the engine.
    engine = get_engine()

    # Create a new asset type.
    with Session(engine) as session:
        # Create a new asset type.
        asset_type = AssetType(
            name="CryptoCurrency",
            description="CryptoCurrency Asset Type",
        )
        session.add(asset_type)
        session.commit()

        # Get the asset type id.
        stmt = select(AssetType)
        asset_type_result = session.execute(stmt).scalar_one()
        asset_type_id = asset_type_result.id

        # Create a new assets.
        from_asset = Asset(
            asset_type_id=asset_type_id,
            name="Bitcoin",
            description="Bitcoin Asset",
            symbol="BTC",
            is_active=True,
        )
        to_asset = Asset(
            asset_type_id=asset_type_id,
            name="Ethereum",
            description="Ethereum Asset",
            symbol="ETH",
            is_active=True,
        )
        session.add(from_asset)
        session.add(to_asset)
        session.commit()

        # Get the asset ids.
        from_asset_stmt = select(Asset).where(Asset.symbol == "BTC")
        to_asset_stmt = select(Asset).where(Asset.symbol == "ETH")
        from_asset_result = session.execute(from_asset_stmt).scalar_one()
        to_asset_result = session.execute(to_asset_stmt).scalar_one()
        from_asset_id = from_asset_result.id
        to_asset_id = to_asset_result.id

        # Create a new provider type.
        provider_type = ProviderType(
            name="CryptoCurrencyExchange",
            description="CryptoCurrency Exchange Provider Type",
        )
        session.add(provider_type)
        session.commit()

        # Get the provider type id.
        stmt = select(ProviderType)
        provider_type_result = session.execute(stmt).scalar_one()
        provider_type_id = provider_type_result.id

        # Create a new provider.
        provider = Provider(
            provider_type_id=provider_type_id,
            name="Kraken",
            description="Kraken CryptoCurrency Exchange Provider",
        )
        session.add(provider)
        session.commit()

        # Get the provider id.
        stmt = select(Provider)
        provider_result = session.execute(stmt).scalar_one()
        provider_id = provider_result.id

        # Generate fake data.
        timestamp = dt.datetime.now()
        fake_data = pd.DataFrame(
            [
                {
                    "timestamp": timestamp,
                    "provider_id": provider_id,
                    "from_asset_id": from_asset_id,
                    "to_asset_id": to_asset_id,
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
        assert provider_asset_order_df.iloc[0].provider_id == provider_id
        assert provider_asset_order_df.iloc[0].from_asset_id == from_asset_id
        assert provider_asset_order_df.iloc[0].to_asset_id == to_asset_id
        assert provider_asset_order_df.iloc[0].price == 10001
        assert provider_asset_order_df.iloc[0].volume == 10002
        assert provider_asset_order_df.iloc[1].timestamp == timestamp
        assert provider_asset_order_df.iloc[1].provider_id == provider_id
        assert provider_asset_order_df.iloc[1].from_asset_id == from_asset_id
        assert provider_asset_order_df.iloc[1].to_asset_id == to_asset_id
        assert provider_asset_order_df.iloc[1].price == 10001
        assert provider_asset_order_df.iloc[1].volume == 10002
        assert provider_asset_order_df.iloc[0].id != provider_asset_order_df.iloc[1].id


@pytest.mark.asyncio
async def test_use_async_set_data_append_to_add_provider_market_data():
    from mc_postgres_db.models import (
        Asset,
        AssetType,
        ProviderType,
        Provider,
        ProviderAssetOrder,
    )
    from mc_postgres_db.prefect.asyncio.tasks import get_engine, set_data

    # Get the engine.
    engine = await get_engine()

    # Create a new asset type.
    with Session(engine) as session:
        # Create a new asset type.
        asset_type = AssetType(
            name="CryptoCurrency",
            description="CryptoCurrency Asset Type",
        )
        session.add(asset_type)
        session.commit()

        # Get the asset type id.
        stmt = select(AssetType)
        asset_type_result = session.execute(stmt).scalar_one()
        asset_type_id = asset_type_result.id

        # Create a new assets.
        from_asset = Asset(
            asset_type_id=asset_type_id,
            name="Bitcoin",
            description="Bitcoin Asset",
            symbol="BTC",
            is_active=True,
        )
        to_asset = Asset(
            asset_type_id=asset_type_id,
            name="Ethereum",
            description="Ethereum Asset",
            symbol="ETH",
            is_active=True,
        )
        session.add(from_asset)
        session.add(to_asset)
        session.commit()

        # Get the asset ids.
        from_asset_stmt = select(Asset).where(Asset.symbol == "BTC")
        to_asset_stmt = select(Asset).where(Asset.symbol == "ETH")
        from_asset_result = session.execute(from_asset_stmt).scalar_one()
        to_asset_result = session.execute(to_asset_stmt).scalar_one()
        from_asset_id = from_asset_result.id
        to_asset_id = to_asset_result.id

        # Create a new provider type.
        provider_type = ProviderType(
            name="CryptoCurrencyExchange",
            description="CryptoCurrency Exchange Provider Type",
        )
        session.add(provider_type)
        session.commit()

        # Get the provider type id.
        stmt = select(ProviderType)
        provider_type_result = session.execute(stmt).scalar_one()
        provider_type_id = provider_type_result.id

        # Create a new provider.
        provider = Provider(
            provider_type_id=provider_type_id,
            name="Kraken",
            description="Kraken CryptoCurrency Exchange Provider",
        )
        session.add(provider)
        session.commit()

        # Get the provider id.
        stmt = select(Provider)
        provider_result = session.execute(stmt).scalar_one()
        provider_id = provider_result.id

        # Generate fake data.
        timestamp = dt.datetime.now()
        fake_data = pd.DataFrame(
            [
                {
                    "timestamp": timestamp,
                    "provider_id": provider_id,
                    "from_asset_id": from_asset_id,
                    "to_asset_id": to_asset_id,
                    "price": 10001,
                    "volume": 10002,
                }
            ]
        )

        # Add the order data using set data.
        await set_data(
            ProviderAssetOrder.__tablename__,
            fake_data,
            operation_type="append",
        )

        # Add the order data again using set data.
        await set_data(
            ProviderAssetOrder.__tablename__,
            fake_data,
            operation_type="append",
        )

        # Check to see if the market data was added.
        stmt = select(ProviderAssetOrder)
        provider_asset_order_df = pd.read_sql(stmt, engine)
        assert provider_asset_order_df.shape[0] == 2
        assert provider_asset_order_df.iloc[0].timestamp == timestamp
        assert provider_asset_order_df.iloc[0].provider_id == provider_id
        assert provider_asset_order_df.iloc[0].from_asset_id == from_asset_id
        assert provider_asset_order_df.iloc[0].to_asset_id == to_asset_id
        assert provider_asset_order_df.iloc[0].price == 10001
        assert provider_asset_order_df.iloc[0].volume == 10002
        assert provider_asset_order_df.iloc[1].timestamp == timestamp
        assert provider_asset_order_df.iloc[1].provider_id == provider_id
        assert provider_asset_order_df.iloc[1].from_asset_id == from_asset_id
        assert provider_asset_order_df.iloc[1].to_asset_id == to_asset_id
        assert provider_asset_order_df.iloc[1].price == 10001
        assert provider_asset_order_df.iloc[1].volume == 10002
        assert provider_asset_order_df.iloc[0].id != provider_asset_order_df.iloc[1].id
