"""
P2.4 Local Inference Handler (Ollama/LM Studio)

Connects to and uses locally-hosted open-source LLMs.
"""

import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional
import httpx


class ModelInfo:
    """Information about a local model."""

    def __init__(self, name: str, size: int, family: str, parameters: Dict[str, Any]):
        self.name = name
        self.size = size  # in bytes
        self.family = family
        self.parameters = parameters


class LLMResponse:
    """Response from local LLM inference."""

    def __init__(self, content: str, model: str, tokens_used: int = 0):
        self.content = content
        self.model = model
        self.tokens_used = tokens_used


class OllamaClient:
    """Client for Ollama local LLM."""

    def __init__(self, host: str = "localhost", port: int = 11434):
        self.base_url = f"http://{host}:{port}"
        self.client = httpx.AsyncClient(timeout=120.0)

    async def close(self) -> None:
        """Close the client."""
        await self.client.aclose()

    async def list_models(self) -> List[ModelInfo]:
        """List available models."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()

            models = []
            for model_data in data.get("models", []):
                model = ModelInfo(
                    name=model_data.get("name", ""),
                    size=model_data.get("size", 0),
                    family=model_data.get("details", {}).get("family", ""),
                    parameters=model_data.get("details", {})
                )
                models.append(model)

            return models
        except Exception:
            return []

    async def generate(
        self,
        prompt: str,
        model: str = "llama2",
        options: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """
        Generate completion from Ollama.

        Args:
            prompt: Input prompt
            model: Model name
            options: Generation options

        Returns:
            LLMResponse with generated text
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }

        if options:
            payload["options"] = options

        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                content=data.get("response", ""),
                model=model,
                tokens_used=data.get("eval_count", 0)
            )
        except Exception as e:
            return LLMResponse(
                content=f"Error: {str(e)}",
                model=model,
                tokens_used=0
            )

    async def stream_generate(
        self,
        prompt: str,
        model: str = "llama2",
        options: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """
        Stream generation from Ollama.

        Args:
            prompt: Input prompt
            model: Model name
            options: Generation options

        Yields:
            Generated text chunks
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True
        }

        if options:
            payload["options"] = options

        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/generate",
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    import json
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                    except json.JSONDecodeError:
                        pass

    async def embed(self, text: str, model: str = "llama2") -> List[float]:
        """
        Generate embeddings.

        Args:
            text: Text to embed
            model: Model name

        Returns:
            Embedding vector
        """
        payload = {
            "model": model,
            "prompt": text
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])
        except Exception:
            return []


class LMStudioClient:
    """Client for LM Studio local LLM."""

    def __init__(self, host: str = "localhost", port: int = 1234):
        self.base_url = f"http://{host}:{port}/v1"
        self.client = httpx.AsyncClient(timeout=120.0)

    async def close(self) -> None:
        """Close the client."""
        await self.client.aclose()

    async def list_models(self) -> List[ModelInfo]:
        """List available models."""
        try:
            response = await self.client.get(f"{self.base_url}/models")
            response.raise_for_status()
            data = response.json()

            models = []
            for model_data in data.get("data", []):
                model = ModelInfo(
                    name=model_data.get("id", ""),
                    size=0,
                    family="",
                    parameters={}
                )
                models.append(model)

            return models
        except Exception:
            return []

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """
        Generate completion from LM Studio (OpenAI-compatible API).

        Args:
            prompt: Input prompt
            model: Model name (optional for LM Studio)
            options: Generation options

        Returns:
            LLMResponse with generated text
        """
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2048,
            "stream": False
        }

        if model:
            payload["model"] = model

        if options:
            payload.update(options)

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {}).get("total_tokens", 0)

            return LLMResponse(
                content=content,
                model=model or "default",
                tokens_used=tokens
            )
        except Exception as e:
            return LLMResponse(
                content=f"Error: {str(e)}",
                model=model or "default",
                tokens_used=0
            )

    async def stream_generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """
        Stream generation from LM Studio.

        Args:
            prompt: Input prompt
            model: Model name
            options: Generation options

        Yields:
            Generated text chunks
        """
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2048,
            "stream": True
        }

        if model:
            payload["model"] = model

        if options:
            payload.update(options)

        async with self.client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    import json
                    try:
                        data = json.loads(line[6:])
                        if data.get("choices"):
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                    except json.JSONDecodeError:
                        pass


class LocalInferenceHandler:
    """Unified handler for local LLM inference."""

    def __init__(self):
        self._ollama_client: Optional[OllamaClient] = None
        self._lmstudio_client: Optional[LMStudioClient] = None

    def connect_ollama(
        self,
        host: str = "localhost",
        port: int = 11434
    ) -> OllamaClient:
        """
        Connect to Ollama.

        Args:
            host: Ollama host
            port: Ollama port

        Returns:
            OllamaClient instance
        """
        self._ollama_client = OllamaClient(host, port)
        return self._ollama_client

    def connect_lmstudio(
        self,
        host: str = "localhost",
        port: int = 1234
    ) -> LMStudioClient:
        """
        Connect to LM Studio.

        Args:
            host: LM Studio host
            port: LM Studio port

        Returns:
            LMStudioClient instance
        """
        self._lmstudio_client = LMStudioClient(host, port)
        return self._lmstudio_client

    async def list_local_models(self) -> List[ModelInfo]:
        """List all available local models."""
        models = []

        if self._ollama_client:
            models.extend(await self._ollama_client.list_models())

        if self._lmstudio_client:
            models.extend(await self._lmstudio_client.list_models())

        return models

    async def inference(
        self,
        prompt: str,
        model: str,
        provider: str = "ollama",
        params: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """
        Run inference on local model.

        Args:
            prompt: Input prompt
            model: Model name
            provider: Provider (ollama or lmstudio)
            params: Additional parameters

        Returns:
            LLMResponse with generated text
        """
        if provider == "ollama" and self._ollama_client:
            return await self._ollama_client.generate(prompt, model, params)
        elif provider == "lmstudio" and self._lmstudio_client:
            return await self._lmstudio_client.generate(prompt, model, params)
        else:
            return LLMResponse(
                content="Error: No local LLM client connected",
                model=model,
                tokens_used=0
            )

    async def stream_inference(
        self,
        prompt: str,
        model: str,
        provider: str = "ollama"
    ) -> AsyncIterator[str]:
        """
        Stream inference from local model.

        Args:
            prompt: Input prompt
            model: Model name
            provider: Provider

        Yields:
            Generated text chunks
        """
        if provider == "ollama" and self._ollama_client:
            async for chunk in self._ollama_client.stream_generate(prompt, model):
                yield chunk
        elif provider == "lmstudio" and self._lmstudio_client:
            async for chunk in self._lmstudio_client.stream_generate(prompt, model):
                yield chunk

    async def embed_text(
        self,
        text: str,
        model: str,
        provider: str = "ollama"
    ) -> List[float]:
        """
        Generate embeddings locally.

        Args:
            text: Text to embed
            model: Embedding model
            provider: Provider

        Returns:
            Embedding vector
        """
        if provider == "ollama" and self._ollama_client:
            return await self._ollama_client.embed(text, model)
        else:
            return []

    async def close(self) -> None:
        """Close all clients."""
        if self._ollama_client:
            await self._ollama_client.close()
        if self._lmstudio_client:
            await self._lmstudio_client.close()
