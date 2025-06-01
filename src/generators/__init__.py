"""
Question generators module.

This module provides class-based question generators for different question types:
- Multiple Choice Questions (MCQ)
- Fill-in-the-blank questions (FIB)
- True/False questions (TF)

All generators inherit from BaseQuestionGenerator and use the factory pattern for creation.

Example usage:
    from src.generators import QuestionGeneratorFactory
    
    # Create a single generator
    mcq_generator = QuestionGeneratorFactory.create_generator('mcq', tenant_id='1305101920')
    
    # Generate questions
    questions = mcq_generator.generate(
        chapter_id='01_01920_ch01_ptg01_hires_001-026',
        num_questions=10,
        difficulty_distribution={'basic': 0.3, 'intermediate': 0.3, 'advanced': 0.4},
        blooms_taxonomy_distribution={'remember': 0.3, 'apply': 0.4, 'analyze': 0.3}
    )
    
    # Create multiple generators
    generators = QuestionGeneratorFactory.create_multiple_generators(['mcq', 'fib', 'tf'])
"""

from .base_generator import BaseQuestionGenerator
from .mcq_generator import MCQGenerator
from .fib_generator import FillInBlankGenerator
from .tf_generator import TrueFalseGenerator
from .factory import QuestionGeneratorFactory

__all__ = [
    'BaseQuestionGenerator',
    'MCQGenerator', 
    'FillInBlankGenerator',
    'TrueFalseGenerator',
    'QuestionGeneratorFactory'
]
