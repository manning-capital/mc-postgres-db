import datetime as dt
import os
import sys

import numpy as np
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "src"))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import pytest
import statsmodels.api as sm
from sqlalchemy.orm import Session
from statsmodels.regression.rolling import RollingOLS

from mc_postgres_db.models import (
    Provider,
    ProviderAssetGroup,
    ProviderAssetGroupAttribute,
    ProviderAssetGroupMember,
    ProviderAssetMarket,
)
from mc_postgres_db.prefect.asyncio.tasks import get_engine as get_engine_async
from mc_postgres_db.prefect.tasks import set_data
from tests.utils import create_base_data


def generate_ol_data(
    S_0: float, T: pd.date_range, mu: float, theta: float, sigma: float
):
    dt = 1 / len(T)
    S = np.zeros(len(T))
    S[0] = S_0
    for i in range(1, len(T)):
        S[i] = (
            S[i - 1] * np.exp(-mu * dt)
            + theta * (1 - np.exp(-mu * dt))
            + sigma
            * np.sqrt((1 - np.exp(-2 * mu * dt)) / (2 * mu))
            * np.random.normal(0, 1)
        )
    return S


@pytest.mark.asyncio
async def test_create_provider_asset_group_attribute():
    # Get the engine.
    engine = await get_engine_async()

    # Create the base data.
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    # Create the time-frame.
    mu = 0.001
    theta = 1
    sigma = 0.01
    window = 60  # 1 hour in minutes
    T = pd.date_range(
        start=dt.datetime.now(),
        end=dt.datetime.now() + dt.timedelta(days=1),
        freq="1min",
    )

    # Create fake market data for the BTC/USD pair.
    starting_price = 10001
    close_prices = generate_ol_data(starting_price, T, mu, theta, sigma)
    fake_market_data_1 = pd.DataFrame(
        {
            "timestamp": T,
            "provider_id": len(T) * [provider.id],
            "from_asset_id": len(T) * [usd_asset.id],
            "to_asset_id": len(T) * [btc_asset.id],
            "close": close_prices,
            "open": close_prices,
            "high": close_prices,
            "low": close_prices,
            "volume": close_prices,
            "best_bid": close_prices,
            "best_ask": close_prices,
        }
    )

    # Create fake market data for the ETH/USD pair.
    starting_price = 300
    close_prices = generate_ol_data(starting_price, T, mu, theta, sigma)
    fake_market_data_2 = pd.DataFrame(
        {
            "timestamp": T,
            "provider_id": len(T) * [provider.id],
            "from_asset_id": len(T) * [usd_asset.id],
            "to_asset_id": len(T) * [eth_asset.id],
            "close": close_prices,
            "open": close_prices,
            "high": close_prices,
            "low": close_prices,
            "volume": close_prices,
            "best_bid": close_prices,
            "best_ask": close_prices,
        }
    )

    # Add the market data to the database.
    set_data(
        ProviderAssetMarket.__tablename__,
        fake_market_data_1,
        operation_type="upsert",
    )
    set_data(
        ProviderAssetMarket.__tablename__,
        fake_market_data_2,
        operation_type="upsert",
    )

    # Create the provider asset group.
    with Session(engine) as session:
        provider_asset_group = ProviderAssetGroup(
            name="BTC (Kraken)/ETH (Kraken) Asset Group",
            description="BTC (Kraken)/ETH (Kraken) Asset Group",
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

    # Create the provider asset group members.
    with Session(engine) as session:
        provider_asset_group_member_1 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
        )
        provider_asset_group_member_2 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=eth_asset.id,
        )
        session.add(provider_asset_group_member_1)
        session.add(provider_asset_group_member_2)
        session.commit()
        session.refresh(provider_asset_group_member_1)
        session.refresh(provider_asset_group_member_2)

    # Pull the market data for the asset group.
    S_2 = fake_market_data_2["close"].to_numpy()
    S_1 = fake_market_data_1["close"].to_numpy()

    # Calculate the rolling OLS.
    y = S_2
    X = sm.add_constant(S_1)
    rolling_ols = RollingOLS(y, X, window=window)
    results = rolling_ols.fit()

    # Create the provider asset group attribute.
    provider_asset_group_attribute_df = pd.DataFrame(
        {
            "timestamp": T,
            "provider_asset_group_id": len(T) * [provider_asset_group.id],
            "lookback_window_seconds": len(T) * [window * 60],
        }
    )
    provider_asset_group_attribute_df["cointegration_p_value"] = results.pvalues[:, 1]
    provider_asset_group_attribute_df["ol_mu"] = mu
    provider_asset_group_attribute_df["ol_theta"] = theta
    provider_asset_group_attribute_df["ol_sigma"] = sigma
    provider_asset_group_attribute_df["linear_fit_alpha"] = results.params[:, 0]
    provider_asset_group_attribute_df["linear_fit_beta"] = results.params[:, 1]
    provider_asset_group_attribute_df["linear_fit_mse"] = results.mse_resid
    provider_asset_group_attribute_df["linear_fit_r_squared"] = results.rsquared
    provider_asset_group_attribute_df["linear_fit_r_squared_adj"] = results.rsquared_adj
    provider_asset_group_attribute_df = provider_asset_group_attribute_df.dropna()

    # Add the provider asset group attribute to the database.
    set_data(
        ProviderAssetGroupAttribute.__tablename__,
        provider_asset_group_attribute_df,
        operation_type="upsert",
    )


@pytest.mark.asyncio
async def test_create_provider_asset_group_with_members():
    """Test creating a ProviderAssetGroup with multiple ProviderAssetGroupMember entries."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a ProviderAssetGroup
        provider_asset_group = ProviderAssetGroup(
            name="Test Crypto Group",
            description="Test group for crypto pairs",
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Add members to the group
        member1 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
        )
        member2 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=eth_asset.id,
        )
        session.add_all([member1, member2])
        session.commit()

        # Verify the group and its members
        retrieved_group = (
            session.query(ProviderAssetGroup)
            .filter_by(id=provider_asset_group.id)
            .one()
        )
        members = (
            session.query(ProviderAssetGroupMember)
            .filter_by(provider_asset_group_id=provider_asset_group.id)
            .all()
        )

        assert len(members) == 2
        assert retrieved_group.name == "Test Crypto Group"
        assert retrieved_group.is_active is True


@pytest.mark.asyncio
async def test_composite_primary_key_constraint():
    """Test that composite primary key constraints prevent duplicate entries."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a ProviderAssetGroup
        provider_asset_group = ProviderAssetGroup(
            name="Test Group",
            description="Test group",
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Add a member
        member = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
        )
        session.add(member)
        session.commit()

        # Attempt to add a duplicate member (same composite key)
        duplicate_member = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
        )
        session.add(duplicate_member)

        # Should raise an IntegrityError
        with pytest.raises(
            Exception
        ):  # SQLite raises Exception, PostgreSQL would raise IntegrityError
            session.commit()
        session.rollback()


@pytest.mark.asyncio
async def test_provider_asset_group_attributes():
    """Test creating and retrieving ProviderAssetGroupAttribute entries."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a ProviderAssetGroup
        provider_asset_group = ProviderAssetGroup(
            name="Test Group",
            description="Test group",
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Create attributes for different timestamps and lookback windows
        timestamp1 = dt.datetime.now()
        timestamp2 = timestamp1 + dt.timedelta(hours=1)

        attribute1 = ProviderAssetGroupAttribute(
            timestamp=timestamp1,
            provider_asset_group_id=provider_asset_group.id,
            lookback_window_seconds=3600,  # 1 hour
            cointegration_p_value=0.05,
            ol_mu=0.1,
            ol_theta=0.5,
            ol_sigma=0.2,
            linear_fit_alpha=1.0,
            linear_fit_beta=0.8,
            linear_fit_mse=0.01,
            linear_fit_r_squared=0.95,
            linear_fit_r_squared_adj=0.94,
        )

        attribute2 = ProviderAssetGroupAttribute(
            timestamp=timestamp2,
            provider_asset_group_id=provider_asset_group.id,
            lookback_window_seconds=7200,  # 2 hours
            cointegration_p_value=0.03,
            ol_mu=0.08,
            ol_theta=0.6,
            ol_sigma=0.15,
            linear_fit_alpha=1.1,
            linear_fit_beta=0.75,
            linear_fit_mse=0.008,
            linear_fit_r_squared=0.97,
            linear_fit_r_squared_adj=0.96,
        )

        session.add_all([attribute1, attribute2])
        session.commit()

        # Retrieve attributes
        retrieved_attr1 = (
            session.query(ProviderAssetGroupAttribute)
            .filter_by(
                provider_asset_group_id=provider_asset_group.id,
                lookback_window_seconds=3600,
                timestamp=timestamp1,
            )
            .one()
        )

        retrieved_attr2 = (
            session.query(ProviderAssetGroupAttribute)
            .filter_by(
                provider_asset_group_id=provider_asset_group.id,
                lookback_window_seconds=7200,
                timestamp=timestamp2,
            )
            .one()
        )

        # Verify attributes
        assert retrieved_attr1.cointegration_p_value == 0.05
        assert retrieved_attr1.ol_mu == 0.1
        assert retrieved_attr1.linear_fit_alpha == 1.0
        assert retrieved_attr1.linear_fit_r_squared == 0.95

        assert retrieved_attr2.cointegration_p_value == 0.03
        assert retrieved_attr2.ol_mu == 0.08
        assert retrieved_attr2.linear_fit_alpha == 1.1
        assert retrieved_attr2.linear_fit_r_squared == 0.97


@pytest.mark.asyncio
async def test_multiple_providers_same_asset_group():
    """Test that multiple providers can have members in the same asset group."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a second provider
        provider2 = Provider(
            provider_type_id=provider_type.id,
            name="Test Provider 2",
            description="Second test provider",
            is_active=True,
        )
        session.add(provider2)
        session.commit()
        session.refresh(provider2)

        # Create a ProviderAssetGroup
        provider_asset_group = ProviderAssetGroup(
            name="Multi-Provider Group",
            description="Group with multiple providers",
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Add members from different providers
        member1 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
        )
        member2 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider2.id,
            from_asset_id=usd_asset.id,
            to_asset_id=eth_asset.id,
        )
        session.add_all([member1, member2])
        session.commit()

        # Verify both providers have members in the same group
        members = (
            session.query(ProviderAssetGroupMember)
            .filter_by(provider_asset_group_id=provider_asset_group.id)
            .all()
        )

        assert len(members) == 2
        provider_ids = {member.provider_id for member in members}
        assert provider.id in provider_ids
        assert provider2.id in provider_ids


@pytest.mark.asyncio
async def test_asset_group_attribute_composite_key():
    """Test that ProviderAssetGroupAttribute composite primary key works correctly."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a ProviderAssetGroup
        provider_asset_group = ProviderAssetGroup(
            name="Test Group",
            description="Test group",
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Create attributes with same timestamp but different lookback windows
        timestamp = dt.datetime.now()

        attribute1 = ProviderAssetGroupAttribute(
            timestamp=timestamp,
            provider_asset_group_id=provider_asset_group.id,
            lookback_window_seconds=3600,  # 1 hour
            cointegration_p_value=0.05,
        )

        attribute2 = ProviderAssetGroupAttribute(
            timestamp=timestamp,
            provider_asset_group_id=provider_asset_group.id,
            lookback_window_seconds=7200,  # 2 hours
            cointegration_p_value=0.03,
        )

        session.add_all([attribute1, attribute2])
        session.commit()

        # Verify both attributes exist
        attributes = (
            session.query(ProviderAssetGroupAttribute)
            .filter_by(
                provider_asset_group_id=provider_asset_group.id, timestamp=timestamp
            )
            .all()
        )

        assert len(attributes) == 2
        lookback_windows = {attr.lookback_window_seconds for attr in attributes}
        assert 3600 in lookback_windows
        assert 7200 in lookback_windows


@pytest.mark.asyncio
async def test_asset_group_member_relationships():
    """Test the relationships between ProviderAssetGroup, ProviderAssetGroupMember, and ProviderAssetGroupAttribute."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a ProviderAssetGroup
        provider_asset_group = ProviderAssetGroup(
            name="Relationship Test Group",
            description="Testing relationships",
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Add a member
        member = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
        )
        session.add(member)
        session.commit()

        # Add an attribute
        attribute = ProviderAssetGroupAttribute(
            timestamp=dt.datetime.now(),
            provider_asset_group_id=provider_asset_group.id,
            lookback_window_seconds=3600,
            cointegration_p_value=0.05,
            ol_mu=0.1,
            ol_theta=0.5,
            ol_sigma=0.2,
        )
        session.add(attribute)
        session.commit()

        # Verify relationships work through queries
        # Get all members for this group
        members = (
            session.query(ProviderAssetGroupMember)
            .filter_by(provider_asset_group_id=provider_asset_group.id)
            .all()
        )
        assert len(members) == 1
        assert members[0].from_asset_id == usd_asset.id
        assert members[0].to_asset_id == btc_asset.id

        # Get all attributes for this group
        attributes = (
            session.query(ProviderAssetGroupAttribute)
            .filter_by(provider_asset_group_id=provider_asset_group.id)
            .all()
        )
        assert len(attributes) == 1
        assert attributes[0].cointegration_p_value == 0.05
        assert attributes[0].ol_mu == 0.1


@pytest.mark.asyncio
async def test_asset_group_inactive_status():
    """Test that ProviderAssetGroup can be marked as inactive."""
    engine = await get_engine_async()

    with Session(engine) as session:
        # Create an active ProviderAssetGroup
        provider_asset_group = ProviderAssetGroup(
            name="Test Group",
            description="Test group",
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Verify it's active
        assert provider_asset_group.is_active is True

        # Mark as inactive
        provider_asset_group.is_active = False
        session.commit()
        session.refresh(provider_asset_group)

        # Verify it's inactive
        assert provider_asset_group.is_active is False

        # Query for active groups should not return this one
        active_groups = (
            session.query(ProviderAssetGroup).filter_by(is_active=True).all()
        )
        group_ids = {group.id for group in active_groups}
        assert provider_asset_group.id not in group_ids


@pytest.mark.asyncio
async def test_provider_asset_group_member_ordering():
    """Test the optional order column for ProviderAssetGroupMember."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a ProviderAssetGroup
        provider_asset_group = ProviderAssetGroup(
            name="Ordered Test Group",
            description="Testing ordering functionality",
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Add members with explicit ordering
        member1 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
            order=1,
        )
        member2 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=eth_asset.id,
            order=2,
        )
        session.add_all([member1, member2])
        session.commit()

        # Verify ordering
        ordered_members = (
            session.query(ProviderAssetGroupMember)
            .filter_by(provider_asset_group_id=provider_asset_group.id)
            .order_by(ProviderAssetGroupMember.order.asc())
            .all()
        )

        assert len(ordered_members) == 2
        assert ordered_members[0].order == 1
        assert ordered_members[0].to_asset_id == btc_asset.id
        assert ordered_members[1].order == 2
        assert ordered_members[1].to_asset_id == eth_asset.id

        # Test mixed ordering (some with order, some without)
        member3 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=btc_asset.id,
            to_asset_id=eth_asset.id,
            order=None,  # No order specified
        )
        session.add(member3)
        session.commit()

        # Query with null handling - ordered items first, then unordered
        mixed_members = (
            session.query(ProviderAssetGroupMember)
            .filter_by(provider_asset_group_id=provider_asset_group.id)
            .order_by(
                ProviderAssetGroupMember.order.asc().nulls_last(),
                ProviderAssetGroupMember.to_asset_id.asc(),
            )
            .all()
        )

        assert len(mixed_members) == 3
        # First two should be ordered
        assert mixed_members[0].order == 1
        assert mixed_members[1].order == 2
        # Last one should be unordered (null)
        assert mixed_members[2].order is None


@pytest.mark.asyncio
async def test_provider_asset_group_member_no_ordering():
    """Test ProviderAssetGroupMember without any ordering."""
    engine = await get_engine_async()

    # Create base data
    asset_type, btc_asset, eth_asset, usd_asset, provider_type, provider = (
        create_base_data(engine)
    )

    with Session(engine) as session:
        # Create a ProviderAssetGroup
        provider_asset_group = ProviderAssetGroup(
            name="Unordered Test Group",
            description="Testing no ordering",
            is_active=True,
        )
        session.add(provider_asset_group)
        session.commit()
        session.refresh(provider_asset_group)

        # Add members without ordering
        member1 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
            order=None,
        )
        member2 = ProviderAssetGroupMember(
            provider_asset_group_id=provider_asset_group.id,
            provider_id=provider.id,
            from_asset_id=usd_asset.id,
            to_asset_id=eth_asset.id,
            order=None,
        )
        session.add_all([member1, member2])
        session.commit()

        # Verify no ordering
        unordered_members = (
            session.query(ProviderAssetGroupMember)
            .filter_by(provider_asset_group_id=provider_asset_group.id)
            .all()
        )

        assert len(unordered_members) == 2
        # Both should have null order
        for member in unordered_members:
            assert member.order is None
