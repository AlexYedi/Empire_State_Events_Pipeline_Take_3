#!/usr/bin/env python3
"""Integrity test for the data pack. Exits non-zero on the first failed assertion.

    python3 eval/check_answer_key.py

Checks: every answer-key span (fields, alt_spans, flags) equals its quote in the source
file; required schema keys are present; flags use the vocabulary; manifests match the files.
"""

import json
import os

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(rel):
    with open(os.path.join(PACK, rel), encoding="utf-8", newline="") as fh:
        return fh.read()


def main():
    schema = json.loads(read("schema/extracted_metrics.schema.json"))
    required_top = schema["required"]
    required_fields = schema["properties"]["fields"]["required"]
    required_metric = schema["$defs"]["metric"]["required"]
    vocab = set(schema["$defs"]["flag"]["properties"]["flag"]["enum"])
    checked = 0
    for key_file, upd_dir in (("answer_key/q2_2026_metrics.json", "updates/Q2_2026"),
                              ("answer_key/q3_2026_metrics.json", "updates/Q3_2026")):
        key = json.loads(read(key_file))
        assert len(key["companies"]) == 22, key_file
        manifest = json.loads(read(f"{upd_dir}/manifest.json"))
        listed = {m["file"] for m in manifest["updates"] if m["file"]}
        on_disk = {f"{upd_dir}/{f}" for f in os.listdir(os.path.join(PACK, upd_dir)) if f != "manifest.json"}
        assert listed == on_disk, (key_file, listed ^ on_disk)
        cache = {}
        for rec in key["companies"]:
            for k in required_top:
                assert k in rec, (rec["company_id"], k)
            for f in required_fields:
                fld = rec["fields"][f]
                for k in required_metric:
                    assert k in fld, (rec["company_id"], f, k)
                spans = []
                if fld["source_span"] is not None:
                    spans.append((fld["source_span"]["start"], fld["source_span"]["end"], fld["quote"]))
                spans += [(a["start"], a["end"], a["quote"]) for a in fld.get("alt_spans", [])]
                for s, e, q in spans:
                    text = cache.setdefault(fld["source_file"], read(fld["source_file"]))
                    assert text[s:e] == q, (key_file, rec["company_id"], f, text[s:e], q)
                    checked += 1
                if fld["value"] is None:
                    assert fld["source_span"] is None and fld["quote"] is None, (rec["company_id"], f)
            for fl in rec["flags"]:
                assert fl["flag"] in vocab, fl
                if fl["source_span"] is not None:
                    text = cache.setdefault(fl["source_file"], read(fl["source_file"]))
                    assert text[fl["source_span"]["start"]:fl["source_span"]["end"]] == fl["quote"], fl
                    checked += 1
    print(f"OK: {checked} spans equal their quotes; schema keys, flag vocabulary and manifests consistent.")


if __name__ == "__main__":
    main()
