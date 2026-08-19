import json
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from .openapi import NormalizedAPISpec, APIEndpointSchema


class PostmanParser:
    """
    Parser for Postman Collection format (v2.0.0 and v2.1.0).
    Converts Postman collections into NormalizedAPISpec format.
    """

    def parse(self, raw_content: str) -> NormalizedAPISpec:
        try:
            data = json.loads(raw_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Postman collection: {e}")

        if not isinstance(data, dict):
            raise ValueError("Postman collection must be a JSON object")

        info = data.get("info", {})
        if not info or not isinstance(info, dict):
            # Check if this might be an item list directly
            if "item" not in data:
                raise ValueError("Not a valid Postman collection: missing 'info' or 'item' object")

        schema_url = str(info.get("schema", ""))
        # Check basic indicators of postman collection
        is_postman = (
            "schema.getpostman.com" in schema_url
            or "_postman_id" in info
            or "item" in data
        )
        if not is_postman:
            raise ValueError("Not a valid Postman collection schema")

        name = info.get("name", "Imported Postman Collection")
        version = info.get("version", "1.0.0")
        if isinstance(version, dict):
            version = f"{version.get('major', 1)}.{version.get('minor', 0)}.{version.get('patch', 0)}"
        elif not isinstance(version, str):
            version = "1.0.0"

        description = info.get("description", "")
        if isinstance(description, dict):
            description = description.get("content", "")

        # Extract collection-level auth
        collection_auth = self._parse_auth(data.get("auth"))

        normalized = NormalizedAPISpec(
            name=name,
            version=version,
            description=str(description or ""),
            authentication=collection_auth,
            endpoints=[],
        )

        base_urls: List[str] = []
        raw_items = data.get("item", [])
        if isinstance(raw_items, list):
            self._extract_items(raw_items, normalized, base_urls, inherited_tags=[])

        # Infer base_url from collected URLs
        if base_urls:
            normalized.base_url = self._select_common_base_url(base_urls)

        if not normalized.endpoints:
            raise ValueError("No valid HTTP requests found in Postman collection")

        return normalized

    def _extract_items(
        self,
        items: List[Dict[str, Any]],
        spec: NormalizedAPISpec,
        base_urls: List[str],
        inherited_tags: List[str],
    ) -> None:
        for item in items:
            if not isinstance(item, dict):
                continue

            name = item.get("name", "")
            # Check if item is a folder containing child items
            if "item" in item and isinstance(item["item"], list):
                folder_tag = name.strip() if name.strip() else "Folder"
                new_tags = inherited_tags + [folder_tag]
                self._extract_items(item["item"], spec, base_urls, new_tags)
            elif "request" in item:
                endpoint = self._parse_request(item, inherited_tags, base_urls)
                if endpoint:
                    spec.endpoints.append(endpoint)

    def _parse_request(
        self,
        item: Dict[str, Any],
        tags: List[str],
        base_urls: List[str],
    ) -> Optional[APIEndpointSchema]:
        req = item.get("request")
        if not req:
            return None

        # Request can be a raw URL string or a dictionary
        if isinstance(req, str):
            req = {"method": "GET", "url": req}

        method = req.get("method", "GET").upper()
        if method not in ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]:
            method = "GET"

        url_obj = req.get("url", {})
        path, base_url, query_params, path_params = self._parse_url(url_obj)

        if base_url:
            base_urls.append(base_url)

        summary = item.get("name", "")
        description = req.get("description", "")
        if isinstance(description, dict):
            description = description.get("content", "")

        # Headers
        headers_parsed: List[Dict[str, Any]] = []
        raw_headers = req.get("header", [])
        if isinstance(raw_headers, list):
            for h in raw_headers:
                if isinstance(h, dict) and not h.get("disabled", False):
                    key = h.get("key", "")
                    if key:
                        headers_parsed.append({
                            "name": key,
                            "type": "string",
                            "required": False,
                            "description": h.get("description", ""),
                            "example": h.get("value", ""),
                        })

        # Request body
        request_body = self._parse_body(req.get("body"))

        # Responses (from Postman example responses)
        responses: Dict[str, Any] = {}
        example_responses = item.get("response", [])
        if isinstance(example_responses, list):
            for ex in example_responses:
                if isinstance(ex, dict):
                    code = str(ex.get("code", 200))
                    ex_body = ex.get("body", "")
                    responses[code] = {
                        "description": ex.get("name", ex.get("status", "Response")),
                        "content": {"application/json": {"example": ex_body}} if ex_body else {},
                    }

        if not responses:
            responses = {"200": {"description": "Successful response"}}

        endpoint = APIEndpointSchema(
            method=method,
            path=path,
            summary=summary,
            description=str(description or ""),
            tags=tags or ["Default"],
            parameters={
                "path": path_params,
                "query": query_params,
                "header": headers_parsed,
                "cookie": [],
            },
            request_body=request_body,
            responses=responses,
        )
        return endpoint

    def _parse_url(self, url_data: Any) -> tuple[str, str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        raw_url = ""
        query_params: List[Dict[str, Any]] = []
        path_params: List[Dict[str, Any]] = []

        if isinstance(url_data, str):
            raw_url = url_data
        elif isinstance(url_data, dict):
            raw_url = url_data.get("raw", "")
            # Query params from object
            for q in url_data.get("query", []):
                if isinstance(q, dict) and not q.get("disabled", False):
                    key = q.get("key", "")
                    if key:
                        query_params.append({
                            "name": key,
                            "type": "string",
                            "required": False,
                            "description": q.get("description", ""),
                            "example": q.get("value", ""),
                        })
            # Path variables from object
            for v in url_data.get("variable", []):
                if isinstance(v, dict):
                    key = v.get("key", "")
                    if key:
                        path_params.append({
                            "name": key,
                            "type": "string",
                            "required": True,
                            "description": v.get("description", ""),
                            "example": v.get("value", ""),
                        })

        base_url = ""
        path = "/"

        if raw_url:
            # Clean up Postman environment templates in scheme/host e.g. {{baseUrl}}
            cleaned_url = raw_url.replace("{{baseUrl}}", "https://api.example.com")
            cleaned_url = re.sub(r"\{\{[^}]+\}\}", "placeholder", cleaned_url)

            # Check if has scheme
            if "://" in cleaned_url:
                parsed = urlparse(cleaned_url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                path = parsed.path or "/"
            else:
                # Relative path or host without scheme
                if cleaned_url.startswith("/"):
                    path = cleaned_url.split("?")[0]
                else:
                    path = "/" + cleaned_url.split("?")[0].lstrip("/")

        # Convert Postman path variables:
        # e.g., /users/:id -> /users/{id}
        path = re.sub(r":([a-zA-Z0-9_]+)", r"{\1}", path)
        # e.g., /users/{{id}} -> /users/{id}
        path = re.sub(r"\{\{([a-zA-Z0-9_]+)\}\}", r"{\1}", path)

        if not path.startswith("/"):
            path = "/" + path

        # If path variables were not in url_obj.variable, infer them from path
        found_vars = re.findall(r"\{([a-zA-Z0-9_]+)\}", path)
        existing_param_names = {p["name"] for p in path_params}
        for var_name in found_vars:
            if var_name not in existing_param_names:
                path_params.append({
                    "name": var_name,
                    "type": "string",
                    "required": True,
                    "description": f"Path parameter {var_name}",
                })

        return path, base_url, query_params, path_params

    def _parse_body(self, body_data: Any) -> Optional[Dict[str, Any]]:
        if not body_data or not isinstance(body_data, dict):
            return None

        mode = body_data.get("mode", "")
        if mode == "raw":
            raw_text = body_data.get("raw", "")
            try:
                parsed_json = json.loads(raw_text)
                return {
                    "content": {
                        "application/json": {
                            "example": parsed_json,
                            "schema": {"type": "object"},
                        }
                    },
                    "required": True,
                }
            except Exception:
                return {
                    "content": {"text/plain": {"example": raw_text}},
                    "required": True,
                }
        elif mode == "urlencoded":
            params = {}
            for p in body_data.get("urlencoded", []):
                if isinstance(p, dict) and not p.get("disabled", False):
                    params[p.get("key", "")] = p.get("value", "")
            return {
                "content": {
                    "application/x-www-form-urlencoded": {
                        "example": params,
                        "schema": {"type": "object"},
                    }
                },
                "required": True,
            }
        elif mode == "formdata":
            params = {}
            for p in body_data.get("formdata", []):
                if isinstance(p, dict) and not p.get("disabled", False):
                    params[p.get("key", "")] = p.get("value", "")
            return {
                "content": {
                    "multipart/form-data": {
                        "example": params,
                        "schema": {"type": "object"},
                    }
                },
                "required": True,
            }
        return None

    def _parse_auth(self, auth_data: Any) -> Dict[str, Any]:
        if not auth_data or not isinstance(auth_data, dict):
            return {"type": "none"}

        auth_type = auth_data.get("type", "none").lower()
        if auth_type == "bearer":
            bearer_params = auth_data.get("bearer", [])
            token_val = ""
            if isinstance(bearer_params, list):
                for p in bearer_params:
                    if isinstance(p, dict) and p.get("key") == "token":
                        token_val = p.get("value", "")
            return {"type": "bearer", "token": token_val}
        elif auth_type == "apikey":
            apikey_params = auth_data.get("apikey", [])
            key_name = "X-API-Key"
            in_loc = "header"
            if isinstance(apikey_params, list):
                for p in apikey_params:
                    if isinstance(p, dict):
                        if p.get("key") == "key":
                            key_name = p.get("value", key_name)
                        elif p.get("key") == "in":
                            in_loc = p.get("value", in_loc)
            return {"type": "apiKey", "name": key_name, "in": in_loc}
        elif auth_type in ["basic", "oauth2"]:
            return {"type": auth_type}

        return {"type": "none"}

    def _select_common_base_url(self, base_urls: List[str]) -> str:
        clean_urls = [u for u in base_urls if u and not u.startswith("placeholder")]
        if not clean_urls:
            return "https://api.example.com"
        # Pick the most frequent
        return max(set(clean_urls), key=clean_urls.count)
