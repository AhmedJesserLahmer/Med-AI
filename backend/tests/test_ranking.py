from ranking import ndcg_at_k, reciprocal_rank_fusion


def test_ndcg_perfect_ranking_scores_one():
    assert ndcg_at_k([2, 2, 1, 0], k=4) == 1.0


def test_ndcg_worse_ranking_scores_less_than_one():
    perfect = ndcg_at_k([2, 1, 0], k=3)
    worse = ndcg_at_k([0, 1, 2], k=3)
    assert worse < perfect


def test_ndcg_no_relevant_docs_is_zero():
    assert ndcg_at_k([0, 0, 0], k=3) == 0.0


def test_ndcg_truncates_to_k():
    # A relevant doc beyond k must not help the score.
    assert ndcg_at_k([0, 0, 0, 2], k=3) == 0.0


def test_rrf_prefers_doc_ranked_highly_in_both_lists():
    dense = ["a", "b", "c"]
    sparse = ["b", "a", "c"]
    fused = reciprocal_rank_fusion([dense, sparse])
    # "a" and "b" both sit near the top of both lists, so either can win the
    # top spot, but "c" (bottom of both) must never outrank them.
    assert fused[0] in ("a", "b")
    assert fused[-1] == "c"


def test_rrf_credits_doc_present_in_only_one_list():
    dense = ["a", "b"]
    sparse = ["c", "b"]
    fused = reciprocal_rank_fusion([dense, sparse])
    assert set(fused) == {"a", "b", "c"}
    # "b" appears in both lists, so it should outrank docs seen in only one.
    assert fused[0] == "b"
