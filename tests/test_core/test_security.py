# tests/test_core/test_security.py
import pytest
import logging
from unittest.mock import patch, MagicMock, ANY
from app.core.security import (
    PasswordHandler,
    password_handler,
    verify_password,
    get_password_hash,
    generate_activation_code
)

class TestPasswordHandler:
    """Tests for PasswordHandler class"""
    
    def test_hash_password_success(self):
        """Test successful password hashing"""
        password = "secure_password123"
        
        # Execute
        hashed = PasswordHandler.hash_password(password)
        
        # Verify
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash identifier
        
        # Verify the hash can be verified
        assert PasswordHandler.verify_password(password, hashed) is True
        
        print("✅ hash_password - success")
    
    def test_hash_password_with_long_password(self):
        """
        Test hashing a password longer than 72 bytes
        Covers line 47-48 (truncation warning and logic)
        """
        # Create a password longer than 72 bytes
        long_password = "a" * 100  # 100 characters > 72 bytes
        
        with patch('app.core.security.logger.warning') as mock_warning:
            # Execute
            hashed = PasswordHandler.hash_password(long_password)
            
            # Verify warning was logged (line 47-48)
            mock_warning.assert_called_once_with(
                "Password too long, truncating to 72 bytes"
            )
            
            # ✅ CORRECTION: Use truncated password for verification
            truncated_password = long_password[:72]  # bcrypt only uses first 72 bytes
            assert PasswordHandler.verify_password(truncated_password, hashed) is True
            
            # Original long password will fail verification (expected)
            assert PasswordHandler.verify_password(long_password, hashed) is False
            
            print("✅ hash_password - long password truncation (lines 47-48)")
    
    def test_hash_password_exception_handling(self):
        """Test exception handling in hash_password
        Covers line 48 (exception raising)
        """
        # Mock bcrypt to raise an exception
        with patch('bcrypt.gensalt', side_effect=Exception("BCrypt error")):
            with pytest.raises(Exception) as exc_info:
                PasswordHandler.hash_password("password")
            
            assert "BCrypt error" in str(exc_info.value)
            print("✅ hash_password - exception propagation")
    
    def test_verify_password_success(self):
        """Test successful password verification"""
        password = "test_password"
        hashed = PasswordHandler.hash_password(password)
        
        # Execute
        result = PasswordHandler.verify_password(password, hashed)
        
        # Verify
        assert result is True
        print("✅ verify_password - success")
    
    def test_verify_password_wrong_password(self):
        """Test verification with wrong password"""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = PasswordHandler.hash_password(password)
        
        # Execute
        result = PasswordHandler.verify_password(wrong_password, hashed)
        
        # Verify
        assert result is False
        print("✅ verify_password - wrong password returns False")
    
    def test_verify_password_exception_handling(self):
        """Test exception handling in verify_password
        Covers line 59 (return False on exception)
        """
        # Mock bcrypt.checkpw to raise an exception
        with patch('bcrypt.checkpw', side_effect=Exception("Verification error")):
            # Execute
            result = PasswordHandler.verify_password("pass", "hash")
            
            # Verify returns False (line 59)
            assert result is False
            
            print("✅ verify_password - exception returns False (line 59)")
    
    def test_verify_password_invalid_hash(self):
        """Test verification with invalid hash format
        Covers line 59 (exception handling)
        """
        # Execute with invalid hash
        result = PasswordHandler.verify_password("password", "invalid_hash")
        
        # Should return False due to exception
        assert result is False
        
        print("✅ verify_password - invalid hash returns False")

class TestWrapperFunctions:
    """Tests for wrapper functions"""
    
    def test_verify_password_wrapper(self):
        """Test verify_password wrapper function
        Covers line 57-58 (wrapper function)
        """
        password = "test_password"
        hashed = get_password_hash(password)
        
        # Execute wrapper
        result = verify_password(password, hashed)
        
        # Verify
        assert result is True
        # ✅ CORRECTION: Verify the wrapper calls the handler correctly
        assert result == password_handler.verify_password(password, hashed)
        
        print("✅ verify_password wrapper (lines 57-58)")
    
    def test_get_password_hash_wrapper(self):
        """
        Test get_password_hash wrapper function
        Covers line 57-58 (wrapper function)
        
        Note: Two hashes of the same password will be different due to random salt,
        so we verify that the hash can be verified instead of comparing directly.
        """
        password = "test_password"
        
        # Execute wrapper
        hashed_wrapper = get_password_hash(password)
        
        # ✅ CORRECTION: Don't compare hashes directly
        assert isinstance(hashed_wrapper, str)
        assert len(hashed_wrapper) > 0
        assert hashed_wrapper.startswith("$2b$")
        
        # Verify that the wrapper hash works with verification
        assert verify_password(password, hashed_wrapper) is True
        
        # Verify that the wrapper calls the handler correctly
        # We can't test equality, but we can test that the handler produces a valid hash
        hashed_direct = password_handler.hash_password(password)
        assert isinstance(hashed_direct, str)
        assert hashed_direct.startswith("$2b$")
        assert verify_password(password, hashed_direct) is True
        
        print("✅ get_password_hash wrapper (lines 57-58)")
    
    def test_wrappers_compatibility(self):
        """Test that wrappers maintain compatibility
        Covers lines 57-58
        """
        password = "compatibility_test"
        
        # Hash with wrapper
        hashed_wrapper = get_password_hash(password)
        
        # Both should verify correctly
        assert verify_password(password, hashed_wrapper) is True
        assert password_handler.verify_password(password, hashed_wrapper) is True
        
        print("✅ wrappers maintain compatibility")

class TestGenerateActivationCode:
    """Tests for generate_activation_code function"""
    
    def test_generate_activation_code_default_length(self):
        """Test code generation with default length (6)
        Covers lines 72-74
        """
        # Execute
        code = generate_activation_code()
        
        # Verify
        assert isinstance(code, str)
        assert len(code) == 6  # default length
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" for c in code)
        
        print("✅ generate_activation_code - default length 6 (lines 72-74)")
    
    def test_generate_activation_code_custom_length(self):
        """Test code generation with custom length
        Covers lines 72-74
        """
        custom_length = 4
        
        # Execute
        code = generate_activation_code(length=custom_length)
        
        # Verify
        assert len(code) == custom_length
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" for c in code)
        
        print(f"✅ generate_activation_code - custom length {custom_length}")
    
    def test_generate_activation_code_different_lengths(self):
        """Test code generation with various lengths
        Covers lines 72-74 for different inputs
        """
        for length in [4, 6, 8, 10]:
            code = generate_activation_code(length=length)
            assert len(code) == length
            assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" for c in code)
        
        print("✅ generate_activation_code - multiple lengths")
    
    def test_generate_activation_code_uniqueness(self):
        """Test that generated codes are reasonably unique
        Covers lines 72-74
        """
        codes = [generate_activation_code() for _ in range(100)]
        
        # Check for duplicates (should be extremely rare)
        unique_codes = set(codes)
        assert len(unique_codes) > 95  # At least 95% unique
        
        print("✅ generate_activation_code - codes are reasonably unique")
    
    def test_generate_activation_code_logging(self):
        """Test that code generation logs appropriately
        Covers line 74 (logging)
        """
        with patch('app.core.security.logger.info') as mock_logger:
            code = generate_activation_code()
            
            # Verify logger was called (line 74)
            mock_logger.assert_called_once_with(
                f"Activation code generated: {code}"
            )
            
            print("✅ generate_activation_code - logging (line 74)")
    
    def test_generate_activation_code_with_zero_length(self):
        """Test edge case with zero length
        Covers lines 72-74 with edge input
        """
        code = generate_activation_code(length=0)
        
        assert code == ""
        print("✅ generate_activation_code - zero length")

class TestSingletonInstance:
    """Tests for the singleton instance"""
    
    def test_password_handler_singleton(self):
        """Test that password_handler is a singleton instance"""
        assert isinstance(password_handler, PasswordHandler)
        print("✅ password_handler singleton instance")