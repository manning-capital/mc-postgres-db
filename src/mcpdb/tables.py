import datetime
from typing import Optional

from sqlalchemy import Engine, ForeignKey, String, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy models.
    This class is used to define the base for all models in the application.
    It inherits from DeclarativeBase, which is a SQLAlchemy class that provides
    a declarative interface for defining models.
    """

    pass


class AssetType(Base):
    __tablename__ = "asset_type"
    __table_args__ = {"comment": "The type of asset, e.g. stock, bond, currency, etc."}

    id: Mapped[int] = mapped_column(
        primary_key=True, comment="The unique identifier of the asset type"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="The name of the asset type"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True, comment="The description of the asset type"
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, comment="Whether the asset type is active"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the creation of the asset type",
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=False,
        server_onupdate=func.now(),
        server_default=func.now(),
        comment="The timestamp of the last update of the asset type",
    )

    def __repr__(self):
        return f"{AssetType.__name__}({self.id}, {self.name})"


class Asset(Base):
    __tablename__ = "asset"
    __table_args__ = {"comment": "The asset, e.g. stock, bond, currency, etc."}

    id: Mapped[int] = mapped_column(
        primary_key=True, comment="The unique identifier of the asset"
    )
    asset_type_id: Mapped[int] = mapped_column(
        ForeignKey("asset_type.id"),
        nullable=False,
        comment="The identifier of the asset type",
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="The name of the asset"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True, comment="The description of the asset"
    )
    symbol: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="The symbol of the asset"
    )
    underlying_asset_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("asset.id"),
        nullable=True,
        comment="The identifier of the underlying asset",
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, comment="Whether the asset is active"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the creation of the asset",
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=False,
        server_onupdate=func.now(),
        server_default=func.now(),
        comment="The timestamp of the last update of the asset",
    )

    def __repr__(self):
        return f"{Asset.__name__}({self.id}, {self.name})"


class ProviderType(Base):
    __tablename__ = "provider_type"
    __table_args__ = {"comment": "The type of provider, e.g. news, social media, etc."}

    id: Mapped[int] = mapped_column(
        primary_key=True, comment="The unique identifier of the provider type"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="The name of the provider type"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True, comment="The description of the provider type"
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, comment="Whether the provider type is active"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the creation of the provider type",
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=False,
        server_onupdate=func.now(),
        server_default=func.now(),
        comment="The timestamp of the last update of the provider type",
    )

    def __repr__(self):
        return f"{ProviderType.__name__}({self.id}, {self.name})"


class Provider(Base):
    __tablename__ = "provider"
    __table_args__ = {
        "comment": "The provider, e.g. data vendor, news, social media, etc."
    }

    id: Mapped[int] = mapped_column(
        primary_key=True, comment="The unique identifier of the provider"
    )
    provider_type_id: Mapped[int] = mapped_column(
        ForeignKey("provider_type.id"),
        nullable=False,
        comment="The identifier of the provider type",
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="The name of the provider"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True, comment="The description of the provider"
    )
    provider_external_code: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="The external code of the provider, this is used to identify the provider in the provider's system. For example, for a news provider, it could be the name of the provider or an internal ID.",
    )
    underlying_provider_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("provider.id"),
        nullable=True,
        comment="The identifier of the underlying provider",
    )
    url: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True, comment="The URL of the provider"
    )
    image_url: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True, comment="The URL of the provider's image"
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, comment="Whether the provider is active"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the creation of the provider",
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=False,
        server_onupdate=func.now(),
        server_default=func.now(),
        comment="The timestamp of the last update of the provider",
    )

    def __repr__(self):
        return f"{Provider.__name__}({self.id}, {self.name})"

    def get_all_assets(
        self,
        engine: Engine,
        asset_ids: list[int] = [],
    ) -> set["ProviderAsset"]:
        with Session(engine) as session:
            # Subquery to get the latest date for each provider_id, asset_id combination
            latest_dates_subq = (
                select(
                    ProviderAsset.provider_id,
                    ProviderAsset.asset_id,
                    func.max(ProviderAsset.date).label("max_date"),
                )
                .where(ProviderAsset.provider_id == self.id, ProviderAsset.is_active)
                .group_by(ProviderAsset.provider_id, ProviderAsset.asset_id)
                .subquery()
            )

            # Query to get assets that have provider_asset entries with the latest dates
            query = (
                select(ProviderAsset)
                .join(Asset, ProviderAsset.asset_id == Asset.id)
                .join(
                    latest_dates_subq,
                    (ProviderAsset.provider_id == latest_dates_subq.c.provider_id)
                    & (ProviderAsset.asset_id == latest_dates_subq.c.asset_id)
                    & (ProviderAsset.date == latest_dates_subq.c.max_date),
                )
                .where(
                    ProviderAsset.provider_id == self.id,
                    ProviderAsset.is_active,
                    Asset.is_active,
                )
            )

            # Add asset ID filter if provided
            if asset_ids:
                query = query.where(ProviderAsset.asset_id.in_(asset_ids))

            # Execute query and return results as a set
            assets = session.scalars(query).all()
            return set(assets)


class ProviderAsset(Base):
    __tablename__ = "provider_asset"
    __table_args__ = {
        "comment": "The provider asset, is meant to map our internal definitions to the provider's definitions."
    }

    date: Mapped[datetime.date] = mapped_column(
        primary_key=True, comment="The date of the provider asset"
    )
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("provider.id"),
        nullable=False,
        primary_key=True,
        comment="The identifier of the provider",
    )
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("asset.id"),
        nullable=False,
        primary_key=True,
        comment="The identifier of the asset",
    )
    asset_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="The code of the asset, this is used to identify the asset in the provider's system. For example, for a stock, it could be the ticker symbol or an internal ID.",
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, comment="Whether the provider asset is active"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the creation of the provider asset",
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=False,
        server_onupdate=func.now(),
        server_default=func.now(),
        comment="The timestamp of the last update of the provider asset",
    )

    def __repr__(self):
        return f"{ProviderAsset.__name__}({self.date}, {self.provider_id}, {self.asset_id})"


class ProviderAssetOrder(Base):
    __tablename__ = "provider_asset_order"
    __table_args__ = {
        "comment": "The provider asset order, will store order data for an asset from a provider."
    }

    id: Mapped[int] = mapped_column(
        primary_key=True, comment="The unique identifier of the provider asset order"
    )
    timestamp: Mapped[datetime.datetime] = mapped_column(
        nullable=False, comment="The timestamp of the provider asset order"
    )
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("provider.id"),
        nullable=False,
        comment="The identifier of the provider",
    )
    from_asset_id: Mapped[int] = mapped_column(
        ForeignKey("asset.id"),
        nullable=False,
        comment="The identifier of the from asset",
    )
    to_asset_id: Mapped[int] = mapped_column(
        ForeignKey("asset.id"), nullable=False, comment="The identifier of the to asset"
    )
    price: Mapped[float] = mapped_column(
        nullable=True, comment="The price of the provider asset order"
    )
    volume: Mapped[float] = mapped_column(
        nullable=True, comment="The volume of the provider asset order"
    )

    def __repr__(self):
        return f"{ProviderAssetOrder.__name__}(id={self.id}, timestamp={self.timestamp}, provider_id={self.provider_id}, from_asset_id={self.from_asset_id}, to_asset_id={self.to_asset_id}, price={self.price}, volume={self.volume})"


class ProviderAssetMarket(Base):
    __tablename__ = "provider_asset_market"
    __table_args__ = {
        "comment": "The provider asset market, will store market data for an asset from a provider."
    }

    timestamp: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        primary_key=True,
        comment="The timestamp of the provider asset market",
    )
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("provider.id"),
        nullable=False,
        primary_key=True,
        comment="The identifier of the provider",
    )
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("asset.id"),
        nullable=False,
        primary_key=True,
        comment="The identifier of the asset",
    )
    close: Mapped[float] = mapped_column(
        nullable=True, comment="The closing price of the provider asset market"
    )
    open: Mapped[float] = mapped_column(
        nullable=True, comment="The opening price of the provider asset market"
    )
    high: Mapped[float] = mapped_column(
        nullable=True, comment="The highest price of the provider asset market"
    )
    low: Mapped[float] = mapped_column(
        nullable=True, comment="The lowest price of the provider asset market"
    )
    volume: Mapped[float] = mapped_column(
        nullable=True, comment="The volume traded of the provider asset market"
    )
    best_bid: Mapped[float] = mapped_column(
        nullable=True, comment="The best bid price of the provider asset market"
    )
    best_ask: Mapped[float] = mapped_column(
        nullable=True, comment="The best ask price of the provider asset market"
    )

    def __repr__(self):
        return f"{ProviderAssetMarket.__name__}(timestamp={self.timestamp}, provider_id={self.provider_id}, asset_id={self.asset_id})"


class ContentType(Base):
    __tablename__ = "content_type"
    __table_args__ = {"comment": "The type of content, e.g. news, social media, etc."}

    id: Mapped[int] = mapped_column(
        primary_key=True, comment="The unique identifier of the content type"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="The name of the content type"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True, comment="The description of the content type"
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, comment="Whether the content type is active"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the creation of the content type",
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=False,
        server_onupdate=func.now(),
        server_default=func.now(),
        comment="The timestamp of the last update of the content type",
    )

    def __repr__(self):
        return f"{ContentType.__name__}({self.id}, {self.name})"


class ProviderContent(Base):
    __tablename__ = "provider_content"
    __table_args__ = {
        "comment": "The provider content, will store content data for a provider."
    }

    id: Mapped[int] = mapped_column(
        primary_key=True, comment="The unique identifier of the provider content"
    )
    timestamp: Mapped[datetime.datetime] = mapped_column(
        nullable=False, comment="The timestamp of the provider content"
    )
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("provider.id"),
        nullable=False,
        comment="The identifier of the provider",
    )
    content_external_code: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        comment="This is the external identifier for the content and will depend on the content provider and the type of content. For example, for a news article, it could be the URL of the article and for a social media post, it could be the post ID.",
    )
    content_type_id: Mapped[int] = mapped_column(
        ForeignKey("content_type.id"),
        nullable=False,
        comment="The identifier of the content type",
    )
    authors: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True, comment="The authors of the provider content"
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True, comment="The title of the provider content"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(5000),
        nullable=True,
        comment="A short description of the provider content",
    )
    content: Mapped[str] = mapped_column(
        String(), nullable=False, comment="The content of the provider content"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the creation of the provider content",
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=False,
        server_onupdate=func.now(),
        server_default=func.now(),
        comment="The timestamp of the last update of the provider content",
    )

    def __repr__(self):
        return f"{ProviderContent.__name__}(id={self.id}, provider_id={self.provider_id}, content_type_id={self.content_type_id}, content_external_code={self.content_external_code})"


class SentimentType(Base):
    __tablename__ = "sentiment_type"
    __table_args__ = {
        "comment": "The type of sentiment in terms of the calculation method, e.g. PROVIDER, NLTK, VADER, etc. This is meant to store the sentiment type that is used to calculate the sentiment of a provider content."
    }

    id: Mapped[int] = mapped_column(
        primary_key=True, comment="The unique identifier of the sentiment type"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="The name of the sentiment type"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True, comment="The description of the sentiment type"
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, comment="Whether the sentiment type is active"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the creation of the sentiment type",
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=False,
        server_onupdate=func.now(),
        server_default=func.now(),
        comment="The timestamp of the last update of the sentiment type",
    )

    def __repr__(self):
        return f"{SentimentType.__name__}({self.id}, {self.name})"


class ProviderContentSentiment(Base):
    __tablename__ = "provider_content_sentiment"
    __table_args__ = {
        "comment": "The provider content sentiment, will store the sentiment of a provider content. This is meant to store the sentiment of a provider content that is internally calculated."
    }

    provider_content_id: Mapped[int] = mapped_column(
        ForeignKey("provider_content.id"),
        primary_key=True,
        nullable=False,
        comment="The identifier of the provider content",
    )
    sentiment_type_id: Mapped[int] = mapped_column(
        ForeignKey("sentiment_type.id"),
        primary_key=True,
        nullable=False,
        comment="The identifier of the sentiment type",
    )
    sentiment_text: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="The sentiment score text of the content that is internally calculated, this is a text that describes the sentiment score.",
    )
    positive_sentiment_score: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="The positive sentiment score of the content that is internally calculated, this is a normalized score between 0 and 1, where 0 is the lowest sentiment and 1 is the highest sentiment.",
    )
    negative_sentiment_score: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="The negative sentiment score of the provider content that is internally calculated, this is a normalized score between 0 and 1, where 0 is the lowest sentiment and 1 is the highest sentiment.",
    )
    neutral_sentiment_score: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="The neutral sentiment score of the provider content that is internally calculated, this is a normalized score between 0 and 1, where 0 is the lowest sentiment and 1 is the highest sentiment.",
    )
    sentiment_score: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="The sentiment score of the provider content that is internally calculated, this is a normalized score between 0 and 1, where 0 is the lowest sentiment and 1 is the highest sentiment.",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the creation of the provider content sentiment",
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=False,
        server_onupdate=func.now(),
        server_default=func.now(),
        comment="The timestamp of the last update of the provider content sentiment",
    )

    def __repr__(self):
        return f"{ProviderContentSentiment.__name__}(provider_content_id={self.provider_content_id}, sentiment_type_id={self.sentiment_type_id}, sentiment_text={self.sentiment_text}, positive_sentiment_score={self.positive_sentiment_score}, negative_sentiment_score={self.negative_sentiment_score}, neutral_sentiment_score={self.neutral_sentiment_score}, sentiment_score={self.sentiment_score})"


class AssetContent(Base):
    __tablename__ = "asset_content"
    __table_args__ = {
        "comment": "The asset content, will store the relationship between an asset and a provider content."
    }

    content_id: Mapped[int] = mapped_column(
        ForeignKey("provider_content.id"),
        primary_key=True,
        nullable=False,
        comment="The identifier of the provider content",
    )
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("asset.id"),
        primary_key=True,
        nullable=False,
        comment="The identifier of the asset",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the creation of the asset content",
    )
