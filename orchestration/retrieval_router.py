class RetrievalRouter:

    def get_retrieval_config(

        self,

        query_type
    ):

        configs = {


            "summary": {

                # Fewer reranker candidates
                "initial_fetch_k": 12,

                # Final chunks
                "final_k": 6
            },

            "risk": {

                "initial_fetch_k": 10,

                "final_k": 5
            },


            "obligation": {

                "initial_fetch_k": 8,

                "final_k": 4
            },


            "comparison": {

                "initial_fetch_k": 10,

                "final_k": 5
            },


            "clause_search": {

                "initial_fetch_k": 6,

                "final_k": 3
            },

            
            "qa": {

                "initial_fetch_k": 8,

                "final_k": 4
            }
        }

        return configs.get(

            query_type,

            configs["qa"]
        )