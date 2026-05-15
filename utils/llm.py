# utils/llm.py
import os
import time
import asyncio
import logging
from dotenv import load_dotenv
import config

load_dotenv()
logger = logging.getLogger(__name__)

if config.LLM_BACKEND == "ollama":
    from openai import OpenAI, AsyncOpenAI
    _client = OpenAI(base_url=config.OLLAMA_BASE_URL, api_key="ollama")
    _async_client = AsyncOpenAI(base_url=config.OLLAMA_BASE_URL, api_key="ollama")

elif config.LLM_BACKEND == "groq":
    from groq import Groq, AsyncGroq
    _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    _async_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

def llm_call(system_prompt, user_prompt, model=None):
    selected_model = model or config.LLM_DEFAULT_MODEL
    for attempt in range(config.LLM_MAX_RETRIES):
        try:
            response = _client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"LLM call failed (attempt {attempt+1}/{config.LLM_MAX_RETRIES}): {e}")
            if attempt < config.LLM_MAX_RETRIES - 1:
                time.sleep(config.LLM_RETRY_DELAY_SECONDS)
            else:
                raise

async def llm_call_async(system_prompt, user_prompt, model=None):
    selected_model = model or config.LLM_DEFAULT_MODEL
    for attempt in range(config.LLM_MAX_RETRIES):
        try:
            response = await _async_client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Async LLM call failed (attempt {attempt+1}/{config.LLM_MAX_RETRIES}): {e}")
            if attempt < config.LLM_MAX_RETRIES - 1:
                await asyncio.sleep(config.LLM_RETRY_DELAY_SECONDS)
            else:
                raise