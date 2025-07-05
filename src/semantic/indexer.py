#!/usr/bin/env python3
"""
Semantic Indexer - Local LlamaIndex implementation for GitHub and Jira content
"""

import os
import json
import pickle
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from dataclasses import dataclass

# LlamaIndex imports
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Local imports
from ..integrations.composio_manager import GitHubData, JiraData

logger = logging.getLogger(__name__)

@dataclass
class IndexedDocument:
    """Structure for indexed documents"""
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    source: str  # 'github' or 'jira'
    doc_type: str  # 'pr', 'commit', 'issue', 'ticket', 'comment'
    author: str
    created_at: str
    embedding: Optional[List[float]] = None

class SemanticIndexer:
    """Handles semantic indexing of GitHub and Jira content using local embeddings"""
    
    def __init__(self, config):
        self.config = config
        self.index: Optional[VectorStoreIndex] = None
        self.storage_context: Optional[StorageContext] = None
        self.documents: List[IndexedDocument] = []
        
        # Index storage paths
        self.index_dir = os.path.join(self.config.embeddings_dir, 'index')
        self.documents_file = os.path.join(self.config.data_dir, 'indexed_documents.pkl')
        
        # Create directories
        os.makedirs(self.index_dir, exist_ok=True)
        
    async def initialize(self):
        """Initialize the semantic indexer with local embeddings"""
        try:
            # Configure LlamaIndex to use local embeddings
            embed_model = HuggingFaceEmbedding(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                cache_folder=os.path.join(self.config.embeddings_dir, 'models')
            )
            
            Settings.embed_model = embed_model
            Settings.chunk_size = 512
            Settings.chunk_overlap = 50
            
            # Initialize storage context
            self._initialize_storage()
            
            # Load existing documents if available
            self._load_existing_documents()
            
            logger.info("Semantic indexer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize semantic indexer: {e}")
            raise
    
    def _initialize_storage(self):
        """Initialize or load storage context"""
        try:
            # Try to load existing storage
            if os.path.exists(os.path.join(self.index_dir, 'docstore.json')):
                # Load existing storage
                docstore = SimpleDocumentStore.from_persist_dir(self.index_dir)
                index_store = SimpleIndexStore.from_persist_dir(self.index_dir)
                vector_store = SimpleVectorStore.from_persist_dir(self.index_dir)
                
                self.storage_context = StorageContext.from_defaults(
                    docstore=docstore,
                    index_store=index_store,
                    vector_store=vector_store
                )
                
                # Load existing index
                self.index = VectorStoreIndex.from_storage_context(self.storage_context)
                logger.info("Loaded existing semantic index")
                
            else:
                # Create new storage
                self.storage_context = StorageContext.from_defaults()
                self.index = VectorStoreIndex([], storage_context=self.storage_context)
                logger.info("Created new semantic index")
                
        except Exception as e:
            logger.error(f"Failed to initialize storage: {e}")
            # Fallback to new storage
            self.storage_context = StorageContext.from_defaults()
            self.index = VectorStoreIndex([], storage_context=self.storage_context)
    
    def _load_existing_documents(self):
        """Load previously indexed documents"""
        try:
            if os.path.exists(self.documents_file):
                with open(self.documents_file, 'rb') as f:
                    self.documents = pickle.load(f)
                logger.info(f"Loaded {len(self.documents)} existing documents")
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
    
    async def index_data(self, github_data: GitHubData, jira_data: JiraData):
        """Index GitHub and Jira data for semantic search"""
        logger.info("Starting semantic indexing of data")
        
        new_documents = []
        
        # Index GitHub data
        new_documents.extend(self._process_github_data(github_data))
        
        # Index Jira data
        new_documents.extend(self._process_jira_data(jira_data))
        
        # Add new documents to index
        if new_documents:
            documents_to_index = self._convert_to_llama_documents(new_documents)
            
            # Add to existing index or create new one
            for doc in documents_to_index:
                self.index.insert(doc)
            
            # Save the index
            self._persist_index()
            
            # Update document list
            self.documents.extend(new_documents)
            self._save_documents()
            
            logger.info(f"Indexed {len(new_documents)} new documents")
        else:
            logger.info("No new documents to index")
    
    def _process_github_data(self, github_data: GitHubData) -> List[IndexedDocument]:
        """Process GitHub data into indexable documents"""
        documents = []
        
        # Process pull requests
        for pr in github_data.pull_requests:
            if pr.get('body'):  # Only index PRs with descriptions
                doc = IndexedDocument(
                    doc_id=f"github_pr_{pr['id']}",
                    content=f"Title: {pr['title']}\n\nDescription: {pr['body']}",
                    metadata={
                        'url': pr['html_url'],
                        'state': pr['state'],
                        'created_at': pr['created_at'],
                        'updated_at': pr['updated_at'],
                        'additions': pr.get('additions', 0),
                        'deletions': pr.get('deletions', 0),
                        'changed_files': pr.get('changed_files', 0)
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
            
            if message and len(message.strip()) > 10:  # Only meaningful commit messages
                doc = IndexedDocument(
                    doc_id=f"github_commit_{commit['sha']}",
                    content=f"Commit message: {message}",
                    metadata={
                        'sha': commit['sha'],
                        'url': commit['html_url'],
                        'author_date': commit_data.get('author', {}).get('date'),
                        'stats': commit.get('stats', {})
                    },
                    source='github',
                    doc_type='commit',
                    author=commit_data.get('author', {}).get('name', 'unknown'),
                    created_at=commit_data.get('author', {}).get('date', '')
                )
                documents.append(doc)
        
        # Process issues
        for issue in github_data.issues:
            if issue.get('body'):  # Only index issues with descriptions
                doc = IndexedDocument(
                    doc_id=f"github_issue_{issue['id']}",
                    content=f"Title: {issue['title']}\n\nDescription: {issue['body']}",
                    metadata={
                        'number': issue['number'],
                        'url': issue['html_url'],
                        'state': issue['state'],
                        'labels': [label['name'] for label in issue.get('labels', [])],
                        'created_at': issue['created_at'],
                        'updated_at': issue['updated_at']
                    },
                    source='github',
                    doc_type='issue',
                    author=issue['user']['login'] if issue.get('user') else 'unknown',
                    created_at=issue['created_at']
                )
                documents.append(doc)
        
        logger.info(f"Processed {len(documents)} GitHub documents")
        return documents
    
    def _process_jira_data(self, jira_data: JiraData) -> List[IndexedDocument]:
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
                    content_parts.append(f"Summary: {summary}")
                if description:
                    content_parts.append(f"Description: {description}")
                
                doc = IndexedDocument(
                    doc_id=f"jira_ticket_{ticket['key']}",
                    content='\n\n'.join(content_parts),
                    metadata={
                        'key': ticket['key'],
                        'issue_type': fields.get('issuetype', {}).get('name'),
                        'status': fields.get('status', {}).get('name'),
                        'priority': fields.get('priority', {}).get('name'),
                        'created': fields.get('created'),
                        'updated': fields.get('updated'),
                        'resolution': fields.get('resolution', {}).get('name') if fields.get('resolution') else None
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
            if body and len(body.strip()) > 20:  # Only substantial comments
                doc = IndexedDocument(
                    doc_id=f"jira_comment_{comment['id']}",
                    content=f"Comment: {body}",
                    metadata={
                        'comment_id': comment['id'],
                        'created': comment.get('created'),
                        'updated': comment.get('updated')
                    },
                    source='jira',
                    doc_type='comment',
                    author=comment.get('author', {}).get('displayName', 'unknown'),
                    created_at=comment.get('created', '')
                )
                documents.append(doc)
        
        logger.info(f"Processed {len(documents)} Jira documents")
        return documents
    
    def _convert_to_llama_documents(self, indexed_docs: List[IndexedDocument]) -> List[Document]:
        """Convert IndexedDocument objects to LlamaIndex Document objects"""
        llama_docs = []
        
        for doc in indexed_docs:
            # Create metadata for LlamaIndex
            metadata = {
                'doc_id': doc.doc_id,
                'source': doc.source,
                'doc_type': doc.doc_type,
                'author': doc.author,
                'created_at': doc.created_at,
                **doc.metadata
            }
            
            llama_doc = Document(
                text=doc.content,
                metadata=metadata,
                doc_id=doc.doc_id
            )
            
            llama_docs.append(llama_doc)
        
        return llama_docs
    
    def _persist_index(self):
        """Persist the index to disk"""
        try:
            self.storage_context.persist(persist_dir=self.index_dir)
            logger.info("Index persisted successfully")
        except Exception as e:
            logger.error(f"Failed to persist index: {e}")
    
    async def semantic_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search on indexed content"""
        try:
            if not self.index:
                logger.warning("Index not initialized")
                return []
            
            # Create query engine
            query_engine = self.index.as_query_engine(
                similarity_top_k=top_k,
                response_mode="no_text"  # We only want the source nodes
            )
            
            # Perform search
            response = query_engine.query(query)
            
            # Extract results
            results = []
            for node in response.source_nodes:
                result = {
                    'content': node.node.text,
                    'score': node.score,
                    'metadata': node.node.metadata
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
    
    async def find_similar_work(self, content: str, author: str, top_k: int = 5) -> List[Dict[str, Any]]:
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
            
            # Return top results from each category
            return {
                'similar_by_author': author_results[:top_k],
                'similar_by_others': other_results[:top_k]
            }
            
        except Exception as e:
            logger.error(f"Failed to find similar work: {e}")
            return {'similar_by_author': [], 'similar_by_others': []}