import os
import sys
import argparse
import yaml

import json
import csv

# Add project root to sys.path to enable importing local packages
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(override=True)

from evaluation.retrieval.benchmark_loader import BenchmarkLoader
from evaluation.ragas.ragas_runner import RagasRunner
from evaluation.ragas.ragas_dataset_builder import RagasDatasetBuilder
from evaluation.ragas.ragas_evaluator import get_evaluator
from evaluation.ragas.report_generator import RagasReportGenerator

def load_yaml_config(config_path: str) -> dict:
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"[Warning] Failed to read config file {config_path}: {e}")
    return {}

def main():
    config_path = os.path.join(project_root, "evaluation", "config.yaml")
    yaml_config = load_yaml_config(config_path)

    parser = argparse.ArgumentParser(description="Ragas Evaluation Module Runner")
    parser.add_argument(
        "--session-id",
        type=str,
        default=yaml_config.get("session_id"),
        help="Session ID to automatically locate ChromaDB path when running in-process."
    )
    parser.add_argument(
        "--benchmark-path",
        type=str,
        default=yaml_config.get("benchmark"),
        help="Path to the benchmark dataset CSV file."
    )
    parser.add_argument(
        "--backend-url",
        type=str,
        default=yaml_config.get("backend_url"),
        help="URL of the running backend API server. If not set, runs using in-process TestClient."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=40,
        help="Limit the number of benchmark queries to evaluate (default: 40 to avoid rate limits)."
    )
    parser.add_argument(
        "--evaluator-type",
        type=str,
        choices=["auto", "official", "fallback"],
        default="fallback",
        help="Evaluation engine type to run (default: fallback for token efficiency)."
    )

    args = parser.parse_args()

    # Determine benchmark path fallback
    benchmark_path = args.benchmark_path
    if not benchmark_path:
        benchmark_path = os.path.join(project_root, "evaluation", "benchmark", "Benchmark dataset.csv")
    else:
        if not os.path.isabs(benchmark_path) and not os.path.exists(benchmark_path):
            benchmark_path = os.path.join(project_root, benchmark_path)

    print("=" * 60)
    print("RAGAS EVALUATION RUNNER")
    print("-" * 60)
    print(f"Benchmark Path: {benchmark_path}")
    print(f"Session ID:     {args.session_id}")
    print(f"Backend URL:    {args.backend_url or 'In-Process TestClient'}")
    if args.limit:
        print(f"Query Limit:    {args.limit}")
    print("=" * 60)

    # 1. Load from cache if present, otherwise load benchmark and query backend
    results_json_path = os.path.join(project_root, "evaluation", "reports", "ragas_results.json")
    results_csv_path = os.path.join(project_root, "evaluation", "reports", "ragas_results.csv")
    results_csv_path_typo = os.path.join(project_root, "evaluation", "reports", "regas_results.csv")
    eval_dataset = []
    use_cached_data = False

    if os.path.exists(results_json_path):
        try:
            with open(results_json_path, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                if cached_data and isinstance(cached_data, list):
                    if args.limit:
                        cached_data = cached_data[:args.limit]
                    
                    for item in cached_data:
                        eval_dataset.append({
                            "question_id": item["question_id"],
                            "document_id": item["document_id"],
                            "question": item["question"],
                            "expected_answer": item["expected_answer"],
                            "generated_answer": item["generated_answer"],
                            "retrieved_context": item["retrieved_context"],
                            "retrieved_chunk_ids": item.get("retrieved_chunk_ids", []),
                            "chunk_metadata": item.get("chunk_metadata", []),
                            "rerank_scores": item.get("rerank_scores", [])
                        })
                    use_cached_data = True
                    print(f"[Info] Found cached results in {results_json_path}. Skipping querying (Steps 1 & 2) and loading {len(eval_dataset)} cached queries...")
        except Exception as e:
            print(f"[Warning] Failed to load cached data from {results_json_path}: {e}. Trying CSV fallback...")

    if not use_cached_data:
        target_csv_path = None
        if os.path.exists(results_csv_path):
            target_csv_path = results_csv_path
        elif os.path.exists(results_csv_path_typo):
            target_csv_path = results_csv_path_typo

        if target_csv_path:
            try:
                with open(target_csv_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    cached_data = list(reader)
                    if cached_data:
                        if args.limit:
                            cached_data = cached_data[:args.limit]
                        
                        for item in cached_data:
                            try:
                                context = json.loads(item["retrieved_context"])
                            except Exception:
                                context = [item["retrieved_context"]]
                                
                            eval_dataset.append({
                                "question_id": item["question_id"],
                                "document_id": item["document_id"],
                                "question": item["question"],
                                "expected_answer": item["expected_answer"],
                                "generated_answer": item["generated_answer"],
                                "retrieved_context": context,
                                "retrieved_chunk_ids": [],
                                "chunk_metadata": [],
                                "rerank_scores": []
                            })
                        use_cached_data = True
                        print(f"[Info] Found cached results in {target_csv_path}. Skipping querying (Steps 1 & 2) and loading {len(eval_dataset)} cached queries...")
            except Exception as e:
                print(f"[Warning] Failed to load cached data from {target_csv_path}: {e}. Proceeding with querying backend.")

    if not use_cached_data:
        # 1. Load benchmark dataset
        print("[1/4] Loading benchmark dataset...")
        benchmark_rows = BenchmarkLoader.load_benchmark(benchmark_path)
        if args.limit:
            benchmark_rows = benchmark_rows[:args.limit]
        print(f"Loaded {len(benchmark_rows)} queries for evaluation.")

        # 2. Query backend to build dataset
        print("[2/4] Querying backend RAG pipeline...")
        runner = RagasRunner(backend_url=args.backend_url, session_id=args.session_id)
        builder = RagasDatasetBuilder(runner)
        eval_dataset = builder.build_dataset(benchmark_rows)

        # Save intermediate results to cache immediately to prevent losing progress if Step 3 fails
        if eval_dataset:
            try:
                os.makedirs(os.path.dirname(results_json_path), exist_ok=True)
                with open(results_json_path, "w", encoding="utf-8") as f:
                    json.dump(eval_dataset, f, indent=4)
                print(f"[Info] Saved intermediate query dataset cache to {results_json_path}")
            except Exception as e:
                print(f"[Warning] Failed to save intermediate query dataset cache: {e}")

    # 3. Evaluate Ragas metrics
    print("\n[3/4] Evaluating Ragas metrics...")
    evaluator = get_evaluator(args.evaluator_type)
    engine_info = evaluator.get_engine_info()
    print(f"Evaluation engine: {engine_info['name']} (Model: {engine_info['llm']})")
    
    results = evaluator.evaluate_dataset(eval_dataset)

    # Compute aggregate metrics safely, filtering out NaN/failed evaluations
    import math
    total = len(results)
    
    def safe_average(key):
        valid_vals = []
        for r in results:
            val = r.get(key)
            if val is not None:
                try:
                    val_float = float(val)
                    if not math.isnan(val_float):
                        valid_vals.append(val_float)
                except ValueError:
                    pass
        return sum(valid_vals) / len(valid_vals) if valid_vals else 0.0

    avg_faithfulness = safe_average("faithfulness")
    avg_correctness = safe_average("answer_correctness")
    avg_precision = safe_average("context_precision")
    avg_recall = safe_average("context_recall")

    summary = {
        "benchmark_size": total,
        "backend": args.backend_url or "In-Process TestClient",
        "evaluation_engine": engine_info,
        "faithfulness": avg_faithfulness,
        "answer_correctness": avg_correctness,
        "context_precision": avg_precision,
        "context_recall": avg_recall
    }

    # 4. Generate reports
    print("\n[4/4] Writing report files...")
    report_gen = RagasReportGenerator()
    csv_path, json_path = report_gen.generate_reports(results, summary)

    # Print summary metrics to console
    print("=" * 60)
    print("EVALUATION RESULTS SUMMARY")
    print("-" * 60)
    print(f"Benchmark Size:     {summary['benchmark_size']} queries")
    print(f"Faithfulness:       {summary['faithfulness']:.4f}")
    print(f"Answer Correctness: {summary['answer_correctness']:.4f}")
    print(f"Context Precision:  {summary['context_precision']:.4f}")
    print(f"Context Recall:     {summary['context_recall']:.4f}")
    print("=" * 60)

if __name__ == "__main__":
    main()
