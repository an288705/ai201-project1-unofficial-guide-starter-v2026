# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:**
My questions ask for specific facts (wait times, prices, deadlines) that are typically stated explicitly in the documents. The one harder question — about pass/fail declaration deadline — is a detail mentioned only once in `admin_pass_fail_option.txt`, so missing that one is realistic. Four of five is a reasonable bar for questions this specific.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:**
The pipeline always includes source citations when answering in-scope questions — `generate.py` formats every chunk as `[from {source}]\n{text}` before sending it to the model. For the system to fail this, the model would have to strip the attribution from its own output. Keeping all five is realistic since the instruction is in the prompt and the sources are visible in the context.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. Swap them for your own if you'd rather —
     just keep five of them, or the "4 of 5" above has nothing to be 4 of. -->

**Why this target:**
The out-of-scope questions are about unrelated topics (Mongolia's capital, oil changes, World Cup, drug dosing, Rust syntax). The corpus has no content remotely related to these, so distances should be uniformly high. The cutoff is set to separate in-corpus from out-of-corpus, so I expect a clean gap with most out-of-corpus questions clearly above the threshold. Four of five allows for one edge case that happens to score near the boundary.

---

## 4. Something about your chunks

Every chunk names its subject without needing a neighbour. In 10 sampled
chunks, at least 9 contain the dining hall / dorm / course name the facts
belong to, rather than a bare "it" or "the building".

<!-- YOU WRITE THIS ONE.

     How would you know if your chunks were the right size? Name something
     countable or observable.

     Examples of the right shape — don't copy these, they should come from
     what you actually saw in Milestone 3:
       - "At least 4 of 5 sampled chunks read as a complete thought, with no
          sentence cut in half at either end."
       - "No chunk is shorter than 200 characters, since anything below that
          in my corpus turned out to be a heading with no content under it." -->



**Why this target:**
Each chunk should be interpretable on its own. When a chunk is just "Machines take $1.75 wash", the word "Machines" has no referent unless you read the title or neighbouring text. My chunker combines titles with the paragraph that follows, so chunks should include the hall, dorm, or course name. Nine of ten allows for one edge case (e.g., a title-less chunk from the middle of a document).


---

## 5. Your choice

No chunk contains facts about more than one topic. Sampled across 10 chunks,
at least 8 cover a single subject (one dining hall's wait time, or one dorm's
laundry, but not both).

<!-- YOU WRITE THIS ONE TOO.

     Pick something you actually care about getting right. It could be about
     speed, about refusals, about a particular kind of question your corpus
     handles badly, about source attribution being correct rather than merely
     present — anything, as long as it names a number or an observable
     outcome. -->



**Why this target:**
Chunks that mix topics (wait times + pricing + salad bar + stir-fry station) have bad embeddings because one vector has to represent multiple unrelated ideas. My paragraph-split strategy separates most topics naturally. Eight of ten allows for edge cases where a paragraph unavoidably covers two related ideas (e.g., "Laundry costs $1.75 wash, $1.50 dry" covers two topics but they're the two sides of the same fact).


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in unit 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->
