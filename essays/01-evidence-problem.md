# Agent memory is an evidence problem, not a retrieval problem

_Iteration 1 of the [Provenance Principle](https://github.com/Hybos/provenance-principle) program. Comments welcome — that is what this gist is for._

---

Here is the claim, so you can decide early whether to keep reading:

> Reads cannot recover what writes discarded.

That is the slogan. The precise, defensible version is this: **read-time inference cannot
reliably reconstruct the validity, supersession or deletion state of stored facts unless the
write path preserved enough provenance to decide.** The quality of an agent's memory is set
by how much evidence about the origin, validity and invalidation of each fact survives the
write — because that evidence can only be captured there.

By provenance I mean metadata and relations captured about the assertion event: when it was
written, by whom or what, from which source, and which previous assertion it superseded —
that last one is a relation between assertion events, and it counts. I do not mean the
asserted content itself — without that boundary the claim would be
circular, since any helpful text could be relabeled "provenance" after the fact.

If that is true, a large share of current memory work is rigorous about the read side while
leaving the evidence preserved at write time unexamined. Rerankers, hybrid search, query
expansion, bigger context windows: all of it operates on whatever the store contains, and
none of it can reconstruct information that was never written down.

These questions stopped being theoretical for me while working on a system for a regulated
domain — compliance management, where the store has to answer what was true on a given date,
who validated it, under which version of a rule, and whether a deletion actually happened.
Regulation demands by law what agent memory lacks by design. Once you have to build for that
standard, the gaps in how we usually persist agent knowledge stop looking like edge cases.

I did not start from this claim, though. I started from a small experiment that kept pointing
at one variable — but the experiment is mine and it is a toy, so the evidence that is not mine
goes first.

## The same variable, three times, none of it mine

What made me write this essay is three independent external lines pointing at the same
variable.

A study of a live multi-agent memory service (arXiv:2606.24535) — the authors measure their
own multi-tenant production service rather than running a benchmark — found several failure
modes (scope enforcement, propagation policy, and ordering). The one most relevant to this
argument sits in the write path's ordering: a
synchronous near-duplicate gate rejected contradictory writes before the asynchronous
contradiction detector could see them, so supersession silently never happened. Their
provenance machinery, meanwhile, reconstructed all the four-hop derivation chains they
tested, with correct writer identity (author-reported, on their own service). Read that
carefully, because it cuts both ways: the store captured provenance well and still failed,
because curation ran in the wrong order. Capture is necessary, not sufficient — the principle
says nothing gets reconstructed without it, not that everything goes right with it. Both
findings sit in the write path, and neither was visible from a design document.

A 2026 survey of evidence tracing in agents (arXiv:2606.04990) argues the field should stop
evaluating final answers and start evaluating process — which claims were supported, what
invalidated what, how memory shaped later decisions. Its taxonomy of provenance relations
(SUPPORT, CONTRADICT, INVALIDATE, UPDATE) is, in effect, a catalogue of the evidence a write
path either preserves or destroys. The survey asks for infrastructure. It stops short of
stating the principle that makes the infrastructure necessary.

And the pattern is older than agent memory. Legal drafting institutionalized versioning
centuries ago, and its digital models work the same way today: a norm's versions are never overwritten;
an amendment is a recorded event that terminates one version and produces the next, so any
past state can be reconstructed with its full justification. Temporal supersession —
invalidating instead of erasing — shows up as the core primitive in agent memory systems and
in legislative knowledge graphs. The convergence is not fully
independent — bitemporal ideas from the database world circulate in both communities — but of
everything available to them, both kept exactly this mechanism.

## The toy that started it, offered as an intuition pump

My own contribution to the evidence is deliberately the weakest of the four, and I want to be
plain about why: the experiment is small, synthetic, and built under assumptions that favor
the hypothesis. It is a constructed intuition pump — a way to make the mechanism executable —
and on its own it proves nothing. (Its
write-time arm gets near-oracular access to update events, and its pressure axis saturates
early; both are documented in the repo, and both are why I keep it at toy status.)

The setup: a store fills with facts, some get updated, stale values accumulate next to
current ones. Three arms answer questions under a matched context budget: store-all with
top-k; store-all plus a read-time filter that can deduplicate and prefer recent; and
write-time supersession. When the read filter can see write order, it ties the write-gated
arm — whoever ships "write-time gating beats read-time filtering" as a flat statement is one
experiment away from embarrassment, and the first version of this work was exactly that.
When write order is hidden, the read filter has nothing to act on and degenerates to the
naive arm by construction — in the code it is literally a no-op without the recency signal.
That identity is exactly what the toy is built to exhibit.

What actually carries weight is the mechanism, and it is analytic. A
current fact and a stale fact about the same field are near-identical in embedding space:
same entity, same attribute, only the value differs, and the query never mentions the value.
Similarity cannot separate them whenever the statements are symmetric restatements and the query never mentions the value. Recency can — but only if someone
recorded it. The information needed to decide was available exactly once, at the moment of
writing. Discard it then, and no read-side machinery gets it back. The toy merely makes that
argument executable.

A toy names a suspect, not a principle. Code and seeds are in the [evidence folder](https://github.com/Hybos/provenance-principle/tree/main/evidence), with its limitations stated in the design notes. It runs in seconds, no API keys.

## The reframe

Take the four observations together and the lifecycle questions collapse into one.

Why do write-time decisions dominate? Because writing is the only moment provenance can be
captured. Why does stale memory get returned with confidence? Because without provenance,
currency is undecidable at read time — the store contains two contradictory sentences and no
fact of the matter about which one stands. Why can't deletion be shown complete? Because
deleting is one more mutation, and a mutation without evidence is exactly as trustworthy as
an unrecorded write.

So the object we should be designing is a belief ledger rather than a cache with search on
top: writes are assertions with evidence attached, updates are revisions that supersede
rather than overwrite, and forgetting is an invalidation event that is itself recorded. Every
part of that sentence is boring, settled practice in databases and in law. Pieces of it exist
in agent memory too — Zep's bitemporal invalidation, Kumiho's belief-revision semantics
(arXiv:2603.17244), Selective Memory's write-time gating results (arXiv:2603.15994). What is
missing is the shared principle underneath them, and any way to measure a system's
completeness against it.

## How this could be wrong

The claim fails if someone shows a read-time mechanism that reconstructs validity and
invalidation of contradictory facts with no provenance preserved at write time. There is a
real candidate: content semantics. "She moved to Berlin" arguably implies it supersedes "she
lives in Madrid" — no timestamps needed. Sometimes language marks its own ordering. The open
question, which the next iteration will try to state precisely, is how far that gets you:
my toy suggests it gets you nothing when the statements are symmetric restatements; how often
real memories fall in that symmetric class, and whether systems exploit semantic ordering when
it does exist, are open questions I cannot answer yet. If
someone demonstrates broad, reliable semantic ordering without stored provenance, this
program loses its central claim and I will say so in this gist's revision history.

Limits, stated plainly: the experiment is synthetic and small; the production evidence is one
study of one service; the legal analogy is an analogy, and legal-tech models are themselves
mostly unvalidated proposals. This essay names a principle and shows it is consistent with
three external observations and one constructed illustration of mine. It does not prove it. Proving a precise version of it is
iteration 2.

## Why builders should care

If you run agents with persistent memory, your roadmap probably says "improve retrieval"
somewhere. Mine did too, until a compliance use case forced the question underneath it. Check first whether your store records why each fact exists, what replaced what,
and when. If it does not, better retrieval will make the answers faster, not truer — and the
cheapest fix available is stamping provenance before you index, which costs a schema change
now and is nearly impossible to retrofit later.

---

_Next iteration: a formal note on when currency is undecidable at read time. The canon for
this program, including how to challenge it, lives in the
[repo](https://github.com/Hybos/provenance-principle)._
