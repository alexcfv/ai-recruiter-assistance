from collections import defaultdict
from typing import Dict, DefaultDict, List, Tuple
from models.search_results import SearchResultItem


def group_by_resume(results: List[SearchResultItem]) -> DefaultDict[str, List[SearchResultItem]]:
    grouped: DefaultDict[str, List[SearchResultItem]] = defaultdict(list)

    for r in results:
        grouped[r.source].append(r)

    return grouped


def compute_scores(grouped: Dict[str, List[SearchResultItem]], best_weight: float = 0.7, avg_weight: float = 0.3) -> Dict[str, float]:
    scores: Dict[str, float] = {}

    for source, chunks in grouped.items():
        best = min(c.distance for c in chunks)
        avg = sum(c.distance for c in chunks) / len(chunks)

        score = best_weight * best + avg_weight * avg
        scores[source] = score

    return scores


def rank_candidates(scores: Dict[str, float]) -> List[Tuple[str, float]]:
    return sorted(scores.items(), key=lambda x: x[1])


def find_best_candidates(results: List[SearchResultItem], best_weight: float = 0.7, avg_weight: float = 0.3) -> List[Tuple[str, float]]:
    grouped = group_by_resume(results)
    scores = compute_scores(grouped, best_weight, avg_weight)
    return rank_candidates(scores)
