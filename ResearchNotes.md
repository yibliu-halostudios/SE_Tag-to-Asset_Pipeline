# Tag-to-Asset Pipeline — Research Notes

> **Purpose:** Working scratchpad for Yibo + AI during the study. Not for final readers.  
> Contains raw data, interim findings, source links, and evolving insights.

---

## Table of Contents
- [Project Context](#project-context)
- [Scope Clarifications](#scope-clarifications)
- [Current Pipeline Architecture](#current-pipeline-architecture)
- [Jira Signal](#jira-signal)
- [Confluence Signal](#confluence-signal)
- [Developer Feedback](#developer-feedback)
- [Open Questions](#open-questions)

---

## Project Context

**Report (to produce):** `Tag-to-Asset_Pipeline_Recommendations.html`  
**Confluence destination:** TBD  
**Study window:** 7/1/2026 → 2/1/2027  
**Prepared by:** Yibo Liu  
**AI-assisted research:** Claude Sonnet 4.6  

**Priority in TA Strategy Roadmap FY27:** #3 overall — "High" scale risk  
(Animation = Critical, Device Machines = Critical, Tag-to-Asset = High)  
**Scope note from TA Roadmap:** "also covers UE Derivation"

**Template:** Modeled after `Meteorite_Animation_Pipeline_Recommendations.html`  
**Reference path:** `C:\Users\yibliu\OneDrive - Microsoft\Projects\SE_Evolution\SE_Anim_Pipeline\`

---

## Scope Clarifications

*(To be filled as interview progresses)*

---

## Current Pipeline Architecture

*(To be filled after codebase analysis)*

---

## Jira Signal

### ST-9441 — Improve how creators work with Blam tags to uplift CVW workflow efficiency
- **Type:** Epic | **Priority:** P0 | **Status:** New (To Do)
- **Team:** ST - Tech Art
- **Description:** "Iteration loops are complex, sometimes fragile, and require specialized knowledge about how to carry out operations in specific sequences."
- **Key sub-story:** ST-9442 — "Develop a plan to uplift efficiency working with Blam tags in CVW workflows"
- **Acceptance criteria note:** ST-9442 requests collecting feedback, documenting in Confluence, reviewing with Creative + Engineering leads

### ST-9444 — Improve UE derivation efficiency
- **Type:** Epic | **Priority:** P2 | **Status:** New
- **Sub-story:** ST-9445 — "Develop a plan to improve UE derivation efficiency"

### ST-9548 — Suggestions for dynamic object pipeline (high-signal developer feedback)
- **Priority:** P2 | Author: experienced TA
- **Key complaints (verbatim):**
  - "Duplicate work to setup tag data. We already have to localize collision and render meshes under joints in maya... Tooling to help support 'scraping' the data from maya to auto-fill these out would save both time and human error."
  - "The socket/marker workflow is just awful from a native UE perspective... UE appears to have broken socket round-tripping in 5.5."
  - "Need additional tooling around not having to create tags by hand... due to not being able to access the actual tag _fields_ via python, you can't hook them together in any automatic way."
  - "Need to be able to access tag data via python."
  - "Need to be able to tag-diff accurately and within blocks."
  - "Exporting collision model tag with the asset loaded in a level causes a 100% repro crash."
  - "Regarding not being able to access tag data via python, this makes all of our animation pipelines in maya pretty well useless."
- **Signal quality:** HIGH — concrete, specific, from a practitioner

---

## Confluence Signal

### CVW Post-Mortem (page 809500699)
- Post mortem in Mural (external link) — not directly accessible
- Database of entries linked but 404 (possibly restricted)

### Worlds Post-Mortem (page 778666110) — HIGH SIGNAL
- "Currently stitched collision workflows are very slow, opaque, and error prone. I suggest we go back to the drawing board on how to author, view, and generate collision"
- "Having separate meshes for Render, Collision, Fallback, and HLODs is bloating our asset count and making things more error-prone"
- "We need a way to instantly update collision meshes when reimporting, without having to export to Blam. Right now, fixing even simple collision bugs takes exponentially more time compared to Infinite."
- "Should be easier to play in editor/load levels without relying heavily on blam"
- "Blam sync crashing level loads"

### Env | HS: Collision, Pathfinding & Blam (page 81691099) — PROCEDURAL SIGNAL
- Collision export takes **3–5 minutes** per run (structure generation)
- **Hard budget cap: 500,000 triangles** → crashes structure generation
- Export & Generate = a required manual step after every collision change
- NavMesh/Pathfinding depends on BSP structure → requires separate "Generate Pathfinding → All BSPs" step after every structure export
- Multiple collision types to configure per asset (SES_Poop_ComplexCollision, etc.)

### Play-In-Editor and Blam (page 68855558) — WORKFLOW SIGNAL
- After *any* UE edit, must manually export tags for Blam to see changes
- Files are never checked in (local-only) — "To ensure people don't collide with check-ins"
- Structural pieces (collision) remain as raw tags on disk, built locally
- Red X = must re-export scenario tag before PIE works
- NavMesh rebuild = separate manual step

### WIP: Stage One Asset Updating — From Reach tags to UE derived content (page 237897589) — WORKFLOW SIGNAL
- Multi-step process: Maya → FBX → UE reimport (must use legacy importer, not interchange)
- Skeleton orientation must be manually zeroed in Maya
- Blam markers must be imported into skeleton before other steps
- Collision pathway: either re-author or pull from Reach (requires 3DS Max or Cyprus share access)
- Naming: all lowercase snake_case required; capitalization changes are blocked by UE workaround

### TA Strategy & Roadmap FY27 (page 831258688)
- Tag-to-Asset Pipeline: Scale Risk = **High**
- Key summary: "Managing BLAM Tags is a repetitive and inefficient part of the current content workflow. NOTE - also covers 'UE Derivation'"

---

## Developer Feedback

*(Interview responses and qualitative signal — to be filled)*

---

## Open Questions

1. **Scope:** The TA Roadmap says Tag-to-Asset Pipeline "also covers UE Derivation." Should this study treat Blam Tags and UE Derivation as one unified topic, or analyze them as separate sub-topics with their own recommendations?
2. What does "CVW" stand for exactly? (Characters / Vehicles / Weapons?)
3. Is there a Perforce query or asset count for how many Tag Data Assets (UAssets) currently exist in the project?
4. Are there any other post-mortems (Characters team, Props team) beyond CVW and Worlds that are accessible?
