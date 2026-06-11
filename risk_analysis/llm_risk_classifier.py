import json

from llm.llm_client import LLMClient


class LLMRiskClassifier:

    def __init__(self):

        self.llm = LLMClient()

    def classify_risk_batch(
        self,
        chunks
    ):


        clause_text = ""

        for idx, chunk in enumerate(chunks):

            clause_text += f"""

CLAUSE {idx+1}:
{chunk['text']}

"""

        system_prompt = """
You are an expert legal contract risk analyzer.

Analyze EACH clause independently.

For every clause return:

- risk_level
- risk_category
- risk_reason

Risk levels:
- Low
- Medium
- High

Return ONLY valid JSON ARRAY.

Example:

[
  {
    "risk_level": "High",
    "risk_category": "Liability",
    "risk_reason": "Unlimited liability exposure."
  },

  {
    "risk_level": "Low",
    "risk_category": "General",
    "risk_reason": "No major concerns."
  }
]
"""


        user_prompt = f"""
Analyze these contract clauses.

{clause_text}
"""

        try:

            response = self.llm.generate(

                system_prompt=system_prompt,

                user_prompt=user_prompt
            )

            parsed = json.loads(response)

            return parsed

        except Exception as e:

            print(
                f"[Risk Batch Error]: {e}"
            )

            # Safe fallback
            fallback = []

            for _ in chunks:

                fallback.append({

                    "risk_level": "Low",

                    "risk_category": "Other",

                    "risk_reason":
                    "Classification failed."
                })

            return fallback