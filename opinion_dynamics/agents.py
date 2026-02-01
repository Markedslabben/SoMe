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

    Supports both English and Norwegian language.
    """

    # ===== ENGLISH WORD LISTS =====
    EMOTIONAL_WORDS_EN = {
        'high': ['outrageous', 'insane', 'ridiculous', 'madness', 'disaster',
                 'catastrophe', 'terrible', 'amazing', 'incredible', 'absurd',
                 'furious', 'disgusted', 'horrified', 'delighted', 'thrilled',
                 'robbery', 'scam', 'fraud', 'crisis', 'emergency', 'collapse'],
        'medium': ['worried', 'concerned', 'frustrated', 'annoyed', 'pleased',
                   'hopeful', 'disappointed', 'surprised', 'confused', 'skeptical',
                   'expensive', 'unfair', 'corrupt', 'broken', 'failing']
    }

    CONFRONTATIONAL_PATTERNS_EN = [
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

    CONSENSUS_MARKERS_EN = [
        r'\bresearch shows\b',
        r'\bexperts agree\b',
        r'\bthe data\b',
        r'\bevidence\b',
        r'\bstudies\b',
        r'\bwhile\b.*\bbut\b',
        r'\bit\'s not simple\b',
        r'\btrade-?offs?\b',
        r'\bbalanced?\b',
        r'\bpragmatic\b',
        r'\breasonable\b',
        r'\backnowledge\b',
        r'\bwe need to consider\b',
    ]

    LOGICAL_CONNECTORS_EN = [
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

    HEDGES_EN = ['perhaps', 'maybe', 'might', 'could', 'possibly', 'seems', 'generally']
    ACKNOWLEDGEMENTS_EN = ['fair point', 'valid concern', 'i understand', 'legitimate']
    ABSOLUTES_EN = ['always', 'never', 'everyone', 'no one', 'all ', 'none ']
    EVIDENCE_WORDS_EN = ['data', 'study', 'research', 'percent', '%', 'billion']
    CHALLENGE_WORDS_EN = ['really', 'seriously', 'honestly']
    IMPERATIVE_STARTERS_EN = ['wake', 'stop', 'look', 'think', 'open']

    # ===== NORWEGIAN WORD LISTS =====
    EMOTIONAL_WORDS_NO = {
        'high': ['skandaløst', 'vanvittig', 'latterlig', 'galskap', 'katastrofe',
                 'forferdelig', 'utrolig', 'absurd', 'rasende', 'forferdet',
                 'ran', 'svindel', 'bedrageri', 'krise', 'nødsituasjon', 'kollaps',
                 'sjokkerende', 'hårreisende', 'grotesk', 'opprørende', 'avskyelig'],
        'medium': ['bekymret', 'urolig', 'frustrert', 'irritert', 'fornøyd',
                   'håpefull', 'skuffet', 'overrasket', 'forvirret', 'skeptisk',
                   'dyrt', 'urettferdig', 'korrupt', 'ødelagt', 'sviktende',
                   'trist', 'lei', 'oppgitt', 'misfornøyd']
    }

    CONFRONTATIONAL_PATTERNS_NO = [
        r'\bvåkn opp\b',
        r'\bdu virkelig\b',
        r'\bhvordan kan du\b',
        r'\bfor en vits\b',
        r'\bsåkalte?\b',
        r'\b"ekspertene"\b',
        r'\båpenbart\b',
        r'\bfeil\b',
        r'\bløgn(er)?\b',
        r'\btåpelig\b',
        r'\bnaiv\b',
        r'\buvitende\b',
        r'\bblind\b',
        r'\bsauer\b',
        r'\bhjernevasket\b',
        r'\bidiotisk\b',
        r'\bpathetic\b',
        r'\bhvem tror du\b',
        r'\bforstår du ikke\b',
        r'\bskjønner du ikke\b',
    ]

    CONSENSUS_MARKERS_NO = [
        r'\bforskning viser\b',
        r'\beksperter er enige\b',
        r'\bdataene\b',
        r'\bevidens\b',
        r'\bstudier\b',
        r'\bselv om\b.*\bmen\b',
        r'\bdet er ikke enkelt\b',
        r'\bavveininger?\b',
        r'\bbalansert\b',
        r'\bpragmatisk\b',
        r'\brimelig\b',
        r'\banerkjenne\b',
        r'\bvi må vurdere\b',
        r'\bfaktisk\b',
        r'\bifølge\b',
    ]

    LOGICAL_CONNECTORS_NO = [
        r'\bfordi\b',
        r'\bderfor\b',
        r'\bimidlertid\b',
        r'\bselv om\b',
        r'\bsiden\b',
        r'\bsåledes\b',
        r'\bhvis\b.*\bda\b',
        r'\bførst\b.*\bderetter\b',
        r'\bfor eksempel\b',
        r'\bmed andre ord\b',
        r'\blikevel\b',
        r'\bpå grunn av\b',
        r'\bfølgelig\b',
    ]

    HEDGES_NO = ['kanskje', 'muligens', 'kan', 'kunne', 'virker', 'generelt', 'antagelig', 'trolig']
    ACKNOWLEDGEMENTS_NO = ['godt poeng', 'gyldig bekymring', 'jeg forstår', 'legitimt', 'du har rett i']
    ABSOLUTES_NO = ['alltid', 'aldri', 'alle ', 'ingen ', 'ingenting', 'absolutt']
    EVIDENCE_WORDS_NO = ['data', 'studie', 'forskning', 'prosent', '%', 'milliard', 'statistikk']
    CHALLENGE_WORDS_NO = ['virkelig', 'seriøst', 'ærlig talt']
    IMPERATIVE_STARTERS_NO = ['våkn', 'stopp', 'se', 'tenk', 'åpne']

    def __init__(self, language: str = "en"):
        """
        Initialize ContentAnalyzer with language setting.

        Args:
            language: Language code - "en" for English, "no" for Norwegian
        """
        self.language = language
        self._set_language_specific_lists()

    def _set_language_specific_lists(self):
        """Set instance variables based on language."""
        if self.language == "no":
            self.EMOTIONAL_WORDS = self.EMOTIONAL_WORDS_NO
            self.CONFRONTATIONAL_PATTERNS = self.CONFRONTATIONAL_PATTERNS_NO
            self.CONSENSUS_MARKERS = self.CONSENSUS_MARKERS_NO
            self.LOGICAL_CONNECTORS = self.LOGICAL_CONNECTORS_NO
            self.HEDGES = self.HEDGES_NO
            self.ACKNOWLEDGEMENTS = self.ACKNOWLEDGEMENTS_NO
            self.ABSOLUTES = self.ABSOLUTES_NO
            self.EVIDENCE_WORDS = self.EVIDENCE_WORDS_NO
            self.CHALLENGE_WORDS = self.CHALLENGE_WORDS_NO
            self.IMPERATIVE_STARTERS = self.IMPERATIVE_STARTERS_NO
            self.YOU_PATTERN = r'\bdu\b'  # Norwegian "you"
        else:  # Default to English
            self.EMOTIONAL_WORDS = self.EMOTIONAL_WORDS_EN
            self.CONFRONTATIONAL_PATTERNS = self.CONFRONTATIONAL_PATTERNS_EN
            self.CONSENSUS_MARKERS = self.CONSENSUS_MARKERS_EN
            self.LOGICAL_CONNECTORS = self.LOGICAL_CONNECTORS_EN
            self.HEDGES = self.HEDGES_EN
            self.ACKNOWLEDGEMENTS = self.ACKNOWLEDGEMENTS_EN
            self.ABSOLUTES = self.ABSOLUTES_EN
            self.EVIDENCE_WORDS = self.EVIDENCE_WORDS_EN
            self.CHALLENGE_WORDS = self.CHALLENGE_WORDS_EN
            self.IMPERATIVE_STARTERS = self.IMPERATIVE_STARTERS_EN
            self.YOU_PATTERN = r'\byou\b'  # English "you"

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
        you_count = len(re.findall(self.YOU_PATTERN, text_lower))
        score += min(you_count * 0.08, 0.24)

        # Scare quotes (dismissive)
        scare_quotes = len(re.findall(r'"[^"]{1,20}"', text)) + len(re.findall(r"'[^']{1,20}'", text))
        score += min(scare_quotes * 0.1, 0.2)

        # Rhetorical questions with challenge words
        if '?' in text and any(w in text_lower for w in self.CHALLENGE_WORDS):
            score += 0.15

        # Imperative mood starters
        words = text_lower.split()
        if words and words[0] in self.IMPERATIVE_STARTERS:
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
        if any(w in text_lower for w in self.EVIDENCE_WORDS):
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
        for hedge in self.HEDGES:
            if hedge in text_lower:
                score += 0.05

        # Acknowledging other side
        if any(phrase in text_lower for phrase in self.ACKNOWLEDGEMENTS):
            score += 0.15

        # Negative for absolute language
        for absolute in self.ABSOLUTES:
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

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", language: str = "en"):
        """
        Initialize the LLM agent handler.

        Args:
            api_key: Anthropic API key
            model: Model to use for generation
            language: Language code - "en" for English, "no" for Norwegian
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.language = language
        self.analyzer = ContentAnalyzer(language=language)

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


def create_test_post(agent: Agent, content: str, language: str = "en") -> Post:
    """
    Create a test post without API call (for debugging).

    Args:
        agent: The agent "authoring" the post
        content: The post content
        language: Language code - "en" for English, "no" for Norwegian

    Returns:
        Post object with analyzed metrics
    """
    analyzer = ContentAnalyzer(language=language)
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
