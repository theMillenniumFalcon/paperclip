"""Vector facts via Supabase pgvector. See docs/memory/semantic.md#supabase."""

from __future__ import annotations

import os
import uuid

from paperclip.config import Settings


class SupabaseFactStore:
    def __init__(self, settings: Settings):
        import openai
        from supabase import create_client

        self.supabase = create_client(
            os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"]
        )
        self.openai = openai.OpenAI()
        self.embed_model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
        self.top_k = settings.retrieval_top_k

    def _embed(self, text: str) -> list[float]:
        return self.openai.embeddings.create(model=self.embed_model, input=[text]).data[0].embedding

    def add(self, subject: str, content: str, source: str = "user") -> None:
        self.supabase.table("rag_chunks").upsert(
            {
                "chunk_id": f"fact-{uuid.uuid4().hex[:12]}",
                "source": subject.lower().strip(),
                "text": content,
                "embedding": self._embed(f"{subject}: {content}"),
            },
            on_conflict="chunk_id",
        ).execute()

    def search(self, query: str, top_k: int = 4) -> list[str]:
        result = self.supabase.rpc(
            "match_chunks",
            {"query_embedding": self._embed(query), "match_count": top_k},
        ).execute()
        return [f"[{row['source']}] {row['text']}" for row in (result.data or [])]
