import mcpdb.tables as tables
import pandas as pd
import pytest
from sqlalchemy import Engine
from typing import Generator, Literal
from unittest.mock import patch
from mcpdb.testing.mocks import MockDatabase

@pytest.fixture
def mock_database() -> Generator[MockDatabase, None, None]:
    """
    A fixture that returns a mock database for testing.
    """
    mock_database = MockDatabase()

    # Create a mock set_data function that uses the mock database.
    def mock_set_data(engine: Engine, table_name: str, data: pd.DataFrame, operation_type: Literal["insert", "append", "upsert"] = "upsert"):
        mock_database.set_data(table_name, data, operation_type)

    # Create a mock set_data function that uses the mock database.
    def mock_set_data_prefect(table_name: str, data: pd.DataFrame, operation_type: Literal["insert", "append", "upsert"] = "upsert"):
        mock_database.set_data(table_name, data, operation_type)
    
    # Create a mock set_data function that uses the mock database.
    async def mock_set_data_prefect_async(table_name: str, data: pd.DataFrame, operation_type: Literal["insert", "append", "upsert"] = "upsert"):
        mock_database.set_data(table_name, data, operation_type)

    # Patch the set_data methods to use the mock database
    with patch("mcpdb.utils.set_data", side_effect=mock_set_data):
        with patch("mcpdb.prefect.utils.set_data", side_effect=mock_set_data_prefect):
            with patch("mcpdb.prefect.asyncio.utils.set_data", side_effect=mock_set_data_prefect_async):
                yield mock_database

class MockDatabase:
    """
    A mock database for testing.

    This class is used to mock the database for testing. It is used to test the database operations without having to connect to a real database.

    Attributes:
        tables: A dictionary of tables in the database. The key is the name of the table and the value is a pandas DataFrame.
    """

    def __init__(self):
        # Initialize the database with an empty dataframe for each table. Make the tables have the correct columns and types.
        self.reset_database()
    
    def get_all_table_names(self) -> list[str]:
        """
        Get the names of all tables in the database.
        """
        # Return the names of all tables
        return list(self.tables.keys())
    
    def get_table(self, table_name: str) -> pd.DataFrame:
        """
        Get a table from the database.
        """
        # Check if the table exists
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")

        # Return the table
        return self.tables[table_name]

    def set_data(self, table_name: str, data: pd.DataFrame, operation_type: Literal["insert", "append", "upsert"] = "upsert"):
        """
        Set data in a table in the database.
        """
        # Check if the table exists
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")

        # Check if the data has the correct columns
        if not set(data.columns).issubset(set(self.tables[table_name].columns)):
            raise ValueError(f"Data has incorrect columns for table {table_name}")

        # Check if the data has the correct types
        for column in data.columns:
            if data[column].dtype != self.tables[table_name][column].dtype:
                raise ValueError(f"Data has incorrect types for column {column} in table {table_name}")
        
        # Set the data.
        if operation_type == "insert":
            self.tables[table_name] = pd.concat([self.tables[table_name], data]).groupby(self.tables[table_name].index, as_index=False).last()
        elif operation_type == "append":
            self.tables[table_name] = pd.concat([self.tables[table_name], data])
        elif operation_type == "upsert":
            self.tables[table_name] = pd.concat([self.tables[table_name], data]).groupby(self.tables[table_name].index, as_index=False).last()
    
    def set_table(self, table_name: str, data: pd.DataFrame):
        """
        Set a table in the database.
        """
        # Check if the table exists
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")

        # Check if the data has the correct columns
        if not set(data.columns).issubset(set(self.tables[table_name].columns)):
            raise ValueError(f"Data has incorrect columns for table {table_name}")

        # Check if the data has the correct types
        for column in data.columns:
            if data[column].dtype != self.tables[table_name][column].dtype:
                raise ValueError(f"Data has incorrect types for column {column} in table {table_name}")

        # Set the data
        self.tables[table_name] = data

    def append_table(self, table_name: str, data: pd.DataFrame):
        """
        Append data to a table in the database.
        """
        # Check if the table exists
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")

        # Check if the data has the correct columns
        if not set(data.columns).issubset(set(self.tables[table_name].columns)):
            raise ValueError(f"Data has incorrect columns for table {table_name}")

        # Check if the data has the correct types
        self.tables[table_name] = pd.concat([self.tables[table_name], data])

    def reset_database(self):
        """
        Reset the database to its initial state.
        """
        self.tables = {table.__tablename__: pd.DataFrame({
            column.key: pd.Series(dtype=column.type.python_type) for column in table.__table__.columns
        }).set_index([column.name for column in table.__table__.primary_key]) for table in tables.Base.__subclasses__()}