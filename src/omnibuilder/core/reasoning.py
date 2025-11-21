"""
P1.3 Core Reasoning Engine

Applies logic, synthesizes information, and generates Chain-of-Thought reasoning.
"""

from typing import Any, Dict, List, Optional
from omnibuilder.models import ReasoningResult, Context


class ChainOfThought:
    """Represents a chain of thought reasoning process."""

    def __init__(self):
        self.steps: List[str] = []
        self.conclusion: Optional[str] = None

    def add_step(self, step: str) -> None:
        """Add a reasoning step."""
        self.steps.append(step)

    def set_conclusion(self, conclusion: str) -> None:
        """Set the final conclusion."""
        self.conclusion = conclusion


class Option:
    """Represents an option to be evaluated."""

    def __init__(self, name: str, description: str, pros: List[str] = None, cons: List[str] = None):
        self.name = name
        self.description = description
        self.pros = pros or []
        self.cons = cons or []
        self.score: float = 0.0


class Synthesis:
    """Result of information synthesis."""

    def __init__(self, summary: str, key_points: List[str], sources: List[str]):
        self.summary = summary
        self.key_points = key_points
        self.sources = sources


class ReasoningEngine:
    """Core reasoning and logic engine."""

    def __init__(self, llm_client: Any = None):
        self.llm_client = llm_client

    async def reason(self, context: Context, query: str) -> ReasoningResult:
        """
        Apply logical reasoning to solve a problem.

        Args:
            context: Current execution context
            query: The question or problem to reason about

        Returns:
            ReasoningResult with conclusion and confidence
        """
        cot = await self.generate_cot(query)

        # Calculate confidence based on reasoning depth
        confidence = min(0.9, 0.5 + (len(cot.steps) * 0.1))

        return ReasoningResult(
            conclusion=cot.conclusion or "Unable to reach conclusion",
            confidence=confidence,
            chain_of_thought=cot.steps,
            evidence=[]
        )

    async def generate_cot(self, problem: str) -> ChainOfThought:
        """
        Generate step-by-step Chain-of-Thought reasoning.

        Args:
            problem: The problem to reason about

        Returns:
            ChainOfThought with reasoning steps
        """
        cot = ChainOfThought()

        if self.llm_client:
            # Use LLM for reasoning
            prompt = f"""Think through this problem step by step:

{problem}

For each step:
1. State what you're considering
2. Analyze the implications
3. Draw intermediate conclusions

Finally, provide your conclusion."""

            response = await self.llm_client.complete(prompt)

            # Parse response into steps
            lines = response.strip().split("\n")
            for line in lines:
                if line.strip():
                    if "conclusion" in line.lower():
                        cot.set_conclusion(line)
                    else:
                        cot.add_step(line.strip())
        else:
            # Simple heuristic reasoning
            cot.add_step(f"Analyzing problem: {problem}")
            cot.add_step("Identifying key components and constraints")
            cot.add_step("Evaluating possible approaches")
            cot.set_conclusion("Further analysis required with LLM")

        return cot

    def synthesize_information(self, sources: List[Dict[str, Any]]) -> Synthesis:
        """
        Combine multiple information sources into a coherent synthesis.

        Args:
            sources: List of information sources with content

        Returns:
            Synthesis with combined information
        """
        if not sources:
            return Synthesis(
                summary="No information to synthesize",
                key_points=[],
                sources=[]
            )

        # Extract key points from each source
        key_points = []
        source_refs = []

        for source in sources:
            if "content" in source:
                # Simple extraction - in production use NLP/LLM
                content = source["content"]
                sentences = content.split(". ")[:3]  # First 3 sentences
                key_points.extend(sentences)

            if "reference" in source:
                source_refs.append(source["reference"])

        # Create summary
        summary = ". ".join(key_points[:5]) if key_points else "No content found"

        return Synthesis(
            summary=summary,
            key_points=key_points,
            sources=source_refs
        )

    def evaluate_options(self, options: List[Option]) -> List[Option]:
        """
        Evaluate and rank options based on pros/cons.

        Args:
            options: List of options to evaluate

        Returns:
            Options sorted by score (highest first)
        """
        for option in options:
            # Simple scoring: +1 for each pro, -1 for each con
            option.score = len(option.pros) - len(option.cons)

            # Bonus for more detailed analysis
            option.score += len(option.description) / 100

        # Sort by score descending
        return sorted(options, key=lambda o: o.score, reverse=True)

    async def analyze_code(self, code: str, question: str) -> ReasoningResult:
        """
        Analyze code to answer a specific question.

        Args:
            code: The code to analyze
            question: What to analyze about the code

        Returns:
            ReasoningResult with analysis
        """
        cot = ChainOfThought()

        # Basic code analysis
        cot.add_step("Parsing code structure")

        # Count basic metrics
        lines = code.split("\n")
        cot.add_step(f"Code has {len(lines)} lines")

        # Check for common patterns
        if "def " in code:
            func_count = code.count("def ")
            cot.add_step(f"Found {func_count} function definitions")

        if "class " in code:
            class_count = code.count("class ")
            cot.add_step(f"Found {class_count} class definitions")

        if "import " in code:
            import_count = code.count("import ")
            cot.add_step(f"Found {import_count} import statements")

        cot.set_conclusion(f"Code analysis complete for: {question}")

        return ReasoningResult(
            conclusion=cot.conclusion,
            confidence=0.7,
            chain_of_thought=cot.steps,
            evidence=[f"Analyzed {len(lines)} lines of code"]
        )

    def make_decision(
        self,
        options: List[str],
        criteria: Dict[str, float],
        context: Optional[str] = None
    ) -> str:
        """
        Make a decision between options based on criteria.

        Args:
            options: List of options to choose from
            criteria: Criteria with weights for evaluation
            context: Optional context for the decision

        Returns:
            The selected option
        """
        if not options:
            return ""

        if len(options) == 1:
            return options[0]

        # Simple scoring (in production, use LLM)
        scores = {option: 0.0 for option in options}

        for option in options:
            option_lower = option.lower()
            for criterion, weight in criteria.items():
                if criterion.lower() in option_lower:
                    scores[option] += weight

        # Return highest scoring option
        return max(scores, key=scores.get)
