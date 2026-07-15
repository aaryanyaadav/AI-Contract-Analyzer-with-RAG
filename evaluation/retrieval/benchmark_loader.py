import csv
import os
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class BenchmarkRow:
    question_id: str
    document_id: str
    question: str
    expected_answer: str
    relevant_chunk_indices: List[int]
    relevant_chunk_ids: List[str]
    question_type: Optional[str] = None
    difficulty: Optional[str] = None
    section: Optional[str] = None

class BenchmarkLoader:
    @staticmethod
    def load_benchmark(file_path: str) -> List[BenchmarkRow]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Benchmark file not found at: {file_path}")

        rows = []
        with open(file_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse relevant chunk indices (e.g. "0" or "0,1" or "0;1")
                indices_str = row.get("relevant_chunk_index", "") or ""
                indices = []
                for part in indices_str.replace(";", ",").split(","):
                    part = part.strip()
                    if part:
                        try:
                            indices.append(int(part))
                        except ValueError:
                            pass

                # Parse relevant chunk IDs (e.g. UUIDs, could be comma/semicolon separated)
                ids_str = row.get("relevant_chunk_id", "") or ""
                ids = []
                for part in ids_str.replace(";", ",").split(","):
                    part = part.strip()
                    if part:
                        ids.append(part)

                benchmark_row = BenchmarkRow(
                    question_id=row.get("question_id", "").strip(),
                    document_id=row.get("document_id", "").strip(),
                    question=row.get("question", "").strip(),
                    expected_answer=row.get("expected_answer", "").strip(),
                    relevant_chunk_indices=indices,
                    relevant_chunk_ids=ids,
                    question_type=row.get("question_type") or None,
                    difficulty=row.get("difficulty") or None,
                    section=row.get("section") or None
                )
                rows.append(benchmark_row)
        return rows
