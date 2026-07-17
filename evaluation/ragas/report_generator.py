import os
import csv
import json
from typing import List, Dict, Any, Optional

class RagasReportGenerator:
    def __init__(self, reports_dir: Optional[str] = None):
        if reports_dir is None:
            # Resolve relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.reports_dir = os.path.join(base_dir, "evaluation", "reports")
        else:
            self.reports_dir = os.path.abspath(reports_dir)
            
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_reports(self, results: List[Dict[str, Any]], summary: Dict[str, Any]) -> tuple:
        """
        Saves detailed metrics per query to CSV, and saves aggregate scores to JSON.
        """
        csv_path = os.path.join(self.reports_dir, "ragas_results.csv")
        json_path = os.path.join(self.reports_dir, "ragas_report.json")

        csv_headers = [
            "question_id",
            "document_id",
            "question",
            "expected_answer",
            "generated_answer",
            "retrieved_context",
            "faithfulness",
            "answer_correctness",
            "context_precision",
            "context_recall"
        ]

        # Write detailed CSV results
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=csv_headers)
            writer.writeheader()
            for row in results:
                writer.writerow({
                    "question_id": row["question_id"],
                    "document_id": row["document_id"],
                    "question": row["question"],
                    "expected_answer": row["expected_answer"],
                    "generated_answer": row["generated_answer"],
                    "retrieved_context": json.dumps(row["retrieved_context"]),
                    "faithfulness": row["faithfulness"],
                    "answer_correctness": row["answer_correctness"],
                    "context_precision": row["context_precision"],
                    "context_recall": row["context_recall"]
                })

        import math
        def sanitize_val(v):
            if isinstance(v, float) and math.isnan(v):
                return None
            return v

        # Sanitize summary values for JSON compatibility
        json_summary = {
            "benchmark_size": summary.get("benchmark_size"),
            "backend": summary.get("backend"),
            "evaluation_engine": summary.get("evaluation_engine"),
            "faithfulness": sanitize_val(summary.get("faithfulness")),
            "answer_correctness": sanitize_val(summary.get("answer_correctness")),
            "context_precision": sanitize_val(summary.get("context_precision")),
            "context_recall": sanitize_val(summary.get("context_recall"))
        }

        # Write summary JSON
        with open(json_path, mode="w", encoding="utf-8") as f:
            json.dump(json_summary, f, indent=4)

        # Sanitize detailed results values for JSON compatibility
        json_results = []
        for row in results:
            sanitized_row = dict(row)
            for k in ["faithfulness", "answer_correctness", "context_precision", "context_recall"]:
                if k in sanitized_row:
                    sanitized_row[k] = sanitize_val(sanitized_row[k])
            json_results.append(sanitized_row)

        # Write detailed cached results JSON
        results_json_path = os.path.join(self.reports_dir, "ragas_results.json")
        with open(results_json_path, mode="w", encoding="utf-8") as f:
            json.dump(json_results, f, indent=4)

        print(f"[RagasReportGenerator] Saved detailed results to: {csv_path}")
        print(f"[RagasReportGenerator] Saved detailed JSON cache to: {results_json_path}")
        print(f"[RagasReportGenerator] Saved aggregate summary to: {json_path}")
        
        return csv_path, json_path
