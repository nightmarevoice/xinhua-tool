"""
Workflow Control Service 同步工具
用于在 backend 项目的数据变更时同步到 workflow-ctl 服务
"""
import httpx
import os
import logging
import time
from typing import Optional, Dict, Any

# 导入数据库相关模块
from app.database import SessionLocal
from app.models.apikey import ApiKey as ApiKeyModel

# 配置日志
logger = logging.getLogger(__name__)

# 从环境变量获取 workflow-ctl 服务地址
WORKFLOW_CTL_BASE_URL = os.getenv("WORKFLOW_CTL_BASE_URL", "http://localhost:8889")

# 从环境变量获取 workflow-ctl 的 API Key（用于认证，当数据库中没有时使用）
WORKFLOW_CTL_API_KEY = os.getenv("WORKFLOW_CTL_API_KEY", "ak_5i_PjMh5bDSjWZN1xLnsLFj2NTV_G3DSwNy1Q01WNgE")

# API Key 缓存（避免频繁查询数据库）
_api_key_cache: Optional[str] = None
_cache_timestamp: float = 0
_cache_ttl: float = 300  # 缓存有效期：5分钟


def _get_apikey_from_db() -> Optional[str]:
    """
    从数据库中获取一个有效的 API Key
    
    Returns:
        Optional[str]: API Key 值，如果不存在则返回 None
    """
    try:
        db = SessionLocal()
        try:
            # 查询第一个状态为 active 的 API Key
            apikey = db.query(ApiKeyModel).filter(
                ApiKeyModel.status == "active"
            ).first()
            
            if apikey:
                logger.debug(f"从数据库获取 API Key: id={apikey.id}, name={apikey.name}")
                return apikey.key
            else:
                logger.warning("数据库中未找到有效的 API Key (status='active')")
                return None
        finally:
            db.close()
    except Exception as e:
        logger.error(f"从数据库获取 API Key 失败: {str(e)}")
        return None


def _get_cached_apikey() -> Optional[str]:
    """
    获取缓存的 API Key，如果缓存过期则从数据库重新获取
    
    Returns:
        Optional[str]: API Key 值，如果不存在则返回 None
    """
    global _api_key_cache, _cache_timestamp
    
    current_time = time.time()
    
    # 如果缓存存在且未过期，直接返回
    if _api_key_cache and (current_time - _cache_timestamp) < _cache_ttl:
        logger.debug("使用缓存的 API Key")
        return _api_key_cache
    
    # 缓存过期或不存在，从数据库获取
    logger.debug("缓存过期或不存在，从数据库获取 API Key")
    _api_key_cache = _get_apikey_from_db()
    _cache_timestamp = current_time
    
    return _api_key_cache


def clear_apikey_cache():
    """
    清除 API Key 缓存，强制下次从数据库重新获取
    用于 API Key 状态改变时及时更新缓存
    """
    global _api_key_cache, _cache_timestamp
    _api_key_cache = None
    _cache_timestamp = 0
    logger.debug("已清除 API Key 缓存")


def get_auth_headers() -> Dict[str, str]:
    """
    获取用于 workflow-ctl 认证的请求头
    
    优先级：
    1. 从 backend 数据库中获取任意一个有效的 API Key（如果存在）
    2. 使用环境变量 WORKFLOW_CTL_API_KEY（如果数据库中没有）
    
    Returns:
        Dict[str, str]: 包含 Authorization 头的字典
    """
    headers = {"Content-Type": "application/json"}
    
    # 优先从数据库获取 API Key
    api_key = _get_cached_apikey()
    
    # 如果数据库中没有，使用环境变量中的 API Key（带默认值）
    if not api_key:
        api_key = WORKFLOW_CTL_API_KEY
        if api_key:
            logger.debug("数据库中没有 API Key，使用环境变量中的 API Key 进行认证")
    
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        logger.debug("使用 API Key 进行认证")
    else:
        logger.warning(
            "未找到有效的 API Key（数据库中也没有状态为 'active' 的 API Key，"
            "且环境变量 WORKFLOW_CTL_API_KEY 也未设置），"
            "同步请求可能因认证失败而失败"
        )
    
    return headers


def get_auth_headers_for_apikey_sync() -> Dict[str, str]:
    """
    获取用于 API Key 同步的认证头
    注意：API Key 同步必须使用环境变量中的 API Key，不能使用数据库中的 API Key
    因为可能存在"鸡生蛋"问题：数据库中的 API Key 还没有同步到 workflow-ctl
    
    Returns:
        Dict[str, str]: 包含 Authorization 头的字典
    """
    headers = {"Content-Type": "application/json"}
    
    # API Key 同步必须使用环境变量中的 API Key（带默认值）
    api_key = WORKFLOW_CTL_API_KEY
    
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        logger.debug("使用环境变量中的 API Key 进行认证")
    else:
        logger.error(
            "API Key 同步失败：环境变量 WORKFLOW_CTL_API_KEY 未设置。"
            "API Key 同步必须使用环境变量中的 API Key，不能使用数据库中的 API Key。"
            "请设置环境变量 WORKFLOW_CTL_API_KEY 为一个在 workflow-ctl 中已存在的有效 API Key。"
        )
    
    return headers


async def sync_apikey_to_workflow_ctl(external_id: str, name: str, description: Optional[str], 
                                       key: str, status: str = "active") -> bool:
    """
    同步 API Key 到 workflow-ctl 服务
    
    Args:
        external_id: backend 系统的 ID（字符串 UUID，需要转换为整数）
        name: API Key 名称
        description: 描述
        key: API Key 值
        status: 状态
    
    Returns:
        bool: 同步是否成功
    """
    try:
        # 将字符串 ID 转换为整数（使用哈希值）
        external_id_int = hash(external_id) % (2**31)  # 确保在 int32 范围内
        
        sync_data = {
            "external_id": external_id_int,
            "name": name,
            "description": description,
            "key": key,
            "status": status
        }
        
        logger.info(f"开始同步 API Key 到 workflow-ctl: external_id={external_id}, name={name}")
        
        # 使用专门的认证头函数，强制使用环境变量中的 API Key
        auth_headers = get_auth_headers_for_apikey_sync()
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{WORKFLOW_CTL_BASE_URL}/api/apikeys/sync",
                json=sync_data,
                headers=auth_headers
            )
            response.raise_for_status()
            logger.info(f"API Key 同步成功: external_id={external_id}, response_status={response.status_code}")
            return True
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text[:500] if e.response.text else "无错误详情"
        logger.error(
            f"API Key 同步失败 (HTTP错误): external_id={external_id}, "
            f"status={e.response.status_code}, error={error_detail}"
        )
        if e.response.status_code == 401:
            logger.error(
                f"认证失败 (401): 请检查环境变量 WORKFLOW_CTL_API_KEY 是否正确，"
                f"以及该 API Key 是否在 workflow-ctl 中存在且状态为 active"
            )
        return False
    except httpx.RequestError as e:
        logger.error(f"API Key 同步失败 (请求错误): external_id={external_id}, error={str(e)}")
        return False
    except Exception as e:
        logger.error(f"API Key 同步失败: external_id={external_id}, 错误: {str(e)}")
        return False


async def sync_workflow_to_workflow_ctl(external_id: str, name: str, description: Optional[str],
                                        workflow_type: str, config: Optional[Dict[str, Any]] = None,
                                        status: str = "active") -> bool:
    """
    同步流程配置到 workflow-ctl 服务
    
    Args:
        external_id: backend 系统的 ID（字符串 UUID）
        name: 流程名称
        description: 描述
        workflow_type: 流程类型
        config: 流程配置（字典）
        status: 流程状态（active/inactive）
    
    Returns:
        bool: 同步是否成功
    """
    try:
        # 将字符串 ID 转换为整数（用于 external_id）
        external_id_int = hash(external_id) % (2**31)
        
        # 如果 config 为空，构建默认配置
        if config is None:
            config = {
                "type": workflow_type,
                "name": name,
                "description": description or ""
            }
        
        sync_data = {
            "external_id": external_id_int,
            "backend_id": external_id,  # 发送原始的字符串 ID
            "name": name,
            "description": description,
            "workflow_type": workflow_type,
            "config": config,
            "status": status
        }
        
        logger.info(f"开始同步流程配置到 workflow-ctl: external_id={external_id}, name={name}, workflow_type={workflow_type}")
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{WORKFLOW_CTL_BASE_URL}/api/workflows/sync",
                json=sync_data,
                headers=get_auth_headers()
            )
            response.raise_for_status()
            logger.info(f"流程配置同步成功: external_id={external_id}, response_status={response.status_code}")
            return True
    except httpx.HTTPStatusError as e:
        error_detail = None
        try:
            error_detail = e.response.json() if e.response.content else None
        except:
            error_detail = e.response.text[:500] if e.response.text else None
        
        logger.error(
            f"流程配置同步失败 (HTTP错误): external_id={external_id}, "
            f"status={e.response.status_code}, "
            f"url={e.request.url if hasattr(e, 'request') else 'unknown'}, "
            f"error={error_detail}"
        )
        if e.response.status_code == 401:
            logger.error(
                f"认证失败 (401): 请检查 API Key 是否正确，"
                f"以及该 API Key 是否在 workflow-ctl 中存在且状态为 active"
            )
        elif e.response.status_code == 422:
            logger.error(
                f"数据验证失败 (422): 请检查发送的数据格式是否正确，"
                f"sync_data={sync_data}"
            )
        return False
    except httpx.RequestError as e:
        logger.error(
            f"流程配置同步失败 (请求错误): external_id={external_id}, "
            f"error={str(e)}, error_type={type(e).__name__}"
        )
        if isinstance(e, httpx.ConnectError):
            logger.error(f"请检查 workflow-ctl 服务是否运行在 {WORKFLOW_CTL_BASE_URL}")
        return False
    except Exception as e:
        import traceback
        logger.error(
            f"流程配置同步失败 (未知错误): external_id={external_id}, "
            f"错误类型: {type(e).__name__}, 错误: {str(e)}"
        )
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return False


async def sync_prompt_to_workflow_ctl(external_id: str, title: str, 
                                      system_prompt: Optional[str] = None,
                                      user_prompt: Optional[str] = None,
                                      model_type: Optional[str] = None) -> bool:
    """
    同步 Prompt 配置到 workflow-ctl 服务
    
    Args:
        external_id: backend 系统的 ID
        title: Prompt 标题
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        model_type: 模型类型
    
    Returns:
        bool: 同步是否成功
    """
    try:
        # 验证必需字段
        if not title:
            logger.error(f"Prompt 同步失败: title 不能为空, external_id={external_id}")
            raise ValueError("title 不能为空")
        if not model_type:
            logger.error(f"Prompt 同步失败: model_type 不能为空, external_id={external_id}")
            raise ValueError("model_type 不能为空")
        
        # 将字符串 ID 转换为整数
        external_id_int = hash(external_id) % (2**31)
        
        sync_data = {
            "external_id": external_id_int,
            "title": title,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "model_type": model_type
        }
        
        sync_url = f"{WORKFLOW_CTL_BASE_URL}/api/prompts/sync"
        logger.info(f"开始同步 Prompt 配置: external_id={external_id} (hash={external_id_int}), title={title}, model_type={model_type}")
        logger.debug(f"同步数据: {sync_data}")
        logger.debug(f"同步目标地址: {sync_url}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(
                    sync_url,
                    json=sync_data,
                    headers=get_auth_headers()
                )
                logger.debug(f"收到响应: status={response.status_code}, headers={dict(response.headers)}")
                
                response.raise_for_status()
                
                response_data = None
                if response.content:
                    try:
                        response_data = response.json()
                    except Exception as json_error:
                        logger.warning(f"无法解析响应 JSON: {str(json_error)}, 响应内容: {response.text[:200]}")
                        response_data = {"raw_text": response.text[:200]}
                
                logger.info(f"Prompt 配置同步成功: external_id={external_id}, response_status={response.status_code}, response={response_data}")
                return True
            except httpx.TimeoutException as e:
                logger.error(f"Prompt 配置同步失败 (超时): external_id={external_id}, url={sync_url}, error={str(e)}")
                return False
            except httpx.ConnectError as e:
                logger.error(f"Prompt 配置同步失败 (连接错误): external_id={external_id}, url={sync_url}, error={str(e)}")
                logger.error(f"请检查 workflow-ctl 服务是否运行在 {WORKFLOW_CTL_BASE_URL}")
                return False
    except httpx.HTTPStatusError as e:
        error_detail = None
        try:
            error_detail = e.response.json() if e.response.content else None
        except:
            error_detail = e.response.text[:500] if e.response.text else None
        
        logger.error(
            f"Prompt 配置同步失败 (HTTP错误): external_id={external_id}, "
            f"status={e.response.status_code}, "
            f"url={e.request.url if hasattr(e, 'request') else sync_url}, "
            f"error={error_detail}"
        )
        return False
    except httpx.RequestError as e:
        logger.error(f"Prompt 配置同步失败 (请求错误): external_id={external_id}, url={sync_url}, error={str(e)}, error_type={type(e).__name__}")
        return False
    except ValueError as e:
        # 验证错误已经在上面记录过了
        return False
    except Exception as e:
        import traceback
        logger.error(f"Prompt 配置同步失败 (未知错误): external_id={external_id}, 错误类型: {type(e).__name__}, 错误: {str(e)}")
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return False


async def sync_model_parameter_to_workflow_ctl(external_id: str, name: str, type: str,
                                                default_value: Any, model_type: str,
                                                description: str, required: bool = False,
                                                validation: Optional[Dict[str, Any]] = None) -> bool:
    """
    同步模型参数配置到 workflow-ctl 服务
    
    Args:
        external_id: backend 系统的 ID
        name: 参数名称
        type: 参数类型
        default_value: 默认值
        model_type: 模型类型
        description: 描述
        required: 是否必需
        validation: 验证规则
    
    Returns:
        bool: 同步是否成功
    """
    try:
        # 将字符串 ID 转换为整数
        external_id_int = hash(external_id) % (2**31)
        
        sync_data = {
            "external_id": external_id_int,
            "name": name,
            "type": type,
            "default_value": default_value,
            "model_type": model_type,
            "description": description,
            "required": required,
            "validation": validation
        }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{WORKFLOW_CTL_BASE_URL}/api/model-parameters/sync",
                json=sync_data,
                headers=get_auth_headers()
            )
            response.raise_for_status()
            logger.info(f"模型参数配置同步成功: {external_id}")
            return True
    except Exception as e:
        logger.error(f"模型参数配置同步失败: {external_id}, 错误: {str(e)}")
        return False


async def sync_llm_provider_to_workflow_ctl(
    external_id: int, name: str, provider: str, default_model_name: str,
    api_key: Optional[str] = None, api_base: Optional[str] = None,
    api_version: Optional[str] = None, custom_config: Optional[Dict[str, str]] = None,
    fast_default_model_name: Optional[str] = None, deployment_name: Optional[str] = None,
    default_vision_model: Optional[str] = None, model_configurations: Optional[list] = None,
    category: str = 'general', is_default_provider: bool = False,
    is_default_vision_provider: bool = False
) -> bool:
    """
    同步 LLM Provider 到 workflow-ctl 服务
    
    Args:
        external_id: backend 系统的 ID（整数）
        name: Provider 名称
        provider: Provider 类型 (openai, azure, anthropic, google, custom)
        default_model_name: 默认模型名称
        api_key: API Key
        api_base: API Base URL
        api_version: API 版本
        custom_config: 自定义配置
        fast_default_model_name: 快速默认模型名称
        deployment_name: 部署名称
        default_vision_model: 默认视觉模型
        model_configurations: 模型配置列表
        category: 类别 (general, professional)
        is_default_provider: 是否为默认 Provider
        is_default_vision_provider: 是否为默认视觉 Provider
    
    Returns:
        bool: 同步是否成功
    """
    try:
        # LLM Provider 的 ID 已经是整数，直接使用
        # 但为了确保一致性，我们仍然使用哈希转换（如果传入的是字符串）
        if isinstance(external_id, str):
            external_id_int = hash(external_id) % (2**31)
        else:
            external_id_int = external_id
        
        # 处理 model_configurations：如果是对象列表，转换为字典列表
        model_configs_list = None
        if model_configurations:
            model_configs_list = []
            for config in model_configurations:
                if hasattr(config, 'dict'):
                    model_configs_list.append(config.dict())
                elif isinstance(config, dict):
                    model_configs_list.append(config)
                else:
                    # 假设是 Pydantic 模型或其他对象
                    model_configs_list.append(dict(config))
        
        sync_data = {
            "external_id": external_id_int,
            "name": name,
            "provider": provider,
            "api_key": api_key,
            "api_base": api_base,
            "api_version": api_version,
            "custom_config": custom_config,
            "default_model_name": default_model_name,
            "fast_default_model_name": fast_default_model_name,
            "deployment_name": deployment_name,
            "default_vision_model": default_vision_model,
            "model_configurations": model_configs_list,
            "category": category,
            "is_default_provider": is_default_provider,
            "is_default_vision_provider": is_default_vision_provider
        }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{WORKFLOW_CTL_BASE_URL}/api/llm-providers/sync",
                json=sync_data,
                headers=get_auth_headers()
            )
            response.raise_for_status()
            logger.info(f"LLM Provider 同步成功: {external_id}")
            return True
    except Exception as e:
        logger.error(f"LLM Provider 同步失败: {external_id}, 错误: {str(e)}")
        return False


async def delete_from_workflow_ctl(resource_type: str, external_id: str) -> bool:
    """
    从 workflow-ctl 服务删除资源
    
    Args:
        resource_type: 资源类型 (apikeys, workflows, prompts, model-parameters, llm-providers)
        external_id: backend 系统的 ID（字符串或整数）
    
    Returns:
        bool: 删除是否成功
    """
    try:
        # 将 ID 转换为整数
        if isinstance(external_id, str):
            external_id_int = hash(external_id) % (2**31)
        else:
            external_id_int = external_id
        
        delete_url = f"{WORKFLOW_CTL_BASE_URL}/api/{resource_type}/sync/{external_id_int}"
        logger.info(f"开始删除 {resource_type} 资源: external_id={external_id} (hash={external_id_int}), url={delete_url}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.delete(
                    delete_url,
                    headers=get_auth_headers()
                )
                logger.debug(f"收到响应: status={response.status_code}")
                
                response.raise_for_status()
                
                response_data = None
                if response.content:
                    try:
                        response_data = response.json()
                    except:
                        response_data = {"raw_text": response.text[:200] if response.text else None}
                
                logger.info(f"{resource_type} 删除同步成功: external_id={external_id}, response_status={response.status_code}, response={response_data}")
                return True
            except httpx.TimeoutException as e:
                logger.error(f"{resource_type} 删除同步失败 (超时): external_id={external_id}, url={delete_url}, error={str(e)}")
                return False
            except httpx.ConnectError as e:
                logger.error(f"{resource_type} 删除同步失败 (连接错误): external_id={external_id}, url={delete_url}, error={str(e)}")
                logger.error(f"请检查 workflow-ctl 服务是否运行在 {WORKFLOW_CTL_BASE_URL}")
                return False
    except httpx.HTTPStatusError as e:
        error_detail = None
        try:
            error_detail = e.response.json() if e.response.content else None
        except:
            error_detail = e.response.text[:500] if e.response.text else None
        
        logger.error(
            f"{resource_type} 删除同步失败 (HTTP错误): external_id={external_id}, "
            f"status={e.response.status_code}, "
            f"url={delete_url}, "
            f"error={error_detail}"
        )
        return False
    except httpx.RequestError as e:
        logger.error(f"{resource_type} 删除同步失败 (请求错误): external_id={external_id}, url={delete_url}, error={str(e)}, error_type={type(e).__name__}")
        return False
    except Exception as e:
        import traceback
        logger.error(f"{resource_type} 删除同步失败 (未知错误): external_id={external_id}, 错误类型: {type(e).__name__}, 错误: {str(e)}")
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return False

