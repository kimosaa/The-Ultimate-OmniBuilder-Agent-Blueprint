"""
Enhanced LLM provider support with multiple backends.

Supports:
- Anthropic (Claude)
- OpenAI (GPT)
- Google (Gemini)
- AWS Bedrock (Claude via AWS)
- Ollama (local)
- LM Studio (local)
"""

import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional
import httpx

from omnibuilder.config import Config


class LLMProvider:
    """Base class for LLM providers."""

    def __init__(self, config: Config):
        self.config = config

    async def complete(self, prompt: str, system: str = "") -> str:
        """Get completion from LLM."""
        raise NotImplementedError

    async def stream_complete(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        """Stream completion from LLM."""
        raise NotImplementedError

    async def embed(self, text: str) -> List[float]:
        """Generate embeddings for text."""
        raise NotImplementedError


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, config: Config):
        super().__init__(config)
        self._client = None

    async def initialize(self) -> None:
        """Initialize the client."""
        try:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(
                api_key=self.config.llm.api_key,
                base_url=self.config.llm.base_url
            )
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    async def complete(self, prompt: str, system: str = "") -> str:
        """Get completion from Claude."""
        if not self._client:
            await self.initialize()

        response = await self._client.messages.create(
            model=self.config.llm.model,
            max_tokens=self.config.llm.max_tokens,
            temperature=self.config.llm.temperature,
            system=system or "You are OmniBuilder, an autonomous development agent.",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    async def stream_complete(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        """Stream completion from Claude."""
        if not self._client:
            await self.initialize()

        async with self._client.messages.stream(
            model=self.config.llm.model,
            max_tokens=self.config.llm.max_tokens,
            temperature=self.config.llm.temperature,
            system=system or "You are OmniBuilder.",
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            async for text in stream.text_stream:
                yield text


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    def __init__(self, config: Config):
        super().__init__(config)
        self._client = None

    async def initialize(self) -> None:
        """Initialize the client."""
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=self.config.llm.api_key,
                base_url=self.config.llm.base_url
            )
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    async def complete(self, prompt: str, system: str = "") -> str:
        """Get completion from GPT."""
        if not self._client:
            await self.initialize()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self.config.llm.model,
            messages=messages,
            max_tokens=self.config.llm.max_tokens,
            temperature=self.config.llm.temperature
        )

        return response.choices[0].message.content

    async def stream_complete(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        """Stream completion from GPT."""
        if not self._client:
            await self.initialize()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        stream = await self._client.chat.completions.create(
            model=self.config.llm.model,
            messages=messages,
            max_tokens=self.config.llm.max_tokens,
            temperature=self.config.llm.temperature,
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embed(self, text: str) -> List[float]:
        """Generate embeddings using OpenAI."""
        if not self._client:
            await self.initialize()

        response = await self._client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )

        return response.data[0].embedding


class GeminiProvider(LLMProvider):
    """Google Gemini provider."""

    def __init__(self, config: Config):
        super().__init__(config)
        self._client = None

    async def initialize(self) -> None:
        """Initialize the client."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.config.llm.api_key)
            self._client = genai.GenerativeModel(self.config.llm.model or 'gemini-pro')
        except ImportError:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")

    async def complete(self, prompt: str, system: str = "") -> str:
        """Get completion from Gemini."""
        if not self._client:
            await self.initialize()

        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = await asyncio.to_thread(
            self._client.generate_content,
            full_prompt
        )

        return response.text

    async def stream_complete(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        """Stream completion from Gemini."""
        if not self._client:
            await self.initialize()

        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        response = await asyncio.to_thread(
            self._client.generate_content,
            full_prompt,
            stream=True
        )

        for chunk in response:
            if chunk.text:
                yield chunk.text


class BedrockProvider(LLMProvider):
    """AWS Bedrock provider (Claude via AWS)."""

    def __init__(self, config: Config):
        super().__init__(config)
        self._client = None

    async def initialize(self) -> None:
        """Initialize the client."""
        try:
            import boto3
            self._client = boto3.client(
                service_name='bedrock-runtime',
                region_name=self.config.llm.base_url or 'us-east-1'
            )
        except ImportError:
            raise ImportError("boto3 not installed. Run: pip install boto3")

    async def complete(self, prompt: str, system: str = "") -> str:
        """Get completion from Bedrock."""
        if not self._client:
            await self.initialize()

        import json

        body = json.dumps({
            "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
            "max_tokens_to_sample": self.config.llm.max_tokens,
            "temperature": self.config.llm.temperature,
            "top_p": 0.9,
        })

        model_id = self.config.llm.model or "anthropic.claude-v2"

        response = await asyncio.to_thread(
            self._client.invoke_model,
            body=body,
            modelId=model_id,
            accept="application/json",
            contentType="application/json"
        )

        response_body = json.loads(response['body'].read())
        return response_body.get('completion', '')


class UnifiedLLMClient:
    """Unified client supporting multiple LLM providers."""

    def __init__(self, config: Config):
        self.config = config
        self._provider: Optional[LLMProvider] = None

    async def initialize(self) -> None:
        """Initialize the appropriate provider."""
        provider_name = self.config.llm.provider.lower()

        if provider_name == "anthropic":
            self._provider = AnthropicProvider(self.config)
        elif provider_name == "openai":
            self._provider = OpenAIProvider(self.config)
        elif provider_name == "gemini" or provider_name == "google":
            self._provider = GeminiProvider(self.config)
        elif provider_name == "bedrock" or provider_name == "aws":
            self._provider = BedrockProvider(self.config)
        else:
            raise ValueError(f"Unsupported provider: {provider_name}")

        await self._provider.initialize()

    async def complete(self, prompt: str, system: str = "") -> str:
        """Get completion from configured provider."""
        if not self._provider:
            await self.initialize()

        return await self._provider.complete(prompt, system)

    async def stream_complete(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        """Stream completion from configured provider."""
        if not self._provider:
            await self.initialize()

        async for chunk in self._provider.stream_complete(prompt, system):
            yield chunk

    async def embed(self, text: str) -> List[float]:
        """Generate embeddings (if supported by provider)."""
        if not self._provider:
            await self.initialize()

        if hasattr(self._provider, 'embed'):
            return await self._provider.embed(text)
        else:
            # Fallback to OpenAI for embeddings
            openai_provider = OpenAIProvider(self.config)
            await openai_provider.initialize()
            return await openai_provider.embed(text)
