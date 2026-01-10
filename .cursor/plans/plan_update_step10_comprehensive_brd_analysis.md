# Plan Update: Step 10 - Comprehensive BRD Analysis for Query Expansion

**Date**: Based on implementation learnings from Step 10 demo  
**Related Step**: Step 10 (Query Expansion)  
**Status**: Plan Updated

---

## Problem Identified

During Step 10 implementation review, it was discovered that the query expansion was only using the BRD executive summary (~150 chars) instead of the full BRD structure. This resulted in:

- Only 10-20% of BRD details being used for query generation
- Insufficient context retrieval for comprehensive engineering planning
- Generated queries missing coverage of business objectives and functional requirements

## Root Cause

The original plan specified "generate queries from BRD" but did not explicitly require:
- Using the FULL BRD structure (all objectives, requirements)
- Ensuring comprehensive coverage of all BRD components
- Dynamic query count based on BRD complexity

## Plan Updates Made

### 1. Step 10: Enhanced Query Generation Requirements

**Updated Requirements**:
- **CRITICAL**: Query generation MUST analyze COMPLETE BRD structure, not just executive summary
- Must extract and use:
  * All business objectives (with priorities and success criteria)
  * All functional requirements (with descriptions and priorities)
  * Executive summary (for overall context)
  * Optional: non-functional requirements, project scope

**Query Generation Strategy**:
- Generate 1-2 queries per business objective
- Generate 1 query per functional requirement
- Generate 2-3 architecture/pattern queries
- Dynamic query count: `min(rag_query_count, num_objectives + num_requirements + 3)`
- Example: BRD with 4 objectives + 5 requirements → 7-12 queries (limited by config)

**Reference BRD**: Use `sample_inputs/brds/demo_step10_query_expansion.json` as template
- This BRD has 4 business objectives + 5 functional requirements
- Implementation should verify queries cover ALL components

### 2. Step 1: Updated Default Configuration Values

**Changes**:
- `rag_top_k`: Default changed from `5` → `15` (to retrieve more chunks for comprehensive planning)
- `rag_query_count`: Default changed from `3` → `7` (to better cover BRDs with multiple objectives/requirements)

**Rationale**: Original defaults were too low for comprehensive planning. New defaults support BRDs with 4+ objectives and 5+ requirements.

### 3. Step 12: Enhanced Context Handling

**Added Requirements**:
- Handle larger context (15-20 chunks vs original 5)
- Format chunks with source citations
- Prioritize chunks if context is too large
- Ensure prompt stays within token limits
- Track which chunks were used in plan generation

**Rationale**: With enhanced query expansion, more chunks are retrieved. PlannerAgent must handle this effectively.

---

## Impact on Implementation

### For Step 10 (Current Step)

**If Step 10 is already implemented**, the Build Agent should:

1. **Review current implementation**:
   - Check if `_generate_expanded_queries()` uses full BRD or just summary
   - Verify query generation covers all BRD components
   - Test with `sample_inputs/brds/demo_step10_query_expansion.json`

2. **Update if needed**:
   - Modify query generation to use full BRD structure
   - Update prompt to explicitly instruct LLM to cover all objectives/requirements
   - Add logging to track which BRD component each query maps to
   - Update test criteria to verify comprehensive coverage

3. **Verify**:
   - Load sample BRD (4 objectives + 5 requirements)
   - Verify generated queries cover ALL 4 objectives
   - Verify generated queries cover ALL 5 requirements
   - Verify query count is appropriate (7-12 queries)

### For Step 1 (Already Complete)

**If Step 1 is already implemented**, the Build Agent should:

1. **Update default values** in `src/brd_agent/config.py`:
   - Change `rag_top_k` default from `5` to `15`
   - Change `rag_query_count` default from `3` to `7`
   - Update docstrings to explain rationale

2. **Note**: This is a configuration change only. No code logic changes needed.

### For Step 12 (Future Step)

**When implementing Step 12**, the Build Agent should:

1. **Follow updated requirements**:
   - Handle 15-20 chunks (not just 5)
   - Format chunks with source citations
   - Add context prioritization if needed
   - Ensure token limit compliance

---

## Test Criteria Updates

### Step 10 Test Criteria (Updated)

1. **Query Generation Coverage**:
   - Load `sample_inputs/brds/demo_step10_query_expansion.json`
   - Verify queries cover ALL 4 business objectives
   - Verify queries cover ALL 5 functional requirements
   - Verify query count is 7-12 (limited by config)

2. **Retrieval Quality**:
   - Verify 10-15 unique chunks retrieved (after deduplication)
   - Verify chunks cover 3-5 different source files
   - Verify chunks are relevant to BRD topics
   - Compare with basic retrieval (should show improvement)

3. **Comprehensive Coverage**:
   - No single source file should dominate (>50% of chunks)
   - Chunks should cover authentication, search, API, configuration, user management topics

---

## Key Learnings

1. **Explicit Requirements**: Plans must explicitly specify "use FULL BRD structure" not just "use BRD"
2. **Reference Examples**: Using actual BRD files as templates ensures concrete, testable requirements
3. **Iterative Planning**: Learning from implementation and updating plans is expected and valuable
4. **Configuration Defaults**: Default values should support realistic use cases (BRDs with multiple objectives/requirements)

---

## Next Steps

1. **Build Agent**: Review Step 10 implementation against updated requirements
2. **Build Agent**: Update Step 1 config defaults if not already done
3. **Build Agent**: When implementing Step 12, follow updated context handling requirements
4. **Planning Agent**: Continue monitoring implementation for additional learnings

---

## Questions?

If the Build Agent has questions about these updates, please refer to:
- Updated Step 10 in `implementation_plan_for_incremental_feature_85db7573.plan.md`
- Reference BRD: `sample_inputs/brds/demo_step10_query_expansion.json`
- This note for context on why changes were made

