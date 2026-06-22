import json
import logging
from typing import Type, Dict, Any
import httpx
from pydantic import BaseModel
from app.config import settings

logger = logging.getLogger(__name__)

LLM_TIMEOUT = settings.LLM_TIMEOUT

async def call_local_llm_api(prompt: str, json_mode: bool = False) -> str:
    if not settings.LOCAL_LLM_URL:
        raise ValueError("LOCAL_LLM_URL is not configured.")

    logger.info(f"Local LLM: url={settings.LOCAL_LLM_URL}, model={settings.LOCAL_LLM_MODEL} (json_mode={json_mode})")

    payload = {
        "model": settings.LOCAL_LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 4096,
    }

    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.LOCAL_LLM_URL.rstrip('/')}/chat/completions",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=LLM_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        if content is None:
            logger.error(f"LLM returned null content. Full response: {data}")
            raise RuntimeError("LLM returned null content")
        return content


def _parse_and_validate_json(text_response: str, response_schema: Type[BaseModel]) -> Dict[str, Any]:
    clean_text = text_response.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    elif clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()

    validated = response_schema.model_validate_json(clean_text)
    if hasattr(validated, "model_dump"):
        return validated.model_dump()
    return validated


def _build_schema_example(response_schema: Type[BaseModel]) -> str:
    schema_dict = response_schema.model_json_schema()
    properties = schema_dict.get("properties", {})
    example = {}
    for k, v in properties.items():
        t = v.get("type", "string")
        if t == "array":
            example[k] = []
        elif t == "integer":
            example[k] = 0
        elif t == "number":
            example[k] = 0.0
        elif t == "boolean":
            example[k] = False
        else:
            example[k] = "text"
    return json.dumps(example)


def _build_schema_fields_block(response_schema: Type[BaseModel]) -> str:
    schema_dict = response_schema.model_json_schema()
    properties = schema_dict.get("properties", {})
    lines = []
    for name, prop in properties.items():
        t = prop.get("type", "string")
        desc = prop.get("description", "")
        allowed = None
        if "enum" in prop:
            allowed = ", ".join(f"'{v}'" for v in prop["enum"])
        if "const" in prop:
            allowed = f"'{prop['const']}'"
        req = "REQUIRED" if name in schema_dict.get("required", []) else "optional"
        field_desc = f"  - `{name}` ({t}, {req}): {desc}"
        if allowed:
            field_desc += f" [allowed values: {allowed}]"
        lines.append(field_desc)
    return "\n".join(lines)


async def generate_structured_json(prompt: str, response_schema: Type[BaseModel]) -> Dict[str, Any]:
    schema_fields = _build_schema_fields_block(response_schema)
    example_json = _build_schema_example(response_schema)

    system_prompt = (
        "You are a precise structured data extraction engine. Your task is to analyze the user's input "
        "and output ONLY valid JSON that strictly conforms to the schema below.\n\n"
        f"## Output Schema Fields\n"
        f"{schema_fields}\n\n"
        f"## Output Requirements\n"
        f"1. Output ONLY a raw JSON object — no markdown, no code fences, no explanations.\n"
        f"2. Every field must match its specified type exactly.\n"
        f"3. For optional fields: set to null if the information is not present in the input.\n"
        f"4. Do NOT fabricate or infer values that are not supported by the input.\n"
        f"5. Use only the allowed enum values where specified.\n"
        f"6. The JSON must start with '{{' and end with '}}'.\n\n"
        f"## Example Output Shape\n"
        f"```json\n{example_json}\n```"
    )

    full_prompt = f"{system_prompt}\n\n## Input\n{prompt}"

    text_response = await call_local_llm_api(full_prompt, json_mode=True)
    return _parse_and_validate_json(text_response, response_schema)


async def generate_text(prompt: str) -> str:
    if not settings.LOCAL_LLM_URL:
        raise ValueError("LOCAL_LLM_URL is not configured.")

    logger.info("Generating text using local LLM...")
    try:
        return await call_local_llm_api(prompt, json_mode=False)
    except Exception as e:
        logger.error(f"Local LLM text generation failed: {e}")
        raise RuntimeError(f"Local LLM failed to generate text: {e}") from e
