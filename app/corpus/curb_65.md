# CURB-65 Severity Score for Community-Acquired Pneumonia

## Purpose
The CURB-65 score is a clinical prediction rule used to predict mortality in patients with community-acquired pneumonia. It helps clinicians decide whether the patient can be safely treated as an outpatient, needs inpatient admission, or requires intensive care unit (ICU) monitoring.

## Inputs Required
- Confusion (new mental confusion or disorientation)
- Urea (blood urea nitrogen > 19 mg/dL or > 7 mmol/L)
- Respiratory rate (>= 30 breaths per minute)
- Blood pressure (systolic < 90 mmHg or diastolic <= 60 mmHg)
- Age >= 65 years

## Scoring Logic
One point is assigned for each of the following criteria met:
- **C**onfusion: +1 point
- **U**rea (BUN > 19 mg/dL): +1 point
- **R**espiratory Rate >= 30 breaths/min: +1 point
- **B**lood Pressure (Systolic < 90 mmHg or Diastolic <= 60 mmHg): +1 point
- **65** (Age >= 65 years): +1 point

Score ranges from 0 to 5.

## Interpretation Bands
- Score 0 to 1: Low risk. 30-day mortality risk is low (< 3%). Suitable for outpatient treatment.
- Score 2: Moderate risk. 30-day mortality risk is moderate (approx. 9%). Consider short-stay inpatient admission or close outpatient monitoring.
- Score 3 to 5: High risk. 30-day mortality risk is high (15% to 57%). Requires urgent hospitalization; for scores 4 or 5, consider intensive care unit (ICU) admission.
