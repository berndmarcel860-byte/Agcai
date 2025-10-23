"""
Database connection and session management
"""
import mysql.connector
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from loguru import logger
from typing import Generator

from .models import Base
from .schema import CREATE_TABLES_SQL


class Database:
    """Database connection manager"""
    
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.engine = None
        self.session_factory = None
        
    def connect(self):
        """Initialize database connection"""
        try:
            # Create database if it doesn't exist
            self._create_database_if_not_exists()
            
            # Create SQLAlchemy engine
            connection_string = f"mysql+mysqlconnector://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
            self.engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            # Create session factory
            self.session_factory = scoped_session(
                sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
            )
            
            logger.info(f"Database connection established to {self.host}:{self.port}/{self.database}")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    def _create_database_if_not_exists(self):
        """Create database if it doesn't exist"""
        try:
            conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.close()
            conn.close()
            logger.info(f"Database {self.database} created or already exists")
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            raise
            
    def initialize_schema(self):
        """Create all tables"""
        try:
            # Create tables using SQLAlchemy
            Base.metadata.create_all(self.engine)
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise
            
    @contextmanager
    def get_session(self) -> Generator:
        """Get database session context manager"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
            
    def close(self):
        """Close database connection"""
        if self.session_factory:
            self.session_factory.remove()
        if self.engine:
            self.engine.dispose()
        logger.info("Database connection closed")
