from fastapi import APIRouter
from openai import AsyncOpenAI

from app.utils.config import settings
from app.utils.logger import logger

router = APIRouter()

openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


@router.post("/agent/response")
async def get_agent_response(message: str) -> str:
    logger.info(f"Getting agent response for message: {message}")
    completion = await openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message},
        ],
    )
    logger.info(f"Agent response: {completion.choices[0].message.content}")
    return completion.choices[0].message.content or ""
