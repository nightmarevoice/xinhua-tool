"""
统一配置文件
存放所有外部服务的 URL 和 API Key
"""

# ==================== 外部服务配置 ====================

# 代理服务配置
PROXY_BASE_URL = "http://185.216.21.215:35287"
PROXY_API_KEY = "xuanfeng_sdfasdfsdfkkllli8i3"

# 违禁词服务配置（使用同一个代理服务）
FORBIDDEN_WORDS_SERVICE_URL = PROXY_BASE_URL
FORBIDDEN_WORDS_API_KEY = PROXY_API_KEY

# 代理服务具体接口
PROXY_LOGS_URL = f"{PROXY_BASE_URL}/v1/logs"
PROXY_STATS_URL = f"{PROXY_BASE_URL}/v1/stats"
FORBIDDEN_WORDS_URL = f"{PROXY_BASE_URL}/v1/forbidden-words"





