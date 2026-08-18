import json
import yaml
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class APIEndpointSchema(BaseModel):
    method: str
    path: str
    summary: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Any] = {}
    tags: List[str] = []

class NormalizedAPISpec(BaseModel):
    name: str
    version: str
    base_url: str = ""
    description: str = ""
    authentication: Dict[str, Any] = {}
    endpoints: List[APIEndpointSchema] = []

class OpenAPIParser:
    def parse(self, raw_content: str) -> NormalizedAPISpec:
        """
        Parses OpenAPI/Swagger specification (JSON or YAML)
        """
        try:
            spec = json.loads(raw_content)
        except json.JSONDecodeError:
            try:
                spec = yaml.safe_load(raw_content)
            except yaml.YAMLError:
                raise ValueError("Invalid OpenAPI specification: must be JSON or YAML")

        if not spec or "openapi" not in spec and "swagger" not in spec:
            raise ValueError("Not a valid OpenAPI/Swagger specification")

        normalized = NormalizedAPISpec(
            name=spec.get("info", {}).get("title", "Unknown API"),
            version=spec.get("info", {}).get("version", "1.0.0"),
            description=spec.get("info", {}).get("description", ""),
        )

        # Base URL extraction
        if "servers" in spec and spec["servers"]:
            normalized.base_url = spec["servers"][0].get("url", "")
        elif "host" in spec:
            scheme = spec.get("schemes", ["https"])[0]
            base_path = spec.get("basePath", "")
            normalized.base_url = f"{scheme}://{spec['host']}{base_path}"

        # Authentication
        security_schemes = spec.get("components", {}).get("securitySchemes", {}) or spec.get("securityDefinitions", {})
        if security_schemes:
            # For simplicity, take the first one
            name = list(security_schemes.keys())[0]
            scheme = security_schemes[name]
            normalized.authentication = {
                "name": name,
                "type": scheme.get("type"),
                "scheme": scheme.get("scheme"),
                "in": scheme.get("in"),
            }

        # Endpoints
        paths = spec.get("paths", {})
        if not isinstance(paths, dict):
            paths = {}
            
        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
                
            for method, details in methods.items():
                if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]:
                    continue
                
                if not isinstance(details, dict):
                    continue
                
                endpoint = APIEndpointSchema(
                    method=method.upper(),
                    path=path,
                    summary=details.get("summary", ""),
                    description=details.get("description", ""),
                    tags=details.get("tags", []),
                    responses=details.get("responses", {}),
                )
                
                # Parameters
                all_params = details.get("parameters", []) + spec.get("parameters", []) # This is a bit simplified
                endpoint.parameters = self._parse_parameters(all_params)
                
                # Request Body
                if "requestBody" in details:
                    endpoint.request_body = details["requestBody"]
                
                normalized.endpoints.append(endpoint)

        return normalized

    def _parse_parameters(self, params: List[Dict[str, Any]]) -> Dict[str, Any]:
        parsed = {"path": [], "query": [], "header": [], "cookie": []}
        for p in params:
            location = p.get("in", "query")
            if location in parsed:
                parsed[location].append({
                    "name": p.get("name"),
                    "required": p.get("required", False),
                    "type": p.get("schema", {}).get("type", "string") if "schema" in p else p.get("type", "string"),
                    "description": p.get("description", "")
                })
        return parsed
