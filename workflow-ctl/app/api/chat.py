from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import logging
import json
import requests
import time
from datetime import datetime
from app.database.database import get_db
from app.models.prompt import Prompt
from app.models.workflow import Workflow
from app.models.llm_provider import LLMProvider
from app.models.apikey import ApiKey
from app.schemas.prompt import Prompt as PromptSchema
from app.schemas.workflow import Workflow as WorkflowSchema
from app.schemas.llm_provider import LLMProvider as LLMProviderSchema
from app.middleware.auth import verify_api_key_dependency
from app.config import PROXY_BASE_URL, PROXY_API_KEY, PROXY_LOGS_URL
from app.utils.crypto import decrypt_api_key
from pydantic import BaseModel

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

PROXY_URL = f"{PROXY_BASE_URL}/v1/chat/completions"

# 文风选项数据（与前端保持一致）
WRITING_STYLES = [
    {
        "style": "政务通报/汇报体",
        "features": "语言严谨、结构规范、逻辑清晰、用词精准、客观陈述",
    },
    {
        "style": "内部参阅/简报体",
        "features": "观点鲜明、分析深刻、篇幅精炼、问题导向、数据支撑",
    },
    {
        "style": "领导讲话/发言稿体",
        "features": "结构庄重、气势恢宏、号召力强、排比对偶多",
    },
    {
        "style": "权威评论体 (新华时评风)",
        "features": "高屋建瓴、观点鲜明、论证有力、引导舆论",
    },
    {
        "style": "深度报道/调查体",
        "features": "叙事完整、细节丰富、逻辑严密、背景深远",
    },
    {
        "style": "标准消息/通稿体",
        "features": "要素齐全（5W1H）、客观中立、倒金字塔结构",
    },
    {
        "style": "新闻特写/人物通讯体",
        "features": "情感饱满、描写生动、故事性强、见微知著",
    },
    {
        "style": "宏观经济报道体",
        "features": "(分析) 全局视角、数据驱动、政策敏感、趋势研判",
    },
    {
        "style": "社会民生报道体",
        "features": "(关怀) 问题导向、政策关联、人文温度、建设性",
    },
    {
        "style": "红色纪念/党史评论体",
        "features": "(论述) 以史鉴今、价值提炼、思想引领、语言庄重",
    },
    {
        "style": "新媒体解读/划重点体",
        "features": "通俗易懂、口语化表达、善用问答和比喻、逻辑清晰",
    },
    {
        "style": "数据新闻/图解文案体",
        "features": "语言精炼、数据驱动、结论清晰、适合可视化呈现",
    },
]

# 创建文风映射字典，便于快速查找
WRITING_STYLES_MAP = {item["style"]: item["features"] for item in WRITING_STYLES}

class ChatRequest(BaseModel):
    """聊天请求模型"""
    user_message: str  # 用户消息
    workflowId: Optional[str] = None  # workflow ID（可选，如果提供则使用对应的 workflow）
    writing_style: Optional[str] = None  # 文风（可选）


def generate_sse_event(data: Dict[str, Any], event: str = "message") -> str:
    """生成 SSE 格式的事件数据"""
    event_data = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {event_data}\n\n"


def save_chat_log(log_data: Dict[str, Any]):
    """调用 Backend API 保存日志"""
    try:
        # 假设 Backend 运行在本地 8888 端口，实际应从配置读取
        backend_url = "http://localhost:8888/api/chat-logs/"
        requests.post(backend_url, json=log_data, timeout=5)
    except Exception as e:
        logger.error(f"保存聊天日志失败: {str(e)}")


def parse_writing_style(user_message: str) -> Optional[Dict[str, str]]:
    """从用户消息中解析文风信息
    
    前端格式: "原始消息,| 文风: XXX | 核心特点：YYY"
    返回: {"writing_style": "XXX", "features": "YYY"} 或 None
    """
    try:
        if ",|" in user_message and "文风:" in user_message:
            # 分割消息和文风信息
            parts = user_message.split(",|", 1)
            if len(parts) == 2:
                style_info = parts[1].strip()
                
                # 解析文风和特点
                writing_style = None
                features = None
                
                if "文风:" in style_info:
                    style_part = style_info.split("文风:", 1)[1]
                    if "|" in style_part:
                        writing_style = style_part.split("|")[0].strip()
                
                if "核心特点：" in style_info or "核心特点:" in style_info:
                    # 处理中文冒号和英文冒号
                    features_part = style_info.split("核心特点", 1)[1]
                    if features_part.startswith("：") or features_part.startswith(":"):
                        features = features_part[1:].strip()
                
                if writing_style or features:
                    return {
                        "writing_style": writing_style or "",
                        "features": features or ""
                    }
    except Exception as e:
        logger.warning(f"解析文风信息失败: {str(e)}")
    
    return None



def call_llm_non_stream(
    messages: List[Dict[str, str]],
    api_base: str,
    api_key: str,
    model: str,
    temperature: float = 0.7
) -> str:
    """非流式调用 LLM（用于专有模型第一步）"""
    try:
        request_body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }
        
        logger.info(f"非流式调用: {api_base}/chat/completions")
        logger.info(f"请求体: {json.dumps(request_body, ensure_ascii=False, indent=2)}")
        
        response = requests.post(
            f"{api_base}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=request_body,
            timeout=120
        )
        
        response.raise_for_status()
        data = response.json()
        
        # 提取内容
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0].get("message", {}).get("content", "")
            logger.info(f"非流式响应内容长度: {len(content)}")
            return content
        else:
            logger.error(f"非流式响应格式错误: {data}")
            raise Exception("模型返回格式错误")
            
    except Exception as e:
        logger.error(f"非流式调用失败: {str(e)}", exc_info=True)
        raise


def stream_chat_response(
    messages: List[Dict[str, str]],
    api_base: str,
    api_key: str,
    model: str,
    temperature: float = 0.7,
    log_info: Dict[str, Any] = None
):
    """流式生成聊天响应"""
    try:
        # 发送初始事件
        yield generate_sse_event(
            {"type": "start", "message": "开始生成响应..."},
            event="start"
        )
        
        # 构建请求体
        request_body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        
        logger.info(f"流式调用: {api_base}/chat/completions")
        logger.info(f"请求体: {json.dumps(request_body, ensure_ascii=False, indent=2)}")
        
        # 使用 requests 调用服务（流式）
        response = requests.post(
            f"{api_base}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=request_body,
            stream=True,
            timeout=None
        )
        
        response.raise_for_status()
        
        # 解析流式响应
        full_content = ""
        line_count = 0
        for line in response.iter_lines():
            if line:
                line_count += 1
                line_text = line.decode('utf-8')
                
                # 跳过空行和 [DONE] 标记
                if not line_text.strip() or line_text.strip() == "data: [DONE]":
                    continue
                
                # 解析 SSE 格式：data: {...}
                if line_text.startswith("data: "):
                    data_str = line_text[6:]
                    try:
                        data = json.loads(data_str)
                        
                        # 提取内容
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            
                            if content:
                                full_content += content
                                # 发送内容块
                                yield generate_sse_event(
                                    {"type": "content", "content": content},
                                    event="message"
                                )
                    except json.JSONDecodeError as e:
                        logger.warning(f"无法解析 SSE 数据: {data_str}, 错误: {e}")
                        continue
        
        logger.info(f"流式响应完成，累计内容长度: {len(full_content)}")
        
        # 发送完成事件
        yield generate_sse_event(
            {"type": "done", "message": "响应生成完成", "full_content": full_content},
            event="done"
        )
        
        # 记录日志
        if log_info:
            try:
                # 更新响应内容和耗时
                if log_info.get("workflow_type") == "proprietary":
                    log_info["proprietary_response"] = full_content
                elif log_info.get("workflow_type") == "proprietary->general":
                    log_info["general_response"] = full_content
                
                log_info["duration"] = time.time() - log_info.get("start_time", 0)
                
                # 移除临时字段
                log_info.pop("workflow_type", None)
                log_info.pop("start_time", None)
                log_info.pop("writing_style_info", None)
                
                save_chat_log(log_info)
            except Exception as e:
                logger.error(f"记录日志出错: {str(e)}")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"请求服务失败: {str(e)}")
        yield generate_sse_event(
            {"type": "error", "message": f"请求服务失败: {str(e)}"},
            event="error"
        )
    except Exception as e:
        logger.error(f"流式响应生成失败: {str(e)}", exc_info=True)
        yield generate_sse_event(
            {"type": "error", "message": f"生成响应失败: {str(e)}"},
            event="error"
        )


@router.post("/stream")
async def stream_chat(
    request: ChatRequest = Body(..., description="聊天请求"),
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    流式聊天接口 - 自动从数据库获取配置
    
    流程：
    1. 获取 workflow 配置（如果提供 workflowId 则使用对应的 workflow，否则使用第一条）
    2. 获取所有 prompts 提示词
    3. 获取所有 llm_providers 模型配置
    4. 根据 workflow_type 决定调用方式：
       - proprietary: 直接调用专有模型（流式）
       - proprietary->general: 先调用专有模型（非流式），再用结果调用通用模型（流式）
    """
    try:
        user_message = request.user_message
        workflow_id = request.workflowId
        writing_style = request.writing_style
        
        logger.info(f"收到用户消息: {user_message[:100]}...")
        logger.info(f"workflowId: {workflow_id}")
        logger.info(f"writing_style: {writing_style}")
        
        # 如果传递了 writing_style 参数，在后端完成拼接
        writing_style_info = None
        if writing_style:
            features = WRITING_STYLES_MAP.get(writing_style)
            if features:
                # 拼接文风信息到 user_message
                user_message = f"{user_message},| {writing_style} | 核心特点：{features}"
                writing_style_info = {
                    "writing_style": writing_style,
                    "features": features
                }
                logger.info(f"已拼接文风信息: {writing_style_info}")
            else:
                logger.warning(f"未找到 writing_style={writing_style} 的核心特点配置")
        else:
            # 兼容旧的解析方式（从 user_message 中解析）
            writing_style_info = parse_writing_style(user_message)
            if writing_style_info:
                logger.info(f"从消息中解析到文风信息: {writing_style_info}")
        
        # 初始化日志信息
        start_time = time.time()
        log_info = {
            "input_params": request.model_dump(),
            "start_time": start_time,
            "proprietary_params": None,
            "proprietary_response": None,
            "general_params": None,
            "general_response": None,
            "duration": 0.0,
            "writing_style_info": writing_style_info
        }
        
        # 第一步：获取 workflow 参数
        if workflow_id:
            # 如果提供了 workflowId，通过 backend_id 查找对应的 workflow
            workflow = db.query(Workflow).filter(Workflow.backend_id == workflow_id).first()
            if not workflow:
                logger.warning(f"未找到 backend_id={workflow_id} 的 workflow，使用默认第一条")
                workflow = db.query(Workflow).first()
            else:
                logger.info(f"使用指定的 workflow: {workflow.name} (backend_id={workflow_id})")
        else:
            # 如果没有提供 workflowId，使用第一条数据
            workflow = db.query(Workflow).first()
            logger.info(f"未提供 workflowId，使用默认第一条 workflow")
        
        if not workflow:
            raise HTTPException(status_code=404, detail="未找到 workflow 配置")
        
        workflow_type = workflow.workflow_type
        logger.info(f"Workflow 类型: {workflow_type}")
        logger.info(f"Workflow 名称: {workflow.name}")
        
        # 第二步：获取 prompts 提示词数据
        prompts = db.query(Prompt).all()
        if not prompts:
            raise HTTPException(status_code=404, detail="未找到 prompts 配置")
        
        prompts_dict = {p.model_type: p for p in prompts}
        logger.info(f"加载了 {len(prompts)} 个 prompts: {list(prompts_dict.keys())}")
        
        # 第三步：获取 llm_providers 模型参数配置
        providers = db.query(LLMProvider).all()
        if not providers:
            raise HTTPException(status_code=404, detail="未找到 llm_providers 配置")
        
        providers_dict = {p.category: p for p in providers}
        logger.info(f"加载了 {len(providers)} 个 providers: {list(providers_dict.keys())}")
        
        # 第四步：根据 workflow_type 处理
        if workflow_type == "proprietary":
            # 纯专有模型流程
            logger.info("执行专有模型流程（流式）")
            
            # 获取专有模型的提示词
            proprietary_prompt = prompts_dict.get("proprietary")
            if not proprietary_prompt:
                raise HTTPException(status_code=404, detail="未找到 model_type=proprietary 的提示词")
            
            # 获取专有模型的配置
            proprietary_provider = providers_dict.get("professional")
            if not proprietary_provider:
                raise HTTPException(status_code=404, detail="未找到 category=professional 的模型配置")
            
            # 提取参数
            system_prompt = proprietary_prompt.system_prompt or ""
            user_prompt_template = proprietary_prompt.user_prompt or "{user_message}"
            user_content = user_prompt_template.replace("{user_message}", user_message)
            
            api_base = proprietary_provider.api_base
            # 解密 API 密钥
            api_key_value = decrypt_api_key(proprietary_provider.api_key) if proprietary_provider.api_key else ""
            model_name = proprietary_provider.default_model_name
            
            # 获取 temperature
            temperature = 0.7
            if proprietary_provider.custom_config and isinstance(proprietary_provider.custom_config, dict):
                temp_value = proprietary_provider.custom_config.get("temperature")
                if temp_value:
                    try:
                        temperature = float(temp_value)
                    except (ValueError, TypeError):
                        pass
            
            logger.info(f"专有模型配置 - model: {model_name}, temperature: {temperature}")
            
            # 记录专有模型参数
            log_info["workflow_type"] = "proprietary"
            proprietary_params = {
                "model": model_name,
                "temperature": temperature,
                "api_base": api_base
            }
            # 添加文风信息
            if writing_style_info:
                proprietary_params["writing_style"] = writing_style_info.get("writing_style", "")
                proprietary_params["writing_features"] = writing_style_info.get("features", "")
            log_info["proprietary_params"] = proprietary_params
            
            # 构建消息
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_content})
            
            # 返回流式响应
            return StreamingResponse(
                stream_chat_response(
                    messages=messages,
                    api_base=api_base,
                    api_key=api_key_value,
                    model=model_name,
                    temperature=temperature,
                    log_info=log_info
                ),
                media_type="text/event-stream",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Allow-Methods": "*",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
            
        elif workflow_type == "proprietary->general":
            # 专有模型 -> 通用模型流程
            logger.info("执行专有模型->通用模型流程")
            
            # 获取专有模型的提示词和配置
            proprietary_prompt = prompts_dict.get("proprietary")
            if not proprietary_prompt:
                raise HTTPException(status_code=404, detail="未找到 model_type=proprietary 的提示词")
            
            proprietary_provider = providers_dict.get("professional")
            if not proprietary_provider:
                raise HTTPException(status_code=404, detail="未找到 category=professional 的模型配置")
            
            # 获取通用模型的提示词和配置
            general_prompt = prompts_dict.get("general")
            if not general_prompt:
                raise HTTPException(status_code=404, detail="未找到 model_type=general 的提示词")
            
            general_provider = providers_dict.get("general")
            if not general_provider:
                raise HTTPException(status_code=404, detail="未找到 category=general 的模型配置")
            
            # 第一步：调用专有模型（非流式）
            logger.info("步骤1: 调用专有模型（非流式）")
            
            proprietary_system = proprietary_prompt.system_prompt or ""
            proprietary_user_template = proprietary_prompt.user_prompt or "{user_message}"
            proprietary_user_content = proprietary_user_template.replace("{user_message}", user_message)
            
            proprietary_messages = []
            if proprietary_system:
                proprietary_messages.append({"role": "system", "content": proprietary_system})
            proprietary_messages.append({"role": "user", "content": proprietary_user_content})
            
            # 专有模型参数
            proprietary_temperature = 0.7
            if proprietary_provider.custom_config and isinstance(proprietary_provider.custom_config, dict):
                temp_value = proprietary_provider.custom_config.get("temperature")
                if temp_value:
                    try:
                        proprietary_temperature = float(temp_value)
                    except (ValueError, TypeError):
                        pass
            
            logger.info(f"专有模型 - model: {proprietary_provider.default_model_name}, temp: {proprietary_temperature}")
            
            # 记录专有模型参数
            log_info["workflow_type"] = "proprietary->general"
            log_info["proprietary_params"] = {
                "model": proprietary_provider.default_model_name,
                "temperature": proprietary_temperature,
                "api_base": proprietary_provider.api_base
            }
            
            # 调用专有模型（非流式）
            try:
                # 解密专有模型的 API 密钥
                proprietary_api_key = decrypt_api_key(proprietary_provider.api_key) if proprietary_provider.api_key else ""
                
                proprietary_result = call_llm_non_stream(
                    messages=proprietary_messages,
                    api_base=proprietary_provider.api_base,
                    api_key=proprietary_api_key,
                    model=proprietary_provider.default_model_name,
                    temperature=proprietary_temperature
                )
                logger.info(f"专有模型返回内容长度: {len(proprietary_result)}")
                log_info["proprietary_response"] = proprietary_result
            except Exception as e:
                logger.error(f"专有模型调用失败: {str(e)}")
                raise HTTPException(status_code=500, detail=f"专有模型调用失败: {str(e)}")
            
            # 第二步：调用通用模型（流式）
            logger.info("步骤2: 调用通用模型（流式）")
            
            general_system = general_prompt.system_prompt or ""
            general_user_template = general_prompt.user_prompt or "{user_message}"
            # 将专有模型的结果作为通用模型的 user_message
            general_user_content = general_user_template.replace("{user_message}", proprietary_result)
            
            general_messages = []
            if general_system:
                general_messages.append({"role": "system", "content": general_system})
            general_messages.append({"role": "user", "content": general_user_content})
            
            # 通用模型参数
            general_temperature = 0.7
            if general_provider.custom_config and isinstance(general_provider.custom_config, dict):
                temp_value = general_provider.custom_config.get("temperature")
                if temp_value:
                    try:
                        general_temperature = float(temp_value)
                    except (ValueError, TypeError):
                        pass
            
            logger.info(f"通用模型 - model: {general_provider.default_model_name}, temp: {general_temperature}")
            
            # 记录通用模型参数
            general_params = {
                "model": general_provider.default_model_name,
                "temperature": general_temperature,
                "api_base": general_provider.api_base
            }
            # 添加文风信息
            if writing_style_info:
                general_params["writing_style"] = writing_style_info.get("writing_style", "")
                general_params["writing_features"] = writing_style_info.get("features", "")
            log_info["general_params"] = general_params
            
            # 解密通用模型的 API 密钥
            general_api_key = decrypt_api_key(general_provider.api_key) if general_provider.api_key else ""
            
            # 返回流式响应
            return StreamingResponse(
                stream_chat_response(
                    messages=general_messages,
                    api_base=general_provider.api_base,
                    api_key=general_api_key,
                    model=general_provider.default_model_name,
                    temperature=general_temperature,
                    log_info=log_info
                ),
                media_type="text/event-stream",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Allow-Methods": "*",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            raise HTTPException(status_code=400, detail=f"不支持的 workflow_type: {workflow_type}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"流式聊天接口错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"流式聊天失败: {str(e)}")


@router.get("/data/list")
async def get_chat_data(
    prompt_skip: int = Query(0, ge=0, description="Prompt 跳过的记录数"),
    prompt_limit: int = Query(10, ge=1, le=100, description="Prompt 返回的记录数"),
    workflow_skip: int = Query(0, ge=0, description="Workflow 跳过的记录数"),
    workflow_limit: int = Query(10, ge=1, le=100, description="Workflow 返回的记录数"),
    llm_provider_skip: int = Query(0, ge=0, description="LLM Provider 跳过的记录数"),
    llm_provider_limit: int = Query(10, ge=1, le=100, description="LLM Provider 返回的记录数"),
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    获取聊天所需的数据列表（prompt, workflow, llm_provider）
    用于前端下拉选择等场景
    """
    try:
        # 查询 Prompts
        prompts = db.query(Prompt).offset(prompt_skip).limit(prompt_limit).all()
        prompt_data = [PromptSchema.model_validate(p) for p in prompts]
        
        # 查询 Workflows
        workflows = db.query(Workflow).offset(workflow_skip).limit(workflow_limit).all()
        workflow_data = [WorkflowSchema.model_validate(w) for w in workflows]
        
        # 查询 LLM Providers
        providers = db.query(LLMProvider).offset(llm_provider_skip).limit(llm_provider_limit).all()
        provider_data = [LLMProviderSchema.model_validate(p) for p in providers]
        
        return {
            "success": True,
            "message": "查询成功",
            "data": {
                "prompts": prompt_data,
                "workflows": workflow_data,
                "llm_providers": provider_data
            }
        }
        
    except Exception as e:
        logger.error(f"获取聊天数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/logs")
async def get_logs(
    lines: int = Query(50, ge=1, le=1000, description="返回的日志行数"),
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    获取代理服务的日志
    调用 http://localhost:6006/v1/logs 获取日志列表
    """
    try:
        # 调用代理服务获取日志
        response = requests.get(
            PROXY_LOGS_URL,
            headers={
                "Authorization": f"Bearer {PROXY_API_KEY}",
                "Content-Type": "application/json"
            },
            params={"lines": lines},
            timeout=10
        )
        
        # 检查响应状态
        response.raise_for_status()
        
        # 返回日志内容
        log_content = response.text
        
        # 计算日志行数（用于统计）
        log_lines = log_content.split('\n')
        line_count = len([line for line in log_lines if line.strip()])
        
        return {
            "success": True,
            "message": "获取日志成功",
            "data": {
                "content": log_content,
                "line_count": line_count,
                "lines": lines
            }
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"请求代理服务日志失败: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail=f"无法连接到代理服务: {str(e)}"
        )
    except Exception as e:
        logger.error(f"获取日志失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")

