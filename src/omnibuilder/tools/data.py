"""
P3.4 Data & Query Tools

Database and storage operations.
"""

from typing import Any, Dict, List, Optional
import json


class QueryResult:
    """Result of a database query."""
    def __init__(self, success: bool, rows: List[Dict], affected: int, message: str):
        self.success = success
        self.rows = rows
        self.affected = affected
        self.message = message


class VectorMatch:
    """A vector similarity search match."""
    def __init__(self, id: str, score: float, metadata: Dict[str, Any]):
        self.id = id
        self.score = score
        self.metadata = metadata


class InsertResult:
    """Result of an insert operation."""
    def __init__(self, success: bool, inserted_ids: List[Any], message: str):
        self.success = success
        self.inserted_ids = inserted_ids
        self.message = message


class TableSchema:
    """Schema definition for a table."""
    def __init__(self, name: str, columns: Dict[str, str], primary_key: str):
        self.name = name
        self.columns = columns  # {"column_name": "type"}
        self.primary_key = primary_key


class BackupResult:
    """Result of a backup operation."""
    def __init__(self, success: bool, path: str, size: int, message: str):
        self.success = success
        self.path = path
        self.size = size
        self.message = message


class DataQueryTools:
    """Database and data query operations."""

    def __init__(self):
        self._connections: Dict[str, Any] = {}

    async def query_sql(
        self,
        connection: str,
        query: str,
        params: Optional[List] = None
    ) -> QueryResult:
        """
        Execute SQL query.

        Args:
            connection: Connection string
            query: SQL query
            params: Query parameters
        """
        try:
            import aiosqlite

            # Simple SQLite support
            if connection.endswith('.db') or connection.endswith('.sqlite'):
                async with aiosqlite.connect(connection) as db:
                    db.row_factory = aiosqlite.Row
                    cursor = await db.execute(query, params or [])

                    if query.strip().upper().startswith('SELECT'):
                        rows = await cursor.fetchall()
                        return QueryResult(
                            success=True,
                            rows=[dict(row) for row in rows],
                            affected=0,
                            message=f"Fetched {len(rows)} rows"
                        )
                    else:
                        await db.commit()
                        return QueryResult(
                            success=True,
                            rows=[],
                            affected=cursor.rowcount,
                            message=f"Affected {cursor.rowcount} rows"
                        )

            return QueryResult(
                success=False,
                rows=[],
                affected=0,
                message="Unsupported database connection"
            )

        except ImportError:
            return QueryResult(
                success=False,
                rows=[],
                affected=0,
                message="aiosqlite not installed"
            )
        except Exception as e:
            return QueryResult(
                success=False,
                rows=[],
                affected=0,
                message=str(e)
            )

    async def query_vector_db(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int = 5
    ) -> List[VectorMatch]:
        """
        Vector similarity search.

        Args:
            collection: Collection name
            query_vector: Query embedding
            top_k: Number of results
        """
        try:
            import chromadb

            client = chromadb.Client()
            coll = client.get_or_create_collection(collection)

            results = coll.query(
                query_embeddings=[query_vector],
                n_results=top_k
            )

            matches = []
            for i, id in enumerate(results['ids'][0]):
                matches.append(VectorMatch(
                    id=id,
                    score=results['distances'][0][i] if results.get('distances') else 0,
                    metadata=results['metadatas'][0][i] if results.get('metadatas') else {}
                ))

            return matches

        except ImportError:
            return []
        except Exception:
            return []

    async def insert_data(
        self,
        connection: str,
        table: str,
        data: List[Dict]
    ) -> InsertResult:
        """
        Insert records into database.

        Args:
            connection: Connection string
            table: Table name
            data: List of records to insert
        """
        if not data:
            return InsertResult(True, [], "No data to insert")

        try:
            import aiosqlite

            if connection.endswith('.db') or connection.endswith('.sqlite'):
                async with aiosqlite.connect(connection) as db:
                    inserted_ids = []

                    for record in data:
                        columns = ', '.join(record.keys())
                        placeholders = ', '.join(['?' for _ in record])
                        values = list(record.values())

                        cursor = await db.execute(
                            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                            values
                        )
                        inserted_ids.append(cursor.lastrowid)

                    await db.commit()

                    return InsertResult(
                        success=True,
                        inserted_ids=inserted_ids,
                        message=f"Inserted {len(data)} records"
                    )

            return InsertResult(False, [], "Unsupported database")

        except Exception as e:
            return InsertResult(False, [], str(e))

    async def create_table(
        self,
        connection: str,
        schema: TableSchema
    ) -> bool:
        """
        Create a database table.

        Args:
            connection: Connection string
            schema: Table schema
        """
        try:
            import aiosqlite

            if connection.endswith('.db') or connection.endswith('.sqlite'):
                columns = []
                for col_name, col_type in schema.columns.items():
                    col_def = f"{col_name} {col_type}"
                    if col_name == schema.primary_key:
                        col_def += " PRIMARY KEY"
                    columns.append(col_def)

                query = f"CREATE TABLE IF NOT EXISTS {schema.name} ({', '.join(columns)})"

                async with aiosqlite.connect(connection) as db:
                    await db.execute(query)
                    await db.commit()
                    return True

            return False

        except Exception:
            return False

    async def backup_database(
        self,
        connection: str,
        dest: str
    ) -> BackupResult:
        """
        Backup database to file.

        Args:
            connection: Source database
            dest: Destination path
        """
        import shutil
        import os

        try:
            if connection.endswith('.db') or connection.endswith('.sqlite'):
                shutil.copy2(connection, dest)
                size = os.path.getsize(dest)

                return BackupResult(
                    success=True,
                    path=dest,
                    size=size,
                    message="Backup completed"
                )

            return BackupResult(False, dest, 0, "Unsupported database type")

        except Exception as e:
            return BackupResult(False, dest, 0, str(e))

    def read_csv(
        self,
        path: str,
        options: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Read CSV file into list of dictionaries.

        Args:
            path: CSV file path
            options: Read options
        """
        import csv

        opts = options or {}
        delimiter = opts.get('delimiter', ',')
        encoding = opts.get('encoding', 'utf-8')

        with open(path, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            return list(reader)

    def write_csv(
        self,
        data: List[Dict],
        path: str,
        options: Optional[Dict] = None
    ) -> bool:
        """
        Write data to CSV file.

        Args:
            data: List of dictionaries
            path: Output path
            options: Write options
        """
        if not data:
            return False

        import csv

        opts = options or {}
        delimiter = opts.get('delimiter', ',')
        encoding = opts.get('encoding', 'utf-8')

        with open(path, 'w', encoding=encoding, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys(), delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)

        return True

    def read_json(self, path: str) -> Any:
        """Read JSON file."""
        with open(path, 'r') as f:
            return json.load(f)

    def write_json(self, data: Any, path: str, indent: int = 2) -> bool:
        """Write data to JSON file."""
        with open(path, 'w') as f:
            json.dump(data, f, indent=indent, default=str)
        return True
