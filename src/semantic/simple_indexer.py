#!/usr/bin/env python3
"""
Simple Semantic Indexer - Fallback without LlamaIndex
Uses basic text similarity and TF-IDF for semantic analysis
"""

import os
import json
import pickle
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from dataclasses import dataclass
from collections import Counter
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Local imports
from ..integrations.composio_manager import GitHubData, JiraData

logger = logging.getLogger(__name__)

@dataclass
class SimpleDocument:
    """Simple document structure for fallback indexer"""
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    source: str  # 'github' or 'jira'
    doc_type: str  # 'pr', 'commit', 'issue', 'ticket', 'comment'
    author: str
    created_at: str
    tfidf_vector: Optional[np.ndarray] = None

class SimpleSemanticIndexer:
    """Fallback semantic indexer using scikit-learn TF-IDF"""
    
    def __init__(self, config):
        self.config = config
        self.documents: List[SimpleDocument] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix: Optional[np.ndarray] = None
        
        # Storage paths
        self.documents_file = os.path.join(self.config.data_dir, 'simple_documents.pkl')
        self.vectorizer_file = os.path.join(self.config.data_dir, 'tfidf_vectorizer.pkl')
        
    async def initialize(self):
        """Initialize the simple semantic indexer"""
        try:
            # Initialize TF-IDF vectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 2),
                max_df=0.95,
                min_df=2
            )
            
            # Load existing documents if available
            self._load_existing_documents()
            
            logger.info("Simple semantic indexer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize simple semantic indexer: {e}")
            raise
    
    def _load_existing_documents(self):
        """Load previously indexed documents"""
        try:
            if os.path.exists(self.documents_file):
                with open(self.documents_file, 'rb') as f:
                    self.documents = pickle.load(f)
                logger.info(f"Loaded {len(self.documents)} existing documents")
                
                # Rebuild TF-IDF matrix if we have documents
                if self.documents:
                    self._rebuild_tfidf_matrix()
                    
        except Exception as e:
            logger.error(f"Failed to load existing documents: {e}")
            self.documents = []
    
    def _save_documents(self):
        """Save indexed documents to disk"""
        try:
            with open(self.documents_file, 'wb') as f:
                pickle.dump(self.documents, f)
        except Exception as e:
            logger.error(f"Failed to save documents: {e}")
    
    def _rebuild_tfidf_matrix(self):
        """Rebuild TF-IDF matrix from existing documents"""
        try:
            if not self.documents:
                return
                
            texts = [doc.content for doc in self.documents]
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # Update document vectors
            for i, doc in enumerate(self.documents):
                doc.tfidf_vector = self.tfidf_matrix[i].toarray()[0]
                
            logger.info(f"Rebuilt TF-IDF matrix for {len(self.documents)} documents")
            
        except Exception as e:
            logger.error(f"Failed to rebuild TF-IDF matrix: {e}")
    
    async def index_data(self, github_data: GitHubData, jira_data: JiraData):
        """Index GitHub and Jira data for semantic search"""
        logger.info("Starting simple semantic indexing of data")
        
        new_documents = []
        
        # Process GitHub data
        new_documents.extend(self._process_github_data(github_data))
        
        # Process Jira data
        new_documents.extend(self._process_jira_data(jira_data))
        
        # Add new documents to collection
        if new_documents:
            self.documents.extend(new_documents)
            
            # Rebuild TF-IDF matrix with all documents
            if self.documents:
                texts = [doc.content for doc in self.documents]
                self.tfidf_matrix = self.vectorizer.fit_transform(texts)
                
                # Update all document vectors
                for i, doc in enumerate(self.documents):
                    doc.tfidf_vector = self.tfidf_matrix[i].toarray()[0]
            
            # Save documents
            self._save_documents()
            
            logger.info(f"Indexed {len(new_documents)} new documents")
        else:
            logger.info("No new documents to index")
    
    def _process_github_data(self, github_data: GitHubData) -> List[SimpleDocument]:
        """Process GitHub data into indexable documents"""
        documents = []
        
        # Process pull requests
        for pr in github_data.pull_requests:
            if pr.get('body') and len(pr['body'].strip()) > 20:
                content = self._clean_text(f"{pr['title']} {pr['body']}")
                doc = SimpleDocument(
                    doc_id=f"github_pr_{pr['id']}",
                    content=content,
                    metadata={
                        'url': pr['html_url'],
                        'state': pr['state'],
                        'created_at': pr['created_at'],
                        'updated_at': pr['updated_at']
                    },
                    source='github',
                    doc_type='pr',
                    author=pr['user']['login'] if pr.get('user') else 'unknown',
                    created_at=pr['created_at']
                )
                documents.append(doc)
        
        # Process commits
        for commit in github_data.commits:
            commit_data = commit.get('commit', {})
            message = commit_data.get('message', '')
            
            if message and len(message.strip()) > 10:
                content = self._clean_text(message)
                doc = SimpleDocument(
                    doc_id=f"github_commit_{commit['sha']}",
                    content=content,
                    metadata={
                        'sha': commit['sha'],
                        'url': commit['html_url'],
                        'author_date': commit_data.get('author', {}).get('date')
                    },
                    source='github',
                    doc_type='commit',
                    author=commit_data.get('author', {}).get('name', 'unknown'),
                    created_at=commit_data.get('author', {}).get('date', '')
                )
                documents.append(doc)
        
        # Process issues
        for issue in github_data.issues:
            if issue.get('body') and len(issue['body'].strip()) > 20:
                content = self._clean_text(f"{issue['title']} {issue['body']}")
                doc = SimpleDocument(
                    doc_id=f"github_issue_{issue['id']}",
                    content=content,
                    metadata={
                        'number': issue['number'],
                        'url': issue['html_url'],
                        'state': issue['state'],
                        'created_at': issue['created_at']
                    },
                    source='github',
                    doc_type='issue',
                    author=issue['user']['login'] if issue.get('user') else 'unknown',
                    created_at=issue['created_at']
                )
                documents.append(doc)
        
        logger.info(f"Processed {len(documents)} GitHub documents")
        return documents
    
    def _process_jira_data(self, jira_data: JiraData) -> List[SimpleDocument]:
        """Process Jira data into indexable documents"""
        documents = []
        
        # Process tickets
        for ticket in jira_data.tickets:
            fields = ticket.get('fields', {})
            summary = fields.get('summary', '')
            description = fields.get('description', '')
            
            if summary or description:
                content_parts = []
                if summary:
                    content_parts.append(summary)
                if description:
                    content_parts.append(description)
                
                content = self._clean_text(' '.join(content_parts))
                
                doc = SimpleDocument(
                    doc_id=f"jira_ticket_{ticket['key']}",
                    content=content,
                    metadata={
                        'key': ticket['key'],
                        'issue_type': fields.get('issuetype', {}).get('name'),
                        'status': fields.get('status', {}).get('name'),
                        'created': fields.get('created')
                    },
                    source='jira',
                    doc_type='ticket',
                    author=fields.get('creator', {}).get('displayName', 'unknown'),
                    created_at=fields.get('created', '')
                )
                documents.append(doc)
        
        # Process comments
        for comment in jira_data.comments:
            body = comment.get('body', '')
            if body and len(body.strip()) > 20:
                content = self._clean_text(body)
                doc = SimpleDocument(
                    doc_id=f"jira_comment_{comment['id']}",
                    content=content,
                    metadata={
                        'comment_id': comment['id'],
                        'created': comment.get('created')
                    },
                    source='jira',
                    doc_type='comment',
                    author=comment.get('author', {}).get('displayName', 'unknown'),
                    created_at=comment.get('created', '')
                )
                documents.append(doc)
        
        logger.info(f"Processed {len(documents)} Jira documents")
        return documents
    
    def _clean_text(self, text: str) -> str:
        """Clean and preprocess text"""
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.lower()
    
    async def semantic_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search using TF-IDF similarity"""
        try:
            if not self.documents or self.tfidf_matrix is None:
                logger.warning("No indexed documents available")
                return []
            
            # Clean and vectorize query
            clean_query = self._clean_text(query)
            query_vector = self.vectorizer.transform([clean_query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0]
            
            # Get top results
            top_indices = similarities.argsort()[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Only include reasonably similar results
                    doc = self.documents[idx]
                    result = {
                        'content': doc.content,
                        'score': similarities[idx],
                        'metadata': {
                            **doc.metadata,
                            'doc_id': doc.doc_id,
                            'source': doc.source,
                            'doc_type': doc.doc_type,
                            'author': doc.author
                        }
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about indexed documents"""
        stats = {
            'total_documents': len(self.documents),
            'by_source': {},
            'by_type': {},
            'by_author': {}
        }
        
        for doc in self.documents:
            # Count by source
            stats['by_source'][doc.source] = stats['by_source'].get(doc.source, 0) + 1
            
            # Count by type
            stats['by_type'][doc.doc_type] = stats['by_type'].get(doc.doc_type, 0) + 1
            
            # Count by author
            stats['by_author'][doc.author] = stats['by_author'].get(doc.author, 0) + 1
        
        return stats
    
    async def find_similar_work(self, content: str, author: str, top_k: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Find similar work by a specific author or others"""
        try:
            # Search for similar content
            results = await self.semantic_search(content, top_k * 2)
            
            # Separate results by author
            author_results = []
            other_results = []
            
            for result in results:
                if result['metadata'].get('author') == author:
                    author_results.append(result)
                else:
                    other_results.append(result)
            
            return {
                'similar_by_author': author_results[:top_k],
                'similar_by_others': other_results[:top_k]
            }
            
        except Exception as e:
            logger.error(f"Failed to find similar work: {e}")
            return {'similar_by_author': [], 'similar_by_others': []}