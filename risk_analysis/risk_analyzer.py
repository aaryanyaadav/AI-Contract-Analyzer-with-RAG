from ingestion.vector_store import (
    ContractVectorStore
)

from llm.llm_client import LLMClient


class RiskAnalyzer:

    def __init__(

            self,

            chroma_path
        ):

        self.vector_store = (
        ContractVectorStore(
        db_path=chroma_path
    )
)

        self.llm = LLMClient()

    def analyze_contract_risks(
        self,
        document_id
    ):

        results = (
            self.vector_store.collection.get(

                where={

                    "$and": [

                        {
                            "document_id":
                            document_id
                        },

                        {
                            "risk_flag":
                            "High"
                        }
                    ]
                },

                include=[
                    "documents",
                    "metadatas"
                ]
            )
        )

        documents = results["documents"]

        metadatas = results["metadatas"]

        if not documents:

            return (
                "No major legal risks "
                "were detected."
            )

        risk_context = ""

        for idx, doc in enumerate(documents):

            section = metadatas[idx].get(
                "parent_section",
                "Unknown"
            )

            risk_context += f"""

[Risk Clause {idx+1}]

Section:
{section}

Clause:
{doc}

"""

        system_prompt = """
You are an expert legal risk analysis AI.

Analyze the provided contract clauses.

Identify:
- legal risks
- liabilities
- penalties
- dangerous obligations
- unusual clauses

Explain:
- why each risk matters
- potential consequences
- severity

Provide a structured legal risk report.
"""

        user_prompt = f"""
CONTRACT RISK CLAUSES:

{risk_context}

Generate a professional legal
risk analysis report.
"""

        report = self.llm.generate(

            system_prompt=system_prompt,

            user_prompt=user_prompt
        )

        return report

    def close(self):

        if hasattr(self, 'vector_store') and self.vector_store:

            self.vector_store.close()