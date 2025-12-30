"""
Prompt Sections.

Implements Composite pattern for building prompt sections.
Each section can contain subsections for hierarchical structure.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class SectionType(Enum):
    """Types of prompt sections."""

    IDENTITY = auto()
    RULES = auto()
    GUARDRAILS = auto()
    WORKFLOW = auto()
    COVE = auto()
    TOOLS = auto()
    FORMATTING = auto()
    EXAMPLES = auto()
    ERROR_HANDLING = auto()


@dataclass
class PromptSection:
    """
    A section of the system prompt.

    Implements Composite pattern - sections can contain subsections.
    """

    title: str
    content: str = ""
    section_type: SectionType = SectionType.RULES
    subsections: list["PromptSection"] = field(default_factory=list)
    level: int = 2
    order: int = 0

    def add_subsection(self, section: "PromptSection") -> "PromptSection":
        """Add a subsection."""
        section.level = self.level + 1
        self.subsections.append(section)
        return self

    def add_content(self, content: str) -> "PromptSection":
        """Append content to this section."""
        if self.content:
            self.content += "\n\n"
        self.content += content
        return self

    def add_bullet(self, item: str) -> "PromptSection":
        """Add a bullet point."""
        if not self.content.endswith("\n") and self.content:
            self.content += "\n"
        self.content += f"- {item}\n"
        return self

    def add_numbered(self, items: list[str]) -> "PromptSection":
        """Add numbered list."""
        for i, item in enumerate(items, 1):
            if not self.content.endswith("\n") and self.content:
                self.content += "\n"
            self.content += f"{i}. {item}\n"
        return self

    def add_code_block(self, code: str, language: str = "") -> "PromptSection":
        """Add a code block."""
        if self.content:
            self.content += "\n\n"
        self.content += f"```{language}\n{code}\n```"
        return self

    def render(self, include_header: bool = True) -> str:
        """Render this section as markdown."""
        lines = []

        if include_header and self.title:
            header = "#" * self.level
            lines.append(f"{header} {self.title}")
            lines.append("")

        if self.content:
            lines.append(self.content.strip())

        for subsection in sorted(self.subsections, key=lambda s: s.order):
            lines.append("")
            lines.append(subsection.render())

        return "\n".join(lines)

    @classmethod
    def identity(cls, title: str, content: str) -> "PromptSection":
        """Create an identity section."""
        return cls(title=title, content=content, section_type=SectionType.IDENTITY, order=0)

    @classmethod
    def rules(cls, title: str) -> "PromptSection":
        """Create a rules section."""
        return cls(title=title, section_type=SectionType.RULES, order=10)

    @classmethod
    def guardrails(cls, title: str) -> "PromptSection":
        """Create a guardrails section."""
        return cls(title=title, section_type=SectionType.GUARDRAILS, order=20)

    @classmethod
    def workflow(cls, title: str) -> "PromptSection":
        """Create a workflow section."""
        return cls(title=title, section_type=SectionType.WORKFLOW, order=30)

    @classmethod
    def cove(cls, title: str) -> "PromptSection":
        """Create a COVE section."""
        return cls(title=title, section_type=SectionType.COVE, order=40)

    @classmethod
    def tools(cls, title: str) -> "PromptSection":
        """Create a tools section."""
        return cls(title=title, section_type=SectionType.TOOLS, order=50)

    @classmethod
    def formatting(cls, title: str) -> "PromptSection":
        """Create a formatting section."""
        return cls(title=title, section_type=SectionType.FORMATTING, order=60)

    @classmethod
    def examples(cls, title: str) -> "PromptSection":
        """Create an examples section."""
        return cls(title=title, section_type=SectionType.EXAMPLES, order=70)

    @classmethod
    def error_handling(cls, title: str) -> "PromptSection":
        """Create an error handling section."""
        return cls(title=title, section_type=SectionType.ERROR_HANDLING, order=80)


class PromptTemplate:
    """
    Template for common prompt patterns.

    Provides reusable structures for prompt composition.
    """

    @staticmethod
    def decision_tree(
        decision_point: str,
        branches: dict[str, str],
    ) -> str:
        """Generate a decision tree structure."""
        lines = [f"**Decision Point:** {decision_point}", ""]
        for condition, action in branches.items():
            lines.append(f"- IF {condition}:")
            lines.append(f"  → {action}")
        return "\n".join(lines)

    @staticmethod
    def constraint_block(
        must_do: list[str],
        must_not: list[str],
    ) -> str:
        """Generate a constraint block."""
        lines = []
        if must_do:
            lines.append("**MUST:**")
            for item in must_do:
                lines.append(f"✅ {item}")
            lines.append("")
        if must_not:
            lines.append("**MUST NOT:**")
            for item in must_not:
                lines.append(f"❌ {item}")
        return "\n".join(lines)

    @staticmethod
    def tool_usage(
        tool_name: str,
        when_to_use: str,
        inputs: list[str],
        outputs: list[str],
    ) -> str:
        """Generate tool usage documentation."""
        lines = [
            f"### `{tool_name}`",
            "",
            f"**When to use:** {when_to_use}",
            "",
            "**Inputs:**",
        ]
        for inp in inputs:
            lines.append(f"- {inp}")
        lines.append("")
        lines.append("**Outputs:**")
        for out in outputs:
            lines.append(f"- {out}")
        return "\n".join(lines)

    @staticmethod
    def step_block(
        step_id: str,
        name: str,
        purpose: str,
        actions: list[str],
        routing: dict[str, str],
    ) -> str:
        """Generate a step definition block."""
        lines = [
            f"### {step_id}: {name}",
            "",
            f"**Purpose:** {purpose}",
            "",
            "**Actions:**",
        ]
        for action in actions:
            lines.append(f"1. {action}")
        lines.append("")
        if routing:
            lines.append("**Routing:**")
            for condition, next_step in routing.items():
                lines.append(f"- {condition} → `{next_step}`")
        return "\n".join(lines)



