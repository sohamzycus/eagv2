"""
Tool Contract Definitions.

Defines the structure and validation for tool specifications.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional
import json


class ToolType(Enum):
    """Types of tools."""

    INTERNAL = auto()  # Company internal API
    EXTERNAL = auto()  # External service
    HYBRID = auto()  # Internal with external dependencies


class ParameterType(Enum):
    """JSON Schema parameter types."""

    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ToolParameter:
    """
    Definition of a tool parameter.

    Maps to JSON Schema property definition.
    """

    name: str
    param_type: ParameterType
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum_values: list[str] = field(default_factory=list)
    items_type: Optional[ParameterType] = None  # For arrays
    properties: dict[str, "ToolParameter"] = field(default_factory=dict)  # For objects

    def to_json_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema property definition."""
        schema: dict[str, Any] = {
            "type": self.param_type.value,
            "description": self.description,
        }

        if self.default is not None:
            schema["default"] = self.default

        if self.enum_values:
            schema["enum"] = self.enum_values

        if self.param_type == ParameterType.ARRAY and self.items_type:
            schema["items"] = {"type": self.items_type.value}

        if self.param_type == ParameterType.OBJECT and self.properties:
            schema["properties"] = {
                name: param.to_json_schema()
                for name, param in self.properties.items()
            }

        return schema


@dataclass
class ToolContract:
    """
    Complete tool contract specification.

    This is the MCP-Zero compatible tool definition.
    """

    tool_name: str
    description: str
    tool_type: ToolType
    input_params: list[ToolParameter] = field(default_factory=list)
    output_schema: dict[str, Any] = field(default_factory=dict)
    endpoint: Optional[str] = None
    method: str = "POST"
    auth_required: bool = True
    cache_ttl: Optional[int] = None
    rate_limit: Optional[int] = None
    timeout_ms: int = 30000
    retry_count: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_parameter(self, param: ToolParameter) -> "ToolContract":
        """Add an input parameter."""
        self.input_params.append(param)
        return self

    def get_required_params(self) -> list[ToolParameter]:
        """Get required parameters."""
        return [p for p in self.input_params if p.required]

    def get_optional_params(self) -> list[ToolParameter]:
        """Get optional parameters."""
        return [p for p in self.input_params if not p.required]

    def to_json_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema for input validation."""
        properties = {}
        required = []

        for param in self.input_params:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    def to_mcp_zero_spec(self) -> dict[str, Any]:
        """Generate MCP-Zero compatible specification."""
        spec = {
            "tool_name": self.tool_name,
            "description": self.description,
            "type": self.tool_type.name.lower(),
            "input_schema": self.to_json_schema(),
            "output_schema": self.output_schema,
            "mcp_zero": {
                "endpoint": self.endpoint,
                "method": self.method,
                "auth_required": self.auth_required,
                "timeout_ms": self.timeout_ms,
                "retry_count": self.retry_count,
            },
        }

        if self.cache_ttl:
            spec["mcp_zero"]["cache_ttl"] = self.cache_ttl

        if self.rate_limit:
            spec["mcp_zero"]["rate_limit"] = self.rate_limit

        if self.metadata:
            spec["metadata"] = self.metadata

        return spec

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_mcp_zero_spec(), indent=indent)

    def to_prompt_text(self) -> str:
        """Generate prompt-friendly tool documentation."""
        lines = [
            f"### `{self.tool_name}`",
            "",
            f"**Description:** {self.description}",
            f"**Type:** {self.tool_type.name}",
            "",
            "**Parameters:**",
        ]

        for param in self.input_params:
            req_marker = " (required)" if param.required else " (optional)"
            lines.append(f"- `{param.name}`: {param.param_type.value}{req_marker}")
            lines.append(f"  {param.description}")

        lines.append("")
        lines.append("**Returns:** See output schema")

        return "\n".join(lines)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolContract":
        """Create from dictionary (deserialization)."""
        tool_type = ToolType[data.get("type", "internal").upper()]

        contract = cls(
            tool_name=data["tool_name"],
            description=data.get("description", ""),
            tool_type=tool_type,
            output_schema=data.get("output_schema", {}),
        )

        # Parse MCP-Zero config
        mcp_config = data.get("mcp_zero", {})
        contract.endpoint = mcp_config.get("endpoint")
        contract.method = mcp_config.get("method", "POST")
        contract.auth_required = mcp_config.get("auth_required", True)
        contract.cache_ttl = mcp_config.get("cache_ttl")
        contract.timeout_ms = mcp_config.get("timeout_ms", 30000)

        # Parse input schema
        input_schema = data.get("input_schema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        for name, prop in properties.items():
            param_type = ParameterType(prop.get("type", "string"))
            param = ToolParameter(
                name=name,
                param_type=param_type,
                description=prop.get("description", ""),
                required=name in required,
                default=prop.get("default"),
                enum_values=prop.get("enum", []),
            )
            contract.add_parameter(param)

        return contract


class ToolContractBuilder:
    """
    Builder for creating tool contracts.

    Provides fluent interface for contract construction.
    """

    def __init__(self, tool_name: str):
        self._contract = ToolContract(
            tool_name=tool_name,
            description="",
            tool_type=ToolType.INTERNAL,
        )

    def description(self, desc: str) -> "ToolContractBuilder":
        """Set description."""
        self._contract.description = desc
        return self

    def tool_type(self, t: ToolType) -> "ToolContractBuilder":
        """Set tool type."""
        self._contract.tool_type = t
        return self

    def endpoint(self, url: str, method: str = "POST") -> "ToolContractBuilder":
        """Set endpoint."""
        self._contract.endpoint = url
        self._contract.method = method
        return self

    def auth_required(self, required: bool = True) -> "ToolContractBuilder":
        """Set auth requirement."""
        self._contract.auth_required = required
        return self

    def cache(self, ttl_seconds: int) -> "ToolContractBuilder":
        """Set cache TTL."""
        self._contract.cache_ttl = ttl_seconds
        return self

    def timeout(self, ms: int) -> "ToolContractBuilder":
        """Set timeout."""
        self._contract.timeout_ms = ms
        return self

    def param(
        self,
        name: str,
        param_type: ParameterType,
        description: str,
        required: bool = True,
        default: Any = None,
    ) -> "ToolContractBuilder":
        """Add a parameter."""
        self._contract.add_parameter(
            ToolParameter(
                name=name,
                param_type=param_type,
                description=description,
                required=required,
                default=default,
            )
        )
        return self

    def string_param(
        self,
        name: str,
        description: str,
        required: bool = True,
        default: str = None,
    ) -> "ToolContractBuilder":
        """Add a string parameter."""
        return self.param(name, ParameterType.STRING, description, required, default)

    def number_param(
        self,
        name: str,
        description: str,
        required: bool = True,
        default: float = None,
    ) -> "ToolContractBuilder":
        """Add a number parameter."""
        return self.param(name, ParameterType.NUMBER, description, required, default)

    def bool_param(
        self,
        name: str,
        description: str,
        required: bool = False,
        default: bool = None,
    ) -> "ToolContractBuilder":
        """Add a boolean parameter."""
        return self.param(name, ParameterType.BOOLEAN, description, required, default)

    def output(self, schema: dict[str, Any]) -> "ToolContractBuilder":
        """Set output schema."""
        self._contract.output_schema = schema
        return self

    def build(self) -> ToolContract:
        """Build the contract."""
        return self._contract



