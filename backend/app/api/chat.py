from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import logging
import requests
import os
import json
from app.database import get_db
from app.utils.response import success_response, error_response
from app.config import PROXY_LOGS_URL, PROXY_STATS_URL, PROXY_API_KEY

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

# 本地日志文件路径（作为备选方案）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_LOG_FILE = os.path.join(SCRIPT_DIR, "proxy.log")


@router.get("/logs")
async def get_logs(
    lines: int = Query(50, ge=1, le=100000, description="返回的日志行数")
):
    """
    获取代理服务的日志
    优先尝试从远程代理服务获取，如果失败则读取本地日志文件
    """
    log_content = None
    
    # 方法1: 尝试从远程代理服务获取日志
    try:
        response = requests.get(
            PROXY_LOGS_URL,
            headers={
                "Authorization": f"Bearer {PROXY_API_KEY}",
                "Content-Type": "application/json"
            },
            params={"lines": lines},
            timeout=5  # 缩短超时时间，快速失败
        )
        response.raise_for_status()
        log_content = response.text
        logger.info(f"成功从远程代理服务获取日志: {len(log_content)} 字符")
    except requests.exceptions.RequestException as e:
        logger.warning(f"无法从远程代理服务获取日志: {str(e)}，尝试读取本地日志文件")
    
    # 方法2: 如果远程获取失败，尝试读取本地日志文件
    if log_content is None:
        try:
            if os.path.exists(LOCAL_LOG_FILE):
                # 尝试多种编码方式读取日志文件
                encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig', 'latin-1']
                log_lines = None
                
                for encoding in encodings:
                    try:
                        with open(LOCAL_LOG_FILE, 'r', encoding=encoding, errors='replace') as f:
                            log_lines = f.readlines()
                            break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                
                if log_lines is None:
                    # 如果所有编码都失败，使用二进制模式读取
                    with open(LOCAL_LOG_FILE, 'rb') as f:
                        content = f.read()
                        log_lines = content.decode('utf-8', errors='replace').splitlines(keepends=True)
                
                # 取最后 N 行
                last_lines = log_lines[-lines:] if len(log_lines) > lines else log_lines
                log_content = "".join(last_lines)
                logger.info(f"成功从本地日志文件获取日志: {len(log_lines)} 行，返回 {len(last_lines)} 行")
            else:
                logger.warning(f"本地日志文件不存在: {LOCAL_LOG_FILE}")
        except Exception as e:
            logger.error(f"读取本地日志文件失败: {str(e)}", exc_info=True)
    
    # 如果两种方法都失败，返回错误
    if log_content is None:
        raise HTTPException(
            status_code=503,
            detail="无法获取日志：远程代理服务不可用且本地日志文件不存在或无法读取"
        )
    
    # 解析日志内容为 JSON 数组
    log_array: List[Dict[str, Any]] = []
    try:
        # 去除首尾空白字符
        log_content = log_content.strip()
        
        # 尝试解析为 JSON 数组
        if log_content:
            log_array = json.loads(log_content)
            # 确保是数组类型
            if not isinstance(log_array, list):
                logger.warning(f"日志内容不是数组格式，转换为数组")
                log_array = [log_array] if log_array else []
    except json.JSONDecodeError as e:
        logger.warning(f"解析日志 JSON 失败: {str(e)}，尝试按行解析")
        # 如果整体解析失败，尝试按行解析（每行一个 JSON 对象）
        try:
            log_lines = log_content.split('\n')
            for line in log_lines:
                line = line.strip()
                if line:
                    try:
                        log_item = json.loads(line)
                        log_array.append(log_item)
                    except json.JSONDecodeError:
                        # 跳过无法解析的行
                        continue
        except Exception as parse_error:
            logger.error(f"按行解析日志失败: {str(parse_error)}")
            # 如果解析完全失败，返回空数组
            log_array = []
    
    # 计算日志条数（用于统计）
    log_count = len(log_array)
    
    return success_response(
        message="获取日志成功",
        data={
            "content": log_array,  # 返回数组而不是字符串
            "line_count": log_count,
            "lines": lines
        }
    )


@router.get("/stats")
async def get_stats():
    """
    获取最近7天的 token 消耗统计
    从远程代理服务获取统计数据
    """
    try:
        response = requests.get(
            PROXY_STATS_URL,
            headers={
                "Authorization": f"Bearer {PROXY_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=15
        )
        response.raise_for_status()
        
        # 解析返回的 JSON 数据
        stats_data = response.json()
        logger.info(f"成功从远程代理服务获取统计数据")
        
        return success_response(
            message="获取统计数据成功",
            data=stats_data
        )
    except requests.exceptions.Timeout:
        logger.error("获取统计数据超时")
        raise HTTPException(
            status_code=504,
            detail="获取统计数据超时，请稍后重试"
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"无法从远程代理服务获取统计数据: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"无法获取统计数据：{str(e)}"
        )
    except json.JSONDecodeError as e:
        logger.error(f"解析统计数据 JSON 失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="统计数据格式错误"
        )
    except Exception as e:
        logger.error(f"获取统计数据时发生未知错误: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"获取统计数据失败：{str(e)}"
        )

