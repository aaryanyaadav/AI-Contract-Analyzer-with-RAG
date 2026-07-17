import os
import re
import time
from typing import List, Dict, Any
from evaluation.ragas.base_evaluator import BaseEvaluator
from llm.llm_client import LLMClient

class FallbackSemanticEvaluator(BaseEvaluator):

    def __init__(self):
        self.llm = None
        self._initialized = False

    def initialize(self) -> None:

        eval_model = os.getenv("GROQ_EVAL_MODEL", "groq/compound-mini")
        self.llm = LLMClient(model_name=eval_model)
        self._initialized = True

    def _safe_generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 512, temperature: float = 0.3) -> str:

        for attempt in range(4):
            response = self.llm.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Check for Groq API rate limits
            if "rate limit reached" in response.lower() or "limit exceeded" in response.lower() or "429" in response:
                sleep_time = 15 * (attempt + 1)
                print(f"\n[RateLimit] Evaluator LLM hit rate limit (429). Sleeping {sleep_time}s before retry...")
                time.sleep(sleep_time)
            else:
                return response
                
        return response

    def _extract_factual_statements(self, text: str) -> List[str]:
        if not text or len(text.strip()) == 0:
            return []

        system_prompt = "You are an AI assistant that extracts independent factual claims from a text."
        user_prompt = (
            f"Extract all independent, single-sentence factual claims made in the following text as a numbered list. "
            f"Do not write summaries or introductory text; output only the numbered claims. "
            f"If there are no factual claims, output 'No claims'.\n\n"
            f"Text: {text}"
        )
        
        response = self._safe_generate(system_prompt, user_prompt, max_tokens=512, temperature=0.1)
        if "no claims" in response.lower() or not response.strip():
            return []

        statements = []
        for line in response.split("\n"):
            line = line.strip()
            match = re.match(r"^\d+[\.\)]\s*(.*)", line)
            if match:
                stmt = match.group(1).strip()
                if stmt:
                    statements.append(stmt)
            elif line.startswith("-") or line.startswith("*"):
                stmt = line[1:].strip()
                if stmt:
                    statements.append(stmt)
                    
        if not statements and len(response.strip()) > 0 and len(response.split("\n")) < 5:
            statements = [response.strip()]
            
        return statements

    def evaluate_item_unified(self, question: str, expected_answer: str, generated_answer: str, retrieved_context: List[str]) -> Dict[str, float]:
        """
        Evaluates all 4 Ragas-equivalent metrics in a single LLM call to save tokens and avoid 429 rate limits.
        """
        context_block = "\n\n".join([f"Chunk {i+1}: {chunk}" for i, chunk in enumerate(retrieved_context)])
        if not context_block.strip():
            context_block = "None"

        system_prompt = (
            "You are an expert AI evaluator assessing RAG system response quality. "
            "You must calculate four standard evaluation metrics: faithfulness, answer_correctness, context_precision, and context_recall. "
            "Respond ONLY with a valid JSON object matching this schema: "
            '{"faithfulness": float, "answer_correctness": float, "context_precision": float, "context_recall": float}'
        )

        user_prompt = (
            f"Please evaluate the following RAG system outputs and generate a JSON object with scores between 0.0 and 1.0:\n\n"
            f"Question: {question}\n\n"
            f"Expected Correct Answer (Ground Truth): {expected_answer}\n\n"
            f"Generated Answer: {generated_answer}\n\n"
            f"Retrieved Context Chunks:\n{context_block}\n\n"
            f"Metric Rules:\n"
            f"1. faithfulness: Measures if the generated answer is factually consistent with and derived ONLY from the retrieved context chunks (no hallucinated facts). Rate 0.0 to 1.0.\n"
            f"2. answer_correctness: Measures semantic correctness and factual similarity of the generated answer compared to the expected answer. Rate 0.0 to 1.0.\n"
            f"3. context_precision: Measures if the retrieved context chunks contain relevant information that directly helps answer the question. Rate 0.0 to 1.0.\n"
            f"4. context_recall: Measures if the information in the expected answer is fully covered/mentioned by the retrieved context chunks. Rate 0.0 to 1.0.\n\n"
            f"Respond ONLY with the JSON block containing the four scores. No explanations."
        )

        response = self._safe_generate(system_prompt, user_prompt, max_tokens=150, temperature=0.0).strip()

        # Parse JSON
        try:
            clean_res = response
            if "```" in response:
                clean_res = response.split("```")[1]
                if clean_res.startswith("json"):
                    clean_res = clean_res[4:]
            
            import json
            data = json.loads(clean_res.strip())
            return {
                "faithfulness": min(max(float(data.get("faithfulness", 0.5)), 0.0), 1.0),
                "answer_correctness": min(max(float(data.get("answer_correctness", 0.5)), 0.0), 1.0),
                "context_precision": min(max(float(data.get("context_precision", 0.5)), 0.0), 1.0),
                "context_recall": min(max(float(data.get("context_recall", 0.5)), 0.0), 1.0)
            }
        except Exception:
            metrics = ["faithfulness", "answer_correctness", "context_precision", "context_recall"]
            scores = {}
            for m in metrics:
                match = re.search(fr'"{m}"\s*:\s*([0-9\.]+)', response)
                if match:
                    scores[m] = float(match.group(1))
                else:
                    scores[m] = 0.5
            return scores

    def evaluate_dataset(self, dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self._initialized:
            raise RuntimeError("FallbackSemanticEvaluator has not been initialized.")
            
        evaluated_dataset = []
        total = len(dataset)
        print(f"\n[FallbackEvaluator] Starting evaluation of {total} queries...")
        for idx, item in enumerate(dataset):
            q = item["question"]
            expected = item["expected_answer"]
            gen = item["generated_answer"]
            ctx = item["retrieved_context"]

            print(f"[FallbackEvaluator] [{idx + 1}/{total}] Evaluating query: '{q[:60]}...'")
            scores = self.evaluate_item_unified(q, expected, gen, ctx)

            evaluated_item = dict(item)
            evaluated_item["faithfulness"] = scores["faithfulness"]
            evaluated_item["answer_correctness"] = scores["answer_correctness"]
            evaluated_item["context_precision"] = scores["context_precision"]
            evaluated_item["context_recall"] = scores["context_recall"]
            evaluated_dataset.append(evaluated_item)
            
            # Wait 3 seconds to let TPM limits cool down
            time.sleep(3)

        return evaluated_dataset

    def get_engine_info(self) -> Dict[str, str]:
        return {
            "name": "Fallback Semantic Evaluator",
            "version": "1.0.0",
            "llm": os.getenv("GROQ_EVAL_MODEL", "groq/compound-mini"),
            "embeddings": "None"
        }
