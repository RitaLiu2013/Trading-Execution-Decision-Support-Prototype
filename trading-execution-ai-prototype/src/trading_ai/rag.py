from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import numpy as np

from .config import EMBEDDING_MODEL_NAME, KNOWLEDGE_DIR, REFUSAL_TEXT
from .llm import generate_grounded_answer


@dataclass
class RetrievalResult:
    score: float
    source: str
    chunk_id: int
    text: str


def chunk_paragraphs(text: str, paragraphs_per_chunk: int = 3, overlap: int = 1) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if overlap >= paragraphs_per_chunk:
        raise ValueError("overlap must be smaller than paragraphs_per_chunk")
    chunks: list[str] = []
    step = paragraphs_per_chunk - overlap
    for start in range(0, len(paragraphs), step):
        group = paragraphs[start:start + paragraphs_per_chunk]
        if not group:
            break
        chunks.append("\n\n".join(group))
        if start + paragraphs_per_chunk >= len(paragraphs):
            break
    return chunks


class TradingRAG:
    def __init__(
        self,
        knowledge_dir: Path | str = KNOWLEDGE_DIR,
        embedding_model_name: str = EMBEDDING_MODEL_NAME,
    ):
        self.knowledge_dir = Path(knowledge_dir)
        self.embedding_model_name = embedding_model_name
        self.documents: list[dict] = []
        self.document_embeddings = None
        self._embedding_model = None

    def _get_embedding_model(self):
        if self._embedding_model is None:
            from sentence_transformers import SentenceTransformer
            self._embedding_model = SentenceTransformer(self.embedding_model_name, device="cpu")
        return self._embedding_model

    def build_index(self) -> None:
        self.documents = []
        for file_path in sorted(self.knowledge_dir.glob("*.txt")):
            text = file_path.read_text(encoding="utf-8")
            for chunk_id, chunk in enumerate(chunk_paragraphs(text, 3, 1)):
                self.documents.append({"source": file_path.name, "chunk_id": chunk_id, "text": chunk})
        model = self._get_embedding_model()
        texts = [d["text"] for d in self.documents]
        self.document_embeddings = model.encode(texts, convert_to_numpy=True, device="cpu", show_progress_bar=False)

    def retrieve(self, question: str, top_k: int = 3) -> list[RetrievalResult]:
        if self.document_embeddings is None:
            self.build_index()
        model = self._get_embedding_model()
        query_embedding = model.encode([question], convert_to_numpy=True, device="cpu")
        from sklearn.metrics.pairwise import cosine_similarity
        scores = cosine_similarity(query_embedding, self.document_embeddings)[0]
        top_indices = scores.argsort()[::-1][:top_k]
        return [
            RetrievalResult(
                score=float(scores[i]),
                source=self.documents[int(i)]["source"],
                chunk_id=int(self.documents[int(i)]["chunk_id"]),
                text=self.documents[int(i)]["text"],
            )
            for i in top_indices
        ]

    @staticmethod
    def build_context(results: list[RetrievalResult]) -> str:
        return "\n\n---\n\n".join(
            f"[Source: {r.source} | Chunk: {r.chunk_id}]\n{r.text}" for r in results
        )

    def answer(self, question: str, top_k: int = 3) -> dict:
        results = self.retrieve(question, top_k=top_k)
        context = self.build_context(results)
        answer = generate_grounded_answer(question, context)
        if answer is None:
            answer = (
                "Local LLM unavailable. Retrieval succeeded; inspect the returned evidence or start Ollama "
                "with qwen3:4b-instruct."
            )
        return {
            "question": question,
            "answer": answer,
            "retrieved_chunks": [r.__dict__ for r in results],
        }
