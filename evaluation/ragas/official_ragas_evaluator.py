import os
import importlib
from typing import List, Dict, Any
from evaluation.ragas.base_evaluator import BaseEvaluator

class OfficialRagasEvaluator(BaseEvaluator):
    def __init__(self):
        self.ragas_version = "0.2.x"
        self._initialized = False
        self._evaluate_fn = None
        self._metrics = None
        self._llm = None
        self._embeddings = None
        self._Dataset_class = None

    def initialize(self) -> None:
        # Dynamically import modules to avoid static linting and IDE validation errors
        ragas = importlib.import_module("ragas")
        datasets = importlib.import_module("datasets")
        self._Dataset_class = getattr(datasets, "Dataset")
        
        ragas_metrics = importlib.import_module("ragas.metrics")
        faithfulness = getattr(ragas_metrics, "faithfulness")
        answer_correctness = getattr(ragas_metrics, "answer_correctness")
        context_precision = getattr(ragas_metrics, "context_precision")
        context_recall = getattr(ragas_metrics, "context_recall")
        
        langchain_groq = importlib.import_module("langchain_groq")
        ChatGroq = getattr(langchain_groq, "ChatGroq")
        
        langchain_huggingface = importlib.import_module("langchain_huggingface")
        HuggingFaceEmbeddings = getattr(langchain_huggingface, "HuggingFaceEmbeddings")
        
        ragas_llms = importlib.import_module("ragas.llms")
        LangchainLLMWrapper = getattr(ragas_llms, "LangchainLLMWrapper")
        
        ragas_embeddings = importlib.import_module("ragas.embeddings")
        LangchainEmbeddingsWrapper = getattr(ragas_embeddings, "LangchainEmbeddingsWrapper")
        
        ragas_run_config = importlib.import_module("ragas.run_config")
        self._RunConfig_class = getattr(ragas_run_config, "RunConfig")
        
        try:
            self.ragas_version = ragas.__version__
        except AttributeError:
            pass

        # Check API key based on provider before initializing
        provider = os.getenv("LLM_PROVIDER", "groq").lower()
        if provider == "together":
            if not os.getenv("TOGETHER_API_KEY"):
                raise ValueError("TOGETHER_API_KEY environment variable is missing.")
            # Dynamically import ChatOpenAI
            langchain_openai = importlib.import_module("langchain_openai")
            ChatOpenAI = getattr(langchain_openai, "ChatOpenAI")
            llm = ChatOpenAI(
                model="meta-llama/Meta-Llama-3-8b-instruct",
                openai_api_key=os.getenv("TOGETHER_API_KEY"),
                openai_api_base="https://api.together.xyz/v1"
            )
            print("[OfficialRagasEvaluator] Initialized LLM using Together AI (meta-llama/Meta-Llama-3-8b-instruct)")
        else:
            if not os.getenv("GROQ_API_KEY"):
                raise ValueError("GROQ_API_KEY environment variable is missing.")
            groq_model = os.getenv("GROQ_EVAL_MODEL", "groq/compound-mini")
            llm = ChatGroq(model=groq_model)
            print(f"[OfficialRagasEvaluator] Initialized LLM using Groq ({groq_model})")
            
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        # Wrap for Ragas
        self._llm = LangchainLLMWrapper(llm)
        self._embeddings = LangchainEmbeddingsWrapper(embeddings)

        # Bind wrappers to metrics
        self._metrics = [faithfulness, answer_correctness, context_precision, context_recall]
        for metric in self._metrics:
            metric.llm = self._llm
            if hasattr(metric, "embeddings"):
                metric.embeddings = self._embeddings

        self._evaluate_fn = getattr(ragas, "evaluate")
        self._initialized = True

    def evaluate_dataset(self, dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self._initialized:
            raise RuntimeError("OfficialRagasEvaluator has not been initialized.")

        # Map dataset list of dicts to dataset expected by datasets.Dataset
        questions = [item["question"] for item in dataset]
        answers = [item["generated_answer"] for item in dataset]
        contexts = [item["retrieved_context"] for item in dataset]
        ground_truths = [item["expected_answer"] for item in dataset]

        data_dict = {
            "question": questions,
            "user_input": questions,
            "answer": answers,
            "response": answers,
            "contexts": contexts,
            "retrieved_contexts": contexts,
            "ground_truth": ground_truths,
            "reference": ground_truths
        }

        ragas_dataset = self._Dataset_class.from_dict(data_dict)

        # Configure run_config to throttle concurrency and handle rate limits
        run_config = self._RunConfig_class(
            max_workers=1,      # Sequential queries to stay under Groq's TPM limits
            max_retries=10,     # Retry on rate limit (429) errors
            timeout=120,        # Give queries ample time
            max_wait=60         # Cooling time between retries
        )

        # Run official evaluate function
        result = self._evaluate_fn(
            dataset=ragas_dataset,
            metrics=self._metrics,
            llm=self._llm,
            embeddings=self._embeddings,
            run_config=run_config
        )

        df = result.to_pandas()
        evaluated_dataset = []
        for idx, item in enumerate(dataset):
            evaluated_item = dict(item)
            evaluated_item["faithfulness"] = float(df.iloc[idx]["faithfulness"])
            evaluated_item["answer_correctness"] = float(df.iloc[idx]["answer_correctness"])
            evaluated_item["context_precision"] = float(df.iloc[idx]["context_precision"])
            evaluated_item["context_recall"] = float(df.iloc[idx]["context_recall"])
            evaluated_dataset.append(evaluated_item)
            
        return evaluated_dataset

    def get_engine_info(self) -> Dict[str, str]:
        return {
            "name": "Official Ragas",
            "version": self.ragas_version,
            "llm": os.getenv("GROQ_EVAL_MODEL", "groq/compound-mini"),
            "embeddings": "all-MiniLM-L6-v2"
        }
