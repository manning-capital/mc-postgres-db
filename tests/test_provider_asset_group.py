import os
import sys
import pandas as pd
import numpy as np
import datetime as dt

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "src"))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import pytest
from sqlalchemy.orm import Session
from mc_postgres_db.prefect.asyncio.tasks import get_engine as get_engine_async
from statsmodels.regression.rolling import RollingOLS
import statsmodels.api as sm
from mc_postgres_db.prefect.tasks import set_data

from mc_postgres_db.models import (
    AssetGroup,
    AssetGroupMember,
    ProviderAssetGroupAttribute,
    ProviderAssetMarket,
)
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

    # Create the asset group.
    with Session(engine) as session:
        asset_group = AssetGroup(
            name="BTC/ETH Asset Group",
            description="BTC/ETH Asset Group",
            is_active=True,
        )
        session.add(asset_group)
        session.commit()
        session.refresh(asset_group)

    # Create the asset group member.
    with Session(engine) as session:
        asset_group_member_1 = AssetGroupMember(
            asset_group_id=asset_group.id,
            from_asset_id=usd_asset.id,
            to_asset_id=btc_asset.id,
        )
        asset_group_member_2 = AssetGroupMember(
            asset_group_id=asset_group.id,
            from_asset_id=usd_asset.id,
            to_asset_id=eth_asset.id,
        )
        session.add(asset_group_member_1)
        session.add(asset_group_member_2)
        session.commit()
        session.refresh(asset_group_member_1)
        session.refresh(asset_group_member_2)

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
            "provider_id": len(T) * [provider.id],
            "asset_group_id": len(T) * [asset_group.id],
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
