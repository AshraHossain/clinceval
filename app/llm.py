import os
import time
from anthropic import Anthropic

class LLMClient:
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
        else:
            self.client = None
        
    def call_claude(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
        tools: list = None,
        tool_choice: dict = None
    ) -> dict:
        """
        Calls Claude model (or returns a simulated mock if no API key is set).
        """
        start_time = time.time()
        
        if not self.client:
            # Generate mock response
            import re
            
            # Extract just the patient query to avoid matching keywords in retrieved context
            query_match = re.search(r"Patient Query:\s*(.*?)\s*(?:Retrieved Context:|$)", user_prompt, re.DOTALL | re.IGNORECASE)
            query_text = query_match.group(1).lower() if query_match else user_prompt.lower()
            
            calculator = "None"
            rationale = "No matching calculator found in the provided context for the given symptoms."
            confidence = 0.8
            citations = []
            chunk_ids = re.findall(r"--- START CHUNK ID: (\S+) ---", user_prompt)
            
            # Parse age to check if it's pediatric (< 18 years old)
            is_pediatric = False
            age_matches = re.findall(r"\b(\d+)\s*-?(?:year|yr)", query_text)
            for age_str in age_matches:
                if int(age_str) < 18:
                    is_pediatric = True
            if ("child" in query_text or "pediatric" in query_text or "infant" in query_text) and "pecarn" not in query_text:
                is_pediatric = True
            
            # Check for missing vitals/data constraints
            is_missing_data = any(w in query_text for w in ["no lab values", "no vitals", "no values", "no urea", "missing"])
            
            if is_pediatric or is_missing_data:
                calculator = "None"
                rationale = "The clinical criteria are not met: patient age is outside calculator constraints or required vital values/labs are missing."
            elif "atrial fibrillation" in query_text or "afib" in query_text or "chads" in query_text:
                if "bleed" in query_text or "has-bled" in query_text or "bleeding" in query_text:
                    calculator = "HAS-BLED Score for Major Bleeding Risk"
                    rationale = "The patient is starting or taking oral anticoagulation for atrial fibrillation, and we need to estimate their major bleeding risk using the HAS-BLED score."
                else:
                    calculator = "CHA2DS2-VASc Score for Atrial Fibrillation Stroke Risk"
                    rationale = "The patient has atrial fibrillation and we need to estimate their risk of stroke to decide on anticoagulant therapy."
            elif "pulmonary embolism" in query_text or "wells pe" in query_text or "pe " in query_text or "perc" in query_text:
                if any(w in query_text for w in ["perc", "rule out", "estrogen", "room air", "low risk"]):
                    calculator = "Pulmonary Embolism Rule-out Criteria (PERC Rule)"
                    rationale = "The patient is low risk for PE and we want to apply the PERC rule to rule out PE without further testing."
                else:
                    calculator = "Wells' Criteria for Pulmonary Embolism (PE)"
                    rationale = "The patient has symptoms suggestive of pulmonary embolism, so we use Wells' Criteria for PE to estimate pre-test probability."
            elif "dvt" in query_text or "deep vein thrombosis" in query_text or "leg swelling" in query_text:
                calculator = "Wells' Criteria for Deep Vein Thrombosis (DVT)"
                rationale = "The patient has suspected deep vein thrombosis based on unilateral leg swelling, tenderness, and pitting edema."
            elif "meld" in query_text or "3-month" in query_text or "creatinine" in query_text or "sodium" in query_text:
                calculator = "MELD Score (Model for End-Stage Liver Disease)"
                rationale = "The patient has end-stage liver disease and we need to estimate their 3-month mortality risk for transplant prioritization."
            elif "liver disease" in query_text or "child-pugh" in query_text or "cirrhosis" in query_text:
                calculator = "Child-Pugh Score for Cirrhosis Mortality"
                rationale = "The patient has cirrhosis and chronic liver disease; we use the Child-Pugh score to assess prognosis and survival rates."
            elif "pneumonia" in query_text or "curb-65" in query_text or "curb 65" in query_text:
                calculator = "CURB-65 Severity Score for Community-Acquired Pneumonia"
                rationale = "The patient has community-acquired pneumonia; we use CURB-65 to assess severity and determine if outpatient vs inpatient care is needed."
            elif "chest pain" in query_text or "heart score" in query_text or "mace" in query_text:
                calculator = "HEART Score for Major Adverse Cardiac Events (MACE)"
                rationale = "The patient presents with chest pain of suspected cardiac origin; we use the HEART Score to risk-stratify the 6-week risk of MACE."
            elif "coma" in query_text or "glasgow" in query_text or "gcs" in query_text or "consciousness" in query_text:
                calculator = "Glasgow Coma Scale (GCS)"
                rationale = "The patient has a head injury / altered level of consciousness; we use GCS to standardize neurological assessment."
            elif "sepsis" in query_text or "qsofa" in query_text:
                calculator = "Quick Sequential Organ Failure Assessment (qSOFA)"
                rationale = "The patient has a suspected infection; we use qSOFA to rapidly assess sepsis risk outside the ICU."
            elif "sirs" in query_text or "systemic inflammatory" in query_text:
                calculator = "Systemic Inflammatory Response Syndrome (SIRS) Criteria"
                rationale = "The patient has signs of systemic inflammation; we use SIRS criteria to evaluate."
            elif "pecarn" in query_text or "pediatric" in query_text:
                calculator = "PECARN Pediatric Head Injury Rule"
                rationale = "The patient is a pediatric patient with minor head trauma; we use the PECARN rule to assess if a head CT is required."

            # Map calculator to chunk prefix for citations
            doc_prefix = ""
            calc_name = calculator.lower()
            if "cha2ds2" in calc_name:
                doc_prefix = "chads2_vasc"
            elif "pecarn" in calc_name:
                doc_prefix = "pecarn_head_injury"
            elif "perc" in calc_name:
                doc_prefix = "perc_rule"
            elif "has-bled" in calc_name:
                doc_prefix = "has_bled"
            elif "meld" in calc_name:
                doc_prefix = "meld"
            elif "child-pugh" in calc_name:
                doc_prefix = "child_pugh"
            elif "glasgow" in calc_name:
                doc_prefix = "gcs"
            elif "curb-65" in calc_name:
                doc_prefix = "curb_65"
            elif "heart" in calc_name:
                doc_prefix = "heart_score"
            elif "qsofa" in calc_name:
                doc_prefix = "qsofa"
            elif "sirs" in calc_name:
                doc_prefix = "sirs"
            elif "pulmonary" in calc_name:
                doc_prefix = "wells_pe"
            elif "deep" in calc_name:
                doc_prefix = "wells_dvt"

            if doc_prefix:
                citations = [cid for cid in chunk_ids if cid.startswith(doc_prefix)]
            
            class MockToolUse:
                def __init__(self, name, input_data):
                    self.type = "tool_use"
                    self.name = name
                    self.input = input_data
                    
            class MockUsage:
                def __init__(self):
                    self.input_tokens = 250
                    self.output_tokens = 150
                    
            class MockResponse:
                def __init__(self, tool_use_block, usage):
                    self.content = [tool_use_block]
                    self.usage = usage

            tool_input = {
                "calculator": calculator,
                "rationale": rationale,
                "confidence": confidence,
                "citations": citations
            }
            
            response = MockResponse(
                MockToolUse("recommend_calculator", tool_input),
                MockUsage()
            )
            
            latency = time.time() - start_time
            return {
                "response": response,
                "latency": latency,
                "input_tokens": 250,
                "output_tokens": 150
            }
            
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        }
        
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice
            
        response = self.client.messages.create(**kwargs)
        latency = time.time() - start_time
        
        # Track usage
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        
        return {
            "response": response,
            "latency": latency,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }

# Global client helper
_global_llm_client = None

def get_llm_client() -> LLMClient:
    global _global_llm_client
    if _global_llm_client is None:
        _global_llm_client = LLMClient()
    return _global_llm_client
