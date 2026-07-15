import os
import csv
import json
from typing import Dict, Any, Optional

class ReportGenerator:
    def __init__(self, reports_dir: Optional[str] = None):
        if reports_dir is None:
            # Resolve relative to the project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.reports_dir = os.path.join(base_dir, "evaluation", "reports")
        else:
            self.reports_dir = os.path.abspath(reports_dir)
            
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_reports(self, evaluation_output: Dict[str, Any]) -> tuple:
        """
        Generates CSV (detailed per-question metrics) and JSON (aggregate metrics) reports.
        """
        results = evaluation_output["results"]
        summary = evaluation_output["summary"]

        csv_path = os.path.join(self.reports_dir, "retrieval_results.csv")
        json_path = os.path.join(self.reports_dir, "retrieval_report.json")

        csv_headers = [
            "question_id",
            "question",
            "document_id",
            "expected_chunk_id",
            "retrieved_chunk_ids",
            "retrieved_scores",
            "hit@k",
            "precision@k",
            "recall@k",
            "reciprocal_rank"
        ]

        # Write detailed CSV results
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=csv_headers)
            writer.writeheader()
            for row in results:
                # expected_chunk_id column handles multiple expected chunk IDs by joining them with commas
                expected_chunk_id_val = ",".join(row["expected_chunk_ids"])
                
                writer.writerow({
                    "question_id": row["question_id"],
                    "question": row["question"],
                    "document_id": row["document_id"],
                    "expected_chunk_id": expected_chunk_id_val,
                    "retrieved_chunk_ids": json.dumps(row["retrieved_chunk_ids"]),
                    "retrieved_scores": json.dumps(row["retrieved_scores"]),
                    "hit@k": row["hit@k"],
                    "precision@k": row["precision@k"],
                    "recall@k": row["recall@k"],
                    "reciprocal_rank": row["reciprocal_rank"]
                })

        # Write aggregate summary JSON
        with open(json_path, mode="w", encoding="utf-8") as f:
            json.dump(summary, f, indent=4)

        print(f"[ReportGenerator] Saved detailed results to: {csv_path}")
        print(f"[ReportGenerator] Saved aggregate summary to: {json_path}")
        
        return csv_path, json_path
