import json
import re
from typing import Any

import httpx
from app.config import settings


class LLMService:
    def __init__(self):
        self.ollama_available = False
        self.groq_available = False

    async def check_provider_status(self) -> dict[str, Any]:
        """
        Checks connectivity to Ollama and validity of Groq API configuration.
        """
        ollama_ok = False
        model_found = False
        groq_ok = bool(settings.groq_api_key and len(settings.groq_api_key.strip()) > 10)

        # Test Ollama
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                res = await client.get(f"{settings.ollama_base_url}/api/tags")
                if res.status_code == 200:
                    ollama_ok = True
                    tags = res.json().get("models", [])
                    target_model = settings.ollama_model.split(":")[0]
                    for m in tags:
                        if target_model in m.get("name", ""):
                            model_found = True
                            break
        except Exception:
            ollama_ok = False

        self.ollama_available = ollama_ok
        self.groq_available = groq_ok

        active_provider = "offline"
        if settings.preferred_provider == "ollama" and ollama_ok:
            active_provider = "ollama"
        elif settings.preferred_provider == "groq" and groq_ok:
            active_provider = "groq"
        elif settings.preferred_provider == "auto":
            if ollama_ok:
                active_provider = "ollama"
            elif groq_ok:
                active_provider = "groq"
            else:
                active_provider = "offline"
        elif settings.preferred_provider == "offline":
            active_provider = "offline"

        return {
            "ollama_connected": ollama_ok,
            "ollama_model_available": model_found,
            "groq_configured": groq_ok,
            "active_provider": active_provider,
        }

    async def _call_ollama(
        self, prompt: str, system_prompt: str = "", json_mode: bool = False
    ) -> str | None:
        try:
            payload = {
                "model": settings.ollama_model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_ctx": 4096},
            }
            if json_mode:
                payload["format"] = "json"

            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(f"{settings.ollama_base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    return res.json().get("response", "")
        except Exception as e:
            print(f"Ollama call failed: {e}")
        return None

    async def _call_groq(
        self, prompt: str, system_prompt: str = "", json_mode: bool = False
    ) -> str | None:
        if not settings.groq_api_key:
            return None
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": settings.groq_model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 2048,
            }
            if json_mode:
                payload["response_format"] = {"type": "json_object"}

            headers = {
                "Authorization": f"Bearer {settings.groq_api_key.strip()}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=35.0) as client:
                res = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers
                )
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
        except Exception as e:
            print(f"Groq call failed: {e}")
        return None

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str = "",
        json_mode: bool = False,
        fallback_offline_fn=None,
    ) -> tuple[str, str]:
        """
        Executes generation through the provider hierarchy.
        Returns tuple: (response_text, provider_name_used)
        """
        status = await self.check_provider_status()
        active = status["active_provider"]

        # Strategy 1: Ollama first if selected or auto with ollama up
        if active == "ollama":
            res = await self._call_ollama(prompt, system_prompt, json_mode)
            if res:
                return res, f"Ollama ({settings.ollama_model})"
            # Fall back to Groq if Ollama fails mid-run
            if status["groq_configured"]:
                res = await self._call_groq(prompt, system_prompt, json_mode)
                if res:
                    return res, f"Groq Fallback ({settings.groq_model})"

        # Strategy 2: Groq
        elif active == "groq":
            res = await self._call_groq(prompt, system_prompt, json_mode)
            if res:
                return res, f"Groq ({settings.groq_model})"
            # Fall back to Ollama if up
            if status["ollama_connected"]:
                res = await self._call_ollama(prompt, system_prompt, json_mode)
                if res:
                    return res, f"Ollama Fallback ({settings.ollama_model})"

        # Strategy 3: Built-in Offline Fallback
        if fallback_offline_fn:
            offline_res = fallback_offline_fn()
            return offline_res, "Local Heuristic Engine"

        return (
            "No LLM provider is currently reachable. Please start Ollama or configure a Groq API key in Settings.",
            "Error",
        )

    def clean_json_response(self, text: str) -> dict[str, Any]:
        """
        Extracts and parses JSON from raw LLM output, handling markdown fences and formatting.
        """
        cleaned = text.strip()
        # Remove ```json ... ``` or ``` ... ```
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1)
        # Find first { and last }
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start : end + 1]

        try:
            return json.loads(cleaned)
        except Exception:
            # Try to fix unescaped newlines or trailing commas
            cleaned_sub = re.sub(r",\s*([\]}])", r"\1", cleaned)
            return json.loads(cleaned_sub)


llm_service = LLMService()
