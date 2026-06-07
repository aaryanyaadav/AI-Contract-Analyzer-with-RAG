class QueryAnalyzer:

    def __init__(

        self,

        llm_client
    ):

        self.llm = llm_client

    # =========================================
    # ANALYZE QUERY
    # =========================================
    def analyze(

        self,

        query
    ):

        system_prompt = """
You are a legal RAG query classifier.

Your task is to classify the user query into EXACTLY ONE category.

Possible categories:

- summary
    User wants:
    summaries, overviews, explanations.

- obligation
    User asks about:
    duties, responsibilities,
    requirements, commitments.

- risk
    User asks about:
    legal risks, liabilities,
    penalties, dangerous clauses,
    indemnification.

- clause_search
    User wants:
    a specific clause,
    section,
    term,
    or provision.

- comparison
    User compares:
    clauses,
    obligations,
    sections,
    agreements,
    terms.

- qa
    General question answering.

IMPORTANT:
Return ONLY the category name.
No explanation.
No punctuation.
No extra text.
"""

        user_prompt = f"""
Classify this query:

{query}

Category:
"""

        try:

            response = self.llm.generate(

                system_prompt=
                system_prompt,

                user_prompt=
                user_prompt,

                max_tokens=20,

                temperature=0
            )

            cleaned = (
                response
                .strip()
                .lower()
            )

            # =====================================
            # VALID CATEGORIES
            # =====================================
            allowed_categories = [

                "summary",

                "obligation",

                "risk",

                "clause_search",

                "comparison",

                "qa"
            ]

            # =====================================
            # EXACT MATCH
            # =====================================
            if cleaned in allowed_categories:

                return cleaned

            # =====================================
            # FALLBACK HEURISTICS
            # =====================================
            query_lower = query.lower()

            # SUMMARY
            if any(

                word in query_lower

                for word in [

                    "summary",

                    "summarize",

                    "overview",

                    "brief",

                    "explain contract"
                ]
            ):

                return "summary"

            # OBLIGATION
            if any(

                word in query_lower

                for word in [

                    "obligation",

                    "duty",

                    "responsibility",

                    "must",

                    "required"
                ]
            ):

                return "obligation"

            # RISK
            if any(

                word in query_lower

                for word in [

                    "risk",

                    "liability",

                    "penalty",

                    "danger",

                    "breach",

                    "termination",

                    "indemnity"
                ]
            ):

                return "risk"

            # COMPARISON
            if any(

                word in query_lower

                for word in [

                    "compare",

                    "difference",

                    "versus",

                    "vs"
                ]
            ):

                return "comparison"

            # CLAUSE SEARCH
            if any(

                word in query_lower

                for word in [

                    "clause",

                    "section",

                    "term",

                    "provision"
                ]
            ):

                return "clause_search"

            # DEFAULT
            return "qa"

        except Exception as e:

            print(
                f"[QueryAnalyzer Error]: {e}"
            )

            return "qa"