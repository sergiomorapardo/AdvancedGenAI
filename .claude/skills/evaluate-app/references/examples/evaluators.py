"""Evaluators to copy and adapt: code checks and LLM judges built from a rubric.

An evaluator receives what LangSmith passes by parameter name (inputs, outputs, reference_outputs)
and returns {"key", "score", "comment"}. score is True/False, a number, or None when it does not
apply or the judge failed: None never counts as 0.

No model calls when imported. A judge calls the model once per answer it scores.
"""

import re

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

CITATION = re.compile(r"\[([\w.-]+\.pdf), p\. (\d+)\]")
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


# --- Code evaluators: free, deterministic; write one per rule a person can state ----------
def retrieval_hit(outputs: dict, reference_outputs: dict) -> dict:
    """The expected file and page is among the retrieved ones (None if nothing should be found)."""
    if reference_outputs.get("source") is None:
        return {"key": "retrieval_hit", "score": None, "comment": "Nothing to retrieve."}
    expected = [reference_outputs["source"], reference_outputs["page"]]
    return {"key": "retrieval_hit", "score": expected in outputs["sources"]}


def citations_ok(outputs: dict, reference_outputs: dict) -> dict:
    """Every [file, p. N] cited was retrieved, and there is one when the question has an answer."""
    cited = {(source, int(page)) for source, page in CITATION.findall(outputs["answer"])}
    retrieved = {(source, page) for source, page in outputs["sources"]}
    needs_citation = reference_outputs.get("source") is not None
    invented = sorted(cited - retrieved)
    score = not invented and (bool(cited) or not needs_citation)
    return {"key": "citations_ok", "score": score, "comment": f"Not retrieved: {invented}" if invented else ""}


def figures_match(outputs: dict, reference_outputs: dict) -> dict:
    """Every figure of the reference appears in the answer (None if the reference has none)."""
    answer = CITATION.sub("", outputs["answer"])  # page numbers are not figures
    expected = set(NUMBER.findall(reference_outputs["reference"]))
    if not expected:
        return {"key": "figures_match", "score": None, "comment": "The reference has no figures."}
    missing = sorted(expected - set(NUMBER.findall(answer)))
    return {"key": "figures_match", "score": not missing, "comment": f"Missing: {missing}" if missing else ""}


# --- LLM judges: a rubric with placeholders, scored by a model ----------------------------
class Judgement(BaseModel):
    """The judge's score with its reasoning."""

    reasoning: str = Field(description="Reasoning that ends with the score given.")
    score: bool = Field(description="true if the answer meets the rubric; false otherwise.")


def build_judge_model(model, max_tokens: int = 2000):
    """More tokens than the answers: the judge reasons before the score. json_schema guarantees both."""
    return model.model_copy(update={"max_tokens": max_tokens}).with_structured_output(
        Judgement, method="json_schema"
    )


# Placeholders a rubric may use, and where each value comes from in a RAG app.
# Same names as the OpenEvals prompts: {inputs}, {outputs}, {reference_outputs}, {context}.
RAG_FIELDS = {
    "inputs": lambda inputs, outputs, reference_outputs: inputs["question"],
    "outputs": lambda inputs, outputs, reference_outputs: outputs["answer"],
    "reference_outputs": lambda inputs, outputs, reference_outputs: reference_outputs["reference"],
    "context": lambda inputs, outputs, reference_outputs: outputs["context"],
}


def make_judge(judge, key: str, rubric: str, fields: dict = RAG_FIELDS):
    """Turn a rubric into an evaluator. Only the placeholders the rubric uses are filled."""
    used = set(re.findall(r"\{(\w+)\}", rubric))
    unknown = used - set(fields)
    if unknown:
        raise ValueError(f"The rubric of {key} uses unknown placeholders: {sorted(unknown)}")

    def evaluator(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
        values = {name: fields[name](inputs, outputs, reference_outputs or {}) for name in used}
        try:
            judgement = judge.invoke([HumanMessage(rubric.format(**values))])
            return {"key": key, "score": judgement.score, "comment": judgement.reasoning}
        except Exception as error:  # noqa: BLE001 -- counted apart, never as a 0
            return {"key": key, "score": None, "comment": f"Invalid format: {error}"}

    evaluator.__name__ = key
    return evaluator


def calibrate(evaluator, labeled: list[dict]) -> dict:
    """Agreement between an evaluator and a person on fixed answers labeled by hand.

    Each labeled row has inputs, outputs, reference_outputs, human (bool) and note.
    """
    rows = []
    for row in labeled:
        result = evaluator(row["inputs"], row["outputs"], row["reference_outputs"])
        rows.append(row | {"score": result["score"], "comment": result["comment"]})
    scored = [row for row in rows if row["score"] is not None]
    agreement = sum(row["score"] == row["human"] for row in scored) / len(scored) if scored else None
    return {
        "agreement": agreement,
        "scored": len(scored),
        "format_failures": len(rows) - len(scored),
        "disagreements": [row for row in scored if row["score"] != row["human"]],
    }
