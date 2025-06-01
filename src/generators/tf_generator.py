"""
True/False question generator implementation.
"""
import uuid
from typing import Dict, List
from .base_generator import BaseQuestionGenerator
from src.utils.helpers import get_difficulty_description, get_blooms_question_guidelines


class TrueFalseGenerator(BaseQuestionGenerator):
    """
    Generator for True/False Questions.
    Inherits shared functionality from BaseQuestionGenerator.
    """
    
    def get_question_type(self) -> str:
        """
        Get the question type identifier for true/false.
        
        Returns:
            Question type string 'tf'
        """
        return "tf"
    
    def _parse_response(self, response_text: str, question_breakdown: Dict[str, Dict]) -> List[Dict]:
        """
        Parse true/false response text into structured question data.
        
        Args:
            response_text: Raw response text from the LLM
            question_breakdown: Question breakdown specifications
            
        Returns:
            List of parsed true/false dictionaries
        """
        responses = []
        # Split by STATEMENT: to separate each question
        statement_blocks = response_text.split("STATEMENT:")
        
        # Create sequence of difficulty/blooms assignments
        question_sequence = self._create_question_sequence(question_breakdown)
        question_index = 0
        
        for block in [b.strip() for b in statement_blocks if b.strip()]:
            question_obj = {
                "question_id": str(uuid.uuid4()),
                "statement": "",
                "answer": "",
                "explanation": "",
                "difficulty": "",
                "blooms_level": "",
                "question_type": "tf"
            }
            
            # Extract statement
            if "ANSWER:" in block:
                question_obj["statement"] = block.split("ANSWER:")[0].strip()
                block = "ANSWER:" + block.split("ANSWER:")[1]
            
            # Extract answer (TRUE or FALSE)
            if "ANSWER:" in block and "EXPLANATION:" in block:
                question_obj["answer"] = block.split("ANSWER:")[1].split("EXPLANATION:")[0].strip()
            elif "ANSWER:" in block:
                question_obj["answer"] = block.split("ANSWER:")[1].strip()
            
            # Extract explanation
            if "EXPLANATION:" in block:
                explanation_text = block.split("EXPLANATION:")[1]
                question_obj["explanation"] = explanation_text.strip()
            
            # Programmatically assign difficulty and blooms_level
            if question_index < len(question_sequence):
                difficulty, blooms_level = question_sequence[question_index]
                question_obj["difficulty"] = difficulty
                question_obj["blooms_level"] = blooms_level
                question_index += 1
            
            responses.append(question_obj)

        return responses
    
    def _build_generation_prompt(self, content_summary: str, num_questions: int, 
                                question_breakdown: Dict[str, Dict]) -> str:
        """
        Build the prompt for true/false generation.
        
        Args:
            content_summary: Content summary for the chapter
            num_questions: Number of questions to generate
            question_breakdown: Question breakdown specifications
            
        Returns:
            True/false generation prompt string
        """
        # Generate all questions in a single prompt with specific guidelines
        all_guidelines = []
        
        for combo_key, specs in question_breakdown.items():
            difficulty = specs['difficulty']
            blooms_level = specs['blooms_level']
            count = specs['count']
            
            guidelines = get_blooms_question_guidelines(blooms_level, "tf")
            difficulty_desc = get_difficulty_description(difficulty)
            
            all_guidelines.append(f"""
For {count} questions at {difficulty.upper()} difficulty and {blooms_level.upper()} Bloom's level:
- Difficulty: {difficulty_desc}
- Bloom's Level Guidelines: {guidelines}
            """)
        
        # Generate true/false questions based on summary
        prompt = f"""
        You are a professor writing sophisticated true/false questions for an upper-level university course. The questions will be based on this chapter summary:

        {content_summary}

        Create exactly {num_questions} true/false questions following these specific guidelines:

        {' '.join(all_guidelines)}

        IMPORTANT FORMATTING INSTRUCTIONS:
        - Start IMMEDIATELY with your first question using "STATEMENT:" 
        - DO NOT write ANY introductory text like "Based on the chapter..." or "I'll create..."
        - DO NOT include ANY preamble or explanation before the first statement

        Each question should:
        1. Match the specified difficulty and Bloom's taxonomy level
        2. Present clear statements appropriate to the cognitive level required
        3. Use domain-specific terminology accurately
        4. Avoid making statements true/false based on single words like "always", "never", or "all"
        5. Be balanced (aim for approximately 50% true and 50% false statements)
        6. For false statements, make them plausible but clearly incorrect based on the chapter

        Format each question exactly as follows:
        STATEMENT: [A clear statement that is either true or false, appropriate to difficulty and Bloom's level]
        ANSWER: [Either "TRUE" or "FALSE" in all caps]
        EXPLANATION: [Explanation of why the statement is true or false, with reference to chapter content and demonstration of required cognitive level]

        Distribution of questions:
        {question_breakdown}
        
        Make sure to vary the cognitive demands according to the Bloom's taxonomy levels specified.
        """
        
        return prompt
