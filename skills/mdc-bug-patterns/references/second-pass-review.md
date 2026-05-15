# Second-Pass Subagent Review

After Pass 3 (the auditor's deep semantic review) produces findings, **Pass 3.5** dispatches an independent **subagent** to re-verify each finding against the actual source code. Its verdict and rationale are merged into the finding JSON and surfaced in the Excel as `子代理复核结论` + `子代理复核依据`.

The point: the auditor agent and the second-pass agent reach the same conclusion through independent reads of the same code. Disagreement is a signal — either the original finding is hallucinated/over-reaching, or the second-pass agent missed context. Either way the human reviewer sees both views before signing off.

> **Iron rule of Pass 3.5:** the subagent must NOT see the auditor's reasoning chain. It only receives the structured finding (template, location, summary, evidence, FP filters claimed, fix suggestions) and is required to *independently* read the code and re-derive the verdict.

## When to Use

- **Always**, after every Pass 3 batch, before producing the final Excel.
- May be skipped only when the user explicitly asks for "no second pass" (e.g. exploratory dry runs).
- Suppressed candidates and audit gaps may also be reviewed if the user wants to double-check that suppressions were correct; default is to review confirmed findings only (high + medium).

## Subagent Choice

Use the `Task` tool with `subagent_type="explore"` (read-only) or `"generalPurpose"`. Read-only is safer because the subagent must not modify files; `explore` is preferred when available.

Set `readonly=true` when calling `generalPurpose`.

## Batching

Do not dispatch one subagent per finding — that wastes context. Batch findings in groups of **5–10** per subagent invocation (small enough that the subagent can read the source for each, large enough to amortise the bootstrapping cost).

Findings should NOT be batched across files when the files are very different — group by file or by directory when possible to share file reads.

## Subagent Prompt Template

Copy-paste this template into your `Task` invocation. Replace `{{FINDINGS_JSON}}` with the JSON array of findings you are reviewing. Replace `{{REPO_PATH}}` with the codebase root (so the subagent can read source files).

```
You are an independent second-pass reviewer for a C/C++ static-analysis-style
audit. You will be given a batch of FINDINGS produced by a first-pass agent.
Your job is to INDEPENDENTLY verify each finding by reading the actual source
code, and emit a structured verdict.

YOU MUST NOT TRUST the first-pass agent's reasoning. You must re-derive the
conclusion yourself from the source code. The first-pass agent may have:
  - Hallucinated line numbers or code excerpts.
  - Falsely claimed to have ruled out a false-positive filter.
  - Missed an additional false-positive filter that DOES apply.
  - Mis-traced data flow, ownership, lock-set, or thread affinity.
  - Mis-classified the severity or template.

Repository root: {{REPO_PATH}}
Findings to review (JSON array):
{{FINDINGS_JSON}}

Procedure for EACH finding:

1. Read the file at finding.location.file. Read at least 30 lines around
   finding.location.line, plus the enclosing function and class declaration
   if member state is involved.
2. For each item in finding.required_evidence: confirm that the cited
   <file:line> actually contains code that matches the excerpt. Note
   verbatim if it does NOT.
3. For each filter id listed in finding.false_positive_filters_ruled_out:
   independently verify that the filter actually does NOT apply (i.e. the
   first-pass agent was right to rule it out). Read the relevant source.
4. Independently apply the template's verification (the template id is
   finding.template_id; if you have access to the templates documentation,
   re-execute its verification checklist).
5. Look for ADDITIONAL false-positive filters the first-pass agent may have
   missed (e.g. fp.dead-code, fp.test-code, fp.generated-code, project-
   specific smart pointer wrappers, surrounding asserts that establish a
   precondition).
6. Decide a verdict for the finding:
     "agree"      — the bug is real; the evidence and FP-filter rule-out
                    are sound.
     "disagree"   — the finding is wrong; either the evidence does not
                    support it, or an applicable FP filter applies.
     "uncertain"  — you cannot decide within the bounded effort
                    (≤ ~5 minutes per finding); explain what you would
                    need to be sure.

OUTPUT FORMAT (strict JSON array, one element per finding, in the same
order as the input). Do NOT include any prose outside the JSON.

[
  {
    "id":          "<finding.id, copied verbatim>",
    "verdict":     "agree" | "disagree" | "uncertain",
    "rationale":   "1–3 sentences in Chinese explaining your verdict.",
    "evidence_check": {
      "all_cited_lines_exist":         true | false,
      "all_cited_lines_match_excerpts": true | false,
      "fp_filters_actually_ruled_out": true | false,
      "additional_fp_filters_found":   ["fp.xxx", ...]
    },
    "supporting_evidence": [
      "src/<file>:<line>  <code excerpt you read>",
      ...
    ]
  },
  ...
]

The output JSON will be merged with the original findings and written into
the final Chinese Excel report under the columns 子代理复核结论 (verdict)
and 子代理复核依据 (rationale + evidence_check + supporting_evidence).

Be terse, factual, and specific. Cite file:line for every claim.
```

## Verdict Schema

The subagent must emit one verdict object per finding, using the keys above. The merge script (`scripts/merge_second_pass.py`) attaches each verdict to the finding it reviews under `finding.second_pass_review`:

```json
{
  "second_pass_review": {
    "verdict": "agree" | "disagree" | "uncertain",
    "rationale": "...",
    "evidence_check": {
      "all_cited_lines_exist": true,
      "all_cited_lines_match_excerpts": true,
      "fp_filters_actually_ruled_out": true,
      "additional_fp_filters_found": []
    },
    "supporting_evidence": ["src/cache.cc:19  Buf* b = new Buf(64);", ...],
    "reviewed_at": "2026-05-14T15:32:00Z",
    "reviewer": "subagent:explore"
  }
}
```

## Common Failure Modes the Subagent Catches

| Failure mode | How the subagent catches it |
|---|---|
| Hallucinated line numbers (cited `cache.cc:88` but file only has 60 lines) | `evidence_check.all_cited_lines_exist == false` |
| Wrong code excerpt (line exists but code doesn't match) | `evidence_check.all_cited_lines_match_excerpts == false` |
| Falsely claimed `fp.ownership.smart-pointer` ruled out (the line below the `new` actually wraps it in `unique_ptr`) | `evidence_check.fp_filters_actually_ruled_out == false`; verdict `disagree` |
| Missed `fp.test-code` (file is `*_test.cc`) | `additional_fp_filters_found: ["fp.test-code"]`; verdict probably `disagree` |
| Missed `fp.generated-code` (file is `.pb.cc`) | same, with `fp.generated-code` |
| Race claimed but actually thread-affinity proof exists (e.g. `DCHECK_CALLED_ON_VALID_SEQUENCE`) | `additional_fp_filters_found: ["fp.concurrency.single-threaded"]`; verdict `disagree` |
| Confidence over-stated (deserves `medium` not `high`) | `verdict: agree` but rationale notes the confidence concern |
| Real bug with weak evidence (auditor cited too few lines) | `verdict: agree` but rationale lists additional confirming evidence |

## How to Drive the Subagent (for the calling agent)

```
1. Group findings into batches (~5-10 each).
2. For each batch:
     - Build the prompt by substituting {{REPO_PATH}} and {{FINDINGS_JSON}}.
     - Dispatch via the Task tool:
         subagent_type = "explore"  (or "generalPurpose" with readonly=true)
         description   = "Second-pass review batch N"
         prompt        = <filled template>
     - The subagent returns a JSON array of verdicts. Save it to
       `audit/verdicts-batchN.jsonl` (one JSON object per line).
3. After all batches finish, concatenate the verdict files and run:
     scripts/merge_second_pass.py \
         --findings findings.json \
         --verdicts verdicts.jsonl \
         --out findings_with_review.json
4. Render the final Excel:
     scripts/excel_helper.py \
         --bugs-file findings_with_review.json \
         --coverage  coverage.json \
         --repo X --scope Y --reviewer Z \
         --output bug_report.xlsx
```

If a finding has no verdict (subagent timed out, JSON malformed, etc.),
`merge_second_pass.py` records `verdict: "missing"` so the human
reviewer sees the gap explicitly rather than silently rendering an
"agree" cell.

## Quality Bar for Verdicts

- Every `disagree` MUST cite at least one piece of `supporting_evidence` that contradicts the original finding.
- Every `uncertain` MUST state in `rationale` what additional information would resolve it (so the human reviewer knows where to look).
- `evidence_check` flags must be honest. If you did not actually verify the cited lines, set the flag to `false`; do not optimistically mark `true`.
