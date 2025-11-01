from typing import List, Dict
from pydantic import BaseModel
from gliner import GLiNER
from app.schemas import ParsedResume, Entity, Section

# Open-vocabulary labels we care about. You can extend later.
GLINER_LABELS = ["Skill", "Education", "Experience"]

def uniq_casefold(items: List[str]) -> List[str]:
    out: List[str] = []
    for s in items:
        t = s.strip()
        if not t:
            continue
        if t.lower() not in [x.lower() for x in out]:
            out.append(t)
    return out

class NLPService:
    def __init__(self) -> None:
        # use a small model for startup speed; change to the one you used
        self._model = GLiNER.from_pretrained("urchade/gliner_small-v2.1")
        self._model.to("cpu")  # or "cuda" if available

    def parse_groups(self, groups: List[Dict]) -> ParsedResume:
        raw_entities: List[Entity] = []
        skills, edu, exp = [], [], []
        sections: List[Section] = []

        for g in groups:
            text = g["text"]
            sections.append(Section(heading=g["section"], text=text))
            ents = self._model.predict_entities(text, labels=GLINER_LABELS)
            for e in ents:
                raw_entities.append(Entity(text=e["text"], label=e["label"], score=e.get("score")))
                if e["label"].lower() == "skill":
                    skills.append(e["text"])
                elif e["label"].lower() == "education":
                    edu.append(e["text"])
                elif e["label"].lower() == "experience":
                    exp.append(e["text"])

        return ParsedResume(
            skills=uniq_casefold(skills),
            education=uniq_casefold(edu),
            experience=uniq_casefold(exp),
            raw_entities=raw_entities,
            sections=sections,
        )
