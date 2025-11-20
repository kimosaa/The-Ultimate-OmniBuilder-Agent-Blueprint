"""
P3.2 Web Research Tools

Web search, scraping, and API interactions.
"""

from typing import Any, Dict, List, Optional
import httpx


class SearchResult:
    """A web search result."""
    def __init__(self, title: str, url: str, snippet: str):
        self.title = title
        self.url = url
        self.snippet = snippet


class ScrapedContent:
    """Content scraped from a webpage."""
    def __init__(self, url: str, title: str, content: str, links: List[str]):
        self.url = url
        self.title = title
        self.content = content
        self.links = links


class APIResponse:
    """Response from an API call."""
    def __init__(self, status: int, data: Any, headers: Dict[str, str]):
        self.status = status
        self.data = data
        self.headers = headers
        self.success = 200 <= status < 300


class DownloadResult:
    """Result of a file download."""
    def __init__(self, success: bool, path: str, size: int, message: str):
        self.success = success
        self.path = path
        self.size = size
        self.message = message


class DocResult:
    """Documentation search result."""
    def __init__(self, title: str, url: str, content: str, source: str):
        self.title = title
        self.url = url
        self.content = content
        self.source = source


class PackageInfo:
    """Information about a package."""
    def __init__(self, name: str, version: str, description: str, dependencies: List[str]):
        self.name = name
        self.version = version
        self.description = description
        self.dependencies = dependencies


class WebResearchTools:
    """Web research and information retrieval tools."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def search_web(
        self,
        query: str,
        num_results: int = 10
    ) -> List[SearchResult]:
        """
        Search the web.

        Note: Requires API key for actual implementation.
        This is a placeholder that demonstrates the interface.
        """
        # Placeholder - would use search API (Google, Bing, etc.)
        return [
            SearchResult(
                title=f"Result for: {query}",
                url=f"https://example.com/search?q={query}",
                snippet="This is a placeholder search result. Implement with actual search API."
            )
        ]

    async def scrape_url(
        self,
        url: str,
        selector: Optional[str] = None
    ) -> ScrapedContent:
        """
        Scrape content from a webpage.

        Args:
            url: URL to scrape
            selector: Optional CSS selector to extract specific content
        """
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            html = response.text

            # Basic parsing (would use BeautifulSoup in production)
            title = ""
            if "<title>" in html:
                start = html.find("<title>") + 7
                end = html.find("</title>")
                title = html[start:end]

            # Extract text content (simplified)
            import re
            # Remove scripts and styles
            content = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
            content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
            # Remove tags
            content = re.sub(r'<[^>]+>', ' ', content)
            # Clean whitespace
            content = ' '.join(content.split())

            # Extract links
            links = re.findall(r'href=["\']([^"\']+)["\']', html)

            return ScrapedContent(
                url=url,
                title=title,
                content=content[:5000],  # Limit content
                links=links[:50]  # Limit links
            )
        except Exception as e:
            return ScrapedContent(
                url=url,
                title="Error",
                content=str(e),
                links=[]
            )

    async def fetch_api(
        self,
        url: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> APIResponse:
        """
        Call a REST API.

        Args:
            url: API endpoint
            method: HTTP method
            data: Request data
            headers: Request headers
        """
        try:
            request_headers = headers or {}

            if method.upper() == "GET":
                response = await self.client.get(url, headers=request_headers, params=data)
            elif method.upper() == "POST":
                response = await self.client.post(url, headers=request_headers, json=data)
            elif method.upper() == "PUT":
                response = await self.client.put(url, headers=request_headers, json=data)
            elif method.upper() == "DELETE":
                response = await self.client.delete(url, headers=request_headers)
            else:
                return APIResponse(400, {"error": f"Unsupported method: {method}"}, {})

            try:
                data = response.json()
            except Exception:
                data = response.text

            return APIResponse(
                status=response.status_code,
                data=data,
                headers=dict(response.headers)
            )
        except Exception as e:
            return APIResponse(
                status=0,
                data={"error": str(e)},
                headers={}
            )

    async def download_file(
        self,
        url: str,
        dest: str
    ) -> DownloadResult:
        """
        Download a file from URL.

        Args:
            url: URL to download
            dest: Destination path
        """
        try:
            async with self.client.stream("GET", url) as response:
                response.raise_for_status()

                with open(dest, 'wb') as f:
                    size = 0
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
                        size += len(chunk)

            return DownloadResult(
                success=True,
                path=dest,
                size=size,
                message="Download complete"
            )
        except Exception as e:
            return DownloadResult(
                success=False,
                path=dest,
                size=0,
                message=str(e)
            )

    async def search_documentation(
        self,
        query: str,
        source: str = "devdocs"
    ) -> List[DocResult]:
        """
        Search documentation sources.

        Args:
            query: Search query
            source: Documentation source
        """
        # Placeholder - would integrate with documentation APIs
        return [
            DocResult(
                title=f"Documentation: {query}",
                url=f"https://devdocs.io/#q={query}",
                content="Placeholder for documentation content",
                source=source
            )
        ]

    async def get_package_info(
        self,
        package: str,
        registry: str = "pypi"
    ) -> PackageInfo:
        """
        Get package metadata from registry.

        Args:
            package: Package name
            registry: Package registry (pypi, npm, etc.)
        """
        if registry == "pypi":
            url = f"https://pypi.org/pypi/{package}/json"
        elif registry == "npm":
            url = f"https://registry.npmjs.org/{package}"
        else:
            return PackageInfo(package, "", "Unknown registry", [])

        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            if registry == "pypi":
                info = data.get("info", {})
                return PackageInfo(
                    name=info.get("name", package),
                    version=info.get("version", ""),
                    description=info.get("summary", ""),
                    dependencies=info.get("requires_dist", []) or []
                )
            elif registry == "npm":
                latest = data.get("dist-tags", {}).get("latest", "")
                version_data = data.get("versions", {}).get(latest, {})
                return PackageInfo(
                    name=data.get("name", package),
                    version=latest,
                    description=data.get("description", ""),
                    dependencies=list(version_data.get("dependencies", {}).keys())
                )

        except Exception as e:
            return PackageInfo(package, "", str(e), [])
