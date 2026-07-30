from typing import List, Dict, Optional
from .query_builder import QueryBuilder

def search_all(params: Dict) -> Dict:
    """
    Execute search across all data sources.
    
    Args:
        params: Dictionary with search parameters:
            - keywords: str
            - start_date: str (ISO format)
            - end_date: str (ISO format)
            - sources: List[str]
            - types: List[str]
            - phone_numbers: List[str]
            - case_id: int
            - confidence: float
    
    Returns:
        Dictionary with results from documents, calls, and SMS
    """
    builder = QueryBuilder()
    
    if 'keywords' in params and params['keywords']:
        builder = builder.with_keywords(params['keywords'])
    
    if 'start_date' in params or 'end_date' in params:
        builder = builder.with_date_range(
            params.get('start_date'),
            params.get('end_date')
        )
    
    if 'types' in params and params['types']:
        builder = builder.with_types(params['types'])
    
    if 'phone_numbers' in params and params['phone_numbers']:
        builder = builder.with_phone_numbers(params['phone_numbers'])
    
    if 'case_id' in params:
        builder = builder.with_case_id(params['case_id'])
    
    if 'confidence' in params:
        builder = builder.with_confidence_threshold(params['confidence'])
    
    results = builder.execute_all()
    
    # Add type labels to results
    for doc in results['documents']:
        doc['result_type'] = 'document'
        doc['source'] = doc.get('doc_type', 'unknown')
    
    for call in results['calls']:
        call['result_type'] = 'call'
        call['source'] = 'call_recording'
    
    for sms in results['sms']:
        sms['result_type'] = 'sms'
        sms['source'] = 'sms_message'
    
    return results

def get_document_detail(doc_id: int) -> Optional[Dict]:
    """Get full document details with all chunks."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from db import get_conn
    
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            return None
        
        columns = [desc[0] for desc in cur.description]
        doc_dict = dict(zip(columns, doc))
        
        # Get chunks
        cur.execute(
            "SELECT * FROM document_chunks WHERE document_id = %s ORDER BY chunk_index",
            (doc_id,)
        )
        chunk_columns = [desc[0] for desc in cur.description]
        doc_dict['chunks'] = [dict(zip(chunk_columns, row)) for row in cur.fetchall()]
        
        return doc_dict
    finally:
        cur.close()
        conn.close()

def get_call_detail(call_id: int) -> Optional[Dict]:
    """Get full call details with transcript chunks."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from db import get_conn
    
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM calls WHERE id = %s", (call_id,))
        call = cur.fetchone()
        if not call:
            return None
        
        columns = [desc[0] for desc in cur.description]
        call_dict = dict(zip(columns, call))
        
        # Get chunks
        cur.execute(
            "SELECT * FROM call_chunks WHERE call_id = %s ORDER BY chunk_index",
            (call_id,)
        )
        chunk_columns = [desc[0] for desc in cur.description]
        call_dict['chunks'] = [dict(zip(chunk_columns, row)) for row in cur.fetchall()]
        
        return call_dict
    finally:
        cur.close()
        conn.close()

def get_sms_detail(sms_id: int) -> Optional[Dict]:
    """Get SMS message details."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from db import get_conn
    
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM sms_messages WHERE id = %s", (sms_id,))
        sms = cur.fetchone()
        if not sms:
            return None
        
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, sms))
    finally:
        cur.close()
        conn.close()

def get_phone_number_context(phone_number: str) -> Dict:
    """Get all evidence linked to a phone number."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from db import get_conn
    
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        # Get phone ID
        cur.execute("SELECT id, label FROM phone_numbers WHERE number = %s", (phone_number,))
        phone = cur.fetchone()
        if not phone:
            return {'error': 'Phone number not found'}
        
        phone_id, label = phone
        
        # Get linked documents
        cur.execute("""
            SELECT d.id, d.title, d.doc_type, d.created_at
            FROM phone_links pl
            JOIN documents d ON pl.source_id = d.id
            WHERE pl.phone_id = %s AND pl.source_type = 'document_chunk'
        """, (phone_id,))
        doc_columns = [desc[0] for desc in cur.description]
        documents = [dict(zip(doc_columns, row)) for row in cur.fetchall()]
        
        # Get linked calls
        cur.execute("""
            SELECT c.id, c.phone_number, c.direction, c.started_at
            FROM phone_links pl
            JOIN calls c ON pl.source_id = c.id
            WHERE pl.phone_id = %s AND pl.source_type = 'call_chunk'
        """, (phone_id,))
        call_columns = [desc[0] for desc in cur.description]
        calls = [dict(zip(call_columns, row)) for row in cur.fetchall()]
        
        # Get linked SMS
        cur.execute("""
            SELECT s.id, s.phone_number, s.direction, s.sent_at
            FROM phone_links pl
            JOIN sms_messages s ON pl.source_id = s.id
            WHERE pl.phone_id = %s AND pl.source_type = 'sms'
        """, (phone_id,))
        sms_columns = [desc[0] for desc in cur.description]
        sms = [dict(zip(sms_columns, row)) for row in cur.fetchall()]
        
        return {
            'phone_number': phone_number,
            'label': label,
            'documents': documents,
            'calls': calls,
            'sms': sms
        }
    finally:
        cur.close()
        conn.close()
