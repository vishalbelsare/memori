"""
MySQL connector for Memori v1.0
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from ...utils.exceptions import DatabaseError


class MySQLConnector:
    """MySQL database connector"""

    def __init__(self, connection_config: Dict[str, str]):
        """Initialize MySQL connector"""
        self.connection_config = connection_config
        self._mysql = None
        self._setup_mysql()

    def _setup_mysql(self):
        """Setup MySQL connection library"""
        try:
            import mysql.connector

            self._mysql = mysql.connector
        except ImportError:
            raise DatabaseError(
                "mysql-connector-python is required for MySQL support. "
                "Install it with: pip install mysql-connector-python"
            )

    def get_connection(self):
        """Get MySQL connection"""
        try:
            conn = self._mysql.connect(**self.connection_config)
            return conn

        except Exception as e:
            raise DatabaseError(f"Failed to connect to MySQL database: {e}")

    def execute_query(
        self, query: str, params: Optional[List] = None
    ) -> List[Dict[str, Any]]:
        """Execute a query and return results"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                results = cursor.fetchall()
                cursor.close()

                return results

        except Exception as e:
            raise DatabaseError(f"Failed to execute query: {e}")

    def execute_insert(self, query: str, params: Optional[List] = None) -> str:
        """Execute an insert query and return the inserted row ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                conn.commit()
                inserted_id = str(cursor.lastrowid)
                cursor.close()

                return inserted_id

        except Exception as e:
            raise DatabaseError(f"Failed to execute insert: {e}")

    def execute_update(self, query: str, params: Optional[List] = None) -> int:
        """Execute an update query and return number of affected rows"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                conn.commit()
                affected_rows = cursor.rowcount
                cursor.close()

                return affected_rows

        except Exception as e:
            raise DatabaseError(f"Failed to execute update: {e}")

    def execute_delete(self, query: str, params: Optional[List] = None) -> int:
        """Execute a delete query and return number of affected rows"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                conn.commit()
                affected_rows = cursor.rowcount
                cursor.close()

                return affected_rows

        except Exception as e:
            raise DatabaseError(f"Failed to execute delete: {e}")

    def execute_transaction(self, queries: List[tuple]) -> bool:
        """Execute multiple queries in a transaction"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                try:
                    for query, params in queries:
                        if params:
                            cursor.execute(query, params)
                        else:
                            cursor.execute(query)

                    conn.commit()
                    cursor.close()
                    return True

                except Exception as e:
                    conn.rollback()
                    cursor.close()
                    raise e

        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            return False

    def test_connection(self) -> bool:
        """Test if the database connection is working"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
