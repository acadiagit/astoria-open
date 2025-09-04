-- Path: database/supabase_functions.sql  
-- File: supabase_vector_search_function.sql
-- Execute in Supabase SQL Editor or via psql
-- Purpose: Create RPC function for vector similarity search

-- Create the vector search function
CREATE OR REPLACE FUNCTION search_documents(
  query_embedding vector(384),  -- Embedding dimension for all-MiniLM-L6-v2
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE sql
STABLE
AS $$
  SELECT
    documents.id,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) as similarity
  FROM documents
  WHERE documents.embedding <=> query_embedding < 1 - match_threshold
  ORDER BY documents.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- Create index on embedding column for faster similarity search (if not exists)
CREATE INDEX IF NOT EXISTS documents_embedding_idx 
ON documents 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION search_documents TO authenticated;
GRANT EXECUTE ON FUNCTION search_documents TO anon;

-- Example usage (for testing):
-- SELECT * FROM search_documents(
--   '[0.1, 0.2, 0.3, ...]'::vector,  -- Your query embedding
--   0.7,  -- Similarity threshold  
--   5     -- Number of results
-- );

--end-of-script