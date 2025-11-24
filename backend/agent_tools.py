from typing import Dict, Any, List, Optional
import httpx
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import parse_qs, urlparse, unquote, urljoin


def detect_query_locale(query: str) -> str:
    """Rudimentary locale detection based on Unicode ranges."""
    locale_map = [
        (r"[\u4e00-\u9fff]", "zh-hant-tw"),
        (r"[\u3040-\u309f\u30a0-\u30ff]", "ja-jp"),
        (r"[\u3130-\u318f\uac00-\ud7af]", "ko-kr"),
        (r"[\u0400-\u04FF]", "ru-ru"),
        (r"[\u0600-\u06FF]", "ar-ae"),
        (r"[\u0370-\u03FF]", "el-gr"),
        (r"[\u0590-\u05FF]", "iw-il"),
    ]
    for pattern, locale in locale_map:
        if re.search(pattern, query):
            return locale
    return "wt-wt"


async def translate_to_english(text: str) -> str:
    translate_url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": "en",
        "dt": "t",
        "q": text
    }
    async with httpx.AsyncClient(timeout=6.0) as client:
        response = await client.get(translate_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data and isinstance(data, list) and data[0]:
            translated_segments = [segment[0] for segment in data[0] if segment and segment[0]]
            combined = ''.join(translated_segments).strip()
            return combined or text
    return text


async def fetch_google_news_results(query: str, max_results: int) -> List[Dict[str, Any]]:
    rss_url = "https://news.google.com/rss/search"
    params = {
        "q": query,
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en"
    }
    headers = {"User-Agent": "Mozilla/5.0 (compatible; MIDASBot/1.0)"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(rss_url, params=params, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "xml")
        items = soup.find_all("item")[:max_results]
        results = []
        for item in items:
            title = item.title.text if item.title else "Untitled"
            link = item.link.text if item.link else ""
            description = item.description.text if item.description else ""
            results.append({
                "title": title,
                "href": link,
                "body": description,
                "locale": "en",
                "source": "google_news"
            })
        return results


def normalize_duckduckgo_redirect(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
        params = parse_qs(parsed.query)
        if "uddg" in params:
            return unquote(params["uddg"][0])
    return url


class AgentTool:
    """Base class for agent tools"""
    
    name: str
    description: str
    parameters: Dict[str, Any]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError


class WebSearchTool(AgentTool):
    name = "web_search"
    description = "Search the web for information using DuckDuckGo"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 5
            }
        },
        "required": ["query"]
    }
    
    async def execute(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        try:
            locale = detect_query_locale(query)
            ddg_primary = "https://html.duckduckgo.com/html/"
            ddg_fallback = "https://duckduckgo.com/html/"
            payload = {
                "q": query,
                "kl": locale,
                "ia": "web"
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; MIDASBot/1.0)",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            redirect_statuses = {301, 302, 303, 307, 308}
            async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
                response = await client.post(ddg_primary, data=payload)
                if response.status_code in redirect_statuses:
                    redirect_url = response.headers.get("location")
                    if redirect_url:
                        redirect_url = urljoin(ddg_primary, redirect_url)
                        response = await client.post(redirect_url, data=payload)
                if response.status_code in redirect_statuses:
                    response = await client.post(ddg_fallback, data=payload, follow_redirects=True)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                raw_results = soup.select(".result")
                results = []
                for item in raw_results:
                    if len(results) >= max_results:
                        break
                    title_el = item.select_one(".result__a")
                    snippet_el = item.select_one(".result__snippet")
                    if not title_el:
                        continue
                    link = title_el.get("href", "")
                    link = normalize_duckduckgo_redirect(link)
                    title = title_el.get_text(strip=True) or "Untitled"
                    description = snippet_el.get_text(" ", strip=True) if snippet_el else ""
                    results.append({
                        "title": title,
                        "href": link,
                        "body": description,
                        "locale": locale,
                        "source": "duckduckgo"
                    })
                if not results:
                    translated_query = query
                    if locale != "wt-wt":
                        try:
                            translated_query = await translate_to_english(query)
                        except Exception:
                            translated_query = query
                    try:
                        news_results = await fetch_google_news_results(translated_query, max_results)
                        if news_results:
                            return {"success": True, "results": news_results}
                    except Exception:
                        pass
                    results.append({
                        "title": "No live results",
                        "href": "",
                        "body": f"No web or news items for: {query}",
                        "locale": locale,
                        "source": "none"
                    })
                return {"success": True, "results": results}
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class WebScrapeTool(AgentTool):
    name = "web_scrape"
    description = "Scrape content from a webpage"
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to scrape"
            }
        },
        "required": ["url"]
    }
    
    async def execute(self, url: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text
                text = soup.get_text()
                
                # Clean up text
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)
                
                return {
                    "success": True,
                    "url": url,
                    "content": text[:10000],  # Limit to 10k chars
                    "title": soup.title.string if soup.title else None
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class CalculatorTool(AgentTool):
    name = "calculator"
    description = "Perform mathematical calculations"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The mathematical expression to evaluate"
            }
        },
        "required": ["expression"]
    }
    
    async def execute(self, expression: str) -> Dict[str, Any]:
        try:
            # Safe eval with limited scope
            allowed_names = {
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow
            }
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return {
                "success": True,
                "expression": expression,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class ImageGenerationTool(AgentTool):
    def __init__(self):
        self.name = "generate_image"
        self.description = "Generate or transform images based on text descriptions. Use this when the user asks to: create/generate/draw a new image, OR transform/modify/edit an uploaded image (e.g., add glasses, change style, apply effects). If an image is uploaded, it will be used as the base for transformation. Returns the URL of the generated image."
        self.parameters = {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Detailed description of the image to generate. Be specific about style, composition, colors, mood, etc."
                },
                "style": {
                    "type": "string",
                    "enum": ["vivid", "natural"],
                    "description": "Style of the generated image. 'vivid' for hyper-real and dramatic, 'natural' for more natural and less hyper-real."
                }
            },
            "required": ["prompt"]
        }
    
    async def execute(self, prompt: str, style: Optional[str] = None, uploaded_image: Optional[str] = None) -> Dict[str, Any]:
        """Execute image generation"""
        try:
            from backend.routes.chat import generate_image_from_prompt
            
            result = await generate_image_from_prompt(
                prompt=prompt,
                model="gpt-image-1",
                image=uploaded_image
            )
            
            return {
                "success": True,
                "image_url": result["url"],
                "revised_prompt": result.get("revised_prompt")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class AgentToolManager:
    def __init__(self):
        self.tools = {
            "web_search": WebSearchTool(),
            "web_scrape": WebScrapeTool(),
            "calculator": CalculatorTool(),
            "generate_image": ImageGenerationTool()
        }
    
    def get_tool(self, tool_name: str) -> AgentTool:
        return self.tools.get(tool_name)
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools.values()
        ]
    
    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """Format tools for LLM function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            for tool in self.tools.values()
        ]


agent_tool_manager = AgentToolManager()
