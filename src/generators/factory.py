"""
Factory class for creating question generators.
"""
from typing import Optional
from .base_generator import BaseQuestionGenerator
from .mcq_generator import MCQGenerator
from .fib_generator import FillInBlankGenerator
from .tf_generator import TrueFalseGenerator


class QuestionGeneratorFactory:
    """
    Factory class for creating appropriate question generators based on question type.
    """
    
    _generators = {
        'mcq': MCQGenerator,
        'fib': FillInBlankGenerator,
        'tf': TrueFalseGenerator
    }
    
    @classmethod
    def create_generator(cls, question_type: str, tenant_id: str = 'cx2201') -> Optional[BaseQuestionGenerator]:
        """
        Create a question generator for the specified type.
        
        Args:
            question_type: Type of questions to generate ('mcq', 'fib', 'tf')
            tenant_id: The tenant ID for the GraphRAG query engine
            
        Returns:
            Appropriate question generator instance
            
        Raises:
            ValueError: If question_type is not supported
        """
        if question_type not in cls._generators:
            supported_types = ', '.join(cls._generators.keys())
            raise ValueError(f"Unsupported question type: {question_type}. Supported types: {supported_types}")
        
        generator_class = cls._generators[question_type]
        return generator_class(tenant_id=tenant_id)
    
    @classmethod
    def get_supported_types(cls) -> list:
        """
        Get list of supported question types.
        
        Returns:
            List of supported question type strings
        """
        return list(cls._generators.keys())
    
    @classmethod
    def create_multiple_generators(cls, question_types: list, tenant_id: str = 'cx2201') -> dict:
        """
        Create multiple generators for different question types.
        
        Args:
            question_types: List of question types to create generators for
            tenant_id: The tenant ID for the GraphRAG query engine
            
        Returns:
            Dictionary mapping question types to generator instances
            
        Raises:
            ValueError: If any question_type is not supported
        """
        generators = {}
        
        for question_type in question_types:
            generators[question_type] = cls.create_generator(question_type, tenant_id)
        
        return generators
