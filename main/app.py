"""
Refactored Question Generation API using class-based modular architecture.

This FastAPI application provides endpoints for generating different types of questions
using GraphRAG with a clean, object-oriented design pattern.
"""
import sys
import os
import uuid
import json
import datetime
import boto3
import asyncio
import concurrent.futures
from typing import Optional, Dict, List, Union
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from enum import Enum

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import settings to configure environment variables first
from src import settings
from src.generators import QuestionGeneratorFactory
from src.utils.constants import metadata_keys, content_tenant_mapping
from src.utils.summary_helper import generate_content_summary_sync

# Initialize DynamoDB client
dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.environ.get('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
)

# Get the DynamoDB tables
table_names = {
    'history': 'question_generation_history',
    'conversation': 'conversation',
    'events': 'events'
}

tables = {}
try:
    for key, table_name in table_names.items():
        tables[key] = dynamodb.Table(table_name)
        # Test if table exists by performing a small operation
        tables[key].scan(Limit=1)
        print(f"Successfully connected to DynamoDB table: {table_name}")
except Exception as e:
    print(f"Warning: DynamoDB table access error - {str(e)}")
    print("Will log to console instead of DynamoDB")
    tables = {key: None for key in table_names.keys()}

app = FastAPI(
    title="Question Generation API - Refactored",
    description="Refactored API for generating different types of questions using GraphRAG with class-based modular architecture",
    version="3.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionType(str, Enum):
    mcq = "mcq"
    tf = "tf"
    fib = "fib"

class BloomsTaxonomy(str, Enum):
    remember = "remember"
    apply = "apply"
    analyze = "analyze"

class DifficultyLevel(str, Enum):
    basic = "basic"
    intermediate = "intermediate"
    advanced = "advanced"

class QuestionRequest(BaseModel):
    contentId: str = "9781305101920_p10_lores.pdf"
    chapter_id: str = "01_01920_ch01_ptg01_hires_001-026"
    learning_objectives: Optional[Union[str, List[str]]] = None
    total_questions: int = 10
    question_type_distribution: Dict[str, float] = {"mcq": 0.4, "fib": 0.3, "tf": 0.3}
    difficulty_distribution: Dict[str, float] = {"basic": 0.3, "intermediate": 0.3, "advanced": 0.4}
    blooms_taxonomy_distribution: Dict[str, float] = {"remember": 0.3, "apply": 0.4, "analyze": 0.3}
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique session identifier")

class QuestionResponse(BaseModel):
    status: str
    message: str
    session_id: str             
    contentId: str                   
    chapter_id: str                    
    learning_objectives: Optional[Union[str, List[str]]]
    total_questions: int              
    question_type_distribution: Dict[str, float]  
    difficulty_distribution: Dict[str, float]     
    blooms_taxonomy_distribution: Dict[str, float]  
    files_generated: list
    data: dict

class QuestionGenerationService:
    """
    Service class that orchestrates question generation using the generator classes.
    """
    
    def __init__(self):
        self.available_keys = list(set(metadata_keys.keys()))
    
    def calculate_question_distribution(self, total_questions: int, question_type_dist: Dict[str, float], 
                                      difficulty_dist: Dict[str, float], blooms_dist: Dict[str, float]):
        """Calculate the exact number of questions for each combination of question type, difficulty, and bloom's level"""
        # First, calculate exact fractional counts for all combinations
        fractional_distribution = {}
        
        for q_type, q_ratio in question_type_dist.items():
            for difficulty, d_ratio in difficulty_dist.items():
                for blooms, b_ratio in blooms_dist.items():
                    exact_count = total_questions * q_ratio * d_ratio * b_ratio
                    key = f"{q_type}_{difficulty}_{blooms}"
                    fractional_distribution[key] = {
                        'question_type': q_type,
                        'difficulty': difficulty,
                        'blooms_level': blooms,
                        'exact_count': exact_count,
                        'count': int(exact_count)  # Floor value
                    }
        
        # Calculate remainder needed to reach total_questions
        current_total = sum([item['count'] for item in fractional_distribution.values()])
        remainder = total_questions - current_total
        
        # Sort by fractional part (descending) to allocate remainder
        sorted_keys = sorted(
            fractional_distribution.keys(),
            key=lambda k: fractional_distribution[k]['exact_count'] - fractional_distribution[k]['count'],
            reverse=True
        )
        
        # Distribute remainder to items with highest fractional parts
        for i in range(remainder):
            if i < len(sorted_keys):
                fractional_distribution[sorted_keys[i]]['count'] += 1
        
        # Remove items with zero count and clean up the structure
        distribution = {}
        for key, item in fractional_distribution.items():
            if item['count'] > 0:
                distribution[key] = {
                    'question_type': item['question_type'],
                    'difficulty': item['difficulty'],
                    'blooms_level': item['blooms_level'],
                    'count': item['count']
                }
        
        return distribution
    
    async def generate_single_question_type_async(self, question_type: str, configs: list, content_summary: str, 
                                                 tenant_id: str, chapter_id: str, learning_objectives: Optional[Union[str, List[str]]],
                                                 difficulty_distribution: Dict[str, float], 
                                                 blooms_distribution: Dict[str, float]) -> tuple:
        """Async wrapper for generating a single question type using the generator classes."""
        
        def generate_sync():
            try:
                # Aggregate counts for this question type
                total_for_type = sum([config['count'] for config in configs])
                
                print(f"[THREAD] Generating {question_type} questions (count: {total_for_type})...")
                
                # Create the appropriate generator using the factory
                generator = QuestionGeneratorFactory.create_generator(question_type, tenant_id)
                
                # Generate questions using the generator
                response_text = generator.generate(
                    chapter_id=chapter_id,
                    learning_objectives=learning_objectives,
                    num_questions=total_for_type,
                    difficulty_distribution=difficulty_distribution,
                    blooms_taxonomy_distribution=blooms_distribution,
                    content_summary=content_summary
                )
                
                # Generate filename exactly as the generator does
                difficulty_str = "_".join([f"{diff}{int(prop*100)}" for diff, prop in difficulty_distribution.items()])
                blooms_str = "_".join([f"{bloom}{int(prop*100)}" for bloom, prop in blooms_distribution.items()])
                
                filename_parts = [chapter_id, difficulty_str, blooms_str]
                if learning_objectives and self.available_keys and 'learning_objectives' in self.available_keys:
                    obj_str = "lo" + ("_".join([str(obj) for obj in learning_objectives]) if isinstance(learning_objectives, list) else str(learning_objectives))
                    filename_parts.append(obj_str)
                
                file_name = "_".join(filename_parts) + f"_{question_type}.json"
                
                # Read the generated JSON file
                with open(file_name, 'r') as json_file:
                    question_data = json.load(json_file)
                
                print(f"[THREAD] Completed generating {question_type} questions")
                return question_type, file_name, question_data, None
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"[THREAD] Error generating {question_type} questions: {str(e)}")
                print(f"[THREAD] Full error details: {error_details}")
                return question_type, None, None, str(e)
        
        # Run the sync function in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, generate_sync)

# Initialize the service
question_service = QuestionGenerationService()

def generate_session_id():
    """Generate a unique session ID"""
    return str(uuid.uuid4())

@app.get("/")
def read_root():
    return {"message": "Question Generation API v3.0 - Refactored with Class-Based Architecture. Use /questionBankService/source/{sourceId}/questions/generate endpoint to create questions."}

@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "version": "3.0.0 - Refactored", 
        "architecture": "class-based modular design",
        "supported_question_types": QuestionGeneratorFactory.get_supported_types()
    }

@app.post("/questionBankService/source/{sourceId}/questions/generate", response_model=QuestionResponse)
async def generate_questions(sourceId: str, request: QuestionRequest, req: Request):
    """
    Generate questions based on the specified parameters using the refactored class-based architecture.
    
    Key Features:
    1. Class-based modular design with inheritance
    2. Factory pattern for generator creation
    3. Service layer for orchestration
    4. Maintained parallel processing capabilities
    5. All original functionality preserved
    """
    # Generate timestamp for the request
    request_timestamp = datetime.datetime.utcnow().isoformat()
    status = "success"
    error_message = ""
    all_question_data = {}
    files_generated = []
    
    # Handle session_id - use from request if provided, otherwise generate a new one
    session_id = request.session_id if request.session_id else generate_session_id()
    tenant_id = content_tenant_mapping.get(request.contentId)
    
    print(f"Processing REFACTORED request for sourceId: {sourceId}")
    print(f"Request parameters: {request.dict()}")
    
    try:
        # Generate shared summary ONCE
        print("🚀 OPTIMIZATION: Generating shared content summary once...")
        start_time = datetime.datetime.utcnow()
        
        content_summary = generate_content_summary_sync(
            tenant_id=tenant_id,
            chapter_id=request.chapter_id,
            learning_objectives=request.learning_objectives,
            all_keys=question_service.available_keys
        )   
        
        summary_time = (datetime.datetime.utcnow() - start_time).total_seconds()
        print(f"✅ Shared summary generated in {summary_time:.2f} seconds (length: {len(content_summary)} characters)")
        
        # Calculate question distribution
        question_dist = question_service.calculate_question_distribution(
            request.total_questions,
            request.question_type_distribution,
            request.difficulty_distribution,
            request.blooms_taxonomy_distribution
        )
        
        print(f"Question distribution: {question_dist}")
        
        # Group by question type for generation
        type_groups = {}
        for key, config in question_dist.items():
            q_type = config['question_type']
            if q_type not in type_groups:
                type_groups[q_type] = []
            type_groups[q_type].append(config)
        
        # Run question generators in TRUE PARALLEL using the service
        print("🚀 OPTIMIZATION: Running question generators in TRUE PARALLEL using class-based architecture...")
        parallel_start_time = datetime.datetime.utcnow()
        
        # Create futures for each question type using the service
        futures = []
        
        for question_type, configs in type_groups.items():
            # Create combined distributions for this question type
            total_for_type = sum([config['count'] for config in configs])
            difficulty_dist_for_type = {}
            blooms_dist_for_type = {}
            
            for config in configs:
                diff = config['difficulty']
                blooms = config['blooms_level']
                count = config['count']
                
                if diff not in difficulty_dist_for_type:
                    difficulty_dist_for_type[diff] = 0
                if blooms not in blooms_dist_for_type:
                    blooms_dist_for_type[blooms] = 0
                    
                difficulty_dist_for_type[diff] += count / total_for_type
                blooms_dist_for_type[blooms] += count / total_for_type
            
            # Submit task using the service method
            future = question_service.generate_single_question_type_async(
                question_type,
                configs,
                content_summary,  # Pass shared summary
                tenant_id,
                request.chapter_id,
                request.learning_objectives,
                difficulty_dist_for_type,
                blooms_dist_for_type
            )
            futures.append(future)
        
        # Wait for all futures to complete
        print(f"⚡ Running {len(futures)} question generators in parallel using class-based architecture...")
        results = await asyncio.gather(*futures, return_exceptions=True)
        
        parallel_time = (datetime.datetime.utcnow() - parallel_start_time).total_seconds()
        print(f"✅ Class-based parallel question generation completed in {parallel_time:.2f} seconds")
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                raise result
            
            question_type, file_name, question_data, error = result
            
            if error:
                raise Exception(f"Error in {question_type}: {error}")
            
            files_generated.append(file_name)
            all_question_data[question_type] = question_data
        
        total_time = (datetime.datetime.utcnow() - start_time).total_seconds()
        
        learning_obj_str = f" with learning objectives: {request.learning_objectives}" if request.learning_objectives else ""
        
        response = QuestionResponse(
            status=status,
            message=f"✅ [REFACTORED] Generated {request.total_questions} questions across {len(type_groups)} question types for sourceId: {sourceId}, chapter: {request.chapter_id}{learning_obj_str} in {total_time:.2f} seconds (Summary: {summary_time:.2f}s, Class-based Parallel Generation: {parallel_time:.2f}s)",
            session_id=session_id,
            files_generated=files_generated,
            contentId=request.contentId,
            chapter_id=request.chapter_id,
            learning_objectives=request.learning_objectives,
            total_questions=request.total_questions,
            question_type_distribution=request.question_type_distribution,
            difficulty_distribution=request.difficulty_distribution,
            blooms_taxonomy_distribution=request.blooms_taxonomy_distribution,
            data=all_question_data
        )
        
    except Exception as e:
        import traceback
        error_message = str(e)
        error_details = traceback.format_exc()
        print(f"Full error details: {error_details}")
        status = "error"
        response = QuestionResponse(
            status=status,
            message=f"❌ Error generating questions for sourceId {sourceId}: {error_message}",
            session_id=session_id,
            contentId=request.contentId,
            chapter_id=request.chapter_id,
            learning_objectives=request.learning_objectives,
            total_questions=request.total_questions,
            question_type_distribution=request.question_type_distribution,
            difficulty_distribution=request.difficulty_distribution,
            blooms_taxonomy_distribution=request.blooms_taxonomy_distribution,
            files_generated=[],
            data={}
        )
        raise HTTPException(status_code=500, detail=f"Error generating questions: {error_message}")
    
    return response

# Run the FastAPI app with uvicorn if executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
