"""
Shared summary generation helper for question generators.
This module centralizes the summary generation logic to avoid duplication.
"""
import os
import sys
# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import settings first to set environment variables
from src import settings
from src.settings import NeptuneEndpoint, VectorStoreEndpoint

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
from src.utils.constants import CENGAGE_GUIDELINES as cengage_guidelines


def generate_content_summary_sync(
    tenant_id: str, 
    chapter_id: str,
    learning_objectives=None,
    all_keys=None
) -> str:
    """
    Synchronous version of content summary generation with multiple filter support.
    Used when async is not available.
    
    Args:
        tenant_id: The tenant ID for the GraphRAG query engine
        chapter_id: The chapter identifier (e.g., '56330_ch10_ptg01') 
        learning_objectives: Optional. Single learning objective or list of learning objectives to filter on
        all_keys: List of all available metadata keys to check against before applying filters
        
    Returns:
        str: Content summary
    """
    chapter_key = 'toc_level_1_title'
    print(f"Generating shared content summary (sync) for chapter: {chapter_id}")
    if learning_objectives:
        print(f"Learning objectives filter: {learning_objectives}")
    
    # Build filters list
    filters = []
    
    # Primary filter for chapter (always present)
    chapter_filter = MetadataFilter(
        key=chapter_key,
        value=chapter_id,
        operator=FilterOperator.EQ
    )
    filters.append(chapter_filter)
    print(f"Added chapter filter: {chapter_key}={chapter_id}")
    
    # Add learning objectives filter if available
    if learning_objectives is not None and all_keys and 'learning_objectives' in all_keys:
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

    filter_to_use = filters
    
    # Initialize stores using the endpoint constants
    graph_store = GraphStoreFactory.for_graph_store(NeptuneEndpoint)
    vector_store = VectorStoreFactory.for_vector_store(VectorStoreEndpoint)
    
    filter_config = FilterConfig(source_filters=filter_to_use)
    
    # Initialize query engine with filter
    query_engine = LexicalGraphQueryEngine.for_traversal_based_search(
        graph_store,
        vector_store,
        filter_config=filter_config,
        tenant_id=tenant_id,
        llm_config={
            "model": "arn:aws:bedrock:us-east-1:051826717360:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            "temperature": 0,
            "max_tokens": 10000,
            "system_prompt": cengage_guidelines
        }
    )
    
    # Generate filter description
    filter_description = f"chapter {chapter_id}"
    if learning_objectives and all_keys and 'learning_objectives' in all_keys:
        filter_description += f" with learning objectives: {learning_objectives if isinstance(learning_objectives, list) else [learning_objectives]}"
    
    summary_query = f"Provide a comprehensive summary of content for {filter_description}. Include key concepts, topics, and important details."
    
    print("Retrieving content summary...")
    summary_response = query_engine.query(summary_query)
    content_summary = summary_response.response
    
    print(f"Summary generated - length: {len(content_summary)} characters")
    return content_summary
