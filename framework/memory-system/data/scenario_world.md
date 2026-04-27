# Synthetic scenario world — Aldermere Strategic Group

This is a fabricated consulting firm and its engagements over a roughly
two-year span (Jan 2027 – Mar 2029). Every name, project, company, and
event in this file is **invented** — zero overlap with ivers-corp,
current pOS, Luke's actual contacts, or any real-world entity I am
aware of. The world is sized to exercise multi-hop graph traversal,
context-aware anchor reranking, and temporal queries with enough
density that those modes have somewhere to walk.

The world is built around **Aldermere Strategic Group**, a small
boutique consultancy. Their client portfolio and internal staff
populate the entity graph; the timeline of engagements provides the
temporal axis.

## The firm

**Aldermere Strategic Group** — boutique consulting firm based in
Bristol, founded 2024 by **Vesna Karolak** (managing partner). The
firm runs three practice areas:

- **Operational restructuring** — led by **Tomek Vrbas**.
- **Market entry advisory** — led by **Ines Saralegui**.
- **Digital transformation** — led by **Renji Okamoto**.

Other senior staff: **Mira Adelyn** (head of analytics), **Sefa
Hristov** (head of client delivery), **Iva Petranek** (chief financial
officer), **Klemen Doric** (head of partnerships).

## Clients

Six client engagements span the timeline:

1. **Halcyon Cartography** — mapping software firm; CEO **Tobi Imari**;
   board chair **Yana Pesek**. Engagement: digital-transformation
   migration off Frostvault to Aldermere (the firm's namesake — yes,
   amusing). Run Mar 2027 – Sep 2027.

2. **Cinnabar Looms** — textile manufacturer; CEO **Pavla Strnad**;
   COO **Lukasz Bortnik**. Engagement: operational restructuring of
   the Quillgate fabric line. Run Jan 2027 – Aug 2027.

3. **Tideglass Hydrology** — water-systems firm; CEO **Anders Vrelich**;
   CTO **Marit Eliasson**. Engagement: market entry advisory for the
   Nordic markets. Run Aug 2027 – Feb 2028.

4. **Rookery Holdings** — investment firm; managing director **Esra
   Kollar**; head of operations **Petar Volk**. Engagement: digital
   transformation of their portfolio reporting. Run Nov 2027 – May 2028.

5. **Ardent Ferrous** — speciality metals supplier; CEO **Marin
   Zelenov**; CFO **Kaja Lindqvist**. Engagement: operational
   restructuring of the Stoneheath foundry. Run Apr 2028 – Oct 2028.

6. **Velmar Optical** — precision optics manufacturer; CEO **Henrik
   Jondahl**; head of R&D **Saoirse Bevan**. Engagement: market entry
   advisory for the Latin American markets. Run Sep 2028 – Mar 2029.

## Key projects, decisions, and events

These are the source material for episodes. Each is a discrete event
that the prototype will ingest as an EpisodeType.text body.

### Halcyon Cartography (Aldermere lead: Renji Okamoto)

- **2027-03-14** — kickoff meeting; Renji Okamoto, Tobi Imari, Yana
  Pesek confirm the project scope. Budget approved: 84,000 GBP.
- **2027-04-22** — Tobi Imari decides to retain the Frostvault format
  for archival data (decision later superseded — see 2027-07-02).
- **2027-05-30** — Renji Okamoto delivers the migration plan; Mira
  Adelyn provides the analytics underpinning.
- **2027-07-02** — supersession event: Halcyon's board (chaired by
  Yana Pesek) decides to abandon Frostvault entirely. The earlier
  archival-retention decision is reversed.
- **2027-09-18** — Aldermere migration completed, ahead of schedule.

### Cinnabar Looms (Aldermere lead: Tomek Vrbas)

- **2027-01-21** — kickoff; Tomek Vrbas, Pavla Strnad, Lukasz Bortnik.
  Budget: 62,000 GBP.
- **2027-03-02** — Lukasz Bortnik raises the option of expanding the
  Quillgate line as part of the restructure (decision deferred).
- **2027-04-30** — Tomek Vrbas delivers a midpoint review; throughput
  targets revised upward 12%.
- **2027-06-15** — Pavla Strnad approves the Quillgate expansion; the
  decision deferred in March is now confirmed.
- **2027-08-09** — engagement closes; final report signed off by Pavla
  Strnad.

### Tideglass Hydrology (Aldermere lead: Ines Saralegui)

- **2027-08-25** — kickoff; Ines Saralegui, Anders Vrelich, Marit
  Eliasson. Budget: 110,000 GBP. Sefa Hristov assigned as delivery
  partner.
- **2027-10-04** — Marit Eliasson identifies a regulatory blocker in
  the Nordic markets — the Norwegian water-licensing regime.
- **2027-11-19** — Klemen Doric introduces Tideglass to a Nordic
  partner: **Sondre Bråten** of Bråten Vannverk. Partnership memo
  signed.
- **2028-01-08** — Anders Vrelich approves the partnership-led
  market-entry strategy; the regulatory blocker is resolved through
  the partnership.
- **2028-02-14** — engagement closes; Tideglass enters Norway with
  Bråten Vannverk as joint partner.

### Rookery Holdings (Aldermere lead: Renji Okamoto)

- **2027-11-12** — kickoff; Renji Okamoto, Esra Kollar, Petar Volk.
  Budget: 145,000 GBP.
- **2028-01-22** — Mira Adelyn delivers the analytics scoping memo.
- **2028-02-09** — Esra Kollar challenges the proposed reporting
  cadence; cadence revised from quarterly to monthly (decision change).
- **2028-04-03** — Renji Okamoto delivers the platform; Iva Petranek
  signs off on cost overrun of 18,000 GBP.
- **2028-05-21** — engagement closes; Petar Volk takes ownership of
  the new portfolio-reporting platform.

### Ardent Ferrous (Aldermere lead: Tomek Vrbas)

- **2028-04-17** — kickoff; Tomek Vrbas, Marin Zelenov, Kaja
  Lindqvist. Budget: 95,000 GBP. Sefa Hristov assigned as delivery
  partner.
- **2028-06-04** — Tomek Vrbas identifies a labour-relations risk at
  the Stoneheath foundry; engagement scope extended.
- **2028-07-30** — Marin Zelenov approves a revised plan; Iva
  Petranek signs off on the additional 22,000 GBP.
- **2028-09-12** — Stoneheath restructure completed; Kaja Lindqvist
  reports a 9% cost reduction in the first month.
- **2028-10-22** — engagement closes.

### Velmar Optical (Aldermere lead: Ines Saralegui)

- **2028-09-08** — kickoff; Ines Saralegui, Henrik Jondahl, Saoirse
  Bevan. Budget: 130,000 GBP.
- **2028-11-05** — Saoirse Bevan delivers a competitive landscape
  analysis on Latin American optics market.
- **2029-01-14** — Henrik Jondahl chooses Brazil as the entry market
  (decision); Mexico ranked second.
- **2029-02-22** — Klemen Doric introduces Velmar to a São Paulo
  partner: **Beatriz Carvalho** of Lente Pampero. Partnership memo
  signed.
- **2029-03-19** — engagement closes.

## Cross-engagement structure (for multi-hop traversal)

The world is structured so the following multi-hop questions are
answerable by graph walks:

- "Which clients has Renji Okamoto led?" → Halcyon Cartography,
  Rookery Holdings (two hops via engagement-led-by edges).
- "Which Aldermere staff worked with Sefa Hristov as delivery
  partner?" → Ines Saralegui (Tideglass), Tomek Vrbas (Ardent
  Ferrous).
- "Who introduced Aldermere clients to Nordic / Latin American
  partners?" → Klemen Doric (Sondre Bråten / Beatriz Carvalho).
- "Which clients had cost overruns approved by Iva Petranek?" →
  Rookery Holdings (18k), Ardent Ferrous (22k).
- "Which engagements were operational restructuring?" → Cinnabar
  Looms, Ardent Ferrous (Tomek Vrbas's practice).

## Cross-engagement temporal structure (for reference_time queries)

The timeline overlaps deliberately so historical questions are
non-trivial:

- "Who was Aldermere working with in May 2027?" → Halcyon and
  Cinnabar (both engagements active).
- "What did Aldermere know about the Frostvault format as of May
  2027?" → Tobi Imari's 2027-04-22 retention decision was current;
  the supersession on 2027-07-02 had not yet occurred.
- "Which Aldermere practice was busiest in October 2027?" →
  Operational restructuring (Cinnabar closing, no other) — actually
  market entry (Tideglass active) and digital transformation
  (Halcyon active).
- "What was the last engagement open before the new year 2028?" →
  Tideglass (closed 2028-02-14) and Rookery (open through May 2028).

## Cross-engagement context structure (for anchor reranking)

When the anchor is Renji Okamoto, retrievals about "platform
delivery" should preferentially return Halcyon and Rookery results
over Cinnabar (not in his portfolio). When the anchor is Sefa
Hristov, retrievals about "delivery partner" should preferentially
return Tideglass and Ardent Ferrous. The pOS scope-of-work model
maps naturally onto this — the active engagement is the anchor.

## Notes on construction

- All numbers (budgets, percentages, headcounts) are made up but
  internally consistent.
- The supersession event for Halcyon (Tobi Imari's 2027-04-22
  decision overruled by 2027-07-02 board decision) is the seed for
  the supersession-detection retrieval mode (R8/R9 context).
- The cost-overrun pattern (Rookery 18k, Ardent 22k) gives a
  multi-hop pattern with a recurring entity (Iva Petranek as
  approver).
- Names mix several language origins to avoid clustering on any one
  cultural pattern that could collide with other invented worlds.
