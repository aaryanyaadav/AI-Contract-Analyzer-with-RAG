import os
import sys
import argparse
import yaml

# Add the project root to sys.path to enable importing local packages
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from evaluation.retrieval.benchmark_loader import BenchmarkLoader
from evaluation.retrieval.retrieval_evaluator import RetrievalEvaluator
from evaluation.retrieval.report_generator import ReportGenerator

def load_yaml_config(config_path: str) -> dict:
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"[Warning] Failed to read config file {config_path}: {e}")
    return {}

def main():
    # Base config path
    config_path = os.path.join(project_root, "evaluation", "config.yaml")
    yaml_config = load_yaml_config(config_path)
    
    parser = argparse.ArgumentParser(description="Retrieval Evaluation CLI tool")
    parser.add_argument(
        "--session-id",
        type=str,
        default=yaml_config.get("session_id"),
        help="Session ID to automatically locate ChromaDB path."
    )
    parser.add_argument(
        "--chroma-path",
        type=str,
        default=yaml_config.get("chroma_path"),
        help="Direct folder path to ChromaDB database."
    )
    parser.add_argument(
        "--benchmark-path",
        type=str,
        default=yaml_config.get("benchmark"),
        help="Path to the benchmark dataset CSV file."
    )
    parser.add_argument(
        "-k", "--top-k",
        type=int,
        default=yaml_config.get("top_k", 5),
        help="Top-K retrieval limit (default: 5)."
    )

    args = parser.parse_args()

    # Determine benchmark path fallback
    benchmark_path = args.benchmark_path
    if not benchmark_path:
        benchmark_path = os.path.join(project_root, "evaluation", "benchmark", "Benchmark dataset.csv")
    else:
        # Resolve path relative to project root if it is a relative path and doesn't exist directly
        if not os.path.isabs(benchmark_path) and not os.path.exists(benchmark_path):
            benchmark_path = os.path.join(project_root, benchmark_path)

    # Require either session-id or chroma-path
    if not args.session_id and not args.chroma_path:
        raise ValueError("You must provide either --session-id or --chroma-path (or specify them in config.yaml).")

    print("=" * 60)
    print("RETRIEVAL EVALUATION")
    print("-" * 60)
    print(f"Benchmark path:  {benchmark_path}")
    if args.session_id:
        print(f"Session ID:      {args.session_id}")
    if args.chroma_path:
        print(f"Chroma DB Path:  {args.chroma_path}")
    print(f"Top-K (K):       {args.top_k}")
    print("=" * 60)

    # 1. Load benchmark dataset
    print("[1/3] Loading benchmark dataset...")
    benchmark_rows = BenchmarkLoader.load_benchmark(benchmark_path)
    print(f"Successfully loaded {len(benchmark_rows)} queries.")

    # 2. Evaluate
    print("[2/3] Executing retrieval pipeline and computing metrics...")
    evaluator = RetrievalEvaluator(session_id=args.session_id, chroma_path=args.chroma_path)
    output = evaluator.evaluate(benchmark_rows, k=args.top_k)

    # 3. Generate Reports
    print("[3/3] Generating evaluation reports...")
    report_gen = ReportGenerator()
    csv_path, json_path = report_gen.generate_reports(output)

    # Print summary metrics to console
    summary = output["summary"]
    print("=" * 60)
    print("EVALUATION RESULTS SUMMARY")
    print("-" * 60)
    print(f"Benchmark Size: {summary['benchmark_size']} queries")
    print(f"Precision@{args.top_k}: {summary['Precision@K']:.4f}")
    print(f"Recall@{args.top_k}:    {summary['Recall@K']:.4f}")
    print(f"Hit@{args.top_k}:       {summary['Hit@K']:.4f}")
    print(f"MRR:            {summary['MRR']:.4f}")
    print("=" * 60)

if __name__ == "__main__":
    main()
