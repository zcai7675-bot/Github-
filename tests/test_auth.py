"""
认证模块单元测试

测试 auth 模块的认证相关功能。
"""

import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
import keyring
import requests

from github_auto_sync.auth import (
    authenticate,
    get_stored_credentials,
    validate_token,
    is_authenticated,
    logout,
    load_dotenv,
    get_auth_token,
    get_auth_username,
    ensure_authenticated,
    get_auth_headers,
    AuthContext,
    AuthenticationError,
    TokenValidationError,
    SERVICE_NAME,
    USERNAME_KEY,
    TOKEN_KEY,
    GITHUB_API_URL,
)


# =============================================================================
# Token 验证测试
# =============================================================================


class TestValidateToken:
    """Token 验证测试"""
    
    def test_empty_token(self):
        """测试空 token"""
        valid, info = validate_token("")
        assert valid is False
        assert "不能为空" in info
    
    def test_none_token(self):
        """测试 None token"""
        valid, info = validate_token(None)
        assert valid is False
    
    def test_invalid_format_token(self):
        """测试无效格式 token"""
        valid, info = validate_token("invalid-token")
        assert valid is False
        assert "格式不正确" in info
    
    def test_valid_classic_token_format(self):
        """测试有效 classic token 格式"""
        with patch("github_auto_sync.auth.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"login": "testuser"}
            mock_get.return_value = mock_response
            
            valid, info = validate_token("ghp_" + "a" * 36)
            assert valid is True
            assert info == "testuser"
    
    def test_valid_fine_grained_token_format(self):
        """测试有效 fine-grained token 格式"""
        with patch("github_auto_sync.auth.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"login": "testuser"}
            mock_get.return_value = mock_response
            
            valid, info = validate_token("github_pat_" + "a" * 30)
            assert valid is True
    
    def test_valid_legacy_token_format(self):
        """测试有效 legacy token 格式"""
        with patch("github_auto_sync.auth.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"login": "testuser"}
            mock_get.return_value = mock_response
            
            # 40 位十六进制
            valid, info = validate_token("a" * 40)
            assert valid is True
    
    def test_unauthorized_token(self):
        """测试未授权 token"""
        with patch("github_auto_sync.auth.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"message": "Bad credentials"}
            mock_get.return_value = mock_response
            
            valid, info = validate_token("ghp_" + "a" * 36)
            assert valid is False
            assert "无效或已过期" in info
    
    def test_rate_limited(self):
        """测试 API 速率限制"""
        with patch("github_auto_sync.auth.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_response.json.return_value = {"message": "API rate limit exceeded"}
            mock_get.return_value = mock_response
            
            valid, info = validate_token("ghp_" + "a" * 36)
            assert valid is False
            assert "速率限制" in info or "权限不足" in info
    
    def test_network_timeout(self):
        """测试网络超时"""
        with patch("github_auto_sync.auth.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()
            
            with pytest.raises(TokenValidationError, match="超时"):
                validate_token("ghp_" + "a" * 36)
    
    def test_network_connection_error(self):
        """测试网络连接错误"""
        with patch("github_auto_sync.auth.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError()
            
            with pytest.raises(TokenValidationError, match="网络连接错误"):
                validate_token("ghp_" + "a" * 36)


# =============================================================================
# 凭证存储测试
# =============================================================================


class TestCredentialStorage:
    """凭证存储测试"""
    
    def test_store_credentials(self, mock_keyring):
        """测试存储凭证"""
        from github_auto_sync.auth import _store_credentials
        
        _store_credentials("testuser", "test-token")
        
        mock_keyring.set_password.assert_any_call(SERVICE_NAME, USERNAME_KEY, "testuser")
        mock_keyring.set_password.assert_any_call(SERVICE_NAME, TOKEN_KEY, "test-token")
    
    def test_get_stored_credentials_found(self, mock_keyring):
        """测试获取存储的凭证 - 找到"""
        mock_keyring.get_password.side_effect = lambda service, key: {
            USERNAME_KEY: "testuser",
            TOKEN_KEY: "test-token",
        }.get(key)
        
        username, token = get_stored_credentials()
        
        assert username == "testuser"
        assert token == "test-token"
    
    def test_get_stored_credentials_not_found(self, mock_keyring):
        """测试获取存储的凭证 - 未找到"""
        mock_keyring.get_password.return_value = None
        
        username, token = get_stored_credentials()
        
        assert username is None
        assert token is None
    
    def test_get_stored_credentials_error(self, mock_keyring):
        """测试获取存储的凭证 - 错误"""
        mock_keyring.get_password.side_effect = Exception("Keyring error")
        
        username, token = get_stored_credentials()
        
        assert username is None
        assert token is None


# =============================================================================
# 认证流程测试
# =============================================================================


class TestAuthenticate:
    """认证流程测试"""
    
    def test_authenticate_with_token(self, mock_keyring):
        """测试使用 token 认证"""
        with patch("github_auto_sync.auth.validate_token") as mock_validate:
            mock_validate.return_value = (True, "testuser")
            
            success, msg = authenticate("ghp_test_token", store=True)
            
            assert success is True
            assert "testuser" in msg
            mock_keyring.set_password.assert_called()
    
    def test_authenticate_from_env(self, mock_keyring, clean_env):
        """测试从环境变量获取 token 认证"""
        os.environ["GITHUB_TOKEN"] = "env-token"
        
        with patch("github_auto_sync.auth.validate_token") as mock_validate:
            mock_validate.return_value = (True, "testuser")
            
            success, msg = authenticate()
            
            assert success is True
            mock_validate.assert_called_with("env-token")
    
    def test_authenticate_no_token_provided(self, mock_keyring, clean_env):
        """测试未提供 token"""
        success, msg = authenticate()
        
        assert success is False
        assert "未提供" in msg or "GITHUB_TOKEN" in msg
    
    def test_authenticate_invalid_token(self, mock_keyring):
        """测试无效 token"""
        with patch("github_auto_sync.auth.validate_token") as mock_validate:
            mock_validate.return_value = (False, "Invalid token")
            
            success, msg = authenticate("invalid-token")
            
            assert success is False
            assert "验证失败" in msg
    
    def test_authenticate_validation_error(self, mock_keyring):
        """测试验证错误"""
        with patch("github_auto_sync.auth.validate_token") as mock_validate:
            mock_validate.side_effect = TokenValidationError("Network error")
            
            with pytest.raises(AuthenticationError):
                authenticate("test-token")
    
    def test_authenticate_without_storing(self, mock_keyring):
        """测试认证但不存储"""
        with patch("github_auto_sync.auth.validate_token") as mock_validate:
            mock_validate.return_value = (True, "testuser")
            
            success, msg = authenticate("test-token", store=False)
            
            assert success is True
            mock_keyring.set_password.assert_not_called()


# =============================================================================
# 认证状态测试
# =============================================================================


class TestAuthenticationStatus:
    """认证状态测试"""
    
    def test_is_authenticated_true(self, mock_keyring):
        """测试已认证"""
        mock_keyring.get_password.side_effect = lambda service, key: {
            USERNAME_KEY: "testuser",
            TOKEN_KEY: "test-token",
        }.get(key)
        
        assert is_authenticated() is True
    
    def test_is_authenticated_false(self, mock_keyring):
        """测试未认证"""
        mock_keyring.get_password.return_value = None
        
        assert is_authenticated() is False
    
    def test_logout_success(self, mock_keyring):
        """测试登出成功"""
        result = logout()
        
        assert result is True
        mock_keyring.delete_password.assert_any_call(SERVICE_NAME, USERNAME_KEY)
        mock_keyring.delete_password.assert_any_call(SERVICE_NAME, TOKEN_KEY)
    
    def test_logout_no_credentials(self, mock_keyring):
        """测试登出 - 无凭证"""
        mock_keyring.delete_password.side_effect = keyring.errors.PasswordDeleteError()
        
        result = logout()
        
        assert result is True
    
    def test_logout_error(self, mock_keyring):
        """测试登出错误"""
        mock_keyring.delete_password.side_effect = Exception("Delete error")
        
        result = logout()
        
        assert result is False


# =============================================================================
# Token 获取测试
# =============================================================================


class TestGetAuthToken:
    """获取认证 token 测试"""
    
    def test_get_auth_token_from_keyring(self, mock_keyring):
        """测试从 keyring 获取 token"""
        mock_keyring.get_password.side_effect = lambda service, key: {
            USERNAME_KEY: "testuser",
            TOKEN_KEY: "keyring-token",
        }.get(key)
        
        token = get_auth_token()
        
        assert token == "keyring-token"
    
    def test_get_auth_token_from_env(self, mock_keyring, clean_env):
        """测试从环境变量获取 token"""
        mock_keyring.get_password.return_value = None
        os.environ["GITHUB_TOKEN"] = "env-token"
        
        token = get_auth_token()
        
        assert token == "env-token"
    
    def test_get_auth_token_not_found(self, mock_keyring, clean_env):
        """测试 token 未找到"""
        mock_keyring.get_password.return_value = None
        
        token = get_auth_token()
        
        assert token is None


class TestGetAuthUsername:
    """获取认证用户名测试"""
    
    def test_get_auth_username_from_keyring(self, mock_keyring):
        """测试从 keyring 获取用户名"""
        mock_keyring.get_password.side_effect = lambda service, key: {
            USERNAME_KEY: "keyring-user",
            TOKEN_KEY: "test-token",
        }.get(key)
        
        username = get_auth_username()
        
        assert username == "keyring-user"
    
    def test_get_auth_username_from_env(self, mock_keyring, clean_env):
        """测试从环境变量获取用户名"""
        mock_keyring.get_password.return_value = None
        os.environ["GITHUB_USERNAME"] = "env-user"
        
        username = get_auth_username()
        
        assert username == "env-user"
    
    def test_get_auth_username_not_found(self, mock_keyring, clean_env):
        """测试用户名未找到"""
        mock_keyring.get_password.return_value = None
        
        username = get_auth_username()
        
        assert username is None


class TestEnsureAuthenticated:
    """确保认证测试"""
    
    def test_ensure_authenticated_success(self, mock_keyring):
        """测试确保认证成功"""
        mock_keyring.get_password.side_effect = lambda service, key: {
            USERNAME_KEY: "testuser",
            TOKEN_KEY: "test-token",
        }.get(key)
        
        token = ensure_authenticated()
        
        assert token == "test-token"
    
    def test_ensure_authenticated_failure(self, mock_keyring, clean_env):
        """测试确保认证失败"""
        mock_keyring.get_password.return_value = None
        
        with pytest.raises(AuthenticationError):
            ensure_authenticated()


class TestGetAuthHeaders:
    """获取认证头测试"""
    
    def test_get_auth_headers_success(self, mock_keyring):
        """测试获取认证头成功"""
        mock_keyring.get_password.side_effect = lambda service, key: {
            USERNAME_KEY: "testuser",
            TOKEN_KEY: "test-token",
        }.get(key)
        
        headers = get_auth_headers()
        
        assert headers["Authorization"] == "Bearer test-token"
        assert "application/vnd.github.v3+json" in headers["Accept"]
        assert "X-GitHub-Api-Version" in headers
    
    def test_get_auth_headers_failure(self, mock_keyring, clean_env):
        """测试获取认证头失败"""
        mock_keyring.get_password.return_value = None
        
        with pytest.raises(AuthenticationError):
            get_auth_headers()


# =============================================================================
# .env 文件加载测试
# =============================================================================


class TestLoadDotenv:
    """.env 文件加载测试"""
    
    def test_load_dotenv_success(self, temp_dir: Path, clean_env):
        """测试成功加载 .env 文件"""
        env_path = temp_dir / ".env"
        env_path.write_text("GITHUB_TOKEN=env-token\nGITHUB_USERNAME=env-user\n")
        
        result = load_dotenv(env_path)
        
        assert result is True
        assert os.environ.get("GITHUB_TOKEN") == "env-token"
        assert os.environ.get("GITHUB_USERNAME") == "env-user"
    
    def test_load_dotenv_file_not_found(self, temp_dir: Path):
        """测试 .env 文件不存在"""
        env_path = temp_dir / ".env"
        
        result = load_dotenv(env_path)
        
        assert result is False
    
    def test_load_dotenv_default_path(self, temp_dir: Path, clean_env):
        """测试加载默认路径的 .env 文件"""
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            env_path = temp_dir / ".env"
            env_path.write_text("GITHUB_TOKEN=default-token\n")
            
            result = load_dotenv()
            
            assert result is True
            assert os.environ.get("GITHUB_TOKEN") == "default-token"
        finally:
            os.chdir(original_cwd)


# =============================================================================
# AuthContext 测试
# =============================================================================


class TestAuthContext:
    """AuthContext 上下文管理器测试"""
    
    def test_auth_context_with_token(self, clean_env):
        """测试使用 token 的上下文"""
        with AuthContext(token="context-token", username="context-user"):
            assert os.environ.get("GITHUB_TOKEN") == "context-token"
            assert os.environ.get("GITHUB_USERNAME") == "context-user"
        
        # 退出上下文后应恢复
        assert "GITHUB_TOKEN" not in os.environ
        assert "GITHUB_USERNAME" not in os.environ
    
    def test_auth_context_restores_original(self, clean_env):
        """测试上下文恢复原始值"""
        os.environ["GITHUB_TOKEN"] = "original-token"
        os.environ["GITHUB_USERNAME"] = "original-user"
        
        with AuthContext(token="context-token", username="context-user"):
            assert os.environ.get("GITHUB_TOKEN") == "context-token"
        
        # 恢复原始值
        assert os.environ.get("GITHUB_TOKEN") == "original-token"
        assert os.environ.get("GITHUB_USERNAME") == "original-user"
    
    def test_auth_context_without_env(self, clean_env):
        """测试不使用环境变量的上下文"""
        os.environ["GITHUB_TOKEN"] = "existing-token"
        
        with AuthContext(use_env=False):
            assert "GITHUB_TOKEN" not in os.environ
        
        # 恢复
        assert os.environ.get("GITHUB_TOKEN") == "existing-token"
    
    def test_auth_context_only_username(self, clean_env):
        """测试只设置用户名的上下文"""
        with AuthContext(username="only-user"):
            assert os.environ.get("GITHUB_USERNAME") == "only-user"
            assert "GITHUB_TOKEN" not in os.environ
