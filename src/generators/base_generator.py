"""
Base question generator class with shared functionality for all question types.
"""
import json
import uuid
import os
import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Tuple

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src import settings
from src.settings import NeptuneEndpoint, VectorStoreEndpoint
from src.utils.constants import CENGAGE_GUIDELINES as cengage_guidelines, metadata_keys
from src.utils.helpers import get_difficulty_description, get_blooms_question_guidelines

from graphrag_toolkit.lexical_graph.storage import (
    GraphStoreFactory,
    VectorStoreFactory
)
from graphrag_toolkit.lexical_graph import LexicalGraphQueryEngine
from graphrag_toolkit.lexical_graph.metadata import FilterConfig
from llama_index.core.vector_stores.types import (
    MetadataFilter,
    FilterOperator
)


class BaseQuestionGenerator(ABC):
    """
    Abstract base class for all question generators.
    Contains shared functionality for GraphRAG integration, filtering, and question breakdown.
    """
    
    def __init__(self, tenant_id: str = 'cx2201'):
        """
        Initialize the base question generator.
        
        Args:
            tenant_id: The tenant ID for the GraphRAG query engine
        """
        self.tenant_id = tenant_id
        self.available_keys = list(set(metadata_keys.keys()))
        self.chapter_key = 'toc_level_1_title'
        
        # Initialize GraphRAG components (will be set up when needed)
        self._graph_store = None
        self._vector_store = None
        self._query_engine = None
    
    def _initialize_graphrag_components(self, filters: List[MetadataFilter]):
        """
        Initialize GraphRAG components with the specified filters.
        
        Args:
            filters: List of metadata filters to apply
        """
        if self._graph_store is None:
            self._graph_store = GraphStoreFactory.for_graph_store(NeptuneEndpoint)
        
        if self._vector_store is None:
            self._vector_store = VectorStoreFactory.for_vector_store(VectorStoreEndpoint)
        
        filter_config = FilterConfig(source_filters=filters)
        
        self._query_engine = LexicalGraphQueryEngine.for_traversal_based_search(
            self._graph_store,
            self._vector_store,
            filter_config=filter_config,
            tenant_id=self.tenant_id,
            llm_config={
                "model": "arn:aws:bedrock:us-east-1:051826717360:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                "temperature": 0,
                "max_tokens": 10000,
                "system_prompt": cengage_guidelines
            }
        )
    
    def _build_filters(self, chapter_id: str, learning_objectives: Optional[Union[str, List[str]]] = None) -> List[MetadataFilter]:
        """
        Build metadata filters for GraphRAG queries.
        
        Args:
            chapter_id: The chapter identifier
            learning_objectives: Optional learning objectives to filter on
            
        Returns:
            List of metadata filters
        """
        filters = []
        
        # Primary filter for chapter (always present)
        chapter_filter = MetadataFilter(
            key=self.chapter_key,
            value=chapter_id,
            operator=FilterOperator.EQ
        )
        filters.append(chapter_filter)
        print(f"Added chapter filter: {self.chapter_key}={chapter_id}")
        
        # Add learning objectives filter if available
        if learning_objectives is not None and 'learning_objectives' in self.available_keys:
            if isinstance(learning_objectives, list) and len(learning_objectives) > 1:
                print(f"Adding learning_objectives filter: IN operator with values: {learning_objectives}")
                lo_filter = MetadataFilter(
                    key='learning_objectives',
                    value=learning_objectives,
                    operator=FilterOperator.IN
                )
                filters.append(lo_filter)
            else:
                value = learning_objectives[0] if isinstance(learning_objectives, list) else learning_objectives
                print(f"Adding learning_objectives filter: EQ operator with value: {value}")
                lo_filter = MetadataFilter(
                    key='learning_objectives',
                    value=value,
                    operator=FilterOperator.EQ
                )
                filters.append(lo_filter)
        elif learning_objectives is not None:
            print("Warning: 'learning_objectives' filter requested but 'learning_objectives' key not found in metadata.")
        
        return filters
    
    def _calculate_question_breakdown(self, num_questions: int, difficulty_distribution: Dict[str, float], 
                                    blooms_taxonomy_distribution: Dict[str, float]) -> Dict[str, Dict]:
        """
        Calculate the breakdown of questions by difficulty and Bloom's taxonomy level.
        
        Args:
            num_questions: Total number of questions to generate
            difficulty_distribution: Distribution of difficulty levels
            blooms_taxonomy_distribution: Distribution of Bloom's taxonomy levels
            
        Returns:
            Dictionary with question breakdown specifications
        """
        question_breakdown = {}
        
        for difficulty, diff_ratio in difficulty_distribution.items():
            for blooms, blooms_ratio in blooms_taxonomy_distribution.items():
                count = int(round(num_questions * diff_ratio * blooms_ratio))
                if count > 0:
                    question_breakdown[f"{difficulty}_{blooms}"] = {
                        'difficulty': difficulty,
                        'blooms_level': blooms,
                        'count': count
                    }
        
        # Adjust to ensure total matches exactly
        total_calculated = sum([item['count'] for item in question_breakdown.values()])
        if total_calculated != num_questions:
            # Add/subtract from the largest group
            largest_key = max(question_breakdown.keys(), key=lambda k: question_breakdown[k]['count'])
            question_breakdown[largest_key]['count'] += (num_questions - total_calculated)
        
        return question_breakdown
    
    def _create_question_sequence(self, question_breakdown: Dict[str, Dict]) -> List[Tuple[str, str]]:
        """
        Create a sequence of (difficulty, blooms_level) tuples based on question breakdown.
        
        Args:
            question_breakdown: Dictionary with question breakdown specifications
            
        Returns:
            List of tuples containing difficulty and blooms level for each question
        """
        sequence = []
        for combo_key, specs in question_breakdown.items():
            difficulty = specs['difficulty']
            blooms_level = specs['blooms_level']
            count = specs['count']
            
            # Add this combination 'count' times to the sequence
            for _ in range(count):
                sequence.append((difficulty, blooms_level))
        
        return sequence
    
    def _generate_content_summary(self, chapter_id: str, learning_objectives: Optional[Union[str, List[str]]] = None) -> str:
        """
        Generate content summary for the specified chapter and learning objectives.
        
        Args:
            chapter_id: The chapter identifier
            learning_objectives: Optional learning objectives to filter on
            
        Returns:
            Content summary string
        """
        filter_description = f"chapter {chapter_id}"
        if learning_objectives and 'learning_objectives' in self.available_keys:
            filter_description += f" with learning objectives: {learning_objectives if isinstance(learning_objectives, list) else [learning_objectives]}"
        
        summary_query = f"Provide a comprehensive summary of content for {filter_description}. Include key concepts, topics, and important details."
        print("Retrieving content summary...")
        
        summary_response = self._query_engine.query(summary_query)
        content_summary = summary_response.response
        print(f"Summary length: {len(content_summary)} characters")
        
        return content_summary
    
    def _generate_filename(self, chapter_id: str, difficulty_distribution: Dict[str, float], 
                          blooms_taxonomy_distribution: Dict[str, float], 
                          learning_objectives: Optional[Union[str, List[str]]] = None) -> str:
        """
        Generate filename based on parameters and question type.
        
        Args:
            chapter_id: The chapter identifier
            difficulty_distribution: Distribution of difficulty levels
            blooms_taxonomy_distribution: Distribution of Bloom's taxonomy levels
            learning_objectives: Optional learning objectives
            
        Returns:
            Generated filename
        """
        difficulty_str = "_".join([f"{diff}{int(prop*100)}" for diff, prop in difficulty_distribution.items()])
        blooms_str = "_".join([f"{bloom}{int(prop*100)}" for bloom, prop in blooms_taxonomy_distribution.items()])
        
        filename_parts = [chapter_id, difficulty_str, blooms_str]
        if learning_objectives and 'learning_objectives' in self.available_keys:
            obj_str = "lo" + ("_".join([str(obj) for obj in learning_objectives]) if isinstance(learning_objectives, list) else str(learning_objectives))
            filename_parts.append(obj_str)
        
        return "_".join(filename_parts) + f"_{self.get_question_type()}.json"
    
    def _save_questions_to_file(self, questions: List[Dict], filename: str):
        """
        Save questions to JSON file.
        
        Args:
            questions: List of question dictionaries
            filename: Output filename
        """
        json_responses = {
            "response": questions
        }
        
        with open(filename, 'w') as json_file:
            json.dump(json_responses, json_file, indent=4)
        
        print(f"Generated {self.get_question_type()} questions and saved to {filename}")
    
    @abstractmethod
    def get_question_type(self) -> str:
        """
        Get the question type identifier.
        
        Returns:
            Question type string (e.g., 'mcq', 'fib', 'tf')
        """
        pass
    
    @abstractmethod
    def _parse_response(self, response_text: str, question_breakdown: Dict[str, Dict]) -> List[Dict]:
        """
        Parse the generated response text into structured question data.
        
        Args:
            response_text: Raw response text from the LLM
            question_breakdown: Question breakdown specifications
            
        Returns:
            List of parsed question dictionaries
        """
        pass
    
    @abstractmethod
    def _build_generation_prompt(self, content_summary: str, num_questions: int, 
                                question_breakdown: Dict[str, Dict]) -> str:
        """
        Build the prompt for question generation.
        
        Args:
            content_summary: Content summary for the chapter
            num_questions: Number of questions to generate
            question_breakdown: Question breakdown specifications
            
        Returns:
            Generation prompt string
        """
        pass
    
    def generate(self, chapter_id: str, learning_objectives: Optional[Union[str, List[str]]] = None,
                num_questions: int = 10, difficulty_distribution: Dict[str, float] = {'advanced': 1.0},
                blooms_taxonomy_distribution: Dict[str, float] = {'analyze': 1.0},
                content_summary: Optional[str] = None) -> str:
        """
        Generate questions for the specified parameters.
        
        Args:
            chapter_id: The chapter identifier
            learning_objectives: Optional learning objectives to filter on
            num_questions: Number of questions to generate
            difficulty_distribution: Distribution of difficulty levels
            blooms_taxonomy_distribution: Distribution of Bloom's taxonomy levels
            content_summary: Pre-generated content summary (optional)
            
        Returns:
            Generated questions text
        """
        print(f"Generating {num_questions} {self.get_question_type()} questions for chapter: {chapter_id}")
        if learning_objectives:
            print(f"Learning objectives filter: {learning_objectives}")
        print(f"Available metadata keys: {self.available_keys}")
        print(f"Difficulty distribution: {difficulty_distribution}")
        print(f"Bloom's taxonomy distribution: {blooms_taxonomy_distribution}")
        
        # Build filters and initialize GraphRAG components
        filters = self._build_filters(chapter_id, learning_objectives)
        self._initialize_graphrag_components(filters)
        
        # Generate or use provided content summary
        if content_summary is None:
            print("Warning: No content summary provided, generating new one...")
            content_summary = self._generate_content_summary(chapter_id, learning_objectives)
        else:
            print(f"Using provided content summary (length: {len(content_summary)} characters)")
        
        # Calculate question breakdown
        question_breakdown = self._calculate_question_breakdown(
            num_questions, difficulty_distribution, blooms_taxonomy_distribution
        )
        print(f"Question breakdown: {question_breakdown}")
        
        # Build generation prompt
        generation_prompt = self._build_generation_prompt(content_summary, num_questions, question_breakdown)
        
        # Generate questions
        print(f"Generating {self.get_question_type()} questions...")
        response = self._query_engine.query(generation_prompt)
        response_text = response.response
        
        # Parse response and save to file
        questions = self._parse_response(response_text, question_breakdown)
        filename = self._generate_filename(chapter_id, difficulty_distribution, blooms_taxonomy_distribution, learning_objectives)
        self._save_questions_to_file(questions, filename)
        
        return response_text
