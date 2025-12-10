"""
加密/解密工具模块
用于敏感数据（如 API 密钥）的加密存储
"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os
import logging

logger = logging.getLogger(__name__)

# 从环境变量获取加密密钥，如果没有则使用默认值（生产环境必须设置）
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "xinhua-tool-default-encryption-key-change-in-production")
SALT = b"xinhua-tool-salt"  # 盐值，生产环境应该使用随机生成并安全存储


def _get_fernet() -> Fernet:
    """获取 Fernet 实例"""
    # 使用 PBKDF2 从密钥生成固定长度的密钥
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY.encode()))
    return Fernet(key)


def encrypt_api_key(api_key: str) -> str:
    """
    加密 API 密钥
    
    Args:
        api_key: 原始 API 密钥
        
    Returns:
        加密后的 API 密钥（Base64 编码）
    """
    if not api_key:
        return ""
    
    try:
        fernet = _get_fernet()
        encrypted = fernet.encrypt(api_key.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"加密 API 密钥失败: {str(e)}")
        raise


def decrypt_api_key(encrypted_key: str) -> str:
    """
    解密 API 密钥
    
    Args:
        encrypted_key: 加密的 API 密钥
        
    Returns:
        解密后的原始 API 密钥
    """
    if not encrypted_key:
        return ""
    
    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(encrypted_key.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"解密 API 密钥失败: {str(e)}")
        raise


def mask_api_key(api_key: str, show_prefix: int = 3, show_suffix: int = 12) -> str:
    """
    脱敏显示 API 密钥
    
    Args:
        api_key: API 密钥（可以是加密的或未加密的）
        show_prefix: 显示的前缀字符数
        show_suffix: 显示的后缀字符数
        
    Returns:
        脱敏后的 API 密钥，例如：sk-****99iJ--goa2xynmofjg
    """
    if not api_key:
        return ""
    
    # 如果密钥太短，直接返回星号
    if len(api_key) <= show_prefix + show_suffix:
        return "*" * len(api_key)
    
    prefix = api_key[:show_prefix]
    suffix = api_key[-show_suffix:]
    return f"{prefix}****{suffix}"


def is_encrypted(value: str) -> bool:
    """
    判断字符串是否已加密
    
    Args:
        value: 待判断的字符串
        
    Returns:
        True 如果已加密，False 如果未加密
    """
    if not value:
        return False
    
    # 尝试解密，如果成功说明已加密
    try:
        fernet = _get_fernet()
        fernet.decrypt(value.encode())
        return True
    except Exception:
        return False

