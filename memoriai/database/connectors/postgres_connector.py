"""
PostgreSQL connector for Memori v1.0
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from ...utils.exceptions import DatabaseError


class PostgreSQLConnector:
    """PostgreSQL database connector"""

    def __init__(self, connection_string: str):
        """Initialize PostgreSQL connector"""
        self.connection_string = connection_string
        self._psycopg2 = None
        self._setup_psycopg2()

    def _setup_psycopg2(self):
        """Setup psycopg2 connection"""
        try:
            import psycopg2
            import psycopg2.extras

            self._psycopg2 = psycopg2
            self._extras = psycopg2.extras
        except ImportError:
            raise DatabaseError(
                "psycopg2 is required for PostgreSQL support. "
                "Install it with: pip install psycopg2-binary"
            )

    def get_connection(self):
        """Get PostgreSQL connection"""
        try:
            conn = self._psycopg2.connect(
                self.connection_string, cursor_factory=self._extras.RealDictCursor
            )
            conn.autocommit = False
            return conn

        except Exception as e:
            raise DatabaseError(f"Failed to connect to PostgreSQL database: {e}")

    def execute_query(
        self, query: str, params: Optional[List] = None
    ) -> List[Dict[str, Any]]:
        """Execute a query and return results"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)

                    # Return results as list of dictionaries
                    results = []
                    for row in cursor.fetchall():
                        results.append(dict(row))

                    return results

        except Exception as e:
            raise DatabaseError(f"Failed to execute query: {e}")

    def execute_insert(self, query: str, params: Optional[List] = None) -> str:
        """Execute an insert query and return the inserted row ID"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)

                    # Try to get the inserted ID
                    inserted_id = None
                    if cursor.rowcount > 0:
                        try:
                            # For PostgreSQL, we need RETURNING clause for ID
                            inserted_id = cursor.fetchone()
                            if inserted_id and hasattr(inserted_id, "values"):
                                inserted_id = str(list(inserted_id.values())[0])
                            else:
                                inserted_id = str(cursor.rowcount)
                        except Exception:
                            inserted_id = str(cursor.rowcount)

                    conn.commit()
                    return inserted_id or "0"

        except Exception as e:
            raise DatabaseError(f"Failed to execute insert: {e}")

    def execute_update(self, query: str, params: Optional[List] = None) -> int:
        """Execute an update query and return number of affected rows"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)

                    conn.commit()
                    return cursor.rowcount

        except Exception as e:
            raise DatabaseError(f"Failed to execute update: {e}")

    def execute_delete(self, query: str, params: Optional[List] = None) -> int:
        """Execute a delete query and return number of affected rows"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)

                    conn.commit()
                    return cursor.rowcount

        except Exception as e:
            raise DatabaseError(f"Failed to execute delete: {e}")

    def execute_transaction(self, queries: List[tuple]) -> bool:
        """Execute multiple queries in a transaction"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:

                    for query, params in queries:
                        if params:
                            cursor.execute(query, params)
                        else:
                            cursor.execute(query)

                    conn.commit()
                    return True

        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            return False

    def test_connection(self) -> bool:
        """Test if the database connection is working"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
