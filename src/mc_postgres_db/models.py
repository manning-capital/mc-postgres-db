import datetime
from typing import Optional

from sqlalchemy import Engine, String, MetaData, ForeignKey, func, select
from sqlalchemy.orm import Mapped, Session, DeclarativeBase, relationship, mapped_column


class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy models.
    This class is used to define the base for all models in the application.
    It inherits from DeclarativeBase, which is a SQLAlchemy class that provides
    a declarative interface for defining models.
    """

    # Define the metadata for the models. This is used to define the primary key constraint name.
    metadata = MetaData(
        naming_convention={
            "pk": "%(table_name)s_pkey",
        }
    )


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
    asset_type: Mapped["AssetType"] = relationship("AssetType")
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
    underlying_asset: Mapped[Optional["Asset"]] = relationship(
        "Asset", remote_side=[id]
    )
    derived_assets: Mapped[list["Asset"]] = relationship(
        "Asset", remote_side=[underlying_asset_id], overlaps="underlying_asset"
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
    provider_type: Mapped["ProviderType"] = relationship("ProviderType")
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
    underlying_provider: Mapped[Optional["Provider"]] = relationship(
        "Provider", remote_side=[id]
    )
    derived_providers: Mapped[list["Provider"]] = relationship(
        "Provider", remote_side=[underlying_provider_id], overlaps="underlying_provider"
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
    provider: Mapped["Provider"] = relationship("Provider")
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("asset.id"),
        nullable=False,
        primary_key=True,
        comment="The identifier of the asset",
    )
    asset: Mapped["Asset"] = relationship("Asset")
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
    provider: Mapped["Provider"] = relationship("Provider")
    from_asset_id: Mapped[int] = mapped_column(
        ForeignKey("asset.id"),
        nullable=False,
        comment="The identifier of the from asset",
    )
    from_asset: Mapped["Asset"] = relationship("Asset", foreign_keys=[from_asset_id])
    to_asset_id: Mapped[int] = mapped_column(
        ForeignKey("asset.id"), nullable=False, comment="The identifier of the to asset"
    )
    to_asset: Mapped["Asset"] = relationship("Asset", foreign_keys=[to_asset_id])
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
    provider: Mapped["Provider"] = relationship("Provider")
    from_asset_id: Mapped[int] = mapped_column(
        ForeignKey("asset.id"),
        nullable=False,
        primary_key=True,
        comment="The identifier of the from asset. This is also called the base asset.",
    )
    from_asset: Mapped["Asset"] = relationship("Asset", foreign_keys=[from_asset_id])
    to_asset_id: Mapped[int] = mapped_column(
        ForeignKey("asset.id"),
        nullable=False,
        primary_key=True,
        comment="The identifier of the to asset. This is also called the quote asset.",
    )
    to_asset: Mapped["Asset"] = relationship("Asset", foreign_keys=[to_asset_id])
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
        return f"{ProviderAssetMarket.__name__}(timestamp={self.timestamp}, provider_id={self.provider_id}, from_asset_id={self.from_asset_id}, to_asset_id={self.to_asset_id})"


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
    provider: Mapped["Provider"] = relationship("Provider")
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
    content_type: Mapped["ContentType"] = relationship("ContentType")
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
    provider_content: Mapped["ProviderContent"] = relationship("ProviderContent")
    sentiment_type_id: Mapped[int] = mapped_column(
        ForeignKey("sentiment_type.id"),
        primary_key=True,
        nullable=False,
        comment="The identifier of the sentiment type",
    )
    sentiment_type: Mapped["SentimentType"] = relationship("SentimentType")
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
    provider_content: Mapped["ProviderContent"] = relationship("ProviderContent")
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("asset.id"),
        primary_key=True,
        nullable=False,
        comment="The identifier of the asset",
    )
    asset: Mapped["Asset"] = relationship("Asset")
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the creation of the asset content",
    )


class AssetGroupType(Base):
    __tablename__ = "asset_group_type"
    __table_args__ = {
        "comment": "The type of asset group, e.g. statistical pairs trading, classical arbitrage, triangular arbitrage, etc."
    }

    id: Mapped[int] = mapped_column(
        primary_key=True, comment="The unique identifier of the asset group type"
    )
    symbol: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="The symbol of the asset group type, e.g. PAIRS_TRADING, CLASSICAL_ARBITRAGE, TRIANGULAR_ARBITRAGE, etc.",
        unique=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        comment="The name of the asset group type, e.g. Pairs Trading, Classical Arbitrage, Triangular Arbitrage, etc.",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="The description of the asset group type, e.g. statistical pairs trading, classical arbitrage, triangular arbitrage, etc.",
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, comment="Whether the asset group type is active"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the creation of the asset group type",
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=False,
        server_onupdate=func.now(),
        server_default=func.now(),
        comment="The timestamp of the last update of the asset group type",
    )

    def __repr__(self):
        return f"{AssetGroupType.__name__}({self.id}, {self.name})"


class ProviderAssetGroup(Base):
    __tablename__ = "provider_asset_group"
    __table_args__ = {
        "comment": "Groups provider assets for calculating aggregated statistical values between members. Each group contains provider asset pairs that share statistical relationships for cointegration analysis, mean reversion modeling, and linear regression calculations."
    }

    id: Mapped[int] = mapped_column(
        primary_key=True, comment="The unique identifier of the asset group"
    )
    asset_group_type_id: Mapped[int] = mapped_column(
        ForeignKey("asset_group_type.id"),
        nullable=False,
        comment="The identifier of the asset group type",
    )
    asset_group_type: Mapped["AssetGroupType"] = relationship("AssetGroupType")
    members: Mapped[list["ProviderAssetGroupMember"]] = relationship(
        "ProviderAssetGroupMember",
        cascade="all, delete-orphan",
        order_by="ProviderAssetGroupMember.order.asc()",
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, comment="Whether the asset group is active"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the creation of the asset group",
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=False,
        server_onupdate=func.now(),
        server_default=func.now(),
        comment="The timestamp of the last update of the asset group",
    )

    def __repr__(self):
        return f"{ProviderAssetGroup.__name__}({self.id})"


class ProviderAssetGroupMember(Base):
    __tablename__ = "provider_asset_group_member"
    __table_args__ = {
        "comment": "Maps provider asset pairs to statistical groups for aggregated calculations. Each record represents a pair of assets (from_asset_id, to_asset_id) from a specific provider that belong to a statistical group. Optional order field allows sequencing within groups for hierarchical analysis."
    }

    provider_asset_group_id: Mapped[int] = mapped_column(
        ForeignKey("provider_asset_group.id"),
        primary_key=True,
        nullable=False,
        comment="The identifier of the provider asset group",
    )
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("provider.id"),
        primary_key=True,
        nullable=False,
        comment="The identifier of the provider",
    )
    provider: Mapped["Provider"] = relationship("Provider")
    from_asset_id: Mapped[int] = mapped_column(
        ForeignKey("asset.id"),
        primary_key=True,
        nullable=False,
        comment="The identifier of the from asset (base asset)",
    )
    from_asset: Mapped["Asset"] = relationship("Asset", foreign_keys=[from_asset_id])
    to_asset_id: Mapped[int] = mapped_column(
        ForeignKey("asset.id"),
        primary_key=True,
        nullable=False,
        comment="The identifier of the to asset (quote asset)",
    )
    to_asset: Mapped["Asset"] = relationship("Asset", foreign_keys=[to_asset_id])
    order: Mapped[int] = mapped_column(
        nullable=False,
        comment="The order of the asset pair within the group (1, 2, 3, etc.). Required field for sequencing members within the group.",
    )
    group: Mapped["ProviderAssetGroup"] = relationship(
        "ProviderAssetGroup", overlaps="members"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the creation of the asset group member",
    )

    def __repr__(self):
        return f"{ProviderAssetGroupMember.__name__}(provider_asset_group_id={self.provider_asset_group_id}, provider_id={self.provider_id}, from_asset_id={self.from_asset_id}, to_asset_id={self.to_asset_id})"


class ProviderAssetGroupAttribute(Base):
    __tablename__ = "provider_asset_group_attribute"
    __table_args__ = {
        "comment": "Stores aggregated statistical calculations for provider asset groups across multiple time windows. Contains cointegration analysis results, Ornstein-Uhlenbeck process parameters for mean reversion modeling, and comprehensive linear regression statistics including coefficients, fit measures, and significance tests."
    }

    timestamp: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        primary_key=True,
        comment="The timestamp of the provider asset group attributes",
    )
    provider_asset_group_id: Mapped[int] = mapped_column(
        ForeignKey("provider_asset_group.id"),
        nullable=False,
        primary_key=True,
        comment="The identifier of the provider asset group",
    )
    provider_asset_group: Mapped["ProviderAssetGroup"] = relationship(
        "ProviderAssetGroup"
    )
    lookback_window_seconds: Mapped[int] = mapped_column(
        nullable=False,
        primary_key=True,
        comment="The lookback window in seconds used for the calculation",
    )
    cointegration_p_value: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="The cointegration p-value for the asset group",
    )
    ou_mu: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="The mu parameter (speed of mean reversion) for the Ornstein-Uhlenbeck process: dX(t) = μ(θ - X(t))dt + σdW(t)",
    )
    ou_theta: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="The theta parameter (long-term mean) for the Ornstein-Uhlenbeck process: dX(t) = μ(θ - X(t))dt + σdW(t)",
    )
    ou_sigma: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="The sigma parameter (volatility) for the Ornstein-Uhlenbeck process: dX(t) = μ(θ - X(t))dt + σdW(t)",
    )
    linear_fit_alpha: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="The alpha parameter (intercept) for the linear fit equation to_asset_2 = alpha + beta * to_asset_1. The numbers correspond to the order in the asset group member table (to_asset_1 = to_asset_id with order of 1, to_asset_2 = to_asset_id with order of 2). From RollingOLS.params[-1, 0] when using sm.add_constant()",
    )
    linear_fit_beta: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="The beta parameter (slope) for the linear fit equation to_asset_2 = alpha + beta * to_asset_1. The numbers correspond to the order in the asset group member table (to_asset_1 = to_asset_id with order of 1, to_asset_2 = to_asset_id with order of 2). From RollingOLS.params[-1, 1] when using sm.add_constant()",
    )
    linear_fit_mse: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="The mean squared error (MSE) of the linear fit between to_asset_1 (independent variable) and to_asset_2 (dependent variable) in the asset group pair. The numbers correspond to the order in the asset group member table (to_asset_1 = to_asset_id with order of 1, to_asset_2 = to_asset_id with order of 2). From RollingOLS.mse_resid",
    )
    linear_fit_r_squared: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="The R-squared (coefficient of determination) of the linear fit, indicating the proportion of variance explained by the regression. From RollingOLS.rsquared",
    )
    linear_fit_r_squared_adj: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="The adjusted R-squared of the linear fit, accounting for the number of predictors. From RollingOLS.rsquared_adj",
    )

    def __repr__(self):
        return f"{ProviderAssetGroupAttribute.__name__}(timestamp={self.timestamp}, provider_asset_group_id={self.provider_asset_group_id})"


class Portfolio(Base):
    __tablename__ = "portfolio"
    __table_args__ = {
        "comment": "The portfolio, represents a collection of assets and their transactions for tracking investment strategies and performance."
    }

    id: Mapped[int] = mapped_column(
        primary_key=True, comment="The unique identifier of the portfolio"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="The name of the portfolio"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True, comment="The description of the portfolio"
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, comment="Whether the portfolio is active"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the creation of the portfolio",
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=False,
        server_onupdate=func.now(),
        server_default=func.now(),
        comment="The timestamp of the last update of the portfolio",
    )

    # Relationship to transactions
    transactions: Mapped[list["PortfolioTransaction"]] = relationship(
        "PortfolioTransaction", back_populates="portfolio"
    )

    def __repr__(self):
        return f"{Portfolio.__name__}({self.id}, {self.name})"


class TransactionType(Base):
    __tablename__ = "transaction_type"
    __table_args__ = {
        "comment": "The type of transaction, e.g. buy, sell, transfer, short, cover, etc."
    }

    id: Mapped[int] = mapped_column(
        primary_key=True, comment="The unique identifier of the transaction type"
    )
    symbol: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="The symbol of the transaction type, e.g. BUY, SELL, TRANSFER, SHORT, COVER, etc.",
        unique=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="The name of the transaction type, e.g. Buy, Sell, Transfer, Short, Cover, etc.",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="The description of the transaction type",
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, comment="Whether the transaction type is active"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the creation of the transaction type",
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=False,
        server_onupdate=func.now(),
        server_default=func.now(),
        comment="The timestamp of the last update of the transaction type",
    )

    def __repr__(self):
        return f"{TransactionType.__name__}({self.id}, {self.name})"


class PortfolioTransaction(Base):
    __tablename__ = "portfolio_transaction"
    __table_args__ = {
        "comment": "Represents individual portfolio transactions including buys, sells, and transfers. Used to track all asset movements within and between portfolios."
    }

    id: Mapped[int] = mapped_column(
        primary_key=True, comment="The unique identifier of the transaction"
    )
    timestamp: Mapped[datetime.datetime] = mapped_column(
        nullable=False, comment="The date and time when the transaction occurred"
    )
    transaction_type_id: Mapped[int] = mapped_column(
        ForeignKey("transaction_type.id"),
        nullable=False,
        comment="The identifier of the transaction type",
    )
    transaction_type: Mapped["TransactionType"] = relationship("TransactionType")
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolio.id"),
        nullable=False,
        comment="The identifier of the portfolio this transaction belongs to",
    )
    portfolio: Mapped["Portfolio"] = relationship(
        "Portfolio", back_populates="transactions"
    )
    from_asset_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("asset.id"),
        nullable=True,
        comment="The identifier of the source asset in the transaction (e.g., cash for buys, the asset being sold for sells)",
    )
    from_asset: Mapped[Optional["Asset"]] = relationship(
        "Asset", foreign_keys=[from_asset_id]
    )
    to_asset_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("asset.id"),
        nullable=True,
        comment="The identifier of the destination asset in the transaction (e.g., the asset being bought for buys, cash for sells)",
    )
    to_asset: Mapped[Optional["Asset"]] = relationship(
        "Asset", foreign_keys=[to_asset_id]
    )
    quantity: Mapped[float] = mapped_column(
        nullable=False, comment="The number of units/shares in the transaction"
    )
    price: Mapped[float] = mapped_column(
        nullable=False, comment="The price per unit at which the transaction occurred"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the creation of the transaction",
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=False,
        server_onupdate=func.now(),
        server_default=func.now(),
        comment="The timestamp of the last update of the transaction",
    )

    # Relationship to groups
    groups: Mapped[list["TransactionGroup"]] = relationship(
        "TransactionGroup",
        secondary="transaction_group_member",
        back_populates="transactions",
    )

    # Relationship to status history
    statuses: Mapped[list["TransactionStatus"]] = relationship(
        "TransactionStatus",
        back_populates="portfolio_transaction",
        order_by="TransactionStatus.timestamp.asc()",
    )

    def __repr__(self):
        return f"{PortfolioTransaction.__name__}(id={self.id}, timestamp={self.timestamp}, transaction_type={self.transaction_type}, portfolio_id={self.portfolio_id})"


class TransactionGroup(Base):
    __tablename__ = "transaction_group"
    __table_args__ = {
        "comment": "Groups related transactions together for market neutral and paired trading strategies. Used to link offsetting long and short positions."
    }

    id: Mapped[int] = mapped_column(
        primary_key=True, comment="The unique identifier of the transaction group"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp when this group was created",
    )

    # Relationship to transactions
    transactions: Mapped[list["PortfolioTransaction"]] = relationship(
        "PortfolioTransaction",
        secondary="transaction_group_member",
        back_populates="groups",
    )

    def __repr__(self):
        return f"{TransactionGroup.__name__}(id={self.id})"


class TransactionGroupMember(Base):
    __tablename__ = "transaction_group_member"
    __table_args__ = {
        "comment": "Junction table linking transactions to their groups. Enables many-to-many relationship between transactions and groups."
    }

    transaction_group_id: Mapped[int] = mapped_column(
        ForeignKey("transaction_group.id"),
        primary_key=True,
        nullable=False,
        comment="The identifier of the transaction group",
    )
    transaction_group: Mapped["TransactionGroup"] = relationship(
        "TransactionGroup", overlaps="transactions"
    )
    portfolio_transaction_id: Mapped[int] = mapped_column(
        ForeignKey("portfolio_transaction.id"),
        primary_key=True,
        nullable=False,
        comment="The identifier of the portfolio transaction",
    )
    portfolio_transaction: Mapped["PortfolioTransaction"] = relationship(
        "PortfolioTransaction", overlaps="groups"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the creation of the transaction group member",
    )

    def __repr__(self):
        return f"{TransactionGroupMember.__name__}(transaction_group_id={self.transaction_group_id}, portfolio_transaction_id={self.portfolio_transaction_id})"


class TransactionStatusType(Base):
    __tablename__ = "transaction_status_type"
    __table_args__ = {
        "comment": "The type of transaction status, e.g. Pending, Open, Closed, Cancelled, etc."
    }

    id: Mapped[int] = mapped_column(
        primary_key=True, comment="The unique identifier of the transaction status type"
    )
    symbol: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="The symbol of the transaction status type, e.g. PENDING, OPEN, CLOSED, CANCELLED, etc.",
        unique=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="The name of the transaction status type, e.g. Pending, Open, Closed, Cancelled, etc.",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="The description of the transaction status type",
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, comment="Whether the transaction status type is active"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the creation of the transaction status type",
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=False,
        server_onupdate=func.now(),
        server_default=func.now(),
        comment="The timestamp of the last update of the transaction status type",
    )

    def __repr__(self):
        return f"{TransactionStatusType.__name__}({self.id}, {self.name})"


class TransactionStatus(Base):
    __tablename__ = "transaction_status"
    __table_args__ = {
        "comment": "Time series table storing status updates for portfolio transactions. Tracks the status history of transactions over time, allowing for audit trails and status change monitoring."
    }

    timestamp: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        primary_key=True,
        comment="The timestamp when the status was recorded",
    )
    portfolio_transaction_id: Mapped[int] = mapped_column(
        ForeignKey("portfolio_transaction.id"),
        nullable=False,
        primary_key=True,
        comment="The identifier of the portfolio transaction",
    )
    portfolio_transaction: Mapped["PortfolioTransaction"] = relationship(
        "PortfolioTransaction", back_populates="statuses"
    )
    transaction_status_type_id: Mapped[int] = mapped_column(
        ForeignKey("transaction_status_type.id"),
        nullable=False,
        comment="The identifier of the transaction status type",
    )
    transaction_status_type: Mapped["TransactionStatusType"] = relationship(
        "TransactionStatusType"
    )

    def __repr__(self):
        return f"{TransactionStatus.__name__}(timestamp={self.timestamp}, portfolio_transaction_id={self.portfolio_transaction_id}, transaction_status_type_id={self.transaction_status_type_id})"
