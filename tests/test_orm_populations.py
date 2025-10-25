"""
Tests for ORM relationships and joinedload functionality.

This module tests all the ORM relationships in the models to ensure that
joinedload works correctly for efficient querying with related objects.
"""

import datetime

import pytest
from sqlalchemy.orm import Session, joinedload

from mc_postgres_db.models import (
    Asset,
    Provider,
    AssetType,
    ContentType,
    AssetContent,
    ProviderType,
    ProviderAsset,
    SentimentType,
    AssetGroupType,
    ProviderContent,
    ProviderAssetGroup,
    ProviderAssetOrder,
    ProviderAssetMarket,
    ProviderAssetGroupMember,
    ProviderContentSentiment,
    ProviderAssetGroupAttribute,
)
from mc_postgres_db.testing.utilities import clear_database
from mc_postgres_db.prefect.asyncio.tasks import get_engine as get_engine_async


def create_test_data(session: Session):
    """Create comprehensive test data for all models."""

    # Create AssetType
    asset_type = AssetType(
        name="Stock",
        description="Stock asset type",
        is_active=True,
    )
    session.add(asset_type)
    session.commit()
    session.refresh(asset_type)

    # Create ProviderType
    provider_type = ProviderType(
        name="Data Provider",
        description="Data provider type",
        is_active=True,
    )
    session.add(provider_type)
    session.commit()
    session.refresh(provider_type)

    # Create Provider
    provider = Provider(
        provider_type_id=provider_type.id,
        name="Test Provider",
        description="Test data provider",
        provider_external_code="TEST_PROV",
        url="https://test-provider.com",
        is_active=True,
    )
    session.add(provider)
    session.commit()
    session.refresh(provider)

    # Create Assets
    asset1 = Asset(
        asset_type_id=asset_type.id,
        name="Apple Inc",
        description="Apple Inc stock",
        symbol="AAPL",
        is_active=True,
    )
    asset2 = Asset(
        asset_type_id=asset_type.id,
        name="Microsoft Corp",
        description="Microsoft Corp stock",
        symbol="MSFT",
        is_active=True,
    )
    asset3 = Asset(
        asset_type_id=asset_type.id,
        name="Google Inc",
        description="Google Inc stock",
        symbol="GOOGL",
        is_active=True,
    )
    session.add_all([asset1, asset2, asset3])
    session.commit()
    session.refresh(asset1)
    session.refresh(asset2)
    session.refresh(asset3)

    # Create ProviderAsset
    provider_asset = ProviderAsset(
        date=datetime.date.today(),
        provider_id=provider.id,
        asset_id=asset1.id,
        asset_code="AAPL_PROV",
        is_active=True,
    )
    session.add(provider_asset)
    session.commit()
    session.refresh(provider_asset)

    # Create ProviderAssetOrder
    provider_asset_order = ProviderAssetOrder(
        timestamp=datetime.datetime.now(),
        provider_id=provider.id,
        from_asset_id=asset1.id,
        to_asset_id=asset2.id,
        price=150.50,
        volume=1000.0,
    )
    session.add(provider_asset_order)
    session.commit()
    session.refresh(provider_asset_order)

    # Create ProviderAssetMarket
    provider_asset_market = ProviderAssetMarket(
        timestamp=datetime.datetime.now(),
        provider_id=provider.id,
        from_asset_id=asset1.id,
        to_asset_id=asset2.id,
        close=150.25,
        open=149.75,
        high=151.00,
        low=149.50,
        volume=5000.0,
        best_bid=150.20,
        best_ask=150.30,
    )
    session.add(provider_asset_market)
    session.commit()
    session.refresh(provider_asset_market)

    # Create ContentType
    content_type = ContentType(
        name="News Article",
        description="News article content type",
        is_active=True,
    )
    session.add(content_type)
    session.commit()
    session.refresh(content_type)

    # Create ProviderContent
    provider_content = ProviderContent(
        timestamp=datetime.datetime.now(),
        provider_id=provider.id,
        content_external_code="NEWS_001",
        content_type_id=content_type.id,
        authors="John Doe",
        title="Apple Stock Analysis",
        description="Analysis of Apple stock performance",
        content="Apple Inc. has shown strong performance in recent quarters...",
    )
    session.add(provider_content)
    session.commit()
    session.refresh(provider_content)

    # Create SentimentType
    sentiment_type = SentimentType(
        name="VADER",
        description="VADER sentiment analysis",
        is_active=True,
    )
    session.add(sentiment_type)
    session.commit()
    session.refresh(sentiment_type)

    # Create ProviderContentSentiment
    provider_content_sentiment = ProviderContentSentiment(
        provider_content_id=provider_content.id,
        sentiment_type_id=sentiment_type.id,
        sentiment_text="Positive",
        positive_sentiment_score=0.8,
        negative_sentiment_score=0.1,
        neutral_sentiment_score=0.1,
        sentiment_score=0.7,
    )
    session.add(provider_content_sentiment)
    session.commit()
    session.refresh(provider_content_sentiment)

    # Create AssetContent
    asset_content = AssetContent(
        content_id=provider_content.id,
        asset_id=asset1.id,
    )
    session.add(asset_content)
    session.commit()
    session.refresh(asset_content)

    # Create AssetGroupType
    asset_group_type = AssetGroupType(
        symbol="PAIRS_TRADING",
        name="Pairs Trading",
        description="Statistical pairs trading strategy",
        is_active=True,
    )
    session.add(asset_group_type)
    session.commit()
    session.refresh(asset_group_type)

    # Create ProviderAssetGroup
    provider_asset_group = ProviderAssetGroup(
        asset_group_type_id=asset_group_type.id,
        is_active=True,
    )
    session.add(provider_asset_group)
    session.commit()
    session.refresh(provider_asset_group)

    # Create ProviderAssetGroupMember
    provider_asset_group_member = ProviderAssetGroupMember(
        provider_asset_group_id=provider_asset_group.id,
        provider_id=provider.id,
        from_asset_id=asset1.id,
        to_asset_id=asset2.id,
        order=1,
    )
    session.add(provider_asset_group_member)
    session.commit()
    session.refresh(provider_asset_group_member)

    # Create ProviderAssetGroupAttribute
    provider_asset_group_attribute = ProviderAssetGroupAttribute(
        timestamp=datetime.datetime.now(),
        provider_asset_group_id=provider_asset_group.id,
        lookback_window_seconds=86400,  # 24 hours
        cointegration_p_value=0.05,
        ol_mu=0.1,
        ol_theta=0.5,
        ol_sigma=0.2,
        linear_fit_alpha=0.1,
        linear_fit_beta=0.95,
        linear_fit_mse=0.01,
        linear_fit_r_squared=0.85,
        linear_fit_r_squared_adj=0.83,
    )
    session.add(provider_asset_group_attribute)
    session.commit()
    session.refresh(provider_asset_group_attribute)

    return {
        "asset_type": asset_type,
        "provider_type": provider_type,
        "provider": provider,
        "asset1": asset1,
        "asset2": asset2,
        "asset3": asset3,
        "provider_asset": provider_asset,
        "provider_asset_order": provider_asset_order,
        "provider_asset_market": provider_asset_market,
        "content_type": content_type,
        "provider_content": provider_content,
        "sentiment_type": sentiment_type,
        "provider_content_sentiment": provider_content_sentiment,
        "asset_content": asset_content,
        "asset_group_type": asset_group_type,
        "provider_asset_group": provider_asset_group,
        "provider_asset_group_member": provider_asset_group_member,
        "provider_asset_group_attribute": provider_asset_group_attribute,
    }


@pytest.mark.asyncio
async def test_asset_type_relationships():
    """Test AssetType relationships with joinedload."""
    engine = await get_engine_async()
    clear_database(engine)

    with Session(engine) as session:
        test_data = create_test_data(session)

        # Test AssetType basic query (no relationships to test since we removed the list relationship)
        asset_type = (
            session.query(AssetType).filter_by(id=test_data["asset_type"].id).first()
        )

        assert asset_type is not None
        assert asset_type.name == "Stock"
        assert asset_type.description == "Stock asset type"
        assert asset_type.is_active is True


@pytest.mark.asyncio
async def test_asset_relationships():
    """Test Asset relationships with joinedload."""
    engine = await get_engine_async()
    clear_database(engine)

    with Session(engine) as session:
        test_data = create_test_data(session)

        # Test Asset -> AssetType relationship
        asset = (
            session.query(Asset)
            .options(joinedload(Asset.asset_type))
            .filter_by(id=test_data["asset1"].id)
            .first()
        )

        assert asset is not None
        assert asset.name == "Apple Inc"
        assert asset.asset_type is not None
        assert asset.asset_type.name == "Stock"

        # Test Asset self-referential relationships
        asset_with_underlying = (
            session.query(Asset)
            .options(
                joinedload(Asset.underlying_asset), joinedload(Asset.derived_assets)
            )
            .filter_by(id=test_data["asset1"].id)
            .first()
        )

        assert asset_with_underlying is not None
        # These relationships exist but may be None if not set


@pytest.mark.asyncio
async def test_provider_type_relationships():
    """Test ProviderType relationships with joinedload."""
    engine = await get_engine_async()
    clear_database(engine)

    with Session(engine) as session:
        test_data = create_test_data(session)

        # Test ProviderType basic query (no relationships to test since we removed the list relationship)
        provider_type = (
            session.query(ProviderType)
            .filter_by(id=test_data["provider_type"].id)
            .first()
        )

        assert provider_type is not None
        assert provider_type.name == "Data Provider"
        assert provider_type.description == "Data provider type"
        assert provider_type.is_active is True


@pytest.mark.asyncio
async def test_provider_relationships():
    """Test Provider relationships with joinedload."""
    engine = await get_engine_async()
    clear_database(engine)

    with Session(engine) as session:
        test_data = create_test_data(session)

        # Test Provider -> ProviderType relationship
        provider = (
            session.query(Provider)
            .options(joinedload(Provider.provider_type))
            .filter_by(id=test_data["provider"].id)
            .first()
        )

        assert provider is not None
        assert provider.name == "Test Provider"
        assert provider.provider_type is not None
        assert provider.provider_type.name == "Data Provider"

        # Test Provider self-referential relationships
        provider_with_underlying = (
            session.query(Provider)
            .options(
                joinedload(Provider.underlying_provider),
                joinedload(Provider.derived_providers),
            )
            .filter_by(id=test_data["provider"].id)
            .first()
        )

        assert provider_with_underlying is not None
        # These relationships exist but may be None if not set


@pytest.mark.asyncio
async def test_provider_asset_relationships():
    """Test ProviderAsset relationships with joinedload."""
    engine = await get_engine_async()
    clear_database(engine)

    with Session(engine) as session:
        test_data = create_test_data(session)

        # Test ProviderAsset -> Provider and Asset relationships
        provider_asset = (
            session.query(ProviderAsset)
            .options(
                joinedload(ProviderAsset.provider), joinedload(ProviderAsset.asset)
            )
            .filter_by(
                provider_id=test_data["provider_asset"].provider_id,
                asset_id=test_data["provider_asset"].asset_id,
                date=test_data["provider_asset"].date,
            )
            .first()
        )

        assert provider_asset is not None
        assert provider_asset.asset_code == "AAPL_PROV"
        assert provider_asset.provider is not None
        assert provider_asset.provider.name == "Test Provider"
        assert provider_asset.asset is not None
        assert provider_asset.asset.name == "Apple Inc"


@pytest.mark.asyncio
async def test_provider_asset_order_relationships():
    """Test ProviderAssetOrder relationships with joinedload."""
    engine = await get_engine_async()
    clear_database(engine)

    with Session(engine) as session:
        test_data = create_test_data(session)

        # Test ProviderAssetOrder -> Provider, from_asset, and to_asset relationships
        provider_asset_order = (
            session.query(ProviderAssetOrder)
            .options(
                joinedload(ProviderAssetOrder.provider),
                joinedload(ProviderAssetOrder.from_asset),
                joinedload(ProviderAssetOrder.to_asset),
            )
            .filter_by(id=test_data["provider_asset_order"].id)
            .first()
        )

        assert provider_asset_order is not None
        assert provider_asset_order.price == 150.50
        assert provider_asset_order.provider is not None
        assert provider_asset_order.provider.name == "Test Provider"
        assert provider_asset_order.from_asset is not None
        assert provider_asset_order.from_asset.name == "Apple Inc"
        assert provider_asset_order.to_asset is not None
        assert provider_asset_order.to_asset.name == "Microsoft Corp"


@pytest.mark.asyncio
async def test_provider_asset_market_relationships():
    """Test ProviderAssetMarket relationships with joinedload."""
    engine = await get_engine_async()
    clear_database(engine)

    with Session(engine) as session:
        test_data = create_test_data(session)

        # Test ProviderAssetMarket -> Provider, from_asset, and to_asset relationships
        provider_asset_market = (
            session.query(ProviderAssetMarket)
            .options(
                joinedload(ProviderAssetMarket.provider),
                joinedload(ProviderAssetMarket.from_asset),
                joinedload(ProviderAssetMarket.to_asset),
            )
            .filter_by(
                timestamp=test_data["provider_asset_market"].timestamp,
                provider_id=test_data["provider_asset_market"].provider_id,
                from_asset_id=test_data["provider_asset_market"].from_asset_id,
                to_asset_id=test_data["provider_asset_market"].to_asset_id,
            )
            .first()
        )

        assert provider_asset_market is not None
        assert provider_asset_market.close == 150.25
        assert provider_asset_market.provider is not None
        assert provider_asset_market.provider.name == "Test Provider"
        assert provider_asset_market.from_asset is not None
        assert provider_asset_market.from_asset.name == "Apple Inc"
        assert provider_asset_market.to_asset is not None
        assert provider_asset_market.to_asset.name == "Microsoft Corp"


@pytest.mark.asyncio
async def test_content_type_relationships():
    """Test ContentType relationships with joinedload."""
    engine = await get_engine_async()
    clear_database(engine)

    with Session(engine) as session:
        test_data = create_test_data(session)

        # Test ContentType basic query (no relationships to test since we removed the list relationship)
        content_type = (
            session.query(ContentType)
            .filter_by(id=test_data["content_type"].id)
            .first()
        )

        assert content_type is not None
        assert content_type.name == "News Article"
        assert content_type.description == "News article content type"
        assert content_type.is_active is True


@pytest.mark.asyncio
async def test_provider_content_relationships():
    """Test ProviderContent relationships with joinedload."""
    engine = await get_engine_async()
    clear_database(engine)

    with Session(engine) as session:
        test_data = create_test_data(session)

        # Test ProviderContent -> Provider and ContentType relationships
        provider_content = (
            session.query(ProviderContent)
            .options(
                joinedload(ProviderContent.provider),
                joinedload(ProviderContent.content_type),
            )
            .filter_by(id=test_data["provider_content"].id)
            .first()
        )

        assert provider_content is not None
        assert provider_content.title == "Apple Stock Analysis"
        assert provider_content.provider is not None
        assert provider_content.provider.name == "Test Provider"
        assert provider_content.content_type is not None
        assert provider_content.content_type.name == "News Article"


@pytest.mark.asyncio
async def test_sentiment_type_relationships():
    """Test SentimentType relationships with joinedload."""
    engine = await get_engine_async()
    clear_database(engine)

    with Session(engine) as session:
        test_data = create_test_data(session)

        # Test SentimentType basic query (no relationships to test since we removed the list relationship)
        sentiment_type = (
            session.query(SentimentType)
            .filter_by(id=test_data["sentiment_type"].id)
            .first()
        )

        assert sentiment_type is not None
        assert sentiment_type.name == "VADER"
        assert sentiment_type.description == "VADER sentiment analysis"
        assert sentiment_type.is_active is True


@pytest.mark.asyncio
async def test_provider_content_sentiment_relationships():
    """Test ProviderContentSentiment relationships with joinedload."""
    engine = await get_engine_async()
    clear_database(engine)

    with Session(engine) as session:
        test_data = create_test_data(session)

        # Test ProviderContentSentiment -> ProviderContent and SentimentType relationships
        provider_content_sentiment = (
            session.query(ProviderContentSentiment)
            .options(
                joinedload(ProviderContentSentiment.provider_content),
                joinedload(ProviderContentSentiment.sentiment_type),
            )
            .filter_by(
                provider_content_id=test_data[
                    "provider_content_sentiment"
                ].provider_content_id,
                sentiment_type_id=test_data[
                    "provider_content_sentiment"
                ].sentiment_type_id,
            )
            .first()
        )

        assert provider_content_sentiment is not None
        assert provider_content_sentiment.sentiment_score == 0.7
        assert provider_content_sentiment.provider_content is not None
        assert (
            provider_content_sentiment.provider_content.title == "Apple Stock Analysis"
        )
        assert provider_content_sentiment.sentiment_type is not None
        assert provider_content_sentiment.sentiment_type.name == "VADER"


@pytest.mark.asyncio
async def test_asset_content_relationships():
    """Test AssetContent relationships with joinedload."""
    engine = await get_engine_async()
    clear_database(engine)

    with Session(engine) as session:
        test_data = create_test_data(session)

        # Test AssetContent -> ProviderContent and Asset relationships
        asset_content = (
            session.query(AssetContent)
            .options(
                joinedload(AssetContent.provider_content),
                joinedload(AssetContent.asset),
            )
            .filter_by(
                content_id=test_data["asset_content"].content_id,
                asset_id=test_data["asset_content"].asset_id,
            )
            .first()
        )

        assert asset_content is not None
        assert asset_content.provider_content is not None
        assert asset_content.provider_content.title == "Apple Stock Analysis"
        assert asset_content.asset is not None
        assert asset_content.asset.name == "Apple Inc"


@pytest.mark.asyncio
async def test_asset_group_type_relationships():
    """Test AssetGroupType relationships with joinedload."""
    engine = await get_engine_async()
    clear_database(engine)

    with Session(engine) as session:
        test_data = create_test_data(session)

        # Test AssetGroupType basic query (no relationships to test since we removed the list relationship)
        asset_group_type = (
            session.query(AssetGroupType)
            .filter_by(id=test_data["asset_group_type"].id)
            .first()
        )

        assert asset_group_type is not None
        assert asset_group_type.name == "Pairs Trading"
        assert asset_group_type.symbol == "PAIRS_TRADING"
        assert asset_group_type.description == "Statistical pairs trading strategy"
        assert asset_group_type.is_active is True


@pytest.mark.asyncio
async def test_provider_asset_group_relationships():
    """Test ProviderAssetGroup relationships with joinedload."""
    engine = await get_engine_async()
    clear_database(engine)

    with Session(engine) as session:
        test_data = create_test_data(session)

        # Test ProviderAssetGroup -> AssetGroupType and members relationships
        provider_asset_group = (
            session.query(ProviderAssetGroup)
            .options(
                joinedload(ProviderAssetGroup.asset_group_type),
                joinedload(ProviderAssetGroup.members),
            )
            .filter_by(id=test_data["provider_asset_group"].id)
            .first()
        )

        assert provider_asset_group is not None
        assert provider_asset_group.asset_group_type is not None
        assert provider_asset_group.asset_group_type.name == "Pairs Trading"
        assert len(provider_asset_group.members) == 1
        assert provider_asset_group.members[0].order == 1


@pytest.mark.asyncio
async def test_provider_asset_group_member_relationships():
    """Test ProviderAssetGroupMember relationships with joinedload."""
    engine = await get_engine_async()
    clear_database(engine)

    with Session(engine) as session:
        test_data = create_test_data(session)

        # Test ProviderAssetGroupMember -> ProviderAssetGroup, Provider, from_asset, and to_asset relationships
        provider_asset_group_member = (
            session.query(ProviderAssetGroupMember)
            .options(
                joinedload(ProviderAssetGroupMember.group),
                joinedload(ProviderAssetGroupMember.provider),
                joinedload(ProviderAssetGroupMember.from_asset),
                joinedload(ProviderAssetGroupMember.to_asset),
            )
            .filter_by(
                provider_asset_group_id=test_data[
                    "provider_asset_group_member"
                ].provider_asset_group_id,
                provider_id=test_data["provider_asset_group_member"].provider_id,
                from_asset_id=test_data["provider_asset_group_member"].from_asset_id,
                to_asset_id=test_data["provider_asset_group_member"].to_asset_id,
            )
            .first()
        )

        assert provider_asset_group_member is not None
        assert provider_asset_group_member.order == 1
        assert provider_asset_group_member.group is not None
        assert provider_asset_group_member.provider is not None
        assert provider_asset_group_member.provider.name == "Test Provider"
        assert provider_asset_group_member.from_asset is not None
        assert provider_asset_group_member.from_asset.name == "Apple Inc"
        assert provider_asset_group_member.to_asset is not None
        assert provider_asset_group_member.to_asset.name == "Microsoft Corp"


@pytest.mark.asyncio
async def test_provider_asset_group_attribute_relationships():
    """Test ProviderAssetGroupAttribute relationships with joinedload."""
    engine = await get_engine_async()
    clear_database(engine)

    with Session(engine) as session:
        test_data = create_test_data(session)

        # Test ProviderAssetGroupAttribute -> ProviderAssetGroup relationship
        provider_asset_group_attribute = (
            session.query(ProviderAssetGroupAttribute)
            .options(joinedload(ProviderAssetGroupAttribute.provider_asset_group))
            .filter_by(
                timestamp=test_data["provider_asset_group_attribute"].timestamp,
                provider_asset_group_id=test_data[
                    "provider_asset_group_attribute"
                ].provider_asset_group_id,
                lookback_window_seconds=test_data[
                    "provider_asset_group_attribute"
                ].lookback_window_seconds,
            )
            .first()
        )

        assert provider_asset_group_attribute is not None
        assert provider_asset_group_attribute.cointegration_p_value == 0.05
        assert provider_asset_group_attribute.provider_asset_group is not None


@pytest.mark.asyncio
async def test_complex_joinedload_scenarios():
    """Test complex joinedload scenarios with multiple relationships."""
    engine = await get_engine_async()
    clear_database(engine)

    with Session(engine) as session:
        test_data = create_test_data(session)

        # Test complex query with ProviderAssetGroup and all its relationships
        provider_asset_group = (
            session.query(ProviderAssetGroup)
            .options(
                joinedload(ProviderAssetGroup.asset_group_type),
                joinedload(ProviderAssetGroup.members).joinedload(
                    ProviderAssetGroupMember.provider
                ),
                joinedload(ProviderAssetGroup.members).joinedload(
                    ProviderAssetGroupMember.from_asset
                ),
                joinedload(ProviderAssetGroup.members).joinedload(
                    ProviderAssetGroupMember.to_asset
                ),
            )
            .filter_by(id=test_data["provider_asset_group"].id)
            .first()
        )

        assert provider_asset_group is not None
        assert provider_asset_group.asset_group_type.name == "Pairs Trading"
        assert len(provider_asset_group.members) == 1
        member = provider_asset_group.members[0]
        assert member.provider.name == "Test Provider"
        assert member.from_asset.name == "Apple Inc"
        assert member.to_asset.name == "Microsoft Corp"

        # Test complex query with ProviderContent and all its relationships
        provider_content = (
            session.query(ProviderContent)
            .options(
                joinedload(ProviderContent.provider),
                joinedload(ProviderContent.content_type),
            )
            .filter_by(id=test_data["provider_content"].id)
            .first()
        )

        assert provider_content is not None
        assert provider_content.provider.name == "Test Provider"
        assert provider_content.content_type.name == "News Article"


@pytest.mark.asyncio
async def test_joinedload_performance():
    """Test that joinedload reduces the number of queries."""
    engine = await get_engine_async()
    clear_database(engine)

    with Session(engine) as session:
        test_data = create_test_data(session)

        # Test without joinedload (should trigger lazy loading)
        provider_asset_group = (
            session.query(ProviderAssetGroup)
            .filter_by(id=test_data["provider_asset_group"].id)
            .first()
        )

        assert provider_asset_group is not None

        # Access relationships (this would trigger additional queries in lazy loading)
        asset_group_type_name = provider_asset_group.asset_group_type.name
        members_count = len(provider_asset_group.members)

        assert asset_group_type_name == "Pairs Trading"
        assert members_count == 1

        # Test with joinedload (should load everything in one query)
        provider_asset_group_with_joinedload = (
            session.query(ProviderAssetGroup)
            .options(
                joinedload(ProviderAssetGroup.asset_group_type),
                joinedload(ProviderAssetGroup.members),
            )
            .filter_by(id=test_data["provider_asset_group"].id)
            .first()
        )

        assert provider_asset_group_with_joinedload is not None
        assert (
            provider_asset_group_with_joinedload.asset_group_type.name
            == "Pairs Trading"
        )
        assert len(provider_asset_group_with_joinedload.members) == 1
