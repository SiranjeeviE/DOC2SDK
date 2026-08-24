import logging
import re
from bs4 import BeautifulSoup
import httpx

from ..core.url_validator import validate_url, create_safe_client, URLValidationError

logger = logging.getLogger(__name__)


class ScraperService:
    @staticmethod
    async def scrape(url: str) -> str:
        # Validate URL for SSRF protection before any network call
        validated_url = validate_url(url)

        client = create_safe_client(timeout=30.0)
        async with client:
            try:
                response = await client.get(validated_url)
                response.raise_for_status()
                
                # Direct detection of API specs (JSON or YAML)
                content_type = response.headers.get("content-type", "").lower()
                url_path = validated_url.split('?')[0]
                is_json = "application/json" in content_type or url_path.endswith(".json")
                is_yaml = "yaml" in content_type or url_path.endswith(".yaml") or url_path.endswith(".yml")
                if is_json or is_yaml:
                    return f"RAW_SPEC_JSON:\n{response.text}"
                
                html = response.text
            except URLValidationError:
                raise
            except httpx.HTTPStatusError as e:
                logger.warning("HTTP error %s while fetching documentation from %s", e.response.status_code, validated_url)
                raise ValueError(f"HTTP error {e.response.status_code} fetching documentation.")
            except httpx.TimeoutException:
                logger.warning("Timeout fetching documentation from %s", validated_url)
                raise ValueError("Documentation fetch timed out.")
            except Exception as e:
                logger.error("Failed to fetch documentation from %s: %s", validated_url, str(e))
                raise ValueError("Failed to fetch documentation from the provided URL.")

        # Use lxml for speed if available, fallback to html.parser
        try:
            soup = BeautifulSoup(html, 'lxml')
        except Exception:
            soup = BeautifulSoup(html, 'html.parser')

        # Remove irrelevant elements
        for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header', 'iframe']):
            element.decompose()

        # Extract text and code blocks
        # We want to preserve structure roughly
        text_content = []
        
        # Helper to process a node
        def process_node(node):
            if node.name in ['script', 'style', 'nav', 'footer', 'aside', 'header', 'iframe', 'svg']:
                return ""
            
            text = ""
            if node.name in ['h1', 'h2', 'h3', 'h4']:
                text = f"\n\n### {node.get_text().strip()} ###\n"
            elif node.name in ['pre', 'code']:
                text = f"\n```\n{node.get_text().strip()}\n```\n"
            elif node.name == 'table':
                # Attempt to format table as text
                rows = []
                for tr in node.find_all('tr'):
                    cells = [td.get_text().strip() for td in tr.find_all(['td', 'th'])]
                    rows.append(" | ".join(cells))
                text = "\n" + "\n".join(rows) + "\n"
            elif node.name in ['p', 'li', 'div', 'span']:
                 # Only add meaningful text
                 t = node.get_text().strip()
                 if len(t) > 2: # Reduce noise
                    text = f"{t}\n"
            
            return text

        # Instead of finding specific tags, iterate over main content areas or just body
        # But to keep it simple and robust, let's target the likely content containers
        # If we can't find a main container, we fallback to body
        content_root = soup.find('main') or soup.find('article') or soup.find('body')
        
        if content_root:
            # Get text with separator to preserve some layout
            # separator=" " might merge too much, so we stick to our manual iteration or use get_text
            cleaned_text = content_root.get_text(separator="\n", strip=True)
        else:
             # Fallback
             cleaned_text = soup.get_text(separator="\n", strip=True)

        # Post-processing to remove excessive whitespace
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        # remove excessive newlines
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        return cleaned_text[:50000] # Cap to 50k chars (Balance between depth and speed)
