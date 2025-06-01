"""
Multiple Choice Question (MCQ) generator implementation.
"""
import uuid
from typing import Dict, List
from .base_generator import BaseQuestionGenerator
from src.utils.helpers import get_difficulty_description, get_blooms_question_guidelines


class MCQGenerator(BaseQuestionGenerator):
    """
    Generator for Multiple Choice Questions (MCQ).
    Inherits shared functionality from BaseQuestionGenerator.
    """
    
    def get_question_type(self) -> str:
        """
        Get the question type identifier for MCQ.
        
        Returns:
            Question type string 'mcq'
        """
        return "mcq"
    
    def _parse_response(self, response_text: str, question_breakdown: Dict[str, Dict]) -> List[Dict]:
        """
        Parse MCQ response text into structured question data.
        
        Args:
            response_text: Raw response text from the LLM
            question_breakdown: Question breakdown specifications
            
        Returns:
            List of parsed MCQ dictionaries
        """
        question_blocks = response_text.split("QUESTION:")
        responses = []
        
        # Create sequence of difficulty/blooms assignments
        question_sequence = self._create_question_sequence(question_breakdown)
        question_index = 0
        
        for block in [b.strip() for b in question_blocks if b.strip()]:
            question_obj = {
                "question_id": str(uuid.uuid4()),
                "question": "",
                "answer": "",
                "explanation": "",
                "distractors": [],
                "difficulty": "",
                "blooms_level": "",
                "question_type": "mcq"
            }
            
            # Extract question content
            if "ANSWER:" in block:
                question_obj["question"] = block.split("ANSWER:")[0].strip()
                block = "ANSWER:" + block.split("ANSWER:")[1]
            
            # Extract answer
            if "ANSWER:" in block and "EXPLANATION:" in block:
                question_obj["answer"] = block.split("ANSWER:")[1].split("EXPLANATION:")[0].strip()
                block = "EXPLANATION:" + block.split("EXPLANATION:")[1]
            
            # Extract explanation
            if "EXPLANATION:" in block:
                explanation_text = block.split("EXPLANATION:")[1]
                if "DISTRACTOR1:" in explanation_text:
                    question_obj["explanation"] = explanation_text.split("DISTRACTOR1:")[0].strip()
                else:
                    question_obj["explanation"] = explanation_text.strip()
            
            # Extract distractors
            distractor_keys = ["DISTRACTOR1:", "DISTRACTOR2:", "DISTRACTOR3:"]
            for i, key in enumerate(distractor_keys):
                if key in block:
                    next_key = distractor_keys[i+1] if i+1 < len(distractor_keys) else None
                    if next_key and next_key in block:
                        distractor = block.split(key)[1].split(next_key)[0].strip()
                    else:
                        distractor = block.split(key)[1].strip()
                    question_obj["distractors"].append(distractor)
            
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
        Build the prompt for MCQ generation.
        
        Args:
            content_summary: Content summary for the chapter
            num_questions: Number of questions to generate
            question_breakdown: Question breakdown specifications
            
        Returns:
            MCQ generation prompt string
        """
        # Generate all questions in a single prompt with specific guidelines
        all_guidelines = []
        
        for combo_key, specs in question_breakdown.items():
            difficulty = specs['difficulty']
            blooms_level = specs['blooms_level']
            count = specs['count']
            
            guidelines = get_blooms_question_guidelines(blooms_level, "mcq")
            difficulty_desc = get_difficulty_description(difficulty)
            
            all_guidelines.append(f"""
For {count} questions at {difficulty.upper()} difficulty and {blooms_level.upper()} Bloom's level:
- Difficulty: {difficulty_desc}
- Bloom's Level Guidelines: {guidelines}
            """)
        
        # Build MCQ generation prompt
        prompt = f"""
        You are a professor writing sophisticated multiple-choice questions for an upper-level university course. The questions will be based on this chapter summary:

        {content_summary}

        Create exactly {num_questions} multiple-choice questions following these specific guidelines:

        {' '.join(all_guidelines)}

        IMPORTANT FORMATTING INSTRUCTIONS:
        - Start IMMEDIATELY with your first question using "QUESTION:" 
        - DO NOT write ANY introductory text like "Based on the chapter..." or "I'll create..."
        - DO NOT include ANY preamble or explanation before the first question

        Each question should:
        1. Match the specified difficulty and Bloom's taxonomy level
        2. Present scenarios appropriate to the cognitive level required
        3. Use domain-specific terminology accurately
        4. Include strong distractors that reflect common misconceptions

        Format each question exactly as follows:
        QUESTION: [Question text appropriate to difficulty and Bloom's level]
        ANSWER: [Correct answer]
        EXPLANATION: [Explanation of correct answer and why it demonstrates the required cognitive level]
        DISTRACTOR1: [First incorrect option]
        DISTRACTOR2: [Second incorrect option]
        DISTRACTOR3: [Third incorrect option]

        Distribution of questions:
        {question_breakdown}
        
        Make sure to vary the cognitive demands according to the Bloom's taxonomy levels specified.
        """
        
        return prompt
