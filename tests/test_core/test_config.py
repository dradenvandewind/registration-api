# tests/test_core/test_config.py
import os
import pytest
from unittest.mock import patch
from app.core.config import Settings

class TestSettingsDatabaseUrl:
    """Tests for database_url_property (lines 22-24)"""
    
    def test_database_url_property_default_main_env(self):
        """
        Test database_url_property in main environment (not test)
        Covers lines 22-24 with default values
        """
        # Clear environment variables that might affect the test
        with patch.dict(os.environ, {}, clear=True):
            # Create settings instance
            settings = Settings()
            
            # Access the property
            url = settings.database_url_property
            
            # Verify
            assert url == "postgresql://user:pass@localhost:5432/main_db"
            print("✅ database_url_property returns main DB URL in default environment")

    def test_database_url_property_with_custom_main_env(self):
        """
        Test database_url_property with custom DATABASE_URL in main environment
        Covers lines 22-24 with custom value
        """
        custom_url = "postgresql://custom:custom@customhost:5432/custom_db"
        
        with patch.dict(os.environ, {"DATABASE_URL": custom_url}, clear=True):
            settings = Settings()
            url = settings.database_url_property
            
            assert url == custom_url
            print("✅ database_url_property returns custom DATABASE_URL when provided")

    def test_database_url_property_test_environment_default(self):
        """
        Test database_url_property in test environment with default TEST_DATABASE_URL
        Covers lines 22-24 with test environment
        """
        with patch.dict(os.environ, {"ENVIRONMENT": "test"}, clear=True):
            settings = Settings()
            url = settings.database_url_property
            
            assert url == "postgresql://user:pass@localhost:5432/test_db"
            print("✅ database_url_property returns test DB URL in test environment")

    def test_database_url_property_test_environment_custom(self):
        """
        Test database_url_property in test environment with custom TEST_DATABASE_URL
        Covers lines 22-24 with custom test URL
        """
        custom_test_url = "postgresql://test:test@testhost:5432/test_custom_db"
        
        with patch.dict(os.environ, {
            "ENVIRONMENT": "test",
            "TEST_DATABASE_URL": custom_test_url
        }, clear=True):
            settings = Settings()
            url = settings.database_url_property
            
            assert url == custom_test_url
            print("✅ database_url_property returns custom TEST_DATABASE_URL in test environment")

    def test_database_url_property_with_both_env_vars_main_env(self):
        """
        Test database_url_property when both DATABASE_URL and TEST_DATABASE_URL are set but ENVIRONMENT is not test
        Should use DATABASE_URL
        Covers lines 22-24
        """
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql://main:main@mainhost:5432/main_db",
            "TEST_DATABASE_URL": "postgresql://test:test@testhost:5432/test_db"
        }, clear=True):
            settings = Settings()
            url = settings.database_url_property
            
            assert url == "postgresql://main:main@mainhost:5432/main_db"
            print("✅ database_url_property uses DATABASE_URL when ENVIRONMENT is not test")

    def test_database_url_property_with_both_env_vars_test_env(self):
        """
        Test database_url_property when both DATABASE_URL and TEST_DATABASE_URL are set and ENVIRONMENT is test
        Should use TEST_DATABASE_URL
        Covers lines 22-24
        """
        with patch.dict(os.environ, {
            "ENVIRONMENT": "test",
            "DATABASE_URL": "postgresql://main:main@mainhost:5432/main_db",
            "TEST_DATABASE_URL": "postgresql://test:test@testhost:5432/test_db"
        }, clear=True):
            settings = Settings()
            url = settings.database_url_property
            
            assert url == "postgresql://test:test@testhost:5432/test_db"
            print("✅ database_url_property uses TEST_DATABASE_URL when ENVIRONMENT is test")

    def test_database_url_property_missing_env_vars(self):
        """
        Test database_url_property when no environment variables are set
        Should fall back to defaults
        Covers lines 22-24
        """
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            url = settings.database_url_property
            
            assert url == "postgresql://user:pass@localhost:5432/main_db"
            print("✅ database_url_property falls back to defaults when no env vars set")

    def test_database_url_property_test_env_missing_test_url(self):
        """
        Test database_url_property in test environment when TEST_DATABASE_URL is not set
        Should fall back to default test URL
        Covers lines 22-24
        """
        with patch.dict(os.environ, {"ENVIRONMENT": "test"}, clear=True):
            settings = Settings()
            url = settings.database_url_property
            
            assert url == "postgresql://user:pass@localhost:5432/test_db"
            print("✅ database_url_property falls back to default test URL when TEST_DATABASE_URL not set")

    def test_database_url_property_with_empty_env_vars(self):
        """
        Test database_url_property with empty string environment variables
        Covers lines 22-24
        """
        with patch.dict(os.environ, {
            "ENVIRONMENT": "test",
            "TEST_DATABASE_URL": ""
        }, clear=True):
            settings = Settings()
            url = settings.database_url_property
            
            # Empty string is considered a value, so it will return empty string
            assert url == ""
            print("✅ database_url_property handles empty environment variables")