"""
LOCOMO Dataset Data Models

Pydantic models for parsing and working with LOCOMO (Long-Term Conversational Memory) benchmark data.
"""

from datetime import datetime
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field


class LocomoDialogueTurn(BaseModel):
    """Individual dialogue turn in a LOCOMO conversation"""
    
    speaker: str = Field(description="Name of the speaker")
    dia_id: str = Field(description="Dialogue ID (e.g., 'D1:3')")
    text: str = Field(description="The actual dialogue text")
    
    # Optional multimodal fields
    img_url: Optional[List[str]] = Field(default=None, description="Image URLs if present")
    blip_caption: Optional[str] = Field(default=None, description="Image caption")
    query: Optional[str] = Field(default=None, description="Image search query")


class LocomoSession(BaseModel):
    """A single session within a LOCOMO conversation"""
    
    session_id: str = Field(description="Session identifier (e.g., 'session_1')")
    date_time: str = Field(description="Session date and time")
    turns: List[LocomoDialogueTurn] = Field(description="Dialogue turns in this session")


class LocomoQAItem(BaseModel):
    """Question-Answer pair from LOCOMO evaluation"""
    
    question: str = Field(description="The question")
    answer: Optional[Union[str, int]] = Field(default=None, description="The correct answer (None for adversarial questions)")
    evidence: List[str] = Field(description="Dialogue IDs that contain evidence")
    category: int = Field(description="Question category (1-5)")
    
    # Optional adversarial answer
    adversarial_answer: Optional[str] = Field(default=None, description="Adversarial/misleading answer")


class LocomoEventGraph(BaseModel):
    """Event graph structure from LOCOMO (if present)"""
    
    events: Dict[str, str] = Field(default_factory=dict, description="Event descriptions")
    relationships: Dict[str, List[str]] = Field(default_factory=dict, description="Event relationships")


class LocomoConversation(BaseModel):
    """Complete LOCOMO conversation with all sessions and QA data"""
    
    # Participant information
    speaker_a: str = Field(description="Name of first speaker")
    speaker_b: str = Field(description="Name of second speaker")
    
    # Session data - dynamically parsed
    sessions: List[LocomoSession] = Field(description="All conversation sessions")
    
    # Evaluation data
    qa_pairs: List[LocomoQAItem] = Field(description="Question-answer pairs for evaluation")
    
    # Optional event graph
    event_graph: Optional[LocomoEventGraph] = Field(default=None, description="Event graph if present")
    
    # Metadata
    total_turns: int = Field(description="Total number of dialogue turns")
    total_tokens: int = Field(default=0, description="Estimated total tokens")
    
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict) -> "LocomoConversation":
        """Create LocomoConversation from raw JSON data"""
        
        conversation_data = raw_data.get("conversation", {})
        qa_data = raw_data.get("qa", [])
        
        # Extract speaker names
        speaker_a = conversation_data.get("speaker_a", "Speaker A")
        speaker_b = conversation_data.get("speaker_b", "Speaker B")
        
        # Parse sessions dynamically
        sessions = []
        session_keys = [k for k in conversation_data.keys() if k.startswith("session_") and not k.endswith("_date_time")]
        
        for session_key in sorted(session_keys):
            session_data = conversation_data[session_key]
            date_time_key = f"{session_key}_date_time"
            date_time = conversation_data.get(date_time_key, "Unknown")
            
            # Parse dialogue turns
            turns = []
            if isinstance(session_data, list):
                for turn_data in session_data:
                    turn = LocomoDialogueTurn(**turn_data)
                    turns.append(turn)
            
            session = LocomoSession(
                session_id=session_key,
                date_time=date_time,
                turns=turns
            )
            sessions.append(session)
        
        # Parse QA pairs
        qa_pairs = []
        for qa_item in qa_data:
            qa_pair = LocomoQAItem(**qa_item)
            qa_pairs.append(qa_pair)
        
        # Calculate metadata
        total_turns = sum(len(session.turns) for session in sessions)
        
        # Estimate tokens (rough approximation: ~4 chars per token)
        total_chars = sum(
            sum(len(turn.text) for turn in session.turns)
            for session in sessions
        )
        total_tokens = total_chars // 4
        
        return cls(
            speaker_a=speaker_a,
            speaker_b=speaker_b,
            sessions=sessions,
            qa_pairs=qa_pairs,
            total_turns=total_turns,
            total_tokens=total_tokens
        )


class LocomoDataset(BaseModel):
    """Complete LOCOMO dataset with all conversations"""
    
    conversations: List[LocomoConversation] = Field(description="All LOCOMO conversations")
    
    @property
    def total_conversations(self) -> int:
        """Total number of conversations in dataset"""
        return len(self.conversations)
    
    @property
    def total_qa_pairs(self) -> int:
        """Total number of QA pairs across all conversations"""
        return sum(len(conv.qa_pairs) for conv in self.conversations)
    
    @property
    def total_turns(self) -> int:
        """Total dialogue turns across all conversations"""
        return sum(conv.total_turns for conv in self.conversations)
    
    def get_qa_by_category(self) -> Dict[int, List[LocomoQAItem]]:
        """Group QA pairs by category"""
        qa_by_category = {}
        for conversation in self.conversations:
            for qa_pair in conversation.qa_pairs:
                category = qa_pair.category
                if category not in qa_by_category:
                    qa_by_category[category] = []
                qa_by_category[category].append(qa_pair)
        return qa_by_category


# Question category mapping based on LOCOMO research
LOCOMO_QUESTION_CATEGORIES = {
    1: "single_hop",      # Answerable from a single session
    2: "temporal",        # Requires reasoning about time and events  
    3: "multi_hop",       # Requires synthesizing information from multiple sessions
    4: "open_domain",     # Requires integrating external knowledge
    5: "adversarial"      # Designed to mislead the agent
}


class LocomotBenchmarkResult(BaseModel):
    """Results from running LOCOMO benchmark"""
    
    conversation_id: str = Field(description="Identifier for the conversation")
    
    # QA Results by category
    single_hop_score: float = Field(default=0.0, description="Single-hop QA accuracy")
    multi_hop_score: float = Field(default=0.0, description="Multi-hop QA accuracy")  
    temporal_score: float = Field(default=0.0, description="Temporal QA accuracy")
    open_domain_score: float = Field(default=0.0, description="Open-domain QA accuracy")
    adversarial_score: float = Field(default=0.0, description="Adversarial QA accuracy")
    
    # Overall metrics
    overall_qa_score: float = Field(default=0.0, description="Overall QA accuracy")
    llm_judge_score: float = Field(default=0.0, description="LLM-as-a-Judge score")
    
    # Performance metrics  
    processing_latency: float = Field(default=0.0, description="Processing time in seconds")
    token_usage: int = Field(default=0, description="Total tokens used")
    
    # Event summarization score (optional)
    event_summary_score: float = Field(default=0.0, description="Event summarization accuracy")
    
    # Metadata
    processed_at: datetime = Field(default_factory=datetime.now)
    processing_metadata: Optional[Dict[str, str]] = Field(default=None)