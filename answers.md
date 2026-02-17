> **Note:** This documentation was enhanced with AI assistance to improve readability and presentation.

---

### Extraction Pipeline for H&P

#### Stage 1: Document Preprocessing
**Input:** Raw H&P document PDF

**Process:**
1. Extract text from the document using appropriate libraries (PDFPlumber for PDFs )
2. Identify document sections using common headers such as:
   - Chief Complaint
   - History of Present Illness (HPI)
   - Past Medical History (PMH)
   - Medications
   - Allergies
   - Physical Examination
   - Vital Signs
   - Laboratory Results
   - Assessment and Plan
3. Segment text by section for targeted extraction, improving accuracy by focusing on relevant portions

#### Stage 2: Vital Signs Extraction
**Target Data:** Blood pressure, heart rate, respiratory rate, temperature, oxygen saturation

**Method A: Pattern Matching (for Structured Reports)**

When vital signs are documented in standardized formats, regular expression patterns can reliably extract:
- **Blood Pressure:** Patterns like "BP: 120/80" or "Blood Pressure 85/60"
- **Heart Rate:** "HR: 110 bpm" or "Pulse 95"
- **Respiratory Rate:** "RR: 24" or "Respirations 22/min"
- **Temperature:** "Temp: 102.5 F" or "T: 38.6 C" (with automatic conversion to Fahrenheit)
- **Oxygen Saturation:** "SpO2: 88%" or "O2 Sat 92%"

Each extracted value includes:
- The parameter name (standardized)
- The numeric value
- The unit of measurement
- LOINC code for interoperability
- Timestamp (extracted from nearby context or document metadata)

**Method B: LLM-Based Extraction (for Unstructured Narratives)**

When vital signs are embedded in narrative text (e.g., "Patient was found to be hypotensive with blood pressure in the 80s"), an LLM is prompted to:
- Identify all vital signs mentioned in the text
- Extract the values and units
- Provide context for each finding
- Return structured JSON output

The LLM approach handles variations in documentation style, abbreviations, and narrative descriptions that regex patterns cannot reliably capture.

**Hybrid Approach:** Start with pattern matching for efficiency, fall back to LLM for sections where patterns fail to extract expected data.

#### Stage 3: Laboratory Results Extraction
**Target Data:** WBC count, blood cultures, platelets, creatinine, liver enzymes, ABG values

**Extraction Strategy:**

**Structured Lab Sections:**
- Use regex patterns to extract common labs with their values, units, and flags
- **WBC Count:** "WBC: 18.5" → extract value, compare to reference range (4.0-11.0), assign "high/normal/low" flag
- **Blood Cultures:** "Blood Culture: positive" → extract result status, look for organism name in nearby text (e.g., "grew Staphylococcus aureus")
- **Platelet Count:** "Platelets: 95" → extract value, flag as low if <150
- **Creatinine:** "Cr: 2.1" → extract value, flag as high if >1.3

**Critical Details:**
- Capture reference ranges when provided
- Extract organisms for positive cultures
- Note whether results are pending vs. finalized
- Map to LOINC codes for standardization

**Unstructured Lab Mentions:**
For labs described narratively, use LLM extraction with explicit instructions to identify lab names, values, units, and clinical interpretation.

#### Stage 4: Clinical Findings Extraction
**Target Data:** Mental status, hemodynamic stability, respiratory status, infection evidence, organ dysfunction

**USE LLM:**
Clinical findings are often documented as narrative assessments rather than discrete data points. Examples:
- "Patient is alert and oriented to person, place, and time" → Mental status: normal
- "Appears ill and lethargic, difficult to arouse" → Altered mental status: present, severe
- "Requiring norepinephrine to maintain blood pressure" → Hemodynamic instability: present, vasopressor-dependent

**LLM Extraction Approach:**
Prompt the LLM to extract:
1. Mental status findings (normal, confused, altered, GCS score)
2. Signs of hemodynamic instability (hypotension, shock, vasopressor use)
3. Respiratory findings (tachypnea, hypoxemia, oxygen requirement)
4. Evidence of infection (fever, source identified, infection suspected)
5. End organ dysfunction (renal failure, hepatic dysfunction, cardiac ischemia)

For each finding, capture:
- Whether it's present (true/false)
- Severity if applicable
- Supporting evidence (quotes from text)
- SNOMED CT codes when possible

#### Stage 5: Treatment/Intervention Extraction
**Target Data:** IV fluids, vasopressors, oxygen therapy, mechanical ventilation, antibiotics

**Pattern-Based Detection:**
- **IV Fluids:** Search for mentions of "IV fluids," "IV hydration," "Normal Saline," "Lactated Ringers"
- **Vasopressors:** Look for specific drug names (norepinephrine, epinephrine, vasopressin, dopamine)
- **Oxygen Therapy:** Extract flow rates from patterns like "4L O2 via nasal cannula"
- **Mechanical Ventilation:** Detect keywords like "intubated," "mechanical ventilation," "ventilator"

**Rationale:** Treatments are often documented with specific terminology, making pattern matching effective. However, LLM can supplement by identifying interventions described in procedural notes.

### Complete Extraction Workflow

**Step-by-step process:**
1. Load the H&P document and extract raw text
2. Segment document into sections using header detection
3. Extract vital signs (pattern matching first, LLM fallback)
4. Extract laboratory results (pattern matching with organism detection)
5. Extract clinical findings (primarily LLM-based)
6. Extract treatments and interventions (pattern matching)
7. Extract patient metadata (MRN, encounter ID, dates)
8. Combine all extracted data into a unified structured format
9. Validate extracted values for physiologic plausibility
10. Return structured JSON output ready for normalization

---

## 2. How to Structure the Data Before Applying Policy Logic

### Data Structuring Strategy

The extracted raw data must be transformed into a **standardized clinical data model** that aligns with the MCG schema's matching conditions. This normalization process ensures consistency and enables reliable matching,
### Principles of Data Structuring

#### 1. Standardized Parameter Naming
**Challenge:** Clinical documents use various terms for the same measurement (e.g., "BP," "Blood Pressure," "B.P.")

**Solution:** Map all variations to a single standardized name:
- "BP," "Blood Pressure," "B.P." → `systolic_blood_pressure` and `diastolic_blood_pressure`
- "HR," "Pulse," "Heart Rate" → `heart_rate`
- "RR," "Respirations" → `respiratory_rate`
- "Temp," "T," "Temperature" → `temperature`
- "SpO2," "O2 Sat" → `oxygen_saturation`

This ensures the matching logic always looks for the same parameter name regardless of how it was documented.

#### 2. Unit Normalization
**Challenge:** Different documents may use different units (Celsius vs. Fahrenheit, different lab units)

**Solution:** Convert all measurements to standard units:
- **Temperature:** Always convert to Fahrenheit for consistency
- **Blood Pressure:** Always mmHg
- **Lab Values:** Use LOINC-specified standard units (e.g., WBC in 10³/µL)

This allows direct numeric comparison without unit conversion during matching.

#### 3. Medical Coding Integration

**Codes Added:**
- **LOINC codes** for all vitals and laboratory values
  - Enables precise identification of what was measured
  - Example: `8480-6` for systolic blood pressure
- **SNOMED CT codes** for clinical findings and diagnoses
  - Standardizes disease/finding terminology
  - Example: `45007003` for hypotension
- **ICD-10 codes** for diagnoses
  - Links to billing and diagnostic systems
  - Example: `I10` for hypertension, `A41.9` for sepsis

#### 4. Flag Calculation
**Purpose:** Pre-compute whether values are abnormal to simplify matching logic

**Process:**
For each vital sign or lab value, compare against normal reference ranges and assign flags:
- **Low:** Below normal range
- **Normal:** Within normal range
- **High:** Above normal range

**Examples:**
- Systolic BP 85 mmHg → Flag: "low" (normal range: 90-140)
- Heart rate 115 bpm → Flag: "high" (normal range: 60-100)
- WBC 18.5 → Flag: "high" (normal range: 4.0-11.0)

This allows matching conditions to simply check: "if systolic_blood_pressure flag == 'low'" rather than computing the comparison during matching.

#### 5. Timestamp Preservation
**Importance:** Clinical decisions often depend on temporal relationships

**Approach:**
- Capture timestamp for every data point when available
- If no explicit timestamp, use document creation time as proxy
- Enables temporal logic like "persists despite observation care"

#### 6. Derived Value Calculation
**Purpose:** Some MCG criteria reference calculated values not directly documented

**Key Derived Values:**

**Shock Index (HR / SBP):**
- Indicates hemodynamic instability
- Normal: <1.0, Abnormal: >1.0
- Example: HR 115 / SBP 85 = 1.35 (HIGH)

**Mean Arterial Pressure ((SBP + 2×DBP) / 3):**
- Better indicator of perfusion than SBP alone
- Normal: >65 mmHg
- Example: (85 + 2×55) / 3 = 63 mmHg (LOW)

These are calculated once during structuring rather than repeatedly during matching.

#### 7. Clinical Finding Generation
**Purpose:** Translate quantitative abnormalities into clinical concepts

**Process:**
Automatically generate clinical finding entries based on vital sign/lab abnormalities:

**From Vital Signs:**
- SBP <90 → Generate finding: "hypotension" (present: true)
- HR >100 → Generate finding: "tachycardia" (present: true)
- RR >20 → Generate finding: "tachypnea" (present: true)
- SpO2 <90 → Generate finding: "hypoxemia" (present: true)
- Temp >100.4°F → Generate finding: "fever" (present: true)

**From Lab Values:**
- Positive blood culture → Generate finding: "bacteremia" (present: true)
- Platelets <150 → Generate finding: "thrombocytopenia" (present: true)
- Creatinine >1.3 → Generate finding: "renal_dysfunction" (present: true)


### Structured Data Model Overview

The final structured format organizes data into seven main categories:

#### Category 1: Patient/Encounter Metadata
- Patient ID (MRN)
- Encounter ID
- Extraction timestamp
- Source document reference

#### Category 2: Vital Signs
Each vital sign entry includes:
- Standardized parameter name
- Numeric value
- Unit of measurement
- Timestamp
- LOINC code
- Abnormality flag (high/low/normal)

#### Category 3: Laboratory Results
Each lab result includes:
- Standardized test name
- Numeric value or categorical result (positive/negative)
- Unit of measurement
- Timestamp
- LOINC code
- Abnormality flag
- Reference range
- Special fields (e.g., organism for cultures)

#### Category 4: Clinical Assessments
Structured assessments like:
- Glasgow Coma Scale
- Mental status evaluation
- Pain scores
Each with values, timestamps, and codes

#### Category 5: Clinical Findings
Boolean or descriptive findings:
- Finding name (standardized)
- Present (true/false)
- Supporting evidence (text quote)
- SNOMED CT code
- Timestamp

#### Category 6: Treatments/Interventions
Active treatments:
- Treatment type
- Active status (true/false)
- Details (dosage, delivery method)
- Timestamp

#### Category 7: Derived Values
Calculated clinical indicators:
- Parameter name
- Calculated value
- Formula used
- Timestamp
- Abnormality flag

### Example Structured Output

Example clinical scenario:

**Vital Signs Section:**
- Systolic BP: 85 mmHg (flag: low, LOINC: 8480-6)
- Heart rate: 115 bpm (flag: high, LOINC: 8867-4)
- Respiratory rate: 24 /min (flag: high, LOINC: 9279-1)
- Temperature: 102.5°F (flag: high, LOINC: 8310-5)
- Oxygen saturation: 88% (flag: low, LOINC: 59408-5)

**Laboratory Results Section:**
- WBC: 18.5 10³/µL (flag: high, LOINC: 6690-2)
- Blood culture performed: true
- Blood culture result: positive, organism: S. aureus
- Platelets: 95 10³/µL (flag: low, LOINC: 777-3)
- Creatinine: 2.1 mg/dL (flag: high, LOINC: 2160-0)

**Clinical Findings Section:**
- Hypotension: present (SNOMED: 45007003)
- Tachycardia: present (SNOMED: 3424008)
- Tachypnea: present (SNOMED: 271823003)
- Hypoxemia: present (SNOMED: 389086002)
- Fever: present (SNOMED: 386661006)
- Bacteremia: present
- Altered mental status: absent

**Derived Values Section:**
- Shock index: 1.35 (flag: high, calculation: HR/SBP)
- Mean arterial pressure: 63 mmHg (flag: low, calculation: (SBP+2×DBP)/3)

**Treatments Section:**
- IV fluids: active, 2L NS bolus
- Oxygen therapy: active, 4L via nasal cannula

This structured format is now ready for matching against MCG criteria.

---

## 3. Assumptions Made in Implementation

### Clinical Assumptions

#### 1. **Standard Clinical Thresholds Apply to All Adult Patients**

**Assumption:** Use universally accepted thresholds for abnormal vital signs - EXAMPLES:
- Hypotension: SBP < 90 mmHg or MAP < 65 mmHg
- Tachycardia: HR > 100 bpm
- Tachypnea: RR > 20 breaths/min
- Hypoxemia: SpO2 < 90%
- Fever: Temperature > 100.4°F (38°C)
- Hypothermia: Temperature < 95°F (35°C)


**Limitation:** Does not account for patient-specific variations:
- Pediatric patients have different normal ranges
- Elderly patients may have different baselines
- Chronic conditions (e.g., COPD patients with baseline low SpO2)
- Pregnancy alters normal vital sign ranges

**Mitigation:** Could be enhanced by adding age/condition-specific logic, but this requires additional patient demographic data.

---

#### 2. **Most Recent Values Are Most Clinically Relevant**

**Assumption:** When multiple measurements exist for the same parameter, use the most recent value for admission decision matching.

**Justification:** Admission decisions are typically based on the patient's current clinical status at time of evaluation, not historical values.

**Example:** If blood pressure was 120/80 at triage but 85/55 at physician evaluation 2 hours later, use the 85/55 value.

**Limitation:** Does not capture trends (improving vs. worsening). For criteria like "persists despite observation care," temporal trends are relevant.

**Enhancement:** Track all values with timestamps to enable trend analysis when needed.

---

#### 3. **Hemodynamic Instability Defined by Multiple Indicators**

**Assumption:** "Hemodynamic instability" is present if ANY of the following:
- SBP < 90 mmHg
- MAP < 65 mmHg
- Shock index (HR/SBP) > 1.0
- Vasopressor requirement documented
- Explicit clinical statement of "hemodynamically unstable"

**Justification:** Hemodynamic instability can manifest through different physiologic parameters. Using OR logic captures all presentations while maintaining clinical validity.

**Example:** A patient with SBP 92 mmHg (borderline) but requiring norepinephrine infusion is clearly unstable, even though SBP alone doesn't meet the <90 threshold.

---

### Technical Assumptions

#### 4. **Semi-Structured Document Format**

**Assumption:** H&P documents follow common organizational patterns with recognizable section headers:
- "Vital Signs" or "VS"
- "Laboratory" or "Labs"
- "Physical Examination" or "PE"
- "Assessment and Plan" or "A/P"

**Justification:** Most EMR systems (Epic, Cerner, Meditech) use standardized templates with consistent headers.

**Fallback:** If headers aren't detected, apply extraction patterns to entire document, but with lower confidence scores requiring manual review.

---

#### 5. **Timestamp Availability and Proximity**

**Assumption:** 
- Timestamps are documented near clinical values
- If no specific timestamp found, use document creation time
- All values in a single H&P are from the same clinical encounter timeframe

**Justification:** Standard clinical documentation practice includes timestamps with measurements, and H&P documents represent a point-in-time assessment.

**Limitation:** May not capture precise timing for serial measurements within the same encounter (e.g., pre- and post-resuscitation vitals).

---

#### 6. **Medical Coding Standards Are Available**

**Assumption:** Standard medical ontologies provide codes for common clinical parameters:
- **LOINC codes** for vitals and lab tests
- **SNOMED CT codes** for clinical findings
- **ICD-10 codes** for diagnoses

**Fallback Strategy:** If code lookup fails (unusual test, regional variation), store:
- Text description
- Flag for manual coding review
- Still allow matching based on parameter name matching

---

#### 7. **Unit Standardization Is Necessary**

**Assumption:** All measurements should be converted to standard units before matching:
- Temperature: Always Fahrenheit
- Blood pressure: Always mmHg
- Labs: Standard SI units per LOINC specifications

**Justification:** Enables direct numeric comparison without real-time conversion during matching.

**Implementation Note:** Conversion formulas must be clinically validated (e.g., °C to °F: multiply by 9/5 and add 32).

---

#### 8. **Missing Data Equals Criterion Not Met**

**Assumption:** If a clinical finding is not documented, assume it is not present.

**Clinical Principle:** "If not documented, not done" is standard in medical-legal practice.

**Example:**
- No mention of blood cultures → Assume not performed
- No documentation of altered mental status → Assume mental status normal
- No vasopressor mentioned → Assume patient not on vasopressors

**Alternative Approach:** Flag missing critical data as "unknown" rather than "absent," requiring manual review for high-stakes criteria.

**Risk:** 
- Incomplete documentation may lead to false negatives
- Emergency situations may have sparse documentation

**Mitigation:** Data quality checks flag unexpectedly sparse documents for review.

---

#### 9. **LLM Extraction Has High Accuracy**

**Assumption:** LLM-based extraction from narrative clinical text achieves >90% accuracy for:
- Clinical concept identification
- Value extraction
- Relationship understanding (e.g., "BP dropped to 80s after standing")

**Mitigation Strategies:**
- Tag all LLM-extracted data with confidence scores
- Use structured extraction (regex) whenever possible as primary method
- Flag low-confidence extractions for manual review
- Validate LLM output against physiologic plausibility (e.g., temperature of 200°F is impossible)

---

#### 10. **One Document = One Clinical Encounter**

**Assumption:** Each H&P document represents a single clinical encounter with a cohesive time window (typically ER visit or admission assessment).

**Justification:** Standard clinical workflow produces one H&P per encounter.

**Limitation:** Does not handle:
- Serial vital sign measurements across hours
- Progression notes documenting clinical course
- Multiple provider assessments within same encounter

**For This Use Case:** Acceptable because MCG admission criteria are typically evaluated at a single decision point (ER evaluation or admission assessment).

---

#### 11. **MCG Criteria Have Explicit Matching Conditions**

**Assumption:** MCG schema can be completely specified with explicit thresholds and logic.

**Reality:** Some criteria are qualitative requiring clinical judgment:
- "Severe or persistent" (how severe? how long is persistent?)
- "Inability to maintain oral hydration" (subjective assessment)
- "Active comorbid illness" (what counts as "active"?)

**Approach:**
- Map qualitative criteria to quantitative proxies where possible (e.g., GCS < 14 for "severe" altered mental status)
- For irreducibly subjective criteria, extract physician's clinical judgment from documentation
- Flag ambiguous cases for manual review

---

#### 12. **Data Quality Is Acceptable**

**Assumption:** Source H&P documents are:
- Legible (adequate OCR quality if scanned)
- Medically complete (all relevant findings documented)
- Authored by qualified clinician
- Free of significant errors

**Mitigation:**
- Pre-processing: OCR cleanup, spell-check on medical terms
- Data validation: Check for physiologically impossible values (temp 200°F, HR 300)
- Completeness checks: Flag documents missing critical sections (no vital signs documented)
- Confidence scoring: Lower confidence for documents with quality issues
---

### Matching Logic Assumptions

#### 13. **MCG Uses Disjunctive (OR) Logic**

**Assumption:** MCG guidelines state "Admission is indicated for 1 or more of the following" → ANY single criterion met triggers admission indication.

**Implementation:** Evaluate all criteria, admission indicated if any criterion matches.

**Example:** Patient has hypoxemia (SpO2 88%) but all other vitals normal:
- Hypoxemia criterion: MET
- Other criteria: NOT MET
- **Result:** Admission indicated (because at least one criterion is met)

---

#### 14. **Conditional Criteria Require Dependency to Be Met First**

**Assumption:** Criteria with conditional language (e.g., "if blood cultures performed") are only evaluated when the condition is satisfied.

**Example - Bacteremia Criterion:**
- **If blood cultures NOT performed:** Criterion is not applicable (neither met nor failed)
- **If blood cultures performed AND positive:** Criterion is MET
- **If blood cultures performed AND negative:** Criterion is NOT MET

**Logic:** Dependencies must be evaluated before main criterion.

---


## Risk Mitigation Summary

**Clinical Safety:**
1. Validate all extracted values against physiologic plausibility
2. Flag ambiguous or borderline cases for manual review
3. Maintain audit trail from source text to matched criteria
4. Allow clinical override of automated determinations

**Technical Reliability:**
1. Use regex for structured data (high precision)
2. Use LLM for narrative text with confidence scoring
3. Validate LLM output format before accepting
4. Log all extraction decisions for debugging

**Quality Assurance:**
1. Data quality checks before matching (completeness, validity)
2. Confidence scores for each extraction method
3. Manual review queue for low-confidence or high-stakes cases
4. Regular validation against gold-standard manual chart reviews

---