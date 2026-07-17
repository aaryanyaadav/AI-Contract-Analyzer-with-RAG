from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseEvaluator(ABC):
    """
    Abstract Base Class defining the common interface for Ragas Evaluators.
    """
    @abstractmethod
    def initialize(self) -> None:
        """
        Initializes the evaluator, loading any required models or packages.
        Should raise an exception if initialization fails.
        """
        pass

    @abstractmethod
    def evaluate_dataset(self, dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Evaluates a dataset list of dictionaries and appends faithfulness,
        answer_correctness, context_precision, and context_recall scores.
        """
        pass

    @abstractmethod
    def get_engine_info(self) -> Dict[str, str]:
        """
        Returns structured metadata information about the evaluation engine,
        including model details and versions.
        """
        pass
