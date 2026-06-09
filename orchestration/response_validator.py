class ResponseValidator:


    def validate(

        self,

        answer,

        retrieved_chunks=None
    ):

        if not answer:

            return False

        if len(answer.strip()) < 10:

            return False


        bad_phrases = [

            "i don't know",

            "no information available",

            "cannot determine",

            "not enough context"
        ]

        answer_lower = answer.lower()

        if any(

            phrase in answer_lower

            for phrase in bad_phrases
        ):

            return False


        if retrieved_chunks:

            combined_context = " ".join([

                chunk["text"].lower()

                for chunk in retrieved_chunks
            ])

            # VERY LIGHT VALIDATION
            # (can improve later)
            important_terms = [

                word.lower()

                for word in answer.split()

                if len(word) > 6
            ]

            overlap = any(

                term in combined_context

                for term in important_terms
            )

            if not overlap:

                print(
                    "[Validator] "
                    "Low context overlap."
                )

        return True