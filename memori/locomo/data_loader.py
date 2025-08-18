"""
LOCOMO Dataset Loader

Loads and parses LOCOMO (Long-Term Conversational Memory) benchmark data from JSON files.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from .data_models import LocomoConversation, LocomoDataset, LOCOMO_QUESTION_CATEGORIES

logger = logging.getLogger(__name__)


class LocomoDataLoader:
    """Loader for LOCOMO dataset with validation and error handling"""
    
    def __init__(self, data_path: Optional[Union[str, Path]] = None):
        """
        Initialize the LOCOMO data loader
        
        Args:
            data_path: Path to LOCOMO data directory. If None, uses default location.
        """
        if data_path is None:
            # Default to the downloaded dataset location
            self.data_path = Path(__file__).parent.parent.parent / "locomo_dataset" / "data"
        else:
            self.data_path = Path(data_path)
        
        logger.info(f"LOCOMO data loader initialized with path: {self.data_path}")
    
    def load_dataset(self, filename: str = "locomo10.json") -> LocomoDataset:
        """
        Load the complete LOCOMO dataset
        
        Args:
            filename: Name of the JSON file to load
            
        Returns:
            LocomoDataset object with all conversations
            
        Raises:
            FileNotFoundError: If the data file doesn't exist
            ValueError: If the JSON data is invalid or malformed
        """
        file_path = self.data_path / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"LOCOMO data file not found: {file_path}")
        
        logger.info(f"Loading LOCOMO dataset from: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            if not isinstance(raw_data, list):
                raise ValueError("LOCOMO data should be a list of conversations")
            
            conversations = []
            for i, conv_data in enumerate(raw_data):
                try:
                    conversation = LocomoConversation.from_raw_data(conv_data)
                    conversations.append(conversation)
                    logger.debug(f"Loaded conversation {i+1}: {conversation.speaker_a} & {conversation.speaker_b}")
                except Exception as e:
                    logger.warning(f"Failed to parse conversation {i+1}: {e}")
                    continue
            
            dataset = LocomoDataset(conversations=conversations)
            
            logger.info(
                f"Successfully loaded {dataset.total_conversations} conversations "
                f"with {dataset.total_qa_pairs} QA pairs and {dataset.total_turns} total turns"
            )
            
            return dataset
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in LOCOMO data file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load LOCOMO dataset: {e}")
    
    def load_single_conversation(self, dataset: LocomoDataset, conversation_index: int) -> LocomoConversation:
        """
        Load a single conversation by index
        
        Args:
            dataset: The loaded LOCOMO dataset
            conversation_index: Index of conversation to retrieve (0-based)
            
        Returns:
            Single LocomoConversation object
            
        Raises:
            IndexError: If conversation_index is out of range
        """
        if conversation_index < 0 or conversation_index >= len(dataset.conversations):
            raise IndexError(
                f"Conversation index {conversation_index} out of range. "
                f"Dataset has {len(dataset.conversations)} conversations."
            )
        
        return dataset.conversations[conversation_index]
    
    def get_conversations_by_speakers(self, dataset: LocomoDataset, speaker_name: str) -> List[LocomoConversation]:
        """
        Get all conversations involving a specific speaker
        
        Args:
            dataset: The loaded LOCOMO dataset  
            speaker_name: Name of speaker to search for
            
        Returns:
            List of conversations involving the speaker
        """
        matching_conversations = []
        for conversation in dataset.conversations:
            if speaker_name in [conversation.speaker_a, conversation.speaker_b]:
                matching_conversations.append(conversation)
        
        logger.info(f"Found {len(matching_conversations)} conversations involving {speaker_name}")
        return matching_conversations
    
    def validate_dataset(self, dataset: LocomoDataset) -> Dict[str, Union[bool, List[str]]]:
        """
        Validate the loaded dataset for completeness and consistency
        
        Args:
            dataset: The dataset to validate
            
        Returns:
            Validation results dictionary
        """
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check if we have expected number of conversations (should be 10 for locomo10)
        if len(dataset.conversations) != 10:
            validation_results["warnings"].append(
                f"Expected 10 conversations, found {len(dataset.conversations)}"
            )
        
        # Validate each conversation
        for i, conversation in enumerate(dataset.conversations):
            conv_prefix = f"Conversation {i+1}"
            
            # Check if conversation has sessions
            if not conversation.sessions:
                validation_results["errors"].append(f"{conv_prefix}: No sessions found")
                validation_results["is_valid"] = False
                continue
            
            # Check if conversation has QA pairs
            if not conversation.qa_pairs:
                validation_results["errors"].append(f"{conv_prefix}: No QA pairs found")
                validation_results["is_valid"] = False
            
            # Check session continuity
            session_ids = [session.session_id for session in conversation.sessions]
            expected_sessions = [f"session_{i+1}" for i in range(len(session_ids))]
            
            if session_ids != expected_sessions:
                validation_results["warnings"].append(
                    f"{conv_prefix}: Session IDs may not be sequential: {session_ids}"
                )
            
            # Validate QA categories
            qa_categories = [qa.category for qa in conversation.qa_pairs]
            invalid_categories = [cat for cat in qa_categories if cat not in LOCOMO_QUESTION_CATEGORIES]
            
            if invalid_categories:
                validation_results["errors"].append(
                    f"{conv_prefix}: Invalid QA categories found: {invalid_categories}"
                )
                validation_results["is_valid"] = False
            
            # Check for dialogue ID consistency in QA evidence
            dialogue_ids = set()
            for session in conversation.sessions:
                for turn in session.turns:
                    dialogue_ids.add(turn.dia_id)
            
            evidence_ids = set()
            for qa in conversation.qa_pairs:
                evidence_ids.update(qa.evidence)
            
            missing_evidence = evidence_ids - dialogue_ids
            if missing_evidence:
                validation_results["warnings"].append(
                    f"{conv_prefix}: QA evidence references missing dialogue IDs: {missing_evidence}"
                )
        
        if validation_results["is_valid"]:
            logger.info("Dataset validation passed")
        else:
            logger.error(f"Dataset validation failed with {len(validation_results['errors'])} errors")
        
        if validation_results["warnings"]:
            logger.warning(f"Dataset validation found {len(validation_results['warnings'])} warnings")
        
        return validation_results
    
    def get_dataset_statistics(self, dataset: LocomoDataset) -> Dict[str, Union[int, float, Dict]]:
        """
        Generate comprehensive statistics about the dataset
        
        Args:
            dataset: The dataset to analyze
            
        Returns:
            Dictionary with dataset statistics
        """
        stats = {
            "total_conversations": dataset.total_conversations,
            "total_qa_pairs": dataset.total_qa_pairs,
            "total_dialogue_turns": dataset.total_turns,
            "total_estimated_tokens": sum(conv.total_tokens for conv in dataset.conversations),
            "qa_by_category": {},
            "conversations_stats": [],
            "average_turns_per_conversation": 0,
            "average_tokens_per_conversation": 0,
            "average_qa_pairs_per_conversation": 0
        }
        
        # QA category breakdown
        qa_by_category = dataset.get_qa_by_category()
        for category_id, qa_list in qa_by_category.items():
            category_name = LOCOMO_QUESTION_CATEGORIES.get(category_id, f"unknown_{category_id}")
            stats["qa_by_category"][category_name] = len(qa_list)
        
        # Per-conversation statistics
        for i, conversation in enumerate(dataset.conversations):
            conv_stats = {
                "conversation_id": i + 1,
                "speakers": [conversation.speaker_a, conversation.speaker_b],
                "sessions": len(conversation.sessions),
                "turns": conversation.total_turns,
                "estimated_tokens": conversation.total_tokens,
                "qa_pairs": len(conversation.qa_pairs)
            }
            stats["conversations_stats"].append(conv_stats)
        
        # Calculate averages
        if dataset.total_conversations > 0:
            stats["average_turns_per_conversation"] = dataset.total_turns / dataset.total_conversations
            stats["average_tokens_per_conversation"] = stats["total_estimated_tokens"] / dataset.total_conversations  
            stats["average_qa_pairs_per_conversation"] = dataset.total_qa_pairs / dataset.total_conversations
        
        logger.info(f"Generated statistics for {dataset.total_conversations} conversations")
        return stats


def load_locomo_dataset(data_path: Optional[Union[str, Path]] = None) -> LocomoDataset:
    """
    Convenience function to load LOCOMO dataset
    
    Args:
        data_path: Path to LOCOMO data directory
        
    Returns:
        Loaded and validated LocomoDataset
    """
    loader = LocomoDataLoader(data_path)
    dataset = loader.load_dataset()
    
    # Validate the loaded dataset
    validation_results = loader.validate_dataset(dataset)
    
    if not validation_results["is_valid"]:
        logger.error("Dataset validation failed!")
        for error in validation_results["errors"]:
            logger.error(f"Validation error: {error}")
    
    return dataset


if __name__ == "__main__":
    # Test the data loader
    logging.basicConfig(level=logging.INFO)
    
    try:
        dataset = load_locomo_dataset()
        loader = LocomoDataLoader()
        stats = loader.get_dataset_statistics(dataset)
        
        print("LOCOMO Dataset Statistics:")
        print(f"Conversations: {stats['total_conversations']}")
        print(f"Total QA Pairs: {stats['total_qa_pairs']}")  
        print(f"Total Turns: {stats['total_dialogue_turns']}")
        print(f"Estimated Tokens: {stats['total_estimated_tokens']}")
        print(f"QA by Category: {stats['qa_by_category']}")
        
    except Exception as e:
        logger.error(f"Failed to test data loader: {e}")
        raise