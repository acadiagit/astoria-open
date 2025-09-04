-- This script sets up the 'documents' table for pgvector and the corresponding search function.

-- Step 1: Create the table to store documents and embeddings.
CREATE TABLE public.documents (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  content text,
  metadata jsonb,
  embedding vector(384) -- Corresponds to the all-MiniLM-L6-v2 model
);

-- Step 2: Create the function to search for similar documents.
CREATE OR REPLACE FUNCTION match_documents (
  query_embedding vector(384),
  match_count int DEFAULT 10,
  filter jsonb DEFAULT '{}'
)
RETURNS TABLE (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    documents.id,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) as similarity
  FROM documents
  WHERE documents.metadata @> filter
  ORDER BY documents.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Step 3: Grant permissions on the new table and function to the API roles.
GRANT ALL ON TABLE public.documents TO service_role;
GRANT ALL ON TABLE public.documents TO anon;
GRANT EXECUTE ON FUNCTION public.match_documents(vector, integer, jsonb) TO service_role;
GRANT EXECUTE ON FUNCTION public.match_documents(vector, integer, jsonb) TO anon;
