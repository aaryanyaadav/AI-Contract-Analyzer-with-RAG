import os
import csv
import json
from typing import List, Dict, Any

class ReportGenerator:
    """
    Generates CSV and JSON reports for System Evaluation.
    """
    def __init__(self, reports_dir: str = None):
        if reports_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.reports_dir = os.path.join(base_dir, "evaluation", "reports")
        else:
            self.reports_dir = os.path.abspath(reports_dir)
            
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_reports(self, metrics_list: List[Dict[str, Any]], aggregate_report: Dict[str, Any]) -> tuple:
        csv_path = os.path.join(self.reports_dir, "system_results.csv")
        json_path = os.path.join(self.reports_dir, "system_report.json")

        csv_headers = [
            "question_id",
            "document_id",
            "question",
            "embedding_time",
            "retrieval_time",
            "prompt_construction_time",
            "llm_generation_time",
            "total_response_time",
            "number_of_retrieved_chunks",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "success",
            "error"
        ]

        # Save system_results.csv
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=csv_headers)
            writer.writeheader()
            for row in metrics_list:
                writer.writerow({
                    "question_id": row["question_id"],
                    "document_id": row["document_id"],
                    "question": row["question"],
                    "embedding_time": row["embedding_time"],
                    "retrieval_time": row["retrieval_time"],
                    "prompt_construction_time": row["prompt_construction_time"],
                    "llm_generation_time": row["llm_generation_time"],
                    "total_response_time": row["total_response_time"],
                    "number_of_retrieved_chunks": row["number_of_retrieved_chunks"],
                    "prompt_tokens": row["prompt_tokens"],
                    "completion_tokens": row["completion_tokens"],
                    "total_tokens": row["total_tokens"],
                    "success": row["success"],
                    "error": row["error"]
                })

        # Save system_report.json
        with open(json_path, mode="w", encoding="utf-8") as f:
            json.dump(aggregate_report, f, indent=4)

        print(f"[ReportGenerator] Saved detailed results to: {csv_path}")
        print(f"[ReportGenerator] Saved aggregate summary to: {json_path}")
        
        return csv_path, json_path
