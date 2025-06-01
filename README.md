# Question Generation API - Refactored

A refactored question generation API built with FastAPI and GraphRAG, featuring a **modular class-based architecture** for generating different types of educational questions.

## 🚀 Key Improvements

This refactored version transforms the original procedural code into a clean, object-oriented design:

### ✨ **Class-Based Architecture**
- **BaseQuestionGenerator**: Abstract base class with shared functionality
- **MCQGenerator**: Multiple choice questions implementation
- **FillInBlankGenerator**: Fill-in-the-blank questions implementation  
- **TrueFalseGenerator**: True/false questions implementation
- **QuestionGeneratorFactory**: Factory pattern for generator creation
- **QuestionGenerationService**: Service layer for orchestration

### 🎯 **Benefits of Refactoring**
- **Modularity**: Each question type has its own class with specialized logic
- **Inheritance**: Shared functionality in base class eliminates code duplication
- **Factory Pattern**: Clean creation and management of generator instances
- **Service Layer**: Clear separation of concerns between API and business logic
- **Maintainability**: Easy to add new question types or modify existing ones
- **Testability**: Individual components can be unit tested in isolation

## 📁 Project Structure

```
question-generation-refactored/
├── main/
│   └── app.py                          # Refactored FastAPI application
├── src/
│   ├── generators/                     # Question generator classes
│   │   ├── __init__.py                # Module exports
│   │   ├── base_generator.py          # Abstract base class
│   │   ├── mcq_generator.py           # MCQ implementation
│   │   ├── fib_generator.py           # Fill-in-blank implementation
│   │   ├── tf_generator.py            # True/false implementation
│   │   └── factory.py                 # Generator factory
│   ├── utils/                         # Utility functions
│   └── services/                      # Business logic services
└── README.md
```

## 🔧 How to Use the Refactored API

### Basic Usage with Factory Pattern

```python
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

# Create multiple generators at once
generators = QuestionGeneratorFactory.create_multiple_generators(['mcq', 'fib', 'tf'])
```

### Advanced Usage with Custom Configuration

```python
from src.generators import MCQGenerator, FillInBlankGenerator

# Direct instantiation for advanced configuration
mcq_gen = MCQGenerator(tenant_id='1305101920')
fib_gen = FillInBlankGenerator(tenant_id='1305101920')

# Generate with learning objectives
mcq_questions = mcq_gen.generate(
    chapter_id='01_01920_ch01_ptg01_hires_001-026',
    learning_objectives=['LO_1.1', 'LO_1.2'],
    num_questions=15,
    difficulty_distribution={'basic': 0.2, 'intermediate': 0.4, 'advanced': 0.4},
    blooms_taxonomy_distribution={'remember': 0.25, 'apply': 0.5, 'analyze': 0.25}
)
```

## 🌐 API Endpoints

### Generate Questions
```
POST /questionBankService/source/{sourceId}/questions/generate
```

**Request Body:**
```json
{
    "contentId": "9781305101920_p10_lores.pdf",
    "chapter_id": "01_01920_ch01_ptg01_hires_001-026",
    "learning_objectives": ["LO_1.1", "LO_1.2"],
    "total_questions": 40,
    "question_type_distribution": {"mcq": 0.4, "fib": 0.3, "tf": 0.3},
    "difficulty_distribution": {"basic": 0.3, "intermediate": 0.3, "advanced": 0.4},
    "blooms_taxonomy_distribution": {"remember": 0.3, "apply": 0.4, "analyze": 0.3}
}
```

### Health Check
```
GET /health
```

Returns information about the refactored architecture and supported question types.

## 🏗️ Architecture Overview

### Class Hierarchy

```
BaseQuestionGenerator (Abstract)
├── MCQGenerator
├── FillInBlankGenerator
└── TrueFalseGenerator
```

### Key Components

1. **BaseQuestionGenerator**: 
   - Abstract base class containing shared functionality
   - GraphRAG integration, filtering, question breakdown calculation
   - Template methods for generation workflow

2. **Specific Generators**:
   - Each implements abstract methods for their question type
   - Custom parsing logic for response formats
   - Specialized prompt building for question type

3. **QuestionGeneratorFactory**:
   - Factory pattern for creating appropriate generators
   - Type safety and validation
   - Support for batch generator creation

4. **QuestionGenerationService**:
   - Service layer orchestrating the generation process
   - Handles parallel processing coordination
   - Manages question distribution calculations

## 🚀 Running the Application

### Development Mode
```bash
cd main
python app.py
```

### Production Mode
```bash
uvicorn main.app:app --host 0.0.0.0 --port 8000
```

### Docker
```bash
docker build -t question-generation-refactored .
docker run -p 8000:8000 question-generation-refactored
```

## 🔍 Key Refactoring Changes

### Before (Procedural)
```python
# utils_mcq.py
def generate_mcqs(tenant_id, chapter_id, ...):
    # MCQ-specific logic mixed with common functionality
    pass

# utils_fib.py  
def generate_fill_in_blank(tenant_id, chapter_id, ...):
    # FIB-specific logic mixed with common functionality
    pass

# app.py
from src.utils.utils_mcq import generate_mcqs
from src.utils.utils_fib import generate_fill_in_blank
# Direct function calls with lots of duplicated code
```

### After (Class-Based)
```python
# generators/base_generator.py
class BaseQuestionGenerator(ABC):
    def __init__(self, tenant_id):
        # Shared initialization
    
    def generate(self, ...):
        # Template method with common workflow
    
    @abstractmethod
    def _parse_response(self, ...):
        # Abstract method for subclasses

# generators/mcq_generator.py
class MCQGenerator(BaseQuestionGenerator):
    def _parse_response(self, ...):
        # MCQ-specific parsing logic

# app.py
from src.generators import QuestionGeneratorFactory
generator = QuestionGeneratorFactory.create_generator('mcq')
# Clean, object-oriented approach
```

## 🎯 Benefits Achieved

1. **Code Reusability**: Common functionality shared through inheritance
2. **Separation of Concerns**: Each class has a single responsibility
3. **Extensibility**: Easy to add new question types by extending BaseQuestionGenerator
4. **Maintainability**: Changes to shared logic only need to be made in one place
5. **Type Safety**: Factory pattern ensures proper generator creation
6. **Testing**: Individual components can be unit tested independently

## 📈 Performance

The refactored version maintains all original performance optimizations:
- ✅ Shared content summary generation
- ✅ True parallel processing with ThreadPoolExecutor
- ✅ Async/await support for concurrent operations
- ✅ Optimized question distribution calculations

## 🔧 Environment Variables

```bash
AWS_REGION=us-east-1
AWS_PROFILE=cengage
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

## 📝 Response Format

The API returns comprehensive response data including:
- Generation status and timing information
- Session tracking and metadata
- Generated question files and data
- Performance metrics for each phase

---

**Repository**: [question-generation-refactored](https://github.com/ismanish/question-generation-refactored)

This refactored version demonstrates modern Python development practices with clean architecture, making the codebase more maintainable, testable, and extensible while preserving all original functionality and performance characteristics.
