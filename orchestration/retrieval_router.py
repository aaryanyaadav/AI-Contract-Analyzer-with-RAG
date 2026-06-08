class RetrievalRouter:

    def get_retrieval_config(

        self,

        query_type
    ):

        configs = {

            # =================================
            # CONTRACT SUMMARY
            # =================================
            "summary": {

                # Fewer reranker candidates
                "initial_fetch_k": 12,

                # Final chunks
                "final_k": 6
            },

            # =================================
            # RISK ANALYSIS
            # =================================
            "risk": {

                "initial_fetch_k": 10,

                "final_k": 5
            },

            # =================================
            # OBLIGATIONS
            # =================================
            "obligation": {

                "initial_fetch_k": 8,

                "final_k": 4
            },

            # =================================
            # COMPARISON
            # =================================
            "comparison": {

                "initial_fetch_k": 10,

                "final_k": 5
            },

            # =================================
            # CLAUSE SEARCH
            # =================================
            "clause_search": {

                "initial_fetch_k": 6,

                "final_k": 3
            },

            # =================================
            # GENERAL QA
            # =================================
            "qa": {

                "initial_fetch_k": 8,

                "final_k": 4
            }
        }

        return configs.get(

            query_type,

            configs["qa"]
        )