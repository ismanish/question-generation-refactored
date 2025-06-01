"""
Helper functions for the application.
"""
import json
from typing import Dict, Any, List

def get_difficulty_description(difficulty):
    """Return a description of what each difficulty level means for question generation."""
    if difficulty == "basic":
        return "recall of facts and basic understanding of concepts"
    elif difficulty == "intermediate":
        return "application of concepts and analysis of relationships"
    elif difficulty == "advanced":
        return "synthesis of multiple concepts and evaluation of complex scenarios"
    else:
        return "appropriate college-level understanding"

def get_blooms_question_guidelines(blooms_level, question_type):
    """Return specific guidelines for creating questions at a given Bloom's level and question type."""
    
    if question_type == "mcq":
        if blooms_level == "remember":
            return "Focus on direct recall of facts, definitions, and basic concepts. Stem should ask for specific information covered in the material."
        elif blooms_level == "apply":
            return "Present a scenario or problem that requires applying learned concepts. Stem should describe a situation where students must use their knowledge."
        elif blooms_level == "analyze":
            return "Present complex scenarios requiring analysis of multiple variables. Stem should require students to examine, compare, or evaluate information."
    
    elif question_type == "tf":
        if blooms_level == "remember":
            return "State facts, definitions, or basic concepts clearly. Focus on information directly covered in the material."
        elif blooms_level == "apply":
            return "Present statements about applying concepts to situations. Focus on whether procedures or principles are correctly applied."
        elif blooms_level == "analyze":
            return "Present statements requiring analysis of complex relationships. Focus on evaluations, comparisons, or synthesis of information."
    
    elif question_type == "fib":
        if blooms_level == "remember":
            return "Remove key terms, definitions, or factual information. Focus on vocabulary, names, dates, and basic concepts."
        elif blooms_level == "apply":
            return "Remove answers that require applying formulas or procedures. Focus on results of calculations or applications."
        elif blooms_level == "analyze":
            return "Remove conclusions, evaluations, or synthesis results. Focus on analytical outcomes or judgments."
    
    return "appropriate cognitive level thinking"
