# HEART Score for Major Adverse Cardiac Events (MACE)

## Purpose
The HEART Score predicts the 6-week risk of a major adverse cardiac event (MACE) in patients presenting to the emergency department with chest pain of suspected cardiac origin. It helps risk-stratify patients and identify those who can be safely discharged.

## Inputs Required
- History (highly suspicious, moderately suspicious, or slightly/non-suspicious chest pain description)
- ECG (significant ST-depression, non-specific repolarization disturbance, or normal)
- Age (< 45, 45-64, or >= 65 years)
- Risk factors (presence of hypertension, hypercholesterolemia, diabetes, smoking, family history of CAD, obesity)
- Troponin (elevated 1-2x normal, > 2x normal, or normal)

## Scoring Logic
Points are assigned from 0 to 2 for each of the 5 categories (HEART):
- **H**istory:
  - Highly suspicious: 2 points
  - Moderately suspicious: 1 point
  - Slightly or non-suspicious: 0 points
- **E**CG:
  - Significant ST-deviation: 2 points
  - Non-specific repolarization disturbance / LBBB / PM: 1 point
  - Normal: 0 points
- **A**ge:
  - Age >= 65: 2 points
  - Age 45 to 64: 1 point
  - Age < 45: 0 points
- **R**isk Factors (HTN, hypercholesterolemia, DM, smoking, family history, obesity):
  - >= 3 risk factors or history of atherosclerotic disease: 2 points
  - 1 or 2 risk factors: 1 point
  - No risk factors: 0 points
- **T**roponin:
  - >= 2x normal limit: 2 points
  - 1 to <2x normal limit: 1 point
  - Normal limit (<= normal): 0 points

Score ranges from 0 to 10.

## Interpretation Bands
- Score 0 to 3: Low risk (0.9% - 1.7% risk of MACE). Candidates for early discharge.
- Score 4 to 6: Intermediate risk (12% - 17% risk of MACE). Observation, serial troponins, and further testing recommended.
- Score 7 to 10: High risk (50% - 65% risk of MACE). Immediate invasive treatment (cardiology consultation, coronary angiography).
