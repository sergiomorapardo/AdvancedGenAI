"""Piece: evaluate a RAG app with a LangSmith dataset, code evaluators and a calibrated judge.

Same questions, same evaluators, two configurations: each one is an experiment. Code evaluators
check what a rule can (page retrieved, citations, figures); judges built from rubrics score
correctness and groundedness. The judge is calibrated against human labels first, and the
experiments do not run if it disagrees too much. At the end the results are downloaded from
LangSmith with their traces and written as a report (results.py).

Run from the repo root (needs LANGSMITH_API_KEY in .env; LANGSMITH_TRACING may stay false):
    uv run python .claude/skills/evaluate-app/references/examples/evaluation.py
Cost: 38 model calls to the project model with the 5 class questions: 8 calibration judgements
+ 2 experiments × (5 answers + 10 judgements). LangSmith: 11 traces (1 calibration trace with the
8 judgements inside + 5 per experiment) and 2 experiments. Creating the dataset and reading the
results are API calls, not traces. Every run creates new experiments: count them before repeating.
"""

import csv
from pathlib import Path

from evaluators import (
    build_judge_model,
    calibrate,
    citations_ok,
    figures_match,
    make_judge,
    retrieval_hit,
)
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langsmith import Client, evaluate, trace, traceable, tracing_context
from project import SAMPLE_DOCUMENTS, SAMPLE_QUESTIONS, SAMPLE_REVIEW_SET, build_model
from pypdf import PdfReader
from results import report

DOCUMENTS = SAMPLE_DOCUMENTS
EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

PARTICIPANT = "example"  # TODO: your name, no spaces: tag of the traces, prefix of the experiments
PROJECT = "rag-eval-example"  # LangSmith project of this app
DATASET = "rag-eval-example"  # created once, then reused; rename it if the questions change
MIN_AGREEMENT = 0.75  # below this the judge is not trusted and the experiments do not run
QUESTION_IDS = ["q04", "q07", "q11", "q16", "q21"]  # a small subset first; all 22 cost ~4x

SYSTEM_PROMPT = (
    "You are the support assistant of ACME, a fintech. "
    "Answer only with the information in the document fragments you receive. "
    "After each fact, cite its source as [file, p. N], exactly as it appears in the fragment. "
    "If the fragments do not contain the answer, say it is not in the documents and do not make it up."
)
PROMPT = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", "Fragments:\n\n{context}\n\nQuestion: {question}")]
)
# Rubrics adapted from openevals.prompts (CORRECTNESS_PROMPT, RAG_GROUNDEDNESS_PROMPT).
CORRECTNESS_PROMPT = """\
You are an expert reviewer judging whether an assistant's answer is correct.
A correct answer gives the same information as the reference, even in other words; has no wrong
figures, deadlines or names; answers every part of the question; and, if the reference says the
data is not in the documents, also says so instead of making one up. Do not judge style, length
or citations. Explain your reasoning before the score.

<question>{inputs}</question>
<answer>{outputs}</answer>
<reference>{reference_outputs}</reference>
"""
GROUNDEDNESS_PROMPT = """\
You are an expert reviewer judging whether an answer is supported by the retrieved fragments.
Check every claim against the fragments; any figure or condition that no fragment states is
unsupported. If the fragments do not contain the answer, a supported answer says so. Judge only
against the fragments, even if you know otherwise. Explain your reasoning before the score.

<fragments>{context}</fragments>
<answer>{outputs}</answer>
"""

def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def load_questions() -> list[dict]:
    """acme_questions.csv: question, expected file and page, and the right answer (reference)."""
    return read_csv(SAMPLE_QUESTIONS)


def ensure_dataset(client: Client, questions: list[dict]) -> list:
    """Create the dataset once; later runs reuse it (existing examples are not updated)."""
    if not client.has_dataset(dataset_name=DATASET):
        client.create_dataset(DATASET, description="RAG questions with a reference answer.")
        client.create_examples(
            dataset_name=DATASET,
            examples=[
                {
                    "inputs": {"question": row["question"]},
                    "outputs": {
                        "reference": row["reference"],
                        "source": row["source"] or None,  # empty for questions without an answer
                        "page": int(row["page"]) if row["page"] else None,
                    },
                    "metadata": {"id": row["id"]},
                }
                for row in questions
            ],
        )
    return list(client.list_examples(dataset_name=DATASET))


def labeled_answers(questions: list[dict]) -> list[dict]:
    """acme_review_set.csv: fixed answers a person labeled correct or not, in the evaluator's shape."""
    by_id = {row["id"]: row for row in questions}
    return [
        {
            "inputs": {"question": by_id[row["id"]]["question"]},
            "outputs": {"answer": row["answer"]},
            "reference_outputs": {"reference": by_id[row["id"]]["reference"]},
            "human": bool(int(row["human_correct"])),
            "note": row["note"],
        }
        for row in read_csv(SAMPLE_REVIEW_SET)
    ]


# --- The app under test: returns what the evaluators need -------------------------------------
def load_chunks(folder: Path) -> list[Document]:
    pages = []
    for path in sorted(folder.glob("*.pdf")):
        for number, page in enumerate(PdfReader(path).pages, 1):
            pages.append(Document(page.extract_text(), metadata={"source": path.name, "page": number}))
    return RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60).split_documents(pages)


def build_app(vector_store, model, k: int, name: str):
    """Answer + context (groundedness) + sources (code evaluators) + tokens (cost)."""

    # Without @traceable the experiment shows only the model call, not what was retrieved.
    @traceable(run_type="retriever", name=f"retrieve · k={k}")
    def retrieve(question: str) -> list[Document]:
        return vector_store.similarity_search(question, k=k)

    @traceable(name=name)
    def app(inputs: dict) -> dict:
        docs = retrieve(inputs["question"])
        context = "\n\n".join(f"[{d.metadata['source']}, p. {d.metadata['page']}]\n{d.page_content}" for d in docs)
        answer = model.invoke(PROMPT.format_messages(context=context, question=inputs["question"]))
        return {
            "answer": answer.text,
            "context": context,
            "sources": [[d.metadata["source"], d.metadata["page"]] for d in docs],
            "input_tokens": answer.usage_metadata["input_tokens"],
            "output_tokens": answer.usage_metadata["output_tokens"],
        }

    return app


def main():
    model = build_model()
    client = Client()
    questions = load_questions()
    examples = [e for e in ensure_dataset(client, questions) if e.metadata["id"] in QUESTION_IDS]
    judge = build_judge_model(model)
    correctness = make_judge(judge, "correctness", CORRECTNESS_PROMPT)
    groundedness = make_judge(judge, "groundedness", GROUNDEDNESS_PROMPT)

    # langsmith caches LANGSMITH_TRACING/PROJECT: turn tracing on with tracing_context, not os.environ.
    with tracing_context(enabled=True, project_name=PROJECT), trace(
        "calibration", tags=[PARTICIPANT], metadata={"participant": PARTICIPANT}, client=client
    ):
        calibration = calibrate(correctness, labeled_answers(questions))
    print(f"Judge-person agreement: {calibration['agreement']:.0%} on {calibration['scored']} answers,"
          f" {calibration['format_failures']} format failures")
    for row in calibration["disagreements"]:
        print(f"- person: {row['note']}\n  judge: {row['comment'][:200]}")
    if calibration["agreement"] is None or calibration["agreement"] < MIN_AGREEMENT:
        raise SystemExit("The judge disagrees with the person too often: fix the rubric before the experiments.")

    store = InMemoryVectorStore.from_documents(load_chunks(DOCUMENTS), FastEmbedEmbeddings(model_name=EMBEDDINGS_MODEL))
    evaluators = [retrieval_hit, citations_ok, figures_match, correctness, groundedness]
    names = []
    for k in (3, 5):
        results = evaluate(
            build_app(store, model, k, f"RAG · k={k}"),
            data=examples,
            evaluators=evaluators,
            experiment_prefix=f"{PARTICIPANT}-k{k}",
            metadata={"participant": PARTICIPANT, "k": k},
            max_concurrency=2,
            disable_evaluator_tracing=True,  # one trace per answer; the scores are still saved
            client=client,
        )
        names.append(results.experiment_name)
    client.flush()  # traces upload in the background: wait before reading them back
    report(client, names, scores_per_row=len(evaluators))  # feedback also arrives late


if __name__ == "__main__":
    main()
