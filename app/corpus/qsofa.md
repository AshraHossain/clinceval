# Quick Sequential Organ Failure Assessment (qSOFA)

## Purpose
The qSOFA score is a clinical tool used to identify patients outside the intensive care unit (ICU) who are at high risk of death or prolonged ICU stay due to suspected infection/sepsis. It is designed to be a rapid, bed-side assessment tool.

## Inputs Required
- Respiratory rate
- Altered mental status
- Systolic blood pressure

## Scoring Logic
One point is assigned for each of the following criteria met:
- Respiratory rate >= 22 breaths per minute: +1 point
- Altered mentation (GCS < 15 or acute change in mental status): +1 point
- Systolic blood pressure <= 100 mmHg: +1 point

Score ranges from 0 to 3.

## Interpretation Bands
- Score 0 to 1: Low risk. Indicates a low risk of in-hospital mortality or ICU stay. Continue clinical monitoring as appropriate.
- Score 2 to 3: High risk. Associated with a significantly higher risk of death or prolonged ICU stay (a 3- to 14-fold increase in mortality). Suggests a high likelihood of sepsis; clinicians should assess for organ dysfunction and consider escalation of care.
