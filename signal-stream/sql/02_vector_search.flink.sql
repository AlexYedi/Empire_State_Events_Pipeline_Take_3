-- ============================================================================
-- Layer 1b (UPGRADE — only after 1a is solid) — ground classification in VECTOR_SEARCH
-- Instead of a static ICP in the prompt, retrieve the nearest ICP entries per event and
-- feed those as context. Improves precision on borderline items.
--
-- ⚠️ VERIFY-BEFORE-RUN: which external vector stores Confluent Cloud Flink VECTOR_SEARCH supports
--    (e.g. MongoDB Atlas, Pinecone, Couchbase — pgvector support is NOT guaranteed; check first),
--    plus the embedding-model + VECTOR_SEARCH syntax:
--    - VECTOR_SEARCH:   https://docs.confluent.io/cloud/current/flink/reference/functions/model-inference-functions.html
--    - external tables: https://docs.confluent.io/cloud/current/flink/reference/statements/create-table.html
--    Pick a store you can stand up fast; if none is quick, STAY on 1a (prompt-based) for the demo.
-- ============================================================================

-- 1) An embedding model (to turn text into vectors).
CREATE MODEL icp_embedder
  INPUT  (text STRING)
  OUTPUT (embedding ARRAY<FLOAT>)
  WITH (
    'provider' = 'openai',
    'openai.connection' = 'signal_model_conn',
    'openai.model_version' = 'text-embedding-3-small'
  );

-- 2) An external vector table holding embedded ICP entries (icp/targets.md rows).
--    Populate it once (offline embed of the ICP list) — shape is store-specific. VERIFY.
CREATE TABLE icp_vectors (
    icp_id STRING,
    icp_text STRING,
    embedding ARRAY<FLOAT>
) WITH ( /* external vector store connector — VERIFY per chosen store */ );

-- 3) Classify with retrieved ICP context:
--    embed each event -> VECTOR_SEARCH nearest ICP rows -> pass them into the classifier prompt.
INSERT INTO gtm_signals
SELECT r.id, r.title, r.url, r.source, p.response, r.ts
FROM raw_signals AS r,
  LATERAL TABLE(ML_PREDICT('icp_embedder', r.title || ' ' || COALESCE(r.text,''))) AS e(embedding),
  LATERAL TABLE(VECTOR_SEARCH('icp_vectors', e.embedding, 3)) AS v(icp_id, icp_text, embedding),
  LATERAL TABLE(
    ML_PREDICT('signal_classifier',
      'ITEM:\n' || COALESCE(r.title,'') || '\n' || COALESCE(r.text,'') ||
      '\n\nNEAREST ICP CONTEXT:\n' || v.icp_text)
  ) AS p(response)
WHERE p.response LIKE '%"relevant":true%';
