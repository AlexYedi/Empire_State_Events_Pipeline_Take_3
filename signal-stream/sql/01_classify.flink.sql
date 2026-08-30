-- ============================================================================
-- Layer 1a — Signal Stream: continuous GTM-signal classification
-- Reads raw_signals -> ML_PREDICT classifies vs ICP -> inserts relevant -> gtm_signals
--
-- ⚠️ VERIFY-BEFORE-RUN: the exact CREATE CONNECTION / CREATE MODEL / ML_PREDICT syntax on
--    Confluent Cloud Flink is version-specific and moves fast. Confirm each verb against the
--    live docs before running — this file is a close template, not copy-paste-guaranteed:
--    - Flink AI models:  https://docs.confluent.io/cloud/current/flink/reference/statements/create-model.html
--    - CREATE CONNECTION: https://docs.confluent.io/cloud/current/flink/reference/statements/create-connection.html
--    - ML_PREDICT:        https://docs.confluent.io/cloud/current/flink/reference/functions/model-inference-functions.html
--    Prefer authoring/running this in the Console → Flink workspace (clearest errors).
-- ============================================================================

-- 0) Assumes raw_signals exists (Datagen for Layer 0, or hn_producer.py for real data) and is
--    registered as a Flink table (Confluent auto-maps topics to tables in the same environment).
--    Expected value shape from hn_producer.py: { id, title, url, source, text, ts }

-- 1) Connection to your model provider (holds the API key server-side; set once).
--    Replace provider/endpoint to match MODEL_PROVIDER in .env and what Flink supports.
CREATE CONNECTION signal_model_conn
  WITH (
    'type' = 'openai',                                   -- VERIFY supported providers
    'endpoint' = 'https://api.openai.com/v1/chat/completions',
    'api-key' = '<MODEL_PROVIDER_API_KEY>'               -- inject securely; do not commit
  );

-- 2) Register the model as a callable Flink object.
CREATE MODEL signal_classifier
  INPUT  (prompt STRING)
  OUTPUT (response STRING)
  WITH (
    'provider' = 'openai',                               -- VERIFY key name
    'openai.connection' = 'signal_model_conn',
    'openai.model_version' = 'gpt-4o-mini',              -- any fast, cheap chat model
    'openai.system_prompt' =
      'You classify news/HN items as GTM signals for a senior AI-native B2B-SaaS operator (Alex). '
      'Relevant = AI-native GTM/sales/CS hiring or leadership; funding/exec-change/product-launch/layoff '
      'at AI-infra or GTM-tooling cos; NYC AI ecosystem moves; his stack (Anthropic, Notion, Supabase, '
      'Confluent, Linear, PostHog, Vercel); or the "agents on streaming data" / "replace SaaS with AI apps" '
      'theses. Not relevant = generic consumer/crypto/hardware with no AI-GTM tie. '
      'Return ONLY compact JSON: {"relevant":bool,"signal_type":"funding|exec_change|product_launch|layoff|hiring|event|thesis|other","company":str_or_null,"why":str,"confidence":0..1}.'
  );

-- 3) Sink table (auto-creates the gtm_signals topic if your env is set to do so; else create it first).
CREATE TABLE gtm_signals (
    id STRING,
    title STRING,
    url STRING,
    source STRING,
    classification STRING,   -- the raw JSON from the model
    ts TIMESTAMP_LTZ(3)
);

-- 4) The continuous job: classify every incoming raw_signals row, keep only the relevant ones.
INSERT INTO gtm_signals
SELECT
    r.id,
    r.title,
    r.url,
    r.source,
    p.response AS classification,
    r.ts
FROM raw_signals AS r,
  LATERAL TABLE(
    ML_PREDICT(
      'signal_classifier',
      -- the per-event prompt: hand the model the item to judge
      'ITEM:\n' || 'title: ' || COALESCE(r.title,'') || '\n'
                || 'source: ' || COALESCE(r.source,'') || '\n'
                || 'text: ' || COALESCE(r.text,'')
    )
  ) AS p(response)
-- keep only rows the model marked relevant (cheap JSON check; refine as needed)
WHERE p.response LIKE '%"relevant":true%';

-- Teardown after a demo session (stop billing): DROP the INSERT statement in the Console,
-- and DROP TABLE gtm_signals / DROP MODEL signal_classifier / DROP CONNECTION signal_model_conn if done.
