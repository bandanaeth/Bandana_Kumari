# QC AUDIT REPORT — Bandana Task Bundle
**Date**: 2026-06-13  
**Task**: Rodriguez Quinceanera Event Supply Readiness Audit  
**Scope**: rubric.json, test_outputs.py, test_weights.json, prompt.txt, mock_data/  
**Verdict**: **NEEDS FIXES**

---

## EXECUTIVE SUMMARY

| Category | Status | Finding Count |
|----------|--------|---|
| **Prompt Quality** | ✅ PASS | 0 issues |
| **Mock Data** | ✅ PASS | 0 issues |
| **Rubric Schema** | ⚠️ MODERATE | 3 issues |
| **Test Suite (Channel A)** | ❌ MAJOR | 3 defects |
| **Test-Rubric Alignment** | ⚠️ MODERATE | 1 issue |
| **Weight Distribution** | ⚠️ MODERATE | 1 issue |

---

## PART A — PROMPT & DATA QUALITY

### A.1 Prompt Structure ✅ PASS

**Status**: Well-formed, decomposable, objective verification possible

**Prompt asks identified:**
1. **A1 (SHORTAGE)**: "Tell me what is actually short"
2. **A2 (COVERAGE)**: "What is already covered"
3. **A3 (APPROVAL GATE)**: "What needs my approval before I spend money or bother a vendor"
4. **A4 (STRUCTURE)**: "Bottom line up top"

**Two-Agent Test**: ✅ Two independent agents would reach identical conclusions
- Shortage → Measurable against mock data (48 required, 22 usable, 26 short)
- Coverage → Verifiable against expenses (catering $400, photography $350)
- Approval → Deterministic (quote $285 > threshold $250)
- Structure → Explicit instruction

**Completeness**: ✅ All asks explicit, no circular dependencies, no contradictions

---

### A.2 Mock Data Integrity ✅ PASS

**API Services**: 7 total (4 required + 3 distractor)
- google-calendar-api: events.csv, calendars.csv, event_attendees.csv ✅
- google-drive-api: files.csv, permissions.csv ✅
- gmail-api: messages.csv, drafts.csv, labels.csv ✅
- quickbooks-api: estimates.json, expenses.json, vendors.csv, customers.csv ✅
- outlook-api (distractor): contacts.csv, messages.csv ✅
- dropbox-api (distractor): files.csv, shared_links.csv ✅
- box-api (distractor): files.csv, folders.csv ✅

**Data Sufficiency**: All asks are answerable from mock data + artifacts
- A1 (shortage): ✅ inventory + damage + photo in mock_data + artifacts
- A2 (coverage): ✅ expenses.json + messages confirm catering/photography
- A3 (approval): ✅ estimates.json + AGENTS.md threshold rule
- A4 (structure): ✅ No data constraint

**Data Joinability**: ✅ Foreign keys validated
- events.csv → calendars.csv via calendar_id ✅
- event_attendees.csv → events.csv via event_id ✅
- estimates.json → customers.csv via CustomerRef ✅
- messages.csv → labels.csv via label_id ✅

---

## PART B — RUBRIC QUALITY

### B.1 Schema Compliance ⚠️ MODERATE

**Issue B1.1 — Missing Template Fields**

The template schema (from 04_Rubric_QC.md) requires:
```json
{
  "number": "R<N>",
  "criterion": "...",
  "is_positive": boolean,
  "type": enum,
  "evaluation_target": enum,
  "importance": enum,
  "score": integer
}
```

**Current rubric.json uses:**
```json
{
  "id": "r_shortage_identification",        // ← "id", not "number"
  "title": "...",                           // ← "title" not in template
  "description": "...",                     // ← "description" not in template
  "is_positive": true,                      // ✅ matches
  "score": 5,                               // ✅ matches
  "judge_prompt": "..."                     // ← "judge_prompt" not in template
}
```

**Missing fields**:
- `number` (present as `id`)
- `type` (should be one of: task completion | instruction following | factuality | tool use | agent behavior | safety)
- `evaluation_target` (should be: state_change | user_facing_message | trajectory | final_answer)
- `importance` (should be: critically_important | important)

**Severity**: MODERATE  
**Fix**: Add required fields to all 18 criteria or adopt a documented custom schema

---

### B.2 Phrasing Rule Audit ✅ PASS (7/7 rules)

**Rule 1 (Punctuation)**: ✅ No em-dashes, brackets, or placeholders
**Rule 2 (Banned qualifiers)**: ✅ No "at least", "approximately", "clearly", "correctly", etc.
**Rule 3 (Atomicity)**: ⚠️ SEE BELOW
**Rule 4+ (Self-containment, coherence)**: ✅ All criteria self-contained

**Atomicity Issue (Rule 3):**

**Criterion r_coverage_confirmation violates atomicity**:
```
"Agent explicitly confirms what IS covered: Modern Elegance theme approved, 
Gold/Ivory/Burgundy palette confirmed, catering and photography deposits already paid."
```

This checks **4 independent facts**:
1. Modern Elegance theme is approved
2. Gold/Ivory/Burgundy palette is confirmed
3. Catering deposit is paid
4. Photography deposit is paid

**Severity**: MODERATE  
**Why**: Single criterion with 4 conjunctions can fail/pass partially, creating ambiguity for scorers  
**Fix**: Split into 4 atomic criteria (r_coverage_theme, r_coverage_palette, r_coverage_catering, r_coverage_photography)

---

### B.3 Score Distribution ✅ PASS

- **Valid scores only**: All criteria use {1, 3, 5} ✅
- **All positive**: 18 positive, 0 negative (appropriate for this rubric) ✅
- **Score frequency**:
  - Score 5 (critical): 7 criteria (39%) ✅
  - Score 3 (important): 7 criteria (39%) ✅
  - Score 1 (minor): 4 criteria (22%) ✅

---

## PART C — TEST SUITE QUALITY (Channel A)

### C.1 Defect 1 — Inverted Mutation-Guard Assertions ❌ MAJOR

Convention B requires: **All assertions phrased POSITIVELY**. Traps are validated via negative weights, NEVER via negated assertions.

**Violation 1: test_no_cancelled_helper_used() [line ~195]**
```python
def test_no_cancelled_helper_used():
    ...
    assert cancelled is not None, "Cancelled event exists"  # ← DEFECT 1
    assert cancelled['status'] == 'cancelled'              # OK - positive
```
**Violation**: `assert ... is not None` — passes when finding is NOT None (inverted logic)

**Violation 2: test_distractor_outlook_messages_zero_rodriguez_content() [line ~207]**
```python
for msg in messages:
    assert 'rodriguez' not in msg.get('body', '').lower()  # ← DEFECT 1
    assert 'napkin' not in msg.get('body', '').lower()     # ← DEFECT 1
```
**Violation**: `assert ... not in` — two instances, both inverted

**Violation 3: test_distractor_dropbox_no_current_event() [line ~217]**
```python
recent_count = sum(1 for f in files if '2026-10' in f.get('client_modified', ''))
assert recent_count == 0, f"Dropbox contains {recent_count} recent files (should be 0)"  # ← DEFECT 1
```
**Violation**: `assert count == 0` — passes when count IS 0 (inverted assertion of "no recent files")

**Total Defect 1 count**: **4 violations** (across 3 test functions)  
**Severity**: MAJOR  
**Why**: Convention B violations are structural defects that compromise scorer reliability  
**Fix**: Rewrite assertions to be positive:
  - Instead of `assert cancelled is not None`, use `assert cancelled is not None and cancelled['status'] == 'cancelled'` (trap exists)
  - Instead of `assert 'rodriguez' not in body`, use `assert 'rodriguez' in body  # trap check (assert trap is present, weight it negatively)`
  - Instead of `assert recent_count == 0`, invert to `assert recent_count > 0  # trap check`

---

### C.2 Defect 4 — Penalty Overlap / Double Penalties ⚠️ MODERATE

Check for negative-weight test stack on same endpoint.

**Google Calendar API negative tests**:
- test_no_cancelled_helper_used: weight **-3**
- test_no_tentative_focal_event_used: weight **-3**
- test_no_wrong_period_event_used: weight **-1**
- **Total**: 3 + 3 + 1 = **-7** (exceeds cap of -5)

**Severity**: MODERATE  
**Why**: §2.7 rule allows max ONE -5 test per endpoint; stacking three tests totaling -7 is over-penalization  
**Fix**: Consolidate trap validation into fewer, higher-weight tests:
  - Combine "no_cancelled_helper_used" + "no_tentative_focal_event_used" into single -5 test
  - Reduce "no_wrong_period_event_used" to -1 or merge

**QuickBooks API negative tests**: None detected ✅

**Distractor API penalties**:
- test_distractor_outlook_messages_zero_rodriguez_content: **-5** ✅
- test_distractor_dropbox_no_current_event: **-3** ✅
- No overlap ✅

---

### C.3 Test Coverage vs Rubric ✅ PASS

| Rubric Criterion | Covered by Tests | Status |
|---|---|---|
| r_shortage_identification | test_storage_assessment_* (28 usable, 8 damaged) | ✅ |
| r_shortage_math_justification | test_inventory_current_file_exists, test_current_inventory_modified_after_stale | ✅ |
| r_temporal_revision_handling | test_inventory_stale_v20_exists, test_current_inventory_modified_after_stale | ✅ |
| r_photo_evidence_cross_ref | test_storage_assessment_28_usable, test_storage_assessment_8_damaged | ✅ |
| r_no_substitution_constraint | test_client_theme_approval_content | ✅ |
| r_current_quote_identification | test_current_quote_exists, test_stale_quote_pricing | ✅ |
| r_approval_threshold_trigger | (rubric-only, no pytest check) | ⚠️ Indirect |
| r_no_vendor_contact_without_approval | (rubric-only, no pytest check) | ⚠️ Indirect |
| r_budget_availability_confirmation | test_budget_internal_note_400_remaining, test_catering_expense_already_paid, test_photography_expense_already_paid | ✅ |
| r_helper_availability_constraint | test_sofia_helper_window_345_to_615, test_setup_window_1000_to_1200 | ✅ |
| r_borrowed_item_risk_assessment | test_borrowed_item_email_exists, test_borrowed_item_3pm_constraint | ✅ |
| r_coverage_confirmation | test_catering_expense_already_paid, test_photography_expense_already_paid | ✅ Partial |
| r_bottom_line_first | (rubric-only) | ⚠️ Indirect |
| r_no_client_overshare | (rubric-only) | ⚠️ Indirect |
| r_quote_expiry_deadline_noted | test_current_quote_expiry_date | ✅ |
| r_no_hallucination_vendor_contact | (rubric-only) | ⚠️ Indirect |
| r_no_hallucination_conflict_resolution | test_storage_assessment_28_usable, test_storage_assessment_8_damaged | ✅ Implicit |
| r_communication_clarity | (rubric-only) | ⚠️ Indirect |

**Assessment**: Channel A (pytest) and Channel B (rubric) have appropriate division:
- Channel A validates hard facts: file existence, exact values, FK consistency
- Channel B validates reasoning, tone, hallucination-freedom, structure

✅ **NO OVERLAP** between rubric criteria and test cases (good separation)

---

## PART D — WEIGHT DISTRIBUTION

### D.1 Weight Scale Compliance ✅ PASS

**Valid scale only**: {-5, -3, -1, 1, 3, 5}
- All 38 tests use valid weights ✅
- No weights of 0, ±2, ±4, or other values ✅

### D.2 Weight Summary ✅ PASS

| Metric | Value | Status |
|--------|-------|--------|
| Total tests | 38 | ✅ |
| Positive tests | 33 | ✅ |
| Negative tests | 5 | ✅ |
| Total positive weight | +98 | ✅ |
| Total negative weight | -12 | ✅ |
| Net weight | +86 | ✅ |
| Pass-all threshold | true | ✅ |

**Distribution**: Heavy positive weighting (86:12 ratio ≈ 7:1) appropriate for this task

---

## SUMMARY OF FINDINGS

### ❌ MAJOR ISSUES (1)
1. **Defect 1 — Inverted Assertions**: 4 violations in negative-weight tests violate Convention B

### ⚠️ MODERATE ISSUES (3)
1. **Schema Incompleteness**: Missing required fields (number, type, evaluation_target, importance)
2. **Atomicity Violation**: r_coverage_confirmation checks 4 independent facts
3. **Penalty Overlap**: Google Calendar API negative tests total -7 (exceeds -5 cap)

### Minor Issues (0)
None

---

## VERDICT: **NEEDS FIXES**

**Path to Push Ready**:

### Fix 1 — Rewrite Negative-Weight Test Assertions (MAJOR)
File: `test_outputs.py`

**Current (WRONG)**:
```python
def test_no_cancelled_helper_used():
    cancelled = next((e for e in events if e['id'] == 'evt_cancelled_helper_001'), None)
    assert cancelled is not None, "Cancelled event exists"  # ← DEFECT
```

**Corrected (POSITIVE)**:
```python
def test_trap_cancelled_helper_present():
    """TRAP: Cancelled helper event must exist in data"""
    cancelled = next((e for e in events if e['id'] == 'evt_cancelled_helper_001'), None)
    assert cancelled is not None and cancelled['status'] == 'cancelled'
```

Same for:
- test_no_tentative_focal_event_used() → rewrite with positive assertion
- test_distractor_outlook_messages_zero_rodriguez_content() → change `assert 'rodriguez' not in` to `assert 'rodriguez' in` (trap check)
- test_distractor_dropbox_no_current_event() → change `assert count == 0` to `assert count > 0` (trap check)

---

### Fix 2 — Add Required Schema Fields to rubric.json (MODERATE)

Add to each criterion:
```json
{
  "number": "R<sequential>",
  "type": "factuality_and_hallucination",  // or task_completion, etc.
  "evaluation_target": "user_facing_message",  // or final_answer, etc.
  "importance": "critically_important"  // or important
}
```

---

### Fix 3 — Split Atomicity-Violating Criterion (MODERATE)

Replace `r_coverage_confirmation` with 4 separate criteria:
1. r_coverage_theme_approved (score: 1)
2. r_coverage_palette_confirmed (score: 1)
3. r_coverage_catering_paid (score: 1)
4. r_coverage_photography_paid (score: 1)

Update test_weights.json to add 4 new entries (if tests support them).

---

### Fix 4 — Consolidate Overlapping Negative Weights (MODERATE)

Merge google-calendar-api trap tests:
- Combine test_no_cancelled_helper_used + test_no_tentative_focal_event_used → single test_trap_invalid_events with weight -5
- Keep test_no_wrong_period_event_used as -1

Update test_weights.json accordingly.

---

## RECOMMENDATIONS FOR NEXT QC RUN

1. Run Prompt-Input-Mock-QC after fixes (prerequisite: this QC must pass)
2. Run Rubric QC (full Phase 0-10) after schema fixes
3. Run Test Outputs QC with updated assertions
4. Validate golden_steer_flow.md alignment with corrected rubric

---

**Report prepared**: 2026-06-13  
**Auditor role**: Skeptical industry veteran, 15+ years in evaluation systems  
**Confidence**: High (all findings traced to schema rules and Convention B)
