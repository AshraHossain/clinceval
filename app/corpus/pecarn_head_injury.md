# PECARN Pediatric Head Injury Rule

## Purpose
The PECARN Pediatric Head Injury Algorithm helps clinicians identify pediatric patients (under 18 years) with minor head trauma who are at very low risk for clinically important traumatic brain injuries (ciTBI), thereby avoiding unnecessary head CT scans.

## Inputs Required
- Age group (under 2 years vs 2 years and older)
- Glasgow Coma Scale (GCS) score
- Signs of basilar skull fracture
- Altered mental status
- History of loss of consciousness (LOC)
- History of vomiting
- Severe mechanism of injury (e.g. MVC with ejection, fall >3 feet for <2 years, fall >5 feet for >=2 years)
- Severe headache (for >=2 years)
- Acted normally per parent (for <2 years)
- Occipital or parietal or temporal scalp hematoma (for <2 years)

## Scoring Logic
The algorithm splits patients into two age categories:
### Age < 2 years:
- High risk (GCS = 14 or altered mental status or palpable skull fracture): CT recommended (ciTBI risk ~4.4%).
- Intermediate risk (LOC >5 sec or severe mechanism of injury or non-frontal scalp hematoma or not acting normally per parent): Observation vs CT (ciTBI risk ~0.9%).
- Low risk (none of the above): CT not recommended (ciTBI risk <0.02%).

### Age >= 2 years:
- High risk (GCS = 14 or altered mental status or signs of basilar skull fracture): CT recommended (ciTBI risk ~4.6%).
- Intermediate risk (history of LOC or history of vomiting or severe mechanism of injury or severe headache): Observation vs CT (ciTBI risk ~0.9%).
- Low risk (none of the above): CT not recommended (ciTBI risk <0.05%).

## Interpretation Bands
- High risk: CT imaging strongly recommended.
- Intermediate risk: Clinical observation prior to decision on CT is appropriate, depending on physician experience, multiple vs isolated findings, worsening signs, or parental preference.
- Low risk: Head CT scan is clinically not indicated.
