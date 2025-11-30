"""
Code Reviewer Tool - Automated Code Analysis

Provides:
- Complexity analysis
- Pattern detection
- Code quality scoring
- Review comment generation
"""

import ast
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


class IssueSeverity(Enum):
    """Severity levels for code issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class CodeIssue:
    """Represents a code issue found during review."""
    file: str
    line: int
    severity: IssueSeverity
    category: str
    message: str
    suggestion: Optional[str] = None


@dataclass
class CodeMetrics:
    """Code quality metrics."""
    lines_of_code: int = 0
    lines_of_comments: int = 0
    blank_lines: int = 0
    functions: int = 0
    classes: int = 0
    avg_function_length: float = 0.0
    max_function_length: int = 0
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    
    @property
    def comment_ratio(self) -> float:
        total = self.lines_of_code + self.lines_of_comments
        if total == 0:
            return 0.0
        return self.lines_of_comments / total


@dataclass
class ReviewResult:
    """Complete code review result."""
    file: str
    metrics: CodeMetrics
    issues: List[CodeIssue] = field(default_factory=list)
    score: float = 0.0  # 0-100
    grade: str = "N/A"  # A-F
    summary: str = ""


class CodeReviewer:
    """
    Performs automated code review for Python files.
    
    Features:
    - Complexity analysis
    - Anti-pattern detection
    - Code smell identification
    - Review comment generation
    """
    
    def __init__(self):
        # Patterns to detect
        self.antipatterns = [
            (r"except\s*:", "Bare except clause", "Specify exception type"),
            (r"print\(", "Debug print statement", "Use logging instead"),
            (r"TODO|FIXME|HACK|XXX", "Unresolved code marker", "Address or track in issue"),
            (r"== None|!= None", "None comparison", "Use 'is None' or 'is not None'"),
            (r"== True|== False", "Boolean comparison", "Use value directly"),
            (r"import \*", "Star import", "Import specific names"),
            (r"^\s{0,3}pass\s*$", "Empty block", "Add implementation or remove"),
        ]
        
        # Magic number pattern
        self.magic_number_pattern = re.compile(r"(?<!['\"])\b(\d{3,})\b(?!['\"])")
        
        # Long line threshold
        self.max_line_length = 100
        
        # Function length thresholds
        self.function_length_warning = 50
        self.function_length_error = 100
    
    async def review_file(self, file_path: str) -> ReviewResult:
        """
        Perform full review of a Python file.
        
        Args:
            file_path: Path to Python file
        
        Returns:
            ReviewResult with metrics, issues, and score
        """
        path = Path(file_path)
        
        if not path.exists():
            return ReviewResult(
                file=str(file_path),
                metrics=CodeMetrics(),
                issues=[CodeIssue(
                    file=str(file_path),
                    line=0,
                    severity=IssueSeverity.ERROR,
                    category="file",
                    message="File not found"
                )],
                score=0,
                grade="F"
            )
        
        content = path.read_text()
        lines = content.split("\n")
        
        # Collect metrics
        metrics = self._analyze_metrics(content, lines)
        
        # Find issues
        issues = []
        issues.extend(self._check_antipatterns(file_path, lines))
        issues.extend(self._check_line_length(file_path, lines))
        issues.extend(self._check_magic_numbers(file_path, lines))
        issues.extend(self._check_ast(file_path, content))
        
        # Calculate score
        score, grade = self._calculate_score(metrics, issues)
        
        # Generate summary
        summary = self._generate_summary(metrics, issues, grade)
        
        return ReviewResult(
            file=str(file_path),
            metrics=metrics,
            issues=issues,
            score=score,
            grade=grade,
            summary=summary
        )
    
    def _analyze_metrics(self, content: str, lines: List[str]) -> CodeMetrics:
        """Analyze code metrics."""
        metrics = CodeMetrics()
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                metrics.blank_lines += 1
            elif stripped.startswith("#"):
                metrics.lines_of_comments += 1
            else:
                metrics.lines_of_code += 1
        
        # Parse AST for detailed metrics
        try:
            tree = ast.parse(content)
            
            function_lengths = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics.functions += 1
                    length = node.end_lineno - node.lineno + 1
                    function_lengths.append(length)
                    
                    # Estimate cyclomatic complexity
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.For, ast.While, ast.And, ast.Or)):
                            metrics.cyclomatic_complexity += 1
                
                elif isinstance(node, ast.ClassDef):
                    metrics.classes += 1
            
            if function_lengths:
                metrics.avg_function_length = sum(function_lengths) / len(function_lengths)
                metrics.max_function_length = max(function_lengths)
                
        except SyntaxError:
            pass
        
        return metrics
    
    def _check_antipatterns(
        self, 
        file_path: str, 
        lines: List[str]
    ) -> List[CodeIssue]:
        """Check for antipatterns."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            for pattern, message, suggestion in self.antipatterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeIssue(
                        file=file_path,
                        line=i,
                        severity=IssueSeverity.WARNING,
                        category="antipattern",
                        message=message,
                        suggestion=suggestion
                    ))
        
        return issues
    
    def _check_line_length(
        self, 
        file_path: str, 
        lines: List[str]
    ) -> List[CodeIssue]:
        """Check for long lines."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if len(line) > self.max_line_length:
                issues.append(CodeIssue(
                    file=file_path,
                    line=i,
                    severity=IssueSeverity.INFO,
                    category="style",
                    message=f"Line too long ({len(line)} > {self.max_line_length})",
                    suggestion="Break into multiple lines"
                ))
        
        return issues
    
    def _check_magic_numbers(
        self, 
        file_path: str, 
        lines: List[str]
    ) -> List[CodeIssue]:
        """Check for magic numbers."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith("#"):
                continue
            
            matches = self.magic_number_pattern.findall(line)
            for match in matches:
                issues.append(CodeIssue(
                    file=file_path,
                    line=i,
                    severity=IssueSeverity.INFO,
                    category="maintainability",
                    message=f"Magic number: {match}",
                    suggestion="Extract to named constant"
                ))
        
        return issues
    
    def _check_ast(self, file_path: str, content: str) -> List[CodeIssue]:
        """AST-based checks."""
        issues = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Check function length
                if isinstance(node, ast.FunctionDef):
                    length = node.end_lineno - node.lineno + 1
                    
                    if length > self.function_length_error:
                        issues.append(CodeIssue(
                            file=file_path,
                            line=node.lineno,
                            severity=IssueSeverity.ERROR,
                            category="complexity",
                            message=f"Function '{node.name}' too long ({length} lines)",
                            suggestion="Split into smaller functions"
                        ))
                    elif length > self.function_length_warning:
                        issues.append(CodeIssue(
                            file=file_path,
                            line=node.lineno,
                            severity=IssueSeverity.WARNING,
                            category="complexity",
                            message=f"Function '{node.name}' is long ({length} lines)",
                            suggestion="Consider splitting"
                        ))
                    
                    # Check for too many arguments
                    arg_count = len(node.args.args)
                    if arg_count > 5:
                        issues.append(CodeIssue(
                            file=file_path,
                            line=node.lineno,
                            severity=IssueSeverity.WARNING,
                            category="complexity",
                            message=f"Function '{node.name}' has {arg_count} arguments",
                            suggestion="Use dataclass or kwargs"
                        ))
                    
                    # Check for missing docstring
                    if not ast.get_docstring(node):
                        issues.append(CodeIssue(
                            file=file_path,
                            line=node.lineno,
                            severity=IssueSeverity.INFO,
                            category="documentation",
                            message=f"Function '{node.name}' missing docstring",
                            suggestion="Add docstring"
                        ))
                
                # Check class docstring
                elif isinstance(node, ast.ClassDef):
                    if not ast.get_docstring(node):
                        issues.append(CodeIssue(
                            file=file_path,
                            line=node.lineno,
                            severity=IssueSeverity.INFO,
                            category="documentation",
                            message=f"Class '{node.name}' missing docstring",
                            suggestion="Add docstring"
                        ))
                        
        except SyntaxError:
            issues.append(CodeIssue(
                file=file_path,
                line=1,
                severity=IssueSeverity.CRITICAL,
                category="syntax",
                message="Syntax error in file"
            ))
        
        return issues
    
    def _calculate_score(
        self, 
        metrics: CodeMetrics, 
        issues: List[CodeIssue]
    ) -> Tuple[float, str]:
        """Calculate overall score and grade."""
        score = 100.0
        
        # Deduct for issues
        for issue in issues:
            if issue.severity == IssueSeverity.CRITICAL:
                score -= 20
            elif issue.severity == IssueSeverity.ERROR:
                score -= 10
            elif issue.severity == IssueSeverity.WARNING:
                score -= 3
            else:  # INFO
                score -= 1
        
        # Bonus for comments
        if metrics.comment_ratio > 0.1:
            score += 5
        
        # Penalty for high complexity
        if metrics.cyclomatic_complexity > 20:
            score -= 10
        
        # Ensure bounds
        score = max(0, min(100, score))
        
        # Determine grade
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"
        
        return score, grade
    
    def _generate_summary(
        self, 
        metrics: CodeMetrics, 
        issues: List[CodeIssue],
        grade: str
    ) -> str:
        """Generate review summary."""
        critical = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        errors = sum(1 for i in issues if i.severity == IssueSeverity.ERROR)
        warnings = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)
        
        lines = [f"**Grade: {grade}**"]
        
        if critical:
            lines.append(f"🔴 {critical} critical issue(s)")
        if errors:
            lines.append(f"🟠 {errors} error(s)")
        if warnings:
            lines.append(f"🟡 {warnings} warning(s)")
        
        lines.append(f"📊 {metrics.functions} functions, {metrics.classes} classes")
        lines.append(f"📝 {metrics.lines_of_code} LOC, {metrics.comment_ratio:.0%} comments")
        
        return "\n".join(lines)
    
    async def review_files(self, file_paths: List[str]) -> Dict[str, ReviewResult]:
        """Review multiple files."""
        results = {}
        for path in file_paths:
            results[path] = await self.review_file(path)
        return results

