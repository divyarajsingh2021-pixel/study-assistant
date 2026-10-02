import json

from app.models.schemas import RevisionQA, RevisionResponse
from app.services.llm_service import llm_service
from app.services.vector_service import vector_service


class RevisionService:
    async def generate_revision_sheet(
        self,
        document_id: str,
        topic: str | None = None,
        user_id: str | None = None,
        is_admin: bool = False,
    ) -> RevisionResponse:
        doc_meta = vector_service.get_document_by_id(
            document_id, user_id=user_id, is_admin=is_admin
        )
        if not doc_meta:
            raise ValueError("Selected document not found or not authorized")
        doc_name = doc_meta["filename"]

        query = (
            topic if topic and topic.strip() else "key definitions principles formulas and summary"
        )
        chunks = await vector_service.query_relevant_chunks(
            query=query, document_id=document_id, user_id=user_id, is_admin=is_admin, n_results=6
        )

        if chunks:
            content_text = "\n\n".join([f"Page {c['page']}: {c['text']}" for c in chunks])
        else:
            content_text = vector_service.get_document_full_text(
                document_id, user_id=user_id, is_admin=is_admin
            )[:5000]

        prompt = f"""You are an elite academic tutor. Create a high-yield, condensed "One-Shot Revision Sheet" from the following study material.

Study Material:
{content_text}

Topic / Focus: {topic or "Comprehensive Overview"}

Produce a structured revision guide containing:
1. 3 to 6 Key Definitions (term and clear concise definition)
2. 5 to 8 Key Points / Core Principles (as distinct, impactful bullet points)
3. 2 to 3 Practice / Example Q&As (common exam-style questions with concise model answers)

Output ONLY valid JSON matching this exact structure:
{{
  "topic": "{topic or "Key Concepts Summary"}",
  "key_definitions": [
    {{"term": "Term Name", "definition": "Clear, concise definition."}}
  ],
  "key_points": [
    "Core point 1 explaining an essential mechanism or rule",
    "Core point 2 highlighting important contrast or formula"
  ],
  "example_qas": [
    {{"question": "Exam-style question?", "answer": "Model concise answer."}}
  ]
}}"""

        system_prompt = "You are a master study summarizer. You create high-yield exam revision sheets returned strictly as valid JSON."

        def offline_revision_fallback() -> str:
            defs = []
            bullets = []
            qas = []

            for c in chunks:
                lines = c["text"].split(". ")
                for sentence in lines:
                    clean = sentence.strip()
                    if (
                        ":" in clean
                        and len(clean.split(":")[0]) < 30
                        and len(clean.split(":")[1]) > 20
                    ):
                        term, defn = clean.split(":", 1)
                        defs.append({"term": term.strip(), "definition": defn.strip()})
                    elif (
                        any(kw in clean.lower() for kw in ["is defined as", "refers to", "means"])
                        and len(clean) < 160
                    ):
                        parts = (
                            clean.split("is defined as")
                            if "is defined as" in clean.lower()
                            else clean.split("refers to")
                        )
                        if len(parts) == 2:
                            defs.append({"term": parts[0].strip(), "definition": parts[1].strip()})
                    elif 30 < len(clean) < 180 and len(bullets) < 8:
                        bullets.append(clean + ".")

            if not defs:
                defs = [
                    {
                        "term": "Core Concept",
                        "definition": f"Key foundational subject matter detailed within {doc_name}.",
                    },
                    {
                        "term": "Primary Method",
                        "definition": "Standard operating procedure or theoretical model described in the text.",
                    },
                    {
                        "term": "Key Metric",
                        "definition": "Quantitative or qualitative benchmark evaluated in this section.",
                    },
                ]
            if not bullets:
                bullets = [
                    f"Thoroughly analyze and memorize the foundational definitions presented in {doc_name}.",
                    "Ensure understanding of operational boundaries and underlying assumptions.",
                    "Review primary relationships between input variables and system outputs.",
                    "Practice answering practical scenarios based on real-world test cases.",
                ]
            if not qas:
                qas = [
                    {
                        "question": f"What is the primary significance of the concepts discussed in {doc_name}?",
                        "answer": "They establish the fundamental theoretical grounding and practical workflows required for mastery of this topic.",
                    },
                    {
                        "question": "How should a student apply these principles to problem-solving?",
                        "answer": "Identify given constraints first, select the appropriate standard formula or model, and verify against boundary conditions.",
                    },
                ]

            return json.dumps(
                {
                    "topic": topic or "Quick Review",
                    "key_definitions": defs[:6],
                    "key_points": bullets[:8],
                    "example_qas": qas[:3],
                }
            )

        resp_text, provider = await llm_service.generate_completion(
            prompt=prompt,
            system_prompt=system_prompt,
            json_mode=True,
            fallback_offline_fn=offline_revision_fallback,
        )

        try:
            data = llm_service.clean_json_response(resp_text)
            key_defs = data.get("key_definitions", [])
            key_pts = data.get("key_points", [])
            example_qas_raw = data.get("example_qas", [])
            topic_str = data.get("topic", topic or "One-Shot Revision")
        except Exception as e:
            print(f"Error parsing revision sheet JSON: {e}")
            fallback_data = json.loads(offline_revision_fallback())
            key_defs = fallback_data["key_definitions"]
            key_pts = fallback_data["key_points"]
            example_qas_raw = fallback_data["example_qas"]
            topic_str = fallback_data["topic"]

        formatted_qas = [
            RevisionQA(question=q.get("question", "Question"), answer=q.get("answer", "Answer"))
            for q in example_qas_raw
        ]

        md_lines = [
            f"# One-Shot Revision Sheet: {topic_str}",
            f"**Source Document:** {doc_name}  \n\n",
            "## 1. Key Definitions & Core Terminology",
        ]
        for d in key_defs:
            md_lines.append(f"- **{d.get('term', '')}**: {d.get('definition', '')}")

        md_lines.append("\n## 2. Key Takeaways & Core Principles")
        for pt in key_pts:
            md_lines.append(f"- {pt}")

        md_lines.append("\n## 3. High-Yield Practice Q&A")
        for idx, qa in enumerate(formatted_qas, 1):
            md_lines.append(f"### Q{idx}: {qa.question}")
            md_lines.append(f"**Answer:** {qa.answer}\n")

        # Increment revised counter in user stats
        target_uid = user_id or "usr_admin"
        vector_service.increment_topics_revised(user_id=target_uid)

        return RevisionResponse(
            document_id=document_id,
            document_name=doc_name,
            topic=topic_str,
            key_definitions=key_defs,
            key_points=key_pts,
            example_qas=formatted_qas,
            raw_markdown="\n".join(md_lines),
        )


revision_service = RevisionService()
