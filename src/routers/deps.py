"""
API 依赖项 - X-API-Key 认证
"""
import os
from fastapi import Header, HTTPException, status


API_KEY = os.getenv("API_KEY", "sk-test-example")


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key"
        )
    return x_api_key
