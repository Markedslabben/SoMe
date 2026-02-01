"""
LLM Agent integration for the Opinion Dynamics Simulation.

Handles Claude API calls to generate agent posts and analyzes
content for emotional/confrontational characteristics.
"""

import re
import anthropic
from typing import Optional
from models import Agent, AgentRole, Post, EmotionalState
from prompts import get_system_prompt, format_prompt


class ContentAnalyzer:
    """
    Analyzes post content to extract emotional and behavioral metrics.

    Uses lexical patterns to estimate:
    - Emotional intensity
    - Provocativeness/confrontation
    - Logical coherence
    - Consensus orientation
    """

    # Emotional intensity markers
    EMOTIONAL_WORDS = {
        'high': ['outrageous', 'insane', 'ridiculous', 'madness', 'disaster',
                 'catastrophe', 'terrible', 'amazing', 'incredible', 'absurd',
                 'furious', 'disgusted', 'horrified', 'delighted', 'thrilled',
                 'robbery', 'scam', 'fraud', 'crisis', 'emergency', 'collapse'],
        'medium': ['worried', 'concerned', 'frustrated', 'annoyed', 'pleased',
                   'hopeful', 'disappointed', 'surprised', 'confused', 'skeptical',
                   'expensive', 'unfair', 'corrupt', 'broken', 'failing']
    }

    # Confrontational markers
    CONFRONTATIONAL_PATTERNS = [
        r'\bwake up\b',
        r'\byou really\b',
        r'\bhow can you\b',
        r'\bwhat a joke\b',
        r'\bso-called\b',
        r'\bthe "experts"\b',
        r'\bobviously\b',
        r'\bwrong\b',
        r'\blie[sd]?\b',
        r'\bfoolish\b',
        r'\bnaive\b',
        r'\bignorant\b',
        r'\bblind\b',
        r'\bsheep\b',
        r'\bbrainwashed\b',
    ]

    # Consensus/cooperative markers
    CONSENSUS_MARKERS = [
        r'\bresearch shows\b',
        r'\bexperts agree\b',
        r'\bthe data\b',
        r'\bevidence\b',
        r'\bstudies\b',
        r'\bwhile\b.*\bbut\b',  # Acknowledging complexity
        r'\bit\'s not simple\b',
        r'\btrade-?offs?\b',
        r'\bbalanced?\b',
        r'\bpragmatic\b',
        r'\breasonable\b',
        r'\backnowledge\b',
        r'\bwe need to consider\b',
    ]

    # Logical structure markers
    LOGICAL_CONNECTORS = [
        r'\bbecause\b',
        r'\btherefore\b',
        r'\bhowever\b',
        r'\balthough\b',
        r'\bsince\b',
        r'\bthus\b',
        r'\bif\b.*\bthen\b',
        r'\bfirst\b.*\bsecond\b',
        r'\bfor example\b',
        r'\bin other words\b',
    ]

    def analyze(self, text: str) -> dict:
        """
        Analyze text and return metrics dict.

        Returns:
            dict with keys: emotional_intensity, provocativeness,
                           logical_coherence, consensus_orientation
        """
        text_lower = text.lower()

        # Emotional intensity
        emotional = self._calculate_emotional_intensity(text, text_lower)

        # Provocativeness
        provocative = self._calculate_provocativeness(text, text_lower)

        # Logical coherence
        logical = self._calculate_logical_coherence(text_lower)

        # Consensus orientation
        consensus = self._calculate_consensus_orientation(text_lower)

        return {
            'emotional_intensity': emotional,
            'provocativeness': provocative,
            'logical_coherence': logical,
            'consensus_orientation': consensus
        }

    def _calculate_emotional_intensity(self, text: str, text_lower: str) -> float:
        """Calculate emotional intensity from text features."""
        score = 0.0

        # Count exclamation marks (strong signal)
        exclamations = text.count('!')
        score += min(exclamations * 0.15, 0.45)

        # Count question marks (rhetorical questions)
        questions = text.count('?')
        score += min(questions * 0.08, 0.24)

        # Caps ratio (SHOUTING)
        if len(text) > 10:
            caps = sum(1 for c in text if c.isupper() and c.isalpha())
            letters = sum(1 for c in text if c.isalpha())
            if letters > 0:
                caps_ratio = caps / letters
                if caps_ratio > 0.3:  # Significant caps
                    score += 0.2

        # High-intensity words
        for word in self.EMOTIONAL_WORDS['high']:
            if word in text_lower:
                score += 0.12

        # Medium-intensity words
        for word in self.EMOTIONAL_WORDS['medium']:
            if word in text_lower:
                score += 0.06

        return min(1.0, score)

    def _calculate_provocativeness(self, text: str, text_lower: str) -> float:
        """Calculate how confrontational/provocative the text is."""
        score = 0.0

        # Direct confrontational patterns
        for pattern in self.CONFRONTATIONAL_PATTERNS:
            if re.search(pattern, text_lower):
                score += 0.15

        # "You" statements (direct address, often confrontational)
        you_count = len(re.findall(r'\byou\b', text_lower))
        score += min(you_count * 0.08, 0.24)

        # Scare quotes (dismissive)
        scare_quotes = len(re.findall(r'"[^"]{1,20}"', text)) + len(re.findall(r"'[^']{1,20}'", text))
        score += min(scare_quotes * 0.1, 0.2)

        # Rhetorical questions with challenge words
        if '?' in text and any(w in text_lower for w in ['really', 'seriously', 'honestly']):
            score += 0.15

        # Imperative mood starters
        imperative_starters = ['wake', 'stop', 'look', 'think', 'open']
        words = text_lower.split()
        if words and words[0] in imperative_starters:
            score += 0.1

        return min(1.0, score)

    def _calculate_logical_coherence(self, text_lower: str) -> float:
        """Calculate logical structure of argument."""
        score = 0.4  # Base score

        # Logical connectors
        for pattern in self.LOGICAL_CONNECTORS:
            if re.search(pattern, text_lower):
                score += 0.1

        # Sentence structure (longer, more structured = higher)
        sentences = re.split(r'[.!?]', text_lower)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) >= 2:
            score += 0.1

        # Average sentence length (not too short)
        if sentences:
            avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_len > 8:
                score += 0.1

        # Evidence references
        if any(w in text_lower for w in ['data', 'study', 'research', 'percent', '%', 'billion']):
            score += 0.15

        return min(1.0, score)

    def _calculate_consensus_orientation(self, text_lower: str) -> float:
        """Calculate how cooperative/consensus-seeking the text is."""
        score = 0.3  # Base score

        # Consensus markers
        for pattern in self.CONSENSUS_MARKERS:
            if re.search(pattern, text_lower):
                score += 0.12

        # Hedging language (nuanced, not absolute)
        hedges = ['perhaps', 'maybe', 'might', 'could', 'possibly', 'seems', 'generally']
        for hedge in hedges:
            if hedge in text_lower:
                score += 0.05

        # Acknowledging other side
        if any(phrase in text_lower for phrase in ['fair point', 'valid concern', 'i understand', 'legitimate']):
            score += 0.15

        # Negative for absolute language
        absolutes = ['always', 'never', 'everyone', 'no one', 'all ', 'none ']
        for absolute in absolutes:
            if absolute in text_lower:
                score -= 0.08

        return max(0.0, min(1.0, score))


class LLMAgent:
    """
    Manages Claude API calls to generate agent posts.

    Each agent's post is generated based on their role-specific
    prompt template, current emotional state, and memory of
    recent posts.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize the LLM agent handler.

        Args:
            api_key: Anthropic API key
            model: Model to use for generation
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.analyzer = ContentAnalyzer()

    def generate_post(
        self,
        agent: Agent,
        topic: str,
        max_tokens: int = 80  # ~280 characters, tweet-length
    ) -> Post:
        """
        Generate a post from an agent based on their state.

        Args:
            agent: The agent generating the post
            topic: The debate topic
            max_tokens: Maximum tokens for response (~80 tokens ≈ 280 chars)

        Returns:
            Post object with content and analyzed metrics
        """
        # Get appropriate prompt template
        template = get_system_prompt(agent.role.name)

        # Format with current state
        emotion_desc = agent.emotional_state.to_description()
        opinion_desc = agent.opinion.to_description() if agent.role == AgentRole.NEUTRAL_OBSERVER else ""

        system_prompt = format_prompt(
            template,
            emotion_description=emotion_desc,
            memory=agent.memory,
            opinion_description=opinion_desc
        )

        # Call Claude API
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": "Write your post now."}]
            )

            content = response.content[0].text.strip()

            # Clean up any markdown artifacts
            content = content.strip('"\'')
            if content.startswith('[') and ']:' in content:
                # Remove any accidental name prefix
                content = content.split(']:', 1)[-1].strip()

        except Exception as e:
            # Fallback content on API error
            content = f"[API Error: {str(e)[:50]}]"
            print(f"Warning: API call failed for agent {agent.id}: {e}")

        # Analyze the content
        metrics = self.analyzer.analyze(content)

        # Create post object
        post = Post(
            author_id=agent.id,
            author_name=agent.name,
            content=content,
            emotional_intensity=metrics['emotional_intensity'],
            provocativeness=metrics['provocativeness'],
            logical_coherence=metrics['logical_coherence'],
            consensus_orientation=metrics['consensus_orientation'],
            author_arousal=agent.emotional_state.arousal,
            author_opinion=agent.opinion.position
        )

        # Record behavioral metrics
        agent.behavior_metrics.record_post(
            confrontation=metrics['provocativeness'],
            consensus_orient=metrics['consensus_orientation']
        )

        return post


def create_test_post(agent: Agent, content: str) -> Post:
    """
    Create a test post without API call (for debugging).

    Args:
        agent: The agent "authoring" the post
        content: The post content

    Returns:
        Post object with analyzed metrics
    """
    analyzer = ContentAnalyzer()
    metrics = analyzer.analyze(content)

    return Post(
        author_id=agent.id,
        author_name=agent.name,
        content=content,
        emotional_intensity=metrics['emotional_intensity'],
        provocativeness=metrics['provocativeness'],
        logical_coherence=metrics['logical_coherence'],
        consensus_orientation=metrics['consensus_orientation'],
        author_arousal=agent.emotional_state.arousal,
        author_opinion=agent.opinion.position
    )
