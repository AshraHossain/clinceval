# MELD Score (Model for End-Stage Liver Disease)

## Purpose
The Model for End-Stage Liver Disease (MELD) is a scoring system used to estimate the 3-month mortality risk in patients aged 12 and older with end-stage liver disease. It is primarily used to prioritize candidates for liver transplantation.

## Inputs Required
- Serum Creatinine (mg/dL)
- Total Bilirubin (mg/dL)
- International Normalized Ratio (INR)
- Serum Sodium (mEq/L)
- Whether the patient has had hemodialysis or renal replacement therapy at least twice in the past week

## Scoring Logic
The traditional MELD score formula is:
MELD = 3.78 * ln(bilirubin [mg/dL]) + 11.2 * ln(INR) + 9.57 * ln(creatinine [mg/dL]) + 6.43

Notes on MELD calculation:
- If bilirubin, creatinine, or INR is < 1.0, use 1.0.
- If the patient has had dialysis twice or more within the past week, or continuous venovenous hemodiafiltration, creatinine is automatically set to 4.0 mg/dL.
- Maximum MELD score is capped at 40.
- Modern MELD (MELD-Na) incorporates serum sodium when MELD > 11.

## Interpretation Bands
Three-month mortality rates based on MELD score:
- MELD score >= 40: 71.3% mortality
- MELD score 30 to 39: 52.6% mortality
- MELD score 20 to 29: 19.6% mortality
- MELD score 10 to 19: 6.0% mortality
- MELD score <= 9: 1.9% mortality
