# Consult note skeleton

One note per specialty variant (SPEC §6.8). A consultant is helpful but never more diagnostic than a competent colleague with the same information. Never name the diagnosis before the Chart holds the result that makes it clear.

- **id:** CN<nn>
- **specialty:** `REF.<SPECIALTY>`
- **variant:** 1 | 2 | 3
- **condition:** what the Chart must already hold, e.g. `{"released_any": ["L26"]}` or `{"finding_released": ["FND.<finding>"]}` (to count only some tests' reports: `{"finding_released": {"findings": ["FND.<finding>"], "from_tests": ["LAB.<test>"]}}`); empty for variant 1
- **origin:** `affected` (on the case's paths) or `rule` (the catalogue's generic note)

Note text, in this order:

1. What was asked and what we reviewed (the Chart so far, in one or two sentences).
2. Our assessment, limited to what the Chart supports.
3. Recommendations: tests to consider, a history to take, treatment to hold or start, as a list.
4. Follow-up: "Happy to review again with the results."
