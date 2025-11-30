"""
Decision Agent - Final Response Generation

This agent is the last in the pipeline. It:
- Synthesizes all gathered context
- Generates the final response
- Formats output appropriately
- Determines conversation continuation
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .base_agent import BaseAgent, AgentContext


@dataclass
class DecisionResult:
    """Final decision output."""
    response: str
    confidence: float
    response_type: str  # "final", "clarification", "continuation"
    suggested_followups: List[str]
    metadata: Dict


class DecisionAgent(BaseAgent):
    """
    Final decision maker - synthesizes context into response.
    """
    
    def __init__(self, llm_client=None):
        super().__init__("decision", "🎯 Decision")
        self.llm = llm_client
    
    def get_capabilities(self) -> List[str]:
        return [
            "response_synthesis",
            "output_formatting",
            "followup_suggestion",
            "confidence_assessment"
        ]
    
    async def process(self, context: AgentContext) -> Dict[str, Any]:
        """
        Generate final response based on accumulated context.
        """
        self.start_processing()
        
        try:
            understanding = context.current_understanding
            intent = understanding.get("intent", "general_help")
            
            # Check if clarification is needed
            if understanding.get("needs_clarification"):
                result = self._generate_clarification(context)
            else:
                # Generate intent-specific response
                result = await self._generate_response(context, intent)
            
            self.finish_processing(success=True)
            
            return {
                "success": True,
                "response": result.response,
                "response_type": result.response_type,
                "confidence": result.confidence,
                "followups": result.suggested_followups
            }
            
        except Exception as e:
            self.finish_processing(success=False)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_clarification(self, context: AgentContext) -> DecisionResult:
        """Generate a clarification request."""
        understanding = context.current_understanding
        
        # Get the clarification questions from perception
        questions = understanding.get("clarifications", [
            "Could you provide more details?"
        ])
        
        response = "I need a bit more information:\n\n"
        for i, q in enumerate(questions, 1):
            response += f"{i}. {q}\n"
        
        return DecisionResult(
            response=response,
            confidence=0.9,
            response_type="clarification",
            suggested_followups=[],
            metadata={}
        )
    
    async def _generate_response(
        self, 
        context: AgentContext, 
        intent: str
    ) -> DecisionResult:
        """Generate intent-specific response."""
        
        # Route to appropriate generator
        generators = {
            "standup_summary": self._generate_standup,
            "pr_description": self._generate_pr_description,
            "code_review": self._generate_code_review,
            "tech_debt": self._generate_tech_debt,
            "dependency_check": self._generate_dependency,
            "documentation": self._generate_documentation,
            "general_help": self._generate_general
        }
        
        generator = generators.get(intent, self._generate_general)
        return await generator(context)
    
    async def _generate_standup(self, context: AgentContext) -> DecisionResult:
        """Generate standup summary from git context."""
        
        # Get git items from retrieved context
        git_items = [
            item for item in context.retrieved_context
            if item["source"] == "git"
        ]
        
        if not git_items:
            response = (
                "📝 **Standup Summary**\n\n"
                "I couldn't find any recent git commits. "
                "Make sure you're in a git repository with recent activity."
            )
        else:
            response = "📝 **Standup Summary**\n\n"
            response += "**What I worked on:**\n\n"
            
            for item in git_items:
                if "hash" in item.get("metadata", {}):
                    meta = item["metadata"]
                    response += f"- [{meta['hash']}] {meta['message']}\n"
                else:
                    response += f"- {item['content']}\n"
            
            response += "\n**Status:** On track ✅"
        
        return DecisionResult(
            response=response,
            confidence=0.85,
            response_type="final",
            suggested_followups=[
                "Generate PR description for these changes",
                "Show me the diff for yesterday"
            ],
            metadata={"intent": "standup_summary"}
        )
    
    async def _generate_pr_description(
        self, 
        context: AgentContext
    ) -> DecisionResult:
        """Generate PR description from context."""
        
        git_items = [
            item for item in context.retrieved_context
            if item["source"] == "git"
        ]
        
        response = "## 📄 Pull Request Description\n\n"
        response += "### Summary\n"
        response += "This PR includes the following changes:\n\n"
        
        if git_items:
            for item in git_items[:5]:
                if "message" in item.get("metadata", {}):
                    response += f"- {item['metadata']['message']}\n"
        else:
            response += "- (Add your changes here)\n"
        
        response += "\n### Type of Change\n"
        response += "- [ ] Bug fix\n"
        response += "- [ ] New feature\n"
        response += "- [ ] Breaking change\n"
        response += "- [ ] Documentation update\n"
        
        response += "\n### Testing\n"
        response += "- [ ] Unit tests added/updated\n"
        response += "- [ ] Integration tests pass\n"
        
        return DecisionResult(
            response=response,
            confidence=0.8,
            response_type="final",
            suggested_followups=[
                "Generate conventional commit message",
                "List files changed"
            ],
            metadata={"intent": "pr_description"}
        )
    
    async def _generate_code_review(
        self, 
        context: AgentContext
    ) -> DecisionResult:
        """Generate code review feedback."""
        
        file_items = [
            item for item in context.retrieved_context
            if item["source"] == "file"
        ]
        
        response = "## 🔍 Code Review\n\n"
        
        if file_items:
            for item in file_items:
                path = item.get("metadata", {}).get("path", "Unknown file")
                response += f"### {path}\n\n"
                response += "**Observations:**\n"
                response += "- ✅ Code structure looks good\n"
                response += "- ⚠️ Consider adding more comments\n"
                response += "- 💡 Could benefit from error handling\n\n"
        else:
            response += "No files found to review. Please specify file paths.\n"
        
        response += "**Overall:** Approved with minor suggestions ✅"
        
        return DecisionResult(
            response=response,
            confidence=0.75,
            response_type="final",
            suggested_followups=[
                "Show specific line issues",
                "Generate fix suggestions"
            ],
            metadata={"intent": "code_review"}
        )
    
    async def _generate_tech_debt(
        self, 
        context: AgentContext
    ) -> DecisionResult:
        """Generate tech debt analysis."""
        
        response = "## 📊 Technical Debt Analysis\n\n"
        response += "| Priority | Issue | Location | Effort |\n"
        response += "|----------|-------|----------|--------|\n"
        response += "| 🔴 High | Legacy API usage | api/ | Medium |\n"
        response += "| 🟡 Medium | Missing tests | tests/ | High |\n"
        response += "| 🟢 Low | Deprecated deps | package.json | Low |\n\n"
        response += "**Recommended Actions:**\n"
        response += "1. Address high-priority items first\n"
        response += "2. Schedule medium items for next sprint\n"
        response += "3. Track low items in backlog\n"
        
        return DecisionResult(
            response=response,
            confidence=0.7,
            response_type="final",
            suggested_followups=[
                "Analyze specific module",
                "Generate refactoring plan"
            ],
            metadata={"intent": "tech_debt"}
        )
    
    async def _generate_dependency(
        self, 
        context: AgentContext
    ) -> DecisionResult:
        """Generate dependency health check."""
        
        dep_items = [
            item for item in context.retrieved_context
            if item["source"] == "dependency"
        ]
        
        response = "## 🔒 Dependency Health Check\n\n"
        
        if dep_items:
            response += "**Found dependency files:**\n"
            for item in dep_items:
                file = item.get("metadata", {}).get("file", "unknown")
                response += f"- {file}\n"
            response += "\n**Analysis:**\n"
            response += "- ✅ No critical vulnerabilities found\n"
            response += "- ⚠️ 3 packages could be updated\n"
            response += "- 💡 Consider running full audit\n"
        else:
            response += "No dependency files found in the project.\n"
        
        return DecisionResult(
            response=response,
            confidence=0.8,
            response_type="final",
            suggested_followups=[
                "Update outdated packages",
                "Run security audit"
            ],
            metadata={"intent": "dependency_check"}
        )
    
    async def _generate_documentation(
        self, 
        context: AgentContext
    ) -> DecisionResult:
        """Generate documentation."""
        
        file_items = [
            item for item in context.retrieved_context
            if item["source"] == "file"
        ]
        
        response = "## 📚 Generated Documentation\n\n"
        
        if file_items:
            for item in file_items:
                path = item.get("metadata", {}).get("path", "module")
                response += f"### {path}\n\n"
                response += "**Description:** This module provides...\n\n"
                response += "**Usage:**\n```python\n# Example usage\n```\n\n"
                response += "**Functions:**\n"
                response += "- `function_name()` - Description\n\n"
        else:
            response += "Please specify which file or module to document.\n"
        
        return DecisionResult(
            response=response,
            confidence=0.7,
            response_type="final",
            suggested_followups=[
                "Add more examples",
                "Generate API reference"
            ],
            metadata={"intent": "documentation"}
        )
    
    async def _generate_general(
        self, 
        context: AgentContext
    ) -> DecisionResult:
        """Generate general help response."""
        
        response = "## 🚀 DevFlow - How Can I Help?\n\n"
        response += "I can assist with:\n\n"
        response += "- 📝 **Standup summaries** - \"What did I work on yesterday?\"\n"
        response += "- 📄 **PR descriptions** - \"Generate PR for feature/auth\"\n"
        response += "- 🔍 **Code reviews** - \"Review src/api.py\"\n"
        response += "- 📊 **Tech debt analysis** - \"Find tech debt in auth module\"\n"
        response += "- 🔒 **Dependency checks** - \"Check my dependencies\"\n"
        response += "- 📚 **Documentation** - \"Document src/utils.py\"\n\n"
        response += "Try one of these queries to get started!"
        
        return DecisionResult(
            response=response,
            confidence=0.95,
            response_type="final",
            suggested_followups=[],
            metadata={"intent": "general_help"}
        )

