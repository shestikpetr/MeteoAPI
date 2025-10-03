"""
Database Management Service
Provides Django Admin-like interface for database tables
"""
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
import pymysql
from app.database.connection import DatabaseManager


class DatabaseService:
    """Service for generic database management operations"""

    # System tables to skip
    SYSTEM_TABLES = [
        'information_schema', 'mysql', 'performance_schema', 'sys',
        '__efmigrationshistory'
    ]

    # Table name validation pattern
    TABLE_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    COLUMN_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

    def __init__(self):
        self.local_db = DatabaseManager.get_local_db()

    def _validate_identifier(self, identifier: str, pattern: re.Pattern) -> bool:
        """Validate SQL identifier (table/column name) to prevent injection"""
        return pattern.match(identifier) is not None

    def _escape_identifier(self, identifier: str) -> str:
        """Escape SQL identifier with backticks"""
        # Remove any existing backticks
        identifier = identifier.replace('`', '')
        return f"`{identifier}`"

    def get_all_tables(self) -> List[Dict[str, Any]]:
        """Get all tables from local database with row counts"""
        tables = []

        # Get local database tables
        try:
            with self.local_db.cursor() as cursor:
                cursor.execute("""
                    SELECT TABLE_NAME, TABLE_ROWS, TABLE_COMMENT
                    FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                """)
                tables = [
                    {
                        'name': row['TABLE_NAME'],
                        'rows': row['TABLE_ROWS'] or 0,
                        'comment': row['TABLE_COMMENT'] or ''
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            print(f"Error fetching tables: {e}")

        return tables

    def get_table_schema(self, table_name: str, database: str = 'local') -> Dict[str, Any]:
        """Get detailed schema information for a table"""
        if not self._validate_identifier(table_name, self.TABLE_NAME_PATTERN):
            raise ValueError(f"Invalid table name: {table_name}")

        db = self.local_db

        schema = {
            'table_name': table_name,
            'database': 'local',
            'columns': [],
            'primary_keys': [],
            'foreign_keys': []
        }

        try:
            with db.cursor() as cursor:
                # Get column information
                cursor.execute(f"""
                    SELECT
                        COLUMN_NAME,
                        DATA_TYPE,
                        IS_NULLABLE,
                        COLUMN_KEY,
                        COLUMN_DEFAULT,
                        EXTRA,
                        CHARACTER_MAXIMUM_LENGTH,
                        NUMERIC_PRECISION,
                        COLUMN_COMMENT
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """, (table_name,))

                columns = cursor.fetchall()

                for col in columns:
                    column_info = {
                        'name': col['COLUMN_NAME'],
                        'type': col['DATA_TYPE'],
                        'nullable': col['IS_NULLABLE'] == 'YES',
                        'key': col['COLUMN_KEY'],
                        'default': col['COLUMN_DEFAULT'],
                        'extra': col['EXTRA'],
                        'max_length': col['CHARACTER_MAXIMUM_LENGTH'],
                        'precision': col['NUMERIC_PRECISION'],
                        'comment': col['COLUMN_COMMENT'] or ''
                    }

                    schema['columns'].append(column_info)

                    if col['COLUMN_KEY'] == 'PRI':
                        schema['primary_keys'].append(col['COLUMN_NAME'])

                # Get foreign key information
                cursor.execute(f"""
                    SELECT
                        COLUMN_NAME,
                        REFERENCED_TABLE_NAME,
                        REFERENCED_COLUMN_NAME,
                        CONSTRAINT_NAME
                    FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = %s
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                """, (table_name,))

                foreign_keys = cursor.fetchall()

                for fk in foreign_keys:
                    schema['foreign_keys'].append({
                        'column': fk['COLUMN_NAME'],
                        'referenced_table': fk['REFERENCED_TABLE_NAME'],
                        'referenced_column': fk['REFERENCED_COLUMN_NAME'],
                        'constraint_name': fk['CONSTRAINT_NAME']
                    })

        except Exception as e:
            raise Exception(f"Error fetching schema for {table_name}: {str(e)}")

        return schema

    def get_table_data(
        self,
        table_name: str,
        database: str = 'local',
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = 'ASC'
    ) -> Dict[str, Any]:
        """Get paginated data from a table with optional search and sorting"""
        if not self._validate_identifier(table_name, self.TABLE_NAME_PATTERN):
            raise ValueError(f"Invalid table name: {table_name}")

        db = self.local_db

        # Get table schema first
        schema = self.get_table_schema(table_name, 'local')

        # Validate sort column
        if sort_by and not self._validate_identifier(sort_by, self.COLUMN_NAME_PATTERN):
            sort_by = None

        # Validate sort order
        if sort_order.upper() not in ['ASC', 'DESC']:
            sort_order = 'ASC'

        offset = (page - 1) * page_size

        try:
            with db.cursor() as cursor:
                # Build query
                escaped_table = self._escape_identifier(table_name)

                # Build WHERE clause for search
                where_clause = ""
                params = []

                if search:
                    # Search across all text columns
                    text_columns = [
                        col['name'] for col in schema['columns']
                        if col['type'] in ['varchar', 'char', 'text', 'longtext', 'mediumtext', 'tinytext']
                    ]

                    if text_columns:
                        search_conditions = []
                        for col in text_columns:
                            escaped_col = self._escape_identifier(col)
                            search_conditions.append(f"{escaped_col} LIKE %s")
                            params.append(f"%{search}%")

                        where_clause = "WHERE " + " OR ".join(search_conditions)

                # Build ORDER BY clause
                order_clause = ""
                if sort_by:
                    escaped_sort = self._escape_identifier(sort_by)
                    order_clause = f"ORDER BY {escaped_sort} {sort_order}"
                elif schema['primary_keys']:
                    # Default sort by primary key
                    escaped_pk = self._escape_identifier(schema['primary_keys'][0])
                    order_clause = f"ORDER BY {escaped_pk} DESC"

                # Count total rows
                count_query = f"SELECT COUNT(*) as total FROM {escaped_table} {where_clause}"
                cursor.execute(count_query, params)
                total_rows = cursor.fetchone()['total']

                # Get data
                data_query = f"""
                    SELECT * FROM {escaped_table}
                    {where_clause}
                    {order_clause}
                    LIMIT %s OFFSET %s
                """
                cursor.execute(data_query, params + [page_size, offset])
                rows = cursor.fetchall()

                # Convert datetime and date objects to strings
                processed_rows = []
                for row in rows:
                    processed_row = {}
                    for key, value in row.items():
                        if isinstance(value, (datetime, date)):
                            processed_row[key] = value.isoformat()
                        elif value is None:
                            processed_row[key] = None
                        else:
                            processed_row[key] = value
                    processed_rows.append(processed_row)

                return {
                    'data': processed_rows,
                    'total': total_rows,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_rows + page_size - 1) // page_size,
                    'schema': schema
                }

        except Exception as e:
            raise Exception(f"Error fetching data from {table_name}: {str(e)}")

    def get_record_by_id(
        self,
        table_name: str,
        record_id: Any,
        database: str = 'local'
    ) -> Optional[Dict[str, Any]]:
        """Get a single record by primary key"""
        if not self._validate_identifier(table_name, self.TABLE_NAME_PATTERN):
            raise ValueError(f"Invalid table name: {table_name}")

        db = self.local_db
        schema = self.get_table_schema(table_name, 'local')

        if not schema['primary_keys']:
            raise ValueError(f"Table {table_name} has no primary key")

        pk_column = schema['primary_keys'][0]

        try:
            with db.cursor() as cursor:
                escaped_table = self._escape_identifier(table_name)
                escaped_pk = self._escape_identifier(pk_column)

                query = f"SELECT * FROM {escaped_table} WHERE {escaped_pk} = %s"
                cursor.execute(query, (record_id,))
                row = cursor.fetchone()

                if row:
                    # Convert datetime and date objects to strings
                    processed_row = {}
                    for key, value in row.items():
                        if isinstance(value, (datetime, date)):
                            processed_row[key] = value.isoformat()
                        elif value is None:
                            processed_row[key] = None
                        else:
                            processed_row[key] = value
                    return processed_row

                return None

        except Exception as e:
            raise Exception(f"Error fetching record from {table_name}: {str(e)}")

    def create_record(
        self,
        table_name: str,
        data: Dict[str, Any],
        database: str = 'local'
    ) -> Dict[str, Any]:
        """Create a new record in the table"""
        if not self._validate_identifier(table_name, self.TABLE_NAME_PATTERN):
            raise ValueError(f"Invalid table name: {table_name}")

        db = self.local_db
        schema = self.get_table_schema(table_name, 'local')

        # Validate all column names
        for col_name in data.keys():
            if not self._validate_identifier(col_name, self.COLUMN_NAME_PATTERN):
                raise ValueError(f"Invalid column name: {col_name}")

        try:
            with db.cursor() as cursor:
                # Filter out auto-increment columns
                columns = [
                    col['name'] for col in schema['columns']
                    if col['name'] in data and 'auto_increment' not in col['extra'].lower()
                ]

                values = [data[col] for col in columns]

                escaped_table = self._escape_identifier(table_name)
                escaped_columns = [self._escape_identifier(col) for col in columns]

                placeholders = ', '.join(['%s'] * len(columns))
                columns_str = ', '.join(escaped_columns)

                query = f"INSERT INTO {escaped_table} ({columns_str}) VALUES ({placeholders})"
                cursor.execute(query, values)

                # Get the inserted record ID
                if schema['primary_keys']:
                    new_id = cursor.lastrowid or data.get(schema['primary_keys'][0])
                    return self.get_record_by_id(table_name, new_id, 'local')

                return {"success": True, "message": "Record created"}

        except Exception as e:
            raise Exception(f"Error creating record in {table_name}: {str(e)}")

    def update_record(
        self,
        table_name: str,
        record_id: Any,
        data: Dict[str, Any],
        database: str = 'local'
    ) -> Dict[str, Any]:
        """Update an existing record"""
        if not self._validate_identifier(table_name, self.TABLE_NAME_PATTERN):
            raise ValueError(f"Invalid table name: {table_name}")

        db = self.local_db
        schema = self.get_table_schema(table_name, 'local')

        if not schema['primary_keys']:
            raise ValueError(f"Table {table_name} has no primary key")

        pk_column = schema['primary_keys'][0]

        # Validate all column names
        for col_name in data.keys():
            if not self._validate_identifier(col_name, self.COLUMN_NAME_PATTERN):
                raise ValueError(f"Invalid column name: {col_name}")

        try:
            with db.cursor() as cursor:
                # Filter out primary key and auto-increment columns
                columns = [
                    col['name'] for col in schema['columns']
                    if col['name'] in data
                    and col['name'] != pk_column
                    and 'auto_increment' not in col['extra'].lower()
                ]

                if not columns:
                    raise ValueError("No columns to update")

                values = [data[col] for col in columns]
                values.append(record_id)

                escaped_table = self._escape_identifier(table_name)
                escaped_pk = self._escape_identifier(pk_column)

                set_clause = ', '.join([
                    f"{self._escape_identifier(col)} = %s" for col in columns
                ])

                query = f"UPDATE {escaped_table} SET {set_clause} WHERE {escaped_pk} = %s"
                cursor.execute(query, values)

                return self.get_record_by_id(table_name, record_id, 'local')

        except Exception as e:
            raise Exception(f"Error updating record in {table_name}: {str(e)}")

    def delete_record(
        self,
        table_name: str,
        record_id: Any,
        database: str = 'local'
    ) -> Dict[str, Any]:
        """Delete a record from the table"""
        if not self._validate_identifier(table_name, self.TABLE_NAME_PATTERN):
            raise ValueError(f"Invalid table name: {table_name}")

        db = self.local_db
        schema = self.get_table_schema(table_name, 'local')

        if not schema['primary_keys']:
            raise ValueError(f"Table {table_name} has no primary key")

        pk_column = schema['primary_keys'][0]

        try:
            with db.cursor() as cursor:
                escaped_table = self._escape_identifier(table_name)
                escaped_pk = self._escape_identifier(pk_column)

                query = f"DELETE FROM {escaped_table} WHERE {escaped_pk} = %s"
                cursor.execute(query, (record_id,))

                return {
                    "success": True,
                    "message": f"Record {record_id} deleted from {table_name}"
                }

        except Exception as e:
            raise Exception(f"Error deleting record from {table_name}: {str(e)}")

    def get_foreign_key_options(
        self,
        table_name: str,
        column_name: str,
        database: str = 'local'
    ) -> List[Dict[str, Any]]:
        """Get options for a foreign key column"""
        schema = self.get_table_schema(table_name, 'local')

        # Find the foreign key relationship
        fk_info = None
        for fk in schema['foreign_keys']:
            if fk['column'] == column_name:
                fk_info = fk
                break

        if not fk_info:
            return []

        db = self.local_db

        try:
            with db.cursor() as cursor:
                ref_table = self._escape_identifier(fk_info['referenced_table'])
                ref_column = self._escape_identifier(fk_info['referenced_column'])

                # Try to find a display column (name, title, etc.)
                ref_schema = self.get_table_schema(fk_info['referenced_table'], 'local')
                display_columns = [
                    col['name'] for col in ref_schema['columns']
                    if col['name'] in ['name', 'title', 'username', 'email', 'code', 'station_number']
                ]

                if display_columns:
                    display_col = self._escape_identifier(display_columns[0])
                    query = f"SELECT {ref_column} as id, {display_col} as label FROM {ref_table} LIMIT 1000"
                else:
                    query = f"SELECT {ref_column} as id, {ref_column} as label FROM {ref_table} LIMIT 1000"

                cursor.execute(query)
                return [{'id': row['id'], 'label': str(row['label'])} for row in cursor.fetchall()]

        except Exception as e:
            print(f"Error fetching foreign key options: {e}")
            return []