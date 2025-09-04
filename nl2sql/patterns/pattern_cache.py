# Path: nl2sql/patterns/pattern_cache.py
# Filename: pattern_cache.py
# Purpose: Caching system for successful query patterns and results

"""
Pattern Cache

Caches successful query patterns and their results to improve
performance for repeated or similar queries.
"""

import hashlib
import json
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Represents a cached query result"""
    query_hash: str
    original_query: str
    normalized_query: str
    sql_query: str
    parameters: List[Any]
    results: Any
    processing_method: str
    execution_time: float
    confidence: float
    created_at: datetime
    last_accessed: datetime
    access_count: int
    success: bool

class PatternCache:
    """Manages caching of successful query patterns and results"""
    
    def __init__(self, max_entries: int = 10000, ttl_hours: int = 24):
        self.max_entries = max_entries
        self.ttl = timedelta(hours=ttl_hours)
        self.cache: Dict[str, CacheEntry] = {}
        self.query_normalizer = QueryNormalizer()
        self.hit_count = 0
        self.miss_count = 0
        
    def _generate_cache_key(self, nl_query: str) -> str:
        """Generate a cache key for a natural language query"""
        normalized = self.query_normalizer.normalize(nl_query)
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def get(self, nl_query: str) -> Optional[CacheEntry]:
        """Retrieve cached result for a query"""
        cache_key = self._generate_cache_key(nl_query)
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            
            # Check if entry has expired
            if datetime.now() - entry.created_at > self.ttl:
                del self.cache[cache_key]
                self.miss_count += 1
                return None
            
            # Update access statistics
            entry.last_accessed = datetime.now()
            entry.access_count += 1
            self.hit_count += 1
            
            logger.debug(f"Cache hit for query: {nl_query[:50]}...")
            return entry
        
        self.miss_count += 1
        return None
    
    def put(self, nl_query: str, sql_query: str, parameters: List[Any], 
            results: Any, processing_method: str, execution_time: float, 
            confidence: float, success: bool = True):
        """Cache a query result"""
        cache_key = self._generate_cache_key(nl_query)
        normalized_query = self.query_normalizer.normalize(nl_query)
        
        entry = CacheEntry(
            query_hash=cache_key,
            original_query=nl_query,
            normalized_query=normalized_query,
            sql_query=sql_query,
            parameters=parameters,
            results=results,
            processing_method=processing_method,
            execution_time=execution_time,
            confidence=confidence,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=1,
            success=success
        )
        
        # Check cache size and evict if necessary
        if len(self.cache) >= self.max_entries:
            self._evict_entries()
        
        self.cache[cache_key] = entry
        logger.debug(f"Cached result for query: {nl_query[:50]}...")
    
    def _evict_entries(self):
        """Evict least recently used entries"""
        # Sort by last_accessed and remove oldest 10%
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1].last_accessed
        )
        
        evict_count = max(1, len(sorted_entries) // 10)
        for i in range(evict_count):
            cache_key = sorted_entries[i][0]
            del self.cache[cache_key]
        
        logger.debug(f"Evicted {evict_count} cache entries")
    
    def find_similar(self, nl_query: str, similarity_threshold: float = 0.8) -> List[CacheEntry]:
        """Find similar cached queries"""
        normalized_query = self.query_normalizer.normalize(nl_query)
        similar_entries = []
        
        for entry in self.cache.values():
            similarity = self._calculate_similarity(normalized_query, entry.normalized_query)
            if similarity >= similarity_threshold:
                similar_entries.append((entry, similarity))
        
        # Sort by similarity descending
        similar_entries.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in similar_entries]
    
    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity between two normalized queries"""
        words1 = set(query1.split())
        words2 = set(query2.split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests) if total_requests > 0 else 0
        
        # Analyze processing methods
        method_stats = {}
        execution_times = []
        confidence_scores = []
        
        for entry in self.cache.values():
            method = entry.processing_method
            method_stats[method] = method_stats.get(method, 0) + 1
            execution_times.append(entry.execution_time)
            confidence_scores.append(entry.confidence)
        
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        return {
            'total_entries': len(self.cache),
            'max_entries': self.max_entries,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': hit_rate,
            'processing_methods': method_stats,
            'average_execution_time': avg_execution_time,
            'average_confidence': avg_confidence,
            'cache_age_hours': (datetime.now() - min(entry.created_at for entry in self.cache.values())).total_seconds() / 3600 if self.cache else 0
        }
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.hit_count = 0
        self.miss_count = 0
        logger.info("Cache cleared")
    
    def remove_expired(self):
        """Remove expired entries"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, entry in self.cache.items():
            if current_time - entry.created_at > self.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"Removed {len(expired_keys)} expired cache entries")
    
    def get_popular_queries(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most frequently accessed queries"""
        sorted_entries = sorted(
            self.cache.values(),
            key=lambda x: x.access_count,
            reverse=True
        )
        
        return [(entry.original_query, entry.access_count) for entry in sorted_entries[:limit]]
    
    def export_cache(self) -> Dict[str, Any]:
        """Export cache data for persistence"""
        export_data = {
            'entries': [],
            'metadata': {
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'max_entries': self.max_entries,
                'ttl_hours': self.ttl.total_seconds() / 3600,
                'export_time': datetime.now().isoformat()
            }
        }
        
        for entry in self.cache.values():
            entry_dict = asdict(entry)
            # Convert datetime objects to ISO strings
            entry_dict['created_at'] = entry.created_at.isoformat()
            entry_dict['last_accessed'] = entry.last_accessed.isoformat()
            export_data['entries'].append(entry_dict)
        
        return export_data
    
    def import_cache(self, data: Dict[str, Any]):
        """Import cache data from persistence"""
        if 'metadata' in data:
            metadata = data['metadata']
            self.hit_count = metadata.get('hit_count', 0)
            self.miss_count = metadata.get('miss_count', 0)
        
        if 'entries' in data:
            for entry_dict in data['entries']:
                # Convert ISO strings back to datetime objects
                entry_dict['created_at'] = datetime.fromisoformat(entry_dict['created_at'])
                entry_dict['last_accessed'] = datetime.fromisoformat(entry_dict['last_accessed'])
                
                entry = CacheEntry(**entry_dict)
                self.cache[entry.query_hash] = entry
        
        logger.info(f"Imported {len(self.cache)} cache entries")


class QueryNormalizer:
    """Normalizes queries for consistent caching"""
    
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can'
        }
        
        self.synonyms = {
            'ship': 'vessel',
            'ships': 'vessels',
            'boat': 'vessel',
            'boats': 'vessels',
            'list': 'show',
            'display': 'show',
            'find': 'show',
            'get': 'show'
        }
    
    def normalize(self, query: str) -> str:
        """Normalize a query for consistent comparison"""
        # Convert to lowercase
        normalized = query.lower().strip()
        
        # Remove punctuation
        normalized = ''.join(char if char.isalnum() or char.isspace() else ' ' for char in normalized)
        
        # Split into words
        words = normalized.split()
        
        # Apply synonyms
        words = [self.synonyms.get(word, word) for word in words]
        
        # Remove stop words (but keep some important ones for maritime queries)
        important_words = {'all', 'how', 'many', 'what', 'which', 'when', 'where'}
        words = [word for word in words if word not in self.stop_words or word in important_words]
        
        # Sort words to handle different word orders
        # Keep the first word in place as it's often the action (list, show, etc.)
        if words:
            first_word = words[0]
            remaining_words = sorted(words[1:])
            words = [first_word] + remaining_words
        
        return ' '.join(words)

#end-of-script