from typing import List, Dict, Optional, Any
from datetime import datetime
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from db import get_conn

class QueryBuilder:
    """Build search queries across documents, calls, and SMS."""
    
    def __init__(self):
        self.params = {}
    
    def with_keywords(self, keywords: str):
        """Add keyword search."""
        self.params['keywords'] = keywords
        return self
    
    def with_date_range(self, start: Optional[str] = None, end: Optional[str] = None):
        """Add date range filter."""
        if start:
            self.params['start_date'] = start
        if end:
            self.params['end_date'] = end
        return self
    
    def with_sources(self, sources: List[str]):
        """Add source filters."""
        self.params['sources'] = sources
        return self
    
    def with_types(self, types: List[str]):
        """Add type filters."""
        self.params['types'] = types
        return self
    
    def with_phone_numbers(self, phone_numbers: List[str]):
        """Add phone number filters."""
        self.params['phone_numbers'] = phone_numbers
        return self
    
    def with_case_id(self, case_id: int):
        """Add case filter."""
        self.params['case_id'] = case_id
        return self
    
    def with_confidence_threshold(self, threshold: float):
        """Add confidence threshold."""
        self.params['confidence'] = threshold
        return self
    
    def build_document_query(self) -> tuple:
        """Build SQL query for document search."""
        conditions = []
        params = []
        
        # Keyword search
        if 'keywords' in self.params:
            conditions.append("(d.title ILIKE %s OR dc.content ILIKE %s)")
            keyword_pattern = f"%{self.params['keywords']}%"
            params.extend([keyword_pattern, keyword_pattern])
        
        # Date range
        if 'start_date' in self.params:
            conditions.append("d.created_at >= %s")
            params.append(self.params['start_date'])
        if 'end_date' in self.params:
            conditions.append("d.created_at <= %s")
            params.append(self.params['end_date'])
        
        # Case filter
        if 'case_id' in self.params:
            conditions.append("d.case_id = %s")
            params.append(self.params['case_id'])
        
        # Type filter
        if 'types' in self.params:
            type_conditions = [f"d.doc_type = %s" for _ in self.params['types']]
            conditions.append(f"({' OR '.join(type_conditions)})")
            params.extend(self.params['types'])
        
        # Phone number filter (via phone_links)
        if 'phone_numbers' in self.params:
            conditions.append("""
                d.id IN (
                    SELECT pl.source_id 
                    FROM phone_links pl 
                    JOIN phone_numbers pn ON pl.phone_id = pn.id 
                    WHERE pl.source_type = 'document_chunk' 
                    AND pn.number = ANY(%s)
                )
            """)
            params.append(self.params['phone_numbers'])
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT DISTINCT d.id, d.title, d.doc_type, d.file_path, d.created_at,
                   dc.content as snippet
            FROM documents d
            LEFT JOIN document_chunks dc ON d.id = dc.document_id
            WHERE {where_clause}
            ORDER BY d.created_at DESC
            LIMIT 100
        """
        
        return query, params
    
    def build_call_query(self) -> tuple:
        """Build SQL query for call search."""
        conditions = []
        params = []
        
        # Keyword search (in transcript)
        if 'keywords' in self.params:
            conditions.append("(c.phone_number ILIKE %s OR cc.content ILIKE %s)")
            keyword_pattern = f"%{self.params['keywords']}%"
            params.extend([keyword_pattern, keyword_pattern])
        
        # Date range
        if 'start_date' in self.params:
            conditions.append("c.started_at >= %s")
            params.append(self.params['start_date'])
        if 'end_date' in self.params:
            conditions.append("c.started_at <= %s")
            params.append(self.params['end_date'])
        
        # Phone number filter
        if 'phone_numbers' in self.params:
            conditions.append("c.phone_number = ANY(%s)")
            params.append(self.params['phone_numbers'])
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT DISTINCT c.id, c.phone_number, c.direction, c.started_at, c.duration,
                   cc.content as snippet
            FROM calls c
            LEFT JOIN call_chunks cc ON c.id = cc.call_id
            WHERE {where_clause}
            ORDER BY c.started_at DESC
            LIMIT 100
        """
        
        return query, params
    
    def build_sms_query(self) -> tuple:
        """Build SQL query for SMS search."""
        conditions = []
        params = []
        
        # Keyword search
        if 'keywords' in self.params:
            conditions.append("(s.phone_number ILIKE %s OR s.content ILIKE %s)")
            keyword_pattern = f"%{self.params['keywords']}%"
            params.extend([keyword_pattern, keyword_pattern])
        
        # Date range
        if 'start_date' in self.params:
            conditions.append("s.sent_at >= %s")
            params.append(self.params['start_date'])
        if 'end_date' in self.params:
            conditions.append("s.sent_at <= %s")
            params.append(self.params['end_date'])
        
        # Phone number filter
        if 'phone_numbers' in self.params:
            conditions.append("s.phone_number = ANY(%s)")
            params.append(self.params['phone_numbers'])
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT s.id, s.phone_number, s.direction, s.sent_at, s.content as snippet
            FROM sms_messages s
            WHERE {where_clause}
            ORDER BY s.sent_at DESC
            LIMIT 100
        """
        
        return query, params
    
    def execute_all(self) -> Dict[str, List[Dict]]:
        """Execute all queries and return combined results."""
        conn = get_conn()
        cur = conn.cursor()
        
        results = {
            'documents': [],
            'calls': [],
            'sms': []
        }
        
        try:
            # Search documents
            doc_query, doc_params = self.build_document_query()
            cur.execute(doc_query, doc_params)
            columns = [desc[0] for desc in cur.description]
            results['documents'] = [dict(zip(columns, row)) for row in cur.fetchall()]
            
            # Search calls
            call_query, call_params = self.build_call_query()
            cur.execute(call_query, call_params)
            columns = [desc[0] for desc in cur.description]
            results['calls'] = [dict(zip(columns, row)) for row in cur.fetchall()]
            
            # Search SMS
            sms_query, sms_params = self.build_sms_query()
            cur.execute(sms_query, sms_params)
            columns = [desc[0] for desc in cur.description]
            results['sms'] = [dict(zip(columns, row)) for row in cur.fetchall()]
            
        finally:
            cur.close()
            conn.close()
        
        return results
