import os
import sys
import argparse
import yaml
import requests
import tqdm

# Add project root to sys.path to enable importing local packages
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(override=True)

from evaluation.retrieval.benchmark_loader import BenchmarkLoader
from evaluation.metrics_collector import MetricsCollector
from evaluation.system_evaluator import SystemEvaluator
from evaluation.report_generator import ReportGenerator

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

    parser = argparse.ArgumentParser(description="RAG System Performance Evaluation Runner")
    parser.add_argument(
        "--session-id",
        type=str,
        default=yaml_config.get("session_id"),
        help="Session ID to locate ChromaDB path."
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
        default=yaml_config.get("limit", 40),
        help="Limit the number of benchmark queries to evaluate (default: 40)."
    )

    args = parser.parse_args()

    # Determine benchmark path fallback
    benchmark_path = args.benchmark_path
    if not benchmark_path:
        benchmark_path = os.path.join(project_root, "evaluation", "benchmark", "Benchmark dataset.csv")
    else:
        if not os.path.isabs(benchmark_path) and not os.path.exists(benchmark_path):
            benchmark_path = os.path.join(project_root, benchmark_path)

    # Setup test client if running in-process
    use_in_process = not args.backend_url or args.backend_url.lower() in ("none", "null", "")

    print("=" * 60)
    print("SYSTEM PERFORMANCE EVALUATION RUNNER")
    print("-" * 60)
    print(f"Benchmark Path: {benchmark_path}")
    print(f"Session ID:     {args.session_id}")
    print(f"Backend URL:    {args.backend_url if not use_in_process else 'In-Process TestClient'}")
    if args.limit:
        print(f"Query Limit:    {args.limit}")
    print("=" * 60)

    # 1. Load benchmark dataset
    print("[1/4] Loading benchmark dataset...")
    benchmark_rows = BenchmarkLoader.load_benchmark(benchmark_path)
    if args.limit:
        benchmark_rows = benchmark_rows[:args.limit]
    print(f"Loaded {len(benchmark_rows)} queries for evaluation.")

    test_client = None
    if use_in_process:
        from fastapi.testclient import TestClient
        from backend.api.main import app
        test_client = TestClient(app)

    # 2. Query backend to collect metrics
    print("\n[2/4] Querying backend and collecting performance metrics...")
    collector = MetricsCollector()

    for row in tqdm.tqdm(benchmark_rows, desc="Evaluating RAG System Performance"):
        payload = {
            "query": row.question,
            "document_id": row.document_id,
            "session_id": args.session_id,
            "evaluation_mode": True
        }

        try:
            if not use_in_process:
                url = f"{args.backend_url.rstrip('/')}/chat"
                response = requests.post(url, json=payload)
                response.raise_for_status()
                res_json = response.json()
            else:
                response = test_client.post("/chat", json=payload)
                response.raise_for_status()
                res_json = response.json()

            collector.collect(
                query_id=row.question_id,
                document_id=row.document_id,
                query=row.question,
                api_response=res_json
            )
        except Exception as e:
            # Record execution failure
            print(f"\n[Error] Request failed for query {row.question_id}: {e}")
            collector.collect(
                query_id=row.question_id,
                document_id=row.document_id,
                query=row.question,
                api_response={"success": False, "error": str(e)}
            )

    # 3. Analyze and Aggregate Metrics
    print("\n[3/4] Aggregating performance results...")
    metrics_list = collector.get_all_metrics()
    agg_report = SystemEvaluator.evaluate(metrics_list)

    # 4. Generate report files
    print("\n[4/4] Writing report files...")
    report_gen = ReportGenerator()
    csv_path, json_path = report_gen.generate_reports(metrics_list, agg_report)

    # Print summary metrics to console
    print("=" * 60)
    print("SYSTEM PERFORMANCE RESULTS SUMMARY")
    print("-" * 60)
    print(f"Total Queries Evaluated: {agg_report['total_runs']}")
    print(f"Successful Queries:      {agg_report['successful_runs']}")
    print("-" * 60)
    
    timing = agg_report.get("timing_summary", {})
    for step, stats in timing.items():
        step_title = step.replace("_", " ").title()
        print(f"{step_title}:")
        print(f"  Avg: {stats['average']:.4f}s  |  Min: {stats['min']:.4f}s  |  Max: {stats['max']:.4f}s")
        print(f"  P50: {stats['median']:.4f}s  |  P95: {stats['p95']:.4f}s  |  P99: {stats['p99']:.4f}s")
        print()
        
    tokens = agg_report.get("token_summary", {})
    print("Token Usage averages:")
    print(f"  Average Prompt Tokens:     {tokens.get('average_prompt_tokens', 0.0):.1f}")
    print(f"  Average Completion Tokens: {tokens.get('average_completion_tokens', 0.0):.1f}")
    print(f"  Average Total Tokens:      {tokens.get('average_total_tokens', 0.0):.1f}")
    print("-" * 60)
    
    chunks = agg_report.get("chunk_summary", {})
    print(f"Average Retrieved Chunks:    {chunks.get('average_retrieved_chunks', 0.0):.2f}")
    print("=" * 60)

if __name__ == "__main__":
    main()
