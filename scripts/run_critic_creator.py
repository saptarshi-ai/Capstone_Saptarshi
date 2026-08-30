"""
Critic-Creator red-team run.
Usage: python scripts/run_critic_creator.py
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.eval.golden import load_golden_set
from src.eval.critic_creator import CriticCreatorAgent
from src.rag.retriever import DenseRetriever
from src.rag.vector_store import ChromaDBStore
from src.rag.embeddings import get_default_embedder


def main():
    dataset = load_golden_set()
    embedder = get_default_embedder()
    store = ChromaDBStore(collect_name="capstone_rag", persist_dir="data/db")
    retriever = DenseRetriever(vector_store=store, embedder=embedder)
    agent = CriticCreatorAgent(max_rounds=2)

    for case in dataset:
        q = case["question"]
        retrieved = retriever.retrieve(q, top_k=5)
        context = "\n\n".join(c["text"] for c in retrieved)
        result = agent.run(query=q, context=context)
        print(f"\n[{case['id']}] {q}")
        print(f"  Rounds: {result['rounds']}")
        print(f"  Final: {result['final_answer'][:200]}...")


if __name__ == "__main__":
    main()
