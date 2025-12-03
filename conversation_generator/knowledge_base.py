"""
Knowledge Base Handler for CSR Agent.

This module provides functionality to load and query a knowledge base
that the CSR agent can use to answer customer questions.
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path


class KnowledgeBase:
    """
    Simple knowledge base for CSR agent.
    
    Stores knowledge items (FAQs, policies, product info) and provides
    methods to retrieve relevant information.
    """
    
    def __init__(self, knowledge_path: Optional[str] = None):
        """
        Initialize knowledge base.
        
        Args:
            knowledge_path: Path to knowledge base file or directory
        """
        self.knowledge_items: List[Dict[str, Any]] = []
        if knowledge_path:
            self.load_knowledge(knowledge_path)
    
    def load_knowledge(self, path: str) -> None:
        """
        Load knowledge from a JSON file.
        
        Args:
            path: Path to knowledge base JSON file
            
        Raises:
            FileNotFoundError: If the path doesn't exist
            ValueError: If the path is neither a file nor directory
        """
        path_obj = Path(path)
        
        if not path_obj.exists():
            raise FileNotFoundError(f"Knowledge base path does not exist: {path}")
        
        if path_obj.is_file() and path_obj.suffix == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.knowledge_items = data
                elif isinstance(data, dict) and 'items' in data:
                    self.knowledge_items = data['items']
        elif path_obj.is_dir():
            # Load all JSON files from directory
            for json_file in path_obj.glob('*.json'):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.knowledge_items.extend(data)
                    elif isinstance(data, dict) and 'items' in data:
                        self.knowledge_items.extend(data['items'])
        else:
            raise ValueError(f"Path must be a JSON file or directory: {path}")
    
    def add_item(self, category: str, question: str, answer: str, 
                 tags: Optional[List[str]] = None) -> None:
        """
        Add a knowledge item to the knowledge base.
        
        Args:
            category: Category of the knowledge item (e.g., "returns", "shipping")
            question: The question or topic
            answer: The answer or information
            tags: Optional tags for the item
        """
        self.knowledge_items.append({
            "category": category,
            "question": question,
            "answer": answer,
            "tags": tags or []
        })
    
    def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all knowledge items."""
        return self.knowledge_items
    
    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get knowledge items by category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of knowledge items in the category
        """
        return [item for item in self.knowledge_items 
                if item.get('category', '').lower() == category.lower()]
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Simple keyword-based search in knowledge base.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching knowledge items
        """
        query_lower = query.lower()
        results = []
        
        for item in self.knowledge_items:
            # Search in question and answer
            if (query_lower in item.get('question', '').lower() or
                query_lower in item.get('answer', '').lower() or
                any(query_lower in tag.lower() for tag in item.get('tags', []))):
                results.append(item)
        
        return results
    
    def to_prompt_context(self, max_items: int = 10) -> str:
        """
        Convert knowledge base to a context string for LLM prompt.
        
        Args:
            max_items: Maximum number of items to include
            
        Returns:
            Formatted string with knowledge base content
        """
        if not self.knowledge_items:
            return "No knowledge base available."
        
        items_to_include = self.knowledge_items[:max_items]
        context_parts = ["Knowledge Base:"]
        
        for i, item in enumerate(items_to_include, 1):
            category = item.get('category', 'General')
            question = item.get('question', '')
            answer = item.get('answer', '')
            context_parts.append(f"\n{i}. [{category}] {question}")
            context_parts.append(f"   Answer: {answer}")
        
        if len(self.knowledge_items) > max_items:
            context_parts.append(f"\n... and {len(self.knowledge_items) - max_items} more items")
        
        return "\n".join(context_parts)
    
    def save_to_file(self, path: str) -> None:
        """
        Save knowledge base to a JSON file.
        
        Args:
            path: Path to save the knowledge base
        """
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                "items": self.knowledge_items
            }, f, indent=2, ensure_ascii=False)
