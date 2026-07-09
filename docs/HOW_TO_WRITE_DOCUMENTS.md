# How to write documents

These rules apply to every document in this repo: markdown docs, README, code comments, and commit messages. They are distilled from Juan Barrera's writing guide. The goal is text that sounds like an engineer who built the system and that survives review without reading as AI-generated.

## Typography

- Never use the em-dash (—). For a pause, use a comma. For an aside, use parentheses. To introduce an explanation or a list, use a colon.
- Numeric ranges use "to" (or "a" in Spanish) or a short hyphen: "5 to 10 fps", "30-90 days".

## Banned constructions

- Antithesis of the form "X, not Y" ("no se trata de X, se trata de Y"), in any variant, including soft ones like "a support, not a substitute". State the idea in positive form: "the system serves as informational support".
- First-person plural openings: "We describe...", "Describimos...". Prefer "This document describes...", "The system uses...", or the Spanish impersonal "se".
- Inflated or AI-flavored phrases: "En la actualidad...", "in today's world...", "it is important to note...", "revolutionary", "game-changer", "paradigm shift", "cutting-edge", "seamless", "significant impact" without evidence, "more than a tool...", "the future of...".
- Structural filler: paragraphs announcing the document's own structure ("The rest of this document is organized as follows..."). Headings already show it.

## Tone and content

- Open with the concrete problem, who it affects, and the constraints. Skip philosophical or trend-driven openings.
- Justify every technology by the need it covers under real constraints. Fashion is never a justification.
- State limitations and trade-offs openly: what a decision costs and what it buys. A declared limitation is evidence of criterio.
- Use construction verbs for things that exist ("designs", "builds", "implements"); reserve "proposes" for generalizable design decisions.
- In Spanish text, keep the technical anglicisms engineers actually say (pipeline, embedding, chunking, prompt, RAG); translate only when the Spanish term is natural (consulta, recuperación, modelo de lenguaje).
- Close prudently: what was built, what it enables, what remains.

## Checklist before finishing

1. Starts from a concrete problem?
2. Every technology justified by a real need?
3. Limitations acknowledged?
4. Decisions explained with costs and benefits?
5. Zero em-dashes, zero banned constructions?
6. Any claim left without evidence?
7. Does it sound like someone who built the system?
