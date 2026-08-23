import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class SpecDiffService:
    """
    Analyzes differences between two API specifications (NormalizedAPISpec or raw dictionaries)
    and categorizes changes into breaking vs non-breaking.
    """

    @classmethod
    def compare_specs(cls, old_spec: Dict[str, Any], new_spec: Dict[str, Any]) -> Dict[str, Any]:
        changes: List[Dict[str, Any]] = []

        old_endpoints = {cls._endpoint_key(ep): ep for ep in old_spec.get("endpoints", [])}
        new_endpoints = {cls._endpoint_key(ep): ep for ep in new_spec.get("endpoints", [])}

        # 1. Removed endpoints (BREAKING)
        for key, old_ep in old_endpoints.items():
            if key not in new_endpoints:
                changes.append({
                    "type": "breaking",
                    "category": "endpoint",
                    "action": "removed",
                    "path": old_ep.get("path", ""),
                    "method": old_ep.get("method", ""),
                    "description": f"Endpoint '{old_ep.get('method')} {old_ep.get('path')}' was removed."
                })

        # 2. Added endpoints (NON-BREAKING)
        for key, new_ep in new_endpoints.items():
            if key not in old_endpoints:
                changes.append({
                    "type": "non-breaking",
                    "category": "endpoint",
                    "action": "added",
                    "path": new_ep.get("path", ""),
                    "method": new_ep.get("method", ""),
                    "description": f"New endpoint '{new_ep.get('method')} {new_ep.get('path')}' was added."
                })

        # 3. Modified existing endpoints
        for key in old_endpoints.keys() & new_endpoints.keys():
            old_ep = old_endpoints[key]
            new_ep = new_endpoints[key]
            endpoint_changes = cls._compare_endpoint(old_ep, new_ep)
            changes.extend(endpoint_changes)

        # 4. Authentication changes
        auth_changes = cls._compare_authentication(
            old_spec.get("authentication", {}),
            new_spec.get("authentication", {})
        )
        changes.extend(auth_changes)

        breaking_count = sum(1 for c in changes if c["type"] == "breaking")
        non_breaking_count = sum(1 for c in changes if c["type"] == "non-breaking")

        return {
            "has_breaking_changes": breaking_count > 0,
            "breaking_count": breaking_count,
            "non_breaking_count": non_breaking_count,
            "total_changes": len(changes),
            "changes": changes,
            "summary": cls._build_summary(breaking_count, non_breaking_count),
        }

    @staticmethod
    def _endpoint_key(ep: Dict[str, Any]) -> str:
        method = str(ep.get("method", "GET")).upper().strip()
        path = str(ep.get("path", "/")).strip().rstrip("/")
        return f"{method} {path}"

    @classmethod
    def _compare_endpoint(cls, old_ep: Dict[str, Any], new_ep: Dict[str, Any]) -> List[Dict[str, Any]]:
        changes: List[Dict[str, Any]] = []
        path = old_ep.get("path", "")
        method = old_ep.get("method", "")

        # A. Parameter checks
        old_params_map = cls._build_param_map(old_ep.get("parameters", {}))
        new_params_map = cls._build_param_map(new_ep.get("parameters", {}))

        # Removed parameters
        for p_key, old_param in old_params_map.items():
            if p_key not in new_params_map:
                is_required = old_param.get("required", False)
                changes.append({
                    "type": "breaking" if is_required else "non-breaking",
                    "category": "parameter",
                    "action": "removed",
                    "path": path,
                    "method": method,
                    "parameter": old_param.get("name"),
                    "location": old_param.get("in"),
                    "description": f"Parameter '{old_param.get('name')}' ({old_param.get('in')}) was removed from '{method} {path}'."
                })

        # Added or modified parameters
        for p_key, new_param in new_params_map.items():
            if p_key not in old_params_map:
                is_required = new_param.get("required", False)
                changes.append({
                    "type": "breaking" if is_required else "non-breaking",
                    "category": "parameter",
                    "action": "added",
                    "path": path,
                    "method": method,
                    "parameter": new_param.get("name"),
                    "location": new_param.get("in"),
                    "description": (
                        f"Required parameter '{new_param.get('name')}' ({new_param.get('in')}) was added to '{method} {path}'."
                        if is_required else
                        f"Optional parameter '{new_param.get('name')}' ({new_param.get('in')}) was added to '{method} {path}'."
                    )
                })
            else:
                old_param = old_params_map[p_key]
                # Changed from optional to required -> BREAKING
                if not old_param.get("required") and new_param.get("required"):
                    changes.append({
                        "type": "breaking",
                        "category": "parameter",
                        "action": "modified",
                        "path": path,
                        "method": method,
                        "parameter": new_param.get("name"),
                        "location": new_param.get("in"),
                        "description": f"Parameter '{new_param.get('name')}' changed from optional to required."
                    })
                # Changed type -> BREAKING
                old_type = old_param.get("type", "string")
                new_type = new_param.get("type", "string")
                if old_type and new_type and old_type != new_type:
                    changes.append({
                        "type": "breaking",
                        "category": "parameter",
                        "action": "modified",
                        "path": path,
                        "method": method,
                        "parameter": new_param.get("name"),
                        "location": new_param.get("in"),
                        "description": f"Parameter '{new_param.get('name')}' type changed from '{old_type}' to '{new_type}'."
                    })

        # B. Request Body checks
        old_body = old_ep.get("request_body") or {}
        new_body = new_ep.get("request_body") or {}
        old_body_req = bool(old_body.get("required", False))
        new_body_req = bool(new_body.get("required", False))

        if not old_body_req and new_body_req:
            changes.append({
                "type": "breaking",
                "category": "request_body",
                "action": "modified",
                "path": path,
                "method": method,
                "description": f"Request body on '{method} {path}' became required."
            })

        # C. Response checks
        old_responses = old_ep.get("responses", {})
        new_responses = new_ep.get("responses", {})
        for code in old_responses.keys():
            if code.startswith("2") and code not in new_responses:
                changes.append({
                    "type": "breaking",
                    "category": "response",
                    "action": "removed",
                    "path": path,
                    "method": method,
                    "description": f"Success status code '{code}' response was removed from '{method} {path}'."
                })

        return changes

    @staticmethod
    def _build_param_map(params: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        param_map = {}
        for location in ["path", "query", "header", "cookie"]:
            items = params.get(location, [])
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        name = item.get("name", "")
                        if name:
                            item_copy = dict(item)
                            item_copy["in"] = location
                            param_map[f"{location}:{name}"] = item_copy
        return param_map

    @classmethod
    def _compare_authentication(cls, old_auth: Dict[str, Any], new_auth: Dict[str, Any]) -> List[Dict[str, Any]]:
        changes = []
        old_type = old_auth.get("type", "none").lower()
        new_type = new_auth.get("type", "none").lower()

        if old_type != new_type:
            changes.append({
                "type": "breaking",
                "category": "authentication",
                "action": "modified",
                "path": "global",
                "method": "*",
                "description": f"API authentication type changed from '{old_type}' to '{new_type}'."
            })
        elif old_type == "apikey":
            old_name = old_auth.get("name", "")
            new_name = new_auth.get("name", "")
            if old_name and new_name and old_name != new_name:
                changes.append({
                    "type": "breaking",
                    "category": "authentication",
                    "action": "modified",
                    "path": "global",
                    "method": "*",
                    "description": f"API key header name changed from '{old_name}' to '{new_name}'."
                })

        return changes

    @staticmethod
    def _build_summary(breaking_count: int, non_breaking_count: int) -> str:
        if breaking_count == 0 and non_breaking_count == 0:
            return "No changes detected between specifications."
        parts = []
        if breaking_count > 0:
            parts.append(f"{breaking_count} breaking change{'s' if breaking_count > 1 else ''}")
        if non_breaking_count > 0:
            parts.append(f"{non_breaking_count} non-breaking change{'s' if non_breaking_count > 1 else ''}")
        return "Detected " + " and ".join(parts) + "."
