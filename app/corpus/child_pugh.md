# Child-Pugh Score for Cirrhosis Mortality

## Purpose
The Child-Pugh score is used to assess the prognosis of chronic liver disease (primarily cirrhosis) and estimate survival rates and likelihood of major complications.

## Inputs Required
- Total Bilirubin (umol/L or mg/dL)
- Serum Albumin (g/dL or g/L)
- INR (or prothrombin time prolongation)
- Ascites (none, mild/medically controlled, or moderate-severe/refractory)
- Hepatic encephalopathy (none, grade 1-2, or grade 3-4)

## Scoring Logic
Points are assigned from 1 to 3 for each of the 5 measures:
- **Total Bilirubin**:
  - < 2.0 mg/dL (< 34 umol/L): 1 point
  - 2.0 to 3.0 mg/dL (34 to 51 umol/L): 2 points
  - > 3.0 mg/dL (> 51 umol/L): 3 points
- **Serum Albumin**:
  - > 3.5 g/dL (> 35 g/L): 1 point
  - 2.8 to 3.5 g/dL (28 to 35 g/L): 2 points
  - < 2.8 g/dL (< 28 g/L): 3 points
- **INR**:
  - < 1.7: 1 point
  - 1.7 to 2.3: 2 points
  - > 2.3: 3 points
- **Ascites**:
  - None: 1 point
  - Mild / Diuretic-responsive: 2 points
  - Moderate to Severe / Refractory: 3 points
- **Encephalopathy**:
  - None: 1 point
  - Grade 1 to 2 (mild confusion, sleep disturbance): 2 points
  - Grade 3 to 4 (somnolence, stupor, coma): 3 points

Score ranges from 5 to 15.

## Interpretation Bands
Three classes are defined:
- **Class A** (Score 5 to 6): Well-compensated disease. 1-year survival: 100%, 2-year survival: 85%.
- **Class B** (Score 7 to 9): Significant functional compromise. 1-year survival: 80%, 2-year survival: 60%.
- **Class C** (Score 10 to 15): Decompensated disease. 1-year survival: 45%, 2-year survival: 35%.
