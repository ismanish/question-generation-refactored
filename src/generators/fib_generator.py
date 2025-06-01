"""
Fill-in-the-blank question generator implementation.
"""
import uuid
from typing import Dict, List
from .base_generator import BaseQuestionGenerator
from src.utils.helpers import get_difficulty_description, get_blooms_question_guidelines


class FillInBlankGenerator(BaseQuestionGenerator):
    """
    Generator for Fill-in-the-blank Questions.
    Inherits shared functionality from BaseQuestionGenerator.
    """
    
    def get_question_type(self) -> str:
        """
        Get the question type identifier for fill-in-the-blank.
        
        Returns:
            Question type string 'fib'
        """
        return "fib"
    
    def _parse_response(self, response_text: str, question_breakdown: Dict[str, Dict]) -> List[Dict]:
        """
        Parse fill-in-the-blank response text into structured question data.
        
        Args:
            response_text: Raw response text from the LLM
            question_breakdown: Question breakdown specifications
            
        Returns:
            List of parsed fill-in-the-blank dictionaries
        """
        responses = []
        question_blocks = response_text.split("QUESTION:")
        
        # Create sequence of difficulty/blooms assignments
        question_sequence = self._create_question_sequence(question_breakdown)
        question_index = 0
        
        for block in [b.strip() for b in question_blocks if b.strip()]:
            question_obj = {
                "question_id": str(uuid.uuid4()),
                "question": "",
                "answer": [],
                "explanation": "",
                "difficulty": "",
                "blooms_level": "",
                "question_type": "fib"
            }
            
            # Extract components using simple string search
            if "ANSWER:" in block:
                question_obj["question"] = block.split("ANSWER:")[0].strip()
                block = "ANSWER:" + block.split("ANSWER:")[1]
            
            if "ANSWER:" in block and "EXPLANATION:" in block:
                answer_text = block.split("ANSWER:")[1].split("EXPLANATION:")[0].strip()
                answer_lines = answer_text.split('\n')
                for line in answer_lines:
                    line = line.strip()
                    # Check if line starts with a number followed by a period (e.g., "1. ")
                    if line and (line[0].isdigit() and '. ' in line):
                        # Remove the numbering and add to the list
                        answer_item = line.split('. ', 1)[1].strip()
                        question_obj["answer"].append(answer_item)
                    elif line:  # If there's text but not in numbered format
                        question_obj["answer"].append(line)
            
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
        Build the prompt for fill-in-the-blank generation.
        
        Args:
            content_summary: Content summary for the chapter
            num_questions: Number of questions to generate
            question_breakdown: Question breakdown specifications
            
        Returns:
            Fill-in-the-blank generation prompt string
        """
        # Generate all questions in a single prompt with specific guidelines
        all_guidelines = []
        
        for combo_key, specs in question_breakdown.items():
            difficulty = specs['difficulty']
            blooms_level = specs['blooms_level']
            count = specs['count']
            
            guidelines = get_blooms_question_guidelines(blooms_level, "fib")
            difficulty_desc = get_difficulty_description(difficulty)
            
            all_guidelines.append(f"""
For {count} questions at {difficulty.upper()} difficulty and {blooms_level.upper()} Bloom's level:
- Difficulty: {difficulty_desc}
- Bloom's Level Guidelines: {guidelines}
            """)
        
        # Generate fill-in-the-blank questions based on summary
        prompt = f"""
        You are a professor writing sophisticated fill-in-the-blank questions for an upper-level university course. The questions will be based on this chapter summary:

        {content_summary}

        Create exactly {num_questions} fill-in-the-blank questions following these specific guidelines:

        {' '.join(all_guidelines)}

        IMPORTANT FORMATTING INSTRUCTIONS:
        - Start IMMEDIATELY with your first question using "QUESTION:" 
        - DO NOT write ANY introductory text like "Based on the chapter..." or "I'll create..."
        - DO NOT include ANY preamble or explanation before the first question
        - Each blank should be indicated by "________" (8 underscores)
        - A question may have multiple blanks if appropriate

        Each question should:
        1. Match the specified difficulty and Bloom's taxonomy level
        2. Present statements appropriate to the cognitive level required
        3. Use domain-specific terminology accurately
        4. Focus on important concepts from the chapter

        Format each question exactly as follows:
        QUESTION: [Statement with ________ for blanks, appropriate to difficulty and Bloom's level]
        ANSWER: [Correct answer(s) that should fill the blank(s), if multiple blanks, list each answer separately]
        EXPLANATION: [Explanation of why this is the correct answer and how it demonstrates the required cognitive level]

        Distribution of questions:
        {question_breakdown}
        
        Make sure to vary the cognitive demands according to the Bloom's taxonomy levels specified.
        """
        
        return prompt
