"""
Improved database connection manager with connection pooling
Provides significant performance improvements over single connection approach
"""
import pymysql
import queue
import threading
import time
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any
from app.config import Config

logger = logging.getLogger(__name__)


class ConnectionPool:
    """Thread-safe MySQL connection pool"""

    def __init__(self, config: Dict[str, Any],
                 min_connections: int = 5,
                 max_connections: int = 20,
                 max_idle_time: int = 3600,
                 connect_timeout: int = 30):
        """
        Initialize connection pool

        Args:
            config: Database connection configuration
            min_connections: Minimum number of connections to maintain
            max_connections: Maximum number of connections allowed
            max_idle_time: Maximum time (seconds) a connection can be idle
            connect_timeout: Connection timeout in seconds
        """
        self.config = config
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        self.connect_timeout = connect_timeout

        # Thread-safe queue for available connections
        self._pool = queue.Queue(maxsize=max_connections)

        # Track active connections and creation times
        self._active_connections = 0
        self._connection_times = {}

        # Thread safety
        self._lock = threading.RLock()

        # Pool state
        self._closed = False

        # Initialize minimum connections
        self._initialize_pool()

    def _create_connection(self) -> pymysql.Connection:
        """Create a new database connection"""
        try:
            connection = pymysql.connect(
                host=self.config['host'],
                port=self.config.get('port', 3306),
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=self.connect_timeout,
                read_timeout=30,
                write_timeout=30,
                autocommit=False
            )

            # Store creation time for idle tracking
            self._connection_times[id(connection)] = time.time()

            logger.debug(f"Created new database connection to {self.config['host']}")
            return connection

        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            raise

    def _initialize_pool(self):
        """Initialize pool with minimum connections"""
        with self._lock:
            for _ in range(self.min_connections):
                try:
                    connection = self._create_connection()
                    self._pool.put(connection, block=False)
                    self._active_connections += 1
                except Exception as e:
                    logger.warning(f"Failed to initialize connection in pool: {e}")

    def _is_connection_valid(self, connection: pymysql.Connection) -> bool:
        """Check if connection is still valid"""
        try:
            # Check if connection is open
            if not connection.open:
                return False

            # Ping the connection
            connection.ping(reconnect=False)

            # Check if connection has been idle too long
            conn_id = id(connection)
            if conn_id in self._connection_times:
                idle_time = time.time() - self._connection_times[conn_id]
                if idle_time > self.max_idle_time:
                    logger.debug(f"Connection {conn_id} idle for {idle_time}s, marking invalid")
                    return False

            return True

        except Exception as e:
            logger.debug(f"Connection validation failed: {e}")
            return False

    def _close_connection(self, connection: pymysql.Connection):
        """Safely close a connection"""
        try:
            conn_id = id(connection)
            if conn_id in self._connection_times:
                del self._connection_times[conn_id]

            if connection.open:
                connection.close()

        except Exception as e:
            logger.debug(f"Error closing connection: {e}")

    def get_connection(self, timeout: int = 30) -> pymysql.Connection:
        """
        Get a connection from the pool

        Args:
            timeout: Maximum time to wait for a connection

        Returns:
            A valid database connection

        Raises:
            Exception: If no connection available within timeout
        """
        if self._closed:
            raise RuntimeError("Connection pool is closed")

        start_time = time.time()

        while time.time() - start_time < timeout:
            # Try to get existing connection from pool
            try:
                connection = self._pool.get(block=False)

                # Validate connection
                if self._is_connection_valid(connection):
                    # Update last used time
                    self._connection_times[id(connection)] = time.time()
                    return connection
                else:
                    # Connection is invalid, close it and try again
                    with self._lock:
                        self._active_connections -= 1
                    self._close_connection(connection)
                    continue

            except queue.Empty:
                # Pool is empty, try to create new connection
                with self._lock:
                    if self._active_connections < self.max_connections:
                        try:
                            connection = self._create_connection()
                            self._active_connections += 1
                            return connection
                        except Exception as e:
                            logger.error(f"Failed to create new connection: {e}")
                            time.sleep(0.1)  # Brief pause before retry
                            continue
                    else:
                        # Pool is at max capacity, wait a bit
                        time.sleep(0.1)
                        continue

        raise TimeoutError(f"Could not get database connection within {timeout} seconds")

    def return_connection(self, connection: pymysql.Connection):
        """Return a connection to the pool"""
        if self._closed:
            self._close_connection(connection)
            return

        # Validate connection before returning
        if self._is_connection_valid(connection):
            try:
                # Reset connection state
                if connection.open:
                    connection.rollback()  # Rollback any uncommitted transactions

                self._pool.put(connection, block=False)
                logger.debug("Connection returned to pool")
            except queue.Full:
                # Pool is full, close this connection
                with self._lock:
                    self._active_connections -= 1
                self._close_connection(connection)
                logger.debug("Pool full, closed returned connection")
        else:
            # Connection is invalid, close it
            with self._lock:
                self._active_connections -= 1
            self._close_connection(connection)
            logger.debug("Invalid connection closed instead of returned")

    def close_all(self):
        """Close all connections and shutdown pool"""
        logger.info("Closing connection pool...")

        with self._lock:
            self._closed = True

            # Close all connections in pool
            while not self._pool.empty():
                try:
                    connection = self._pool.get(block=False)
                    self._close_connection(connection)
                except queue.Empty:
                    break

            self._active_connections = 0
            self._connection_times.clear()

        logger.info("Connection pool closed")

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self._lock:
            return {
                'active_connections': self._active_connections,
                'available_connections': self._pool.qsize(),
                'max_connections': self.max_connections,
                'min_connections': self.min_connections,
                'pool_closed': self._closed
            }


class PooledDatabaseConnection:
    """Database connection manager with connection pooling"""

    def __init__(self, config: Dict[str, Any], **pool_kwargs):
        """
        Initialize pooled database connection

        Args:
            config: Database connection configuration
            **pool_kwargs: Additional arguments for ConnectionPool
        """
        self.config = config
        self._pool = ConnectionPool(config, **pool_kwargs)

        logger.info(f"Initialized pooled database connection to {config['host']}")

    @contextmanager
    def cursor(self):
        """Context manager for database cursor with automatic connection management"""
        connection = None
        try:
            # Get connection from pool
            connection = self._pool.get_connection()
            cursor = connection.cursor()

            try:
                yield cursor
                connection.commit()
            except Exception as e:
                connection.rollback()
                raise e
            finally:
                cursor.close()

        finally:
            # Always return connection to pool
            if connection:
                self._pool.return_connection(connection)

    def execute_query(self, query: str, params=None):
        """Execute a query and return results"""
        with self.cursor() as cursor:
            cursor.execute(query, params)
            if cursor.description:
                return cursor.fetchall()
            return cursor.rowcount

    def close(self):
        """Close the connection pool"""
        self._pool.close_all()

    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return self._pool.get_stats()


class PooledDatabaseManager:
    """Enhanced database manager with connection pooling"""

    _instances = {}
    _lock = threading.RLock()

    @classmethod
    def get_local_db(cls) -> PooledDatabaseConnection:
        """Get local database with connection pooling"""
        with cls._lock:
            if 'local' not in cls._instances:
                cls._instances['local'] = PooledDatabaseConnection({
                    'host': Config.LOCAL_DB_HOST,
                    'port': Config.LOCAL_DB_PORT,
                    'user': Config.LOCAL_DB_USER,
                    'password': Config.LOCAL_DB_PASSWORD,
                    'database': Config.LOCAL_DB_NAME
                }, min_connections=3, max_connections=15)

            return cls._instances['local']

    @classmethod
    def get_sensor_db(cls) -> PooledDatabaseConnection:
        """Get sensor database with connection pooling"""
        with cls._lock:
            if 'sensor' not in cls._instances:
                cls._instances['sensor'] = PooledDatabaseConnection({
                    'host': Config.SENSOR_DB_HOST,
                    'port': Config.SENSOR_DB_PORT,
                    'user': Config.SENSOR_DB_USER,
                    'password': Config.SENSOR_DB_PASSWORD,
                    'database': Config.SENSOR_DB_NAME
                }, min_connections=2, max_connections=10)

            return cls._instances['sensor']

    @classmethod
    def close_all(cls):
        """Close all database pools"""
        with cls._lock:
            for name, instance in cls._instances.items():
                logger.info(f"Closing {name} database pool")
                instance.close()
            cls._instances.clear()

    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all database pools"""
        with cls._lock:
            return {name: instance.get_stats()
                   for name, instance in cls._instances.items()}