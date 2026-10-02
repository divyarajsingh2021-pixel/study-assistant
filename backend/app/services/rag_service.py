from app.models.schemas import ChatMessage, ChatResponse, Citation
from app.services.llm_service import llm_service
from app.services.vector_service import vector_service


class RAGService:
    async def answer_question(
        self,
        question: str,
        document_id: str | None = None,
        history: list[ChatMessage] | None = None,
        user_id: str | None = None,
        is_admin: bool = False,
    ) -> ChatResponse:
        # Retrieve top relevant chunks from ChromaDB for this user
        chunks = await vector_service.query_relevant_chunks(
            query=question, document_id=document_id, user_id=user_id, is_admin=is_admin, n_results=4
        )

        if not chunks:
            return ChatResponse(
                answer="I couldn't find any relevant study material in your uploaded documents for this question. Please upload notes or select a document from your library.",
                citations=[],
                provider_used="System",
            )

        # Build citations
        citations = []
        for c in chunks:
            snippet_text = c["text"]
            if len(snippet_text) > 280:
                snippet_text = snippet_text[:280].strip() + "..."
            citations.append(
                Citation(
                    document_id=c["document_id"],
                    document_name=c["filename"],
                    page=c["page"],
                    snippet=snippet_text,
                    similarity_score=c["similarity"],
                )
            )

        # Format context for prompt
        context_parts = []
        for idx, c in enumerate(chunks, 1):
            context_parts.append(
                f"[Source {idx} | Document: '{c['filename']}' | Page {c['page']}]:\n{c['text']}"
            )
        context_str = "\n\n---\n\n".join(context_parts)

        # Build conversation history if provided
        history_str = ""
        if history and len(history) > 0:
            recent_turns = history[-4:]
            formatted_turns = [f"{turn.role.capitalize()}: {turn.content}" for turn in recent_turns]
            history_str = "Recent Conversation History:\n" + "\n".join(formatted_turns) + "\n\n"

        prompt = f"""You are an expert AI Study Assistant. Answer the student's question accurately and thoroughly based strictly on the provided study excerpts.

Grounding Rules:
1. Base your answer strictly on the facts present in the Context excerpts.
2. Structure your explanation with clear paragraphs, bullet points, or definitions where helpful.
3. Cite the relevant source names and pages when presenting key concepts (e.g. "According to [Document Name, Page X]...").
4. If the provided excerpts do not contain enough information to fully answer, answer what is present and acknowledge the limitation.

Context Material:
{context_str}

{history_str}Student Question: {question}

Helpful & Grounded Explanation:"""

        system_prompt = "You are a helpful, rigorous AI Study Assistant who explains academic concepts clearly and always grounds answers in the student's uploaded notes."

        def offline_fallback() -> str:
            key_sentences = []
            q_words = set(question.lower().split())
            for c in chunks:
                for line in c["text"].split(". "):
                    line_clean = line.strip()
                    if len(line_clean) > 25 and any(
                        w in line_clean.lower() for w in q_words if len(w) > 3
                    ):
                        key_sentences.append(f"• {line_clean}.")
                        if len(key_sentences) >= 4:
                            break
                if len(key_sentences) >= 4:
                    break

            if not key_sentences:
                return f"Based on your study material in **{chunks[0]['filename']}** (Page {chunks[0]['page']}):\n\n{chunks[0]['text'][:400]}..."

            return (
                f"Based on your uploaded study notes in **{chunks[0]['filename']}** (Page {chunks[0]['page']}):\n\n"
                + "\n".join(key_sentences)
            )

        answer_text, provider_name = await llm_service.generate_completion(
            prompt=prompt,
            system_prompt=system_prompt,
            json_mode=False,
            fallback_offline_fn=offline_fallback,
        )

        return ChatResponse(
            answer=answer_text.strip(), citations=citations, provider_used=provider_name
        )


rag_service = RAGService()
