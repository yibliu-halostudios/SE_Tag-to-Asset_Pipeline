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

- **Unified study**: Blam Tags (upstream) + UE Derivation (downstream) = one end-to-end pipeline
- **CVW = Characters, Vehicles, Weapons** — the primary consumers of this pipeline
- **Both new-from-scratch AND legacy Reach updates** are in scope for M2/M3
- **Pain is front-loaded**: initial UE Derivation setup = 1–3 weeks; iteration on derived assets is fast
- **Python tag field access prototype exists** — confirmed achievable and promising
- **Team also open to architectural refactoring** if capacity allows

---

## Phase 2: Deep Analysis

### 2A. Full End-to-End Workflow Map

#### The Two Directions of Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  DIRECTION 1: BLAM → UE ("Tag Loading")                                            │
│  ──────────────────────────────────────                                              │
│  Legacy Reach tag binary → BlamTagIoHandler → UBlamTagDataAssetBase (UE DataAsset)  │
│  • Automatic, no artist intervention                                                │
│  • UAssets in /Game/Tags/ with strict 1:1 naming to BLAM tag path                   │
│  • Lazy-loaded at runtime via FBlamTagToAssetManager                                │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  DIRECTION 2: UE → BLAM ("UE Derivation")                                          │
│  ──────────────────────────────────────────                                          │
│  UE Content → Sidecar XML → FBX Export → Foundation Tool → BLAM Binary → Reload    │
│  • MANUAL setup per new asset (1–3 weeks)                                           │
│  • Fast iteration once initially configured                                          │
│  • This is where the M2/M3 scaling bottleneck lives                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

#### UE Derivation: Step-by-Step Workflow (New CVW Asset)

```
PHASE A — INITIAL SETUP (the 1–3 week bottleneck)
══════════════════════════════════════════════════
Step 1: Maya/DCC Authoring
  • Artist creates SkeletalMesh, collision meshes, physics asset, animations
  • Must conform to naming conventions (all snake_case)
  • Must manually zero skeleton orientation
  • Must set up regions/permutations/bones in Maya rig

Step 2: FBX Export from Maya → UE Import
  • Must use legacy importer (not Interchange)
  • Import Blam markers into skeleton FIRST
  • Collision: either re-author or pull from Reach (requires 3DS Max / Cyprus share)

Step 3: Create Tag UAssets in UE
  • Create UBlamModelTagDataAsset (.model) in /Game/Tags/...
  • Create sub-tags: collision_model, skeleton_model, physics_model, model_animation_graph
  • Each must follow exact naming convention matching BLAM tag path
  • NO Python automation available — all manual via UE editor
  • NO auto-mapping (BlamDerivedTagToAssetMapper was DELETED)

Step 4: Wire Up References
  • Model tag → point to SkeletonModel, CollisionModel, PhysicsModel, AnimGraph sub-tags
  • CollisionModel → wire each FBlamCollisionMeshData entry:
    - Region (manual), Material (manual), Permutation (manual), Bone (manual), CollisionMesh (ref)
  • PhysicsModel → wire physics bodies to bones
  • All data already exists in Maya rig but CANNOT be auto-scraped (no Python tag field access)
  ⚠️ THIS IS THE CORE BOTTLENECK: duplicating Maya structure into BLAM tags by hand

Step 5: Configure Sidecar XML & Export
  • Model tag generates sidecar.xml (via FBlamTagSidecarGenerator)
  • Sidecar describes folder structure + intermediate FBX paths
  • UE exports FBXs into intermediate folder
  • Foundation/BLAM tool picks up sidecar + FBXs → generates BLAM binary structure
  • Structure generation: 3–5 minutes for collision
  • 500K triangle limit — crashes if exceeded

Step 6: Blueprint & Game Integration
  • Create UE Blueprint for the object
  • Wire Blueprint to tag DataAssets
  • Configure gameplay parameters (player interaction, destruction, etc.)
  • Test in PIE (requires re-export to BLAM before every PIE session)

PHASE B — ITERATION (fast once setup is complete)
══════════════════════════════════════════════════
  • Edit mesh/anim in Maya → re-export FBX → reimport in UE
  • Hit "Import" on model tag → regenerates BLAM binary (3–5 min for collision)
  • Test in PIE
  • ⚠️ Cannot have asset loaded in level during collision export (100% crash)
  • ⚠️ Must manually rebuild NavMesh after collision changes
```

#### Critical Failure Modes in the Pipeline

| Step | Failure Mode | Impact | Frequency |
|------|-------------|--------|-----------|
| 3 | Tag naming doesn't match BLAM path | Asset silently fails to load | Occasional |
| 4 | Region/Permutation/Bone mis-wired | Collision doesn't work in game | Common |
| 5 | Exceeds 500K triangle budget | Structure generator crashes | Occasional |
| 5 | Asset loaded in level during export | Editor crash (100% repro) | Very common |
| 6 | Forgot to re-export before PIE | PIE uses stale data, confusing results | Every session |
| 4 | Cannot undo naming mistake | Capitalization-only rename blocked by UE | Rare but painful |

---

### 2B. Scale Impact Analysis

#### M1 Baseline
- ~34,300 BLAM tags total in the project
- CVW: ~18,900 assets (chars ~13.6K, vehicles ~3.7K, weapons ~1.6K)
- All important CVW assets (~50+) went through full UE Derivation for M1 ship
- Each new asset: 1–3 weeks of TA time for initial setup
- Package size: 86 GB (already 40% over 50 GB target)

#### M2 Projection (Halo CE → Halo 2 scaling)
| Content | M1 | M2 Projected | New Assets Needing UE Derivation |
|---------|-----|-------------|----------------------------------|
| Weapons | ~10 types | ~15 types (+ dual-wield) | ~5 new weapon types |
| Vehicles | ~6 types | ~9 types (+ hijacking) | ~3 new vehicle types |
| Characters | Current roster | + Brutes, Drones, Arbiter, Prophets | ~5–8 new enemy/character types |
| Device Machines | Deliberately limited | Significantly more needed | Dozens |
| MP Maps | 0 (campaign only) | 12+ competitive maps | Each with unique collision/nav |

#### Cost Projection at Current Rate
- New CVW assets for M2: **~13–16 genuinely new types** (weapons + vehicles + characters)
- At **1–3 weeks** UE Derivation setup per type: **13–48 person-weeks** just for initial setup
- Device machines (related pipeline): dozens more
- Plus: each MP map requires full collision/nav/HLOD/streaming pipeline work
- **Conservative estimate: 6–12 person-months of pure UE Derivation setup work for M2 alone**
- This does NOT include iteration time, bug fixing, or the crash/workaround overhead

#### What Breaks at M2/M3 Scale
1. **TA bottleneck**: Only TAs can do UE Derivation (specialized BLAM knowledge required). Team size is fixed.
2. **Innovation tax**: Every new feature on an asset adds setup time. This causes features to be cut.
3. **Error compounding**: Manual wiring × more assets = more bugs. Each collision mis-wire takes hours to diagnose.
4. **No outsource path**: Cannot outsource UE Derivation (requires deep BLAM knowledge, no documentation).
5. **Collision pipeline**: Each MP map needs full collision/navmesh. At 3–5 min per export with frequent crashes, this doesn't scale.

---

### 2C. Root Cause Analysis

| Pain Point | Root Cause Category | BLAM-Fundamental? | Fixable via Tooling? |
|-----------|--------------------|--------------------|---------------------|
| P0: 1–3 week setup | **No automation** — manual duplication of Maya data into BLAM tags | Partially (BLAM binary format is fixed) | **YES** — Python tag field access would automate most of this |
| P1: 3–5 min structure gen | **BLAM structure generator** performance | YES — BLAM tool, not ours | Partially (incremental builds could help) |
| P2: No Python tag fields | **Missing API layer** between Python and BLAM tag binary | No — this is a tooling gap | **YES** — prototype exists |
| P3: Crash on export w/ asset loaded | **Engine concurrency bug** | BLAM/UE integration bug | YES — engineering fix |
| P4: Socket round-trip broken | **UE 5.5 regression** | No — UE bug | YES — UE upgrade or workaround |
| P5: Must re-export before PIE | **Architecture** — BLAM reads from disk, not UE memory | YES — by design | Partially (could auto-export on PIE) |
| P6: Naming constraints | **Strict 1:1 coupling** between UE path and BLAM tag path | YES — by design | Partially (rename tooling) |
| P7: Separate mesh bloat | **BLAM requires** distinct meshes per purpose | YES — BLAM architecture | No (without BLAM changes) |
| P8: Duplicate Maya→tag data | **No data bridge** between DCC and BLAM | No — tooling gap | **YES** — Maya scraping → auto-fill |
| P9: Collision redesign needed | **Multiple factors**: slow gen, crash, manual wiring | Partially BLAM | YES (preview, incremental) |

#### Root Cause Categorization Summary

| Category | Count | Fixable? |
|----------|-------|----------|
| **Tooling/automation gap** (Python, Maya bridge, rename tools) | 4 (P0, P2, P8, P6) | YES — highest ROI |
| **BLAM-fundamental** (structure gen, separate meshes, disk-based) | 3 (P1, P5, P7) | Partially — workarounds possible |
| **Engineering bugs** (crash, socket, concurrency) | 2 (P3, P4) | YES — discrete fixes |
| **Needs architectural change** (collision redesign) | 1 (P9) | Requires multi-team effort |

#### The "80/20" Finding
**4 of 9 pain points trace to the same root cause: lack of Python read/write access to tag field data.** Fixing this single capability gap would:
- Enable automated UE Derivation setup (P0 → minutes instead of weeks)
- Unlock Maya data scraping into tags (P8 → no more duplicate manual work)
- Enable batch validation and tag diffing (P2 → catch wiring errors early)
- Enable scripted rename/refactoring tools (P6 → safe tag renaming)

**This is the single highest-leverage investment identified in this study.**

---

## Current Pipeline Architecture

### Tag Type Taxonomy (from BlamDerivedTagDataAssets.h)
Every BLAM tag type maps to a `UBlamTagDataAssetBase` subclass (a UE DataAsset). The file enumerates ~100+ tag types. Key CVW-relevant types:

| Tag Extension | Class | Notes |
|---|---|---|
| `biped` | UBlamBipedTagDataAsset | Character/AI entity |
| `character` | UBlamCharacterTagDataAsset | Character behavior |
| `model` | UBlamModelTagDataAsset | Master dynamic object tag — owns sub-tags |
| `collision_model` | UBlamCollisionModelTagDataAsset | Physical collision |
| `physics_model` | UBlamPhysicsModelTagDataAsset | Ragdoll/physics |
| `render_model` | UBlamRenderModelTagDataAsset | Render mesh |
| `skeleton_model` | UBlamSkeletonModelTagDataAsset | Skeleton/rig |
| `model_animation_graph` | UBlamModelAnimationGraphTagDataAsset | Animation state machine |
| `vehicle` | UBlamVehicleTagDataAsset | Vehicle entity |
| `weapon` | UBlamWeaponTagDataAsset | Weapon entity |
| `object` | UBlamObjectTagDataAsset | Base object |

### The Model Tag Cluster (core of CVW pipeline)
`UBlamModelTagDataAsset` is the master tag for any dynamic object. It owns:
- `SkeletonModel` → `UBlamSkeletonModelTagDataAsset`
- `CollisionModel` → `UBlamCollisionModelTagDataAsset`
- `PhysicsModel` → `UBlamPhysicsModelTagDataAsset`
- `ModelAnimationGraph` → `UBlamModelAnimationGraphTagDataAsset`
- `ModelRegionStringTable` → regions, permutations, materials

**Import arguments** (what the model tag exports FROM UE INTO Blam):
`["physics", "collision", "animations", "skeleton"]`

### Tag Data Flow — Two Directions
1. **BLAM → UE ("Loading"):** Reading legacy Reach tag binary into UE DataAsset bulk data — handled automatically
2. **UE → BLAM ("UE Derivation" / "Import into Blam"):** Taking UE skeletal meshes, static meshes, physics assets, animations and exporting them into BLAM tag binary format — requires many **manual steps**

The term "UE Derivation" in practice means: re-authoring an asset so UE content (rather than legacy Reach files) becomes the source of truth. The BLAM tags are then *derived from* the UE content.

### Collision Model — Key Complexity
`UBlamCollisionModelTagDataAsset` has array of `FBlamCollisionMeshData`:
- Each entry = { Region, Material, Permutation, Bone, CollisionMesh (UStaticMesh) }
- All four fields must be manually wired up per mesh
- Has soft reference back to the parent ModelTag (needed for reload chaining)
- **Reload dependency chain**: saving collision_model triggers reload of model tag
- Has a vestigial `OriginalReachSourceModelFile` field (GR2 path from Reach) — still needed to recover local-space matrices lost during FBX conversion

### BlamDerivedTagToAssetMapper — DELETED
`BlamDerivedTagToAssetMapper.h` was deleted in changelist 340820. This class previously mapped Derived Tags to UE assets automatically. Its deletion may have left manual wiring as the only path.

### Tag I/O System
- Tags exist in two forms: **disk files** (raw Reach binary) and **IoStore packages** (cooked)
- `BlamTagIoHandlerDisk` / `BlamTagIoHandlerIoStore` — two loading paths
- Tag loading priority (from scenario tag doc): In-memory bulk data → disk file → UAsset lookup
- Local tag files (structure exports) are **never checked in** — built locally from UE map

### BlamTagToAssetManager — Runtime Tag→UAsset Resolution
`FBlamTagToAssetManager` is the runtime system that maps BLAM tag indices to UE DataAssets:
- **20 "well-known" tag group types** tracked at runtime: biped, device_control, crate, creature, effect_scenery, equipment, giant, device_machine, projectile, scenery, device_terminal, vehicle, weapon, effect, sound, sound_looping, sound_combiner, sound_scenery, cinematic, damage_response_definition
- **Asset path is derived from BLAM tag name**: `/Game/Tags/{path}/{name}-{ext}.{name}-{ext}` — strict 1:1 naming
  - Example: BLAM tag `objects/vehicles/banshee/banshee` → UE path `/Game/Tags/objects/vehicles/banshee/banshee-vehicle.banshee-vehicle`
  - **This is why renaming is so hard**: UE path must always match the BLAM tag name exactly
- Default fallback assets live at `/Game/Tags/Default/default-{ext}.default-{ext}` — used when the expected UE asset is missing
- Tags are lazy-loaded asynchronously via `FBlamLazyLoadedAsset` + `FStreamableManager`
- If default asset is missing at PIE start → warning dialog + PIE shutdown (hard failure)

### Sidecar XML System (UE → BLAM Export Path)
`FBlamTagSidecarGenerator` generates a `.sidecar.xml` file that drives the export from UE into BLAM:
- Format: `Metadata > Header + Asset + Folders + Contents` — this is the Foundation (Halo DAM tool) XML format
- Contains folder structure: `models/work`, `models`, `animations`, `export/models`, `export/animations`, etc.
- Contains `ContentObjects` with `IntermediateFile` paths pointing to FBX exports
- Generated by `UBlamModelTagDataAsset` (header says "created by UBlamModelTagDataAsset 0.1")
- The sidecar XML is passed to Foundation/BLAM toolchain which processes it and writes binary tag data

### Full UE Derivation Flow (reconstructed from code)
1. Artist creates/updates content in UE: SkeletalMesh, StaticMesh (collision), PhysicsAsset, AnimSequences
2. Opens the model `.uasset` DataAsset in the UE tag editor
3. Hits "Import" (derives BLAM from UE) — calls `GetImportArguments()` → `["physics", "collision", "animations", "skeleton"]`
4. For each sub-type, generates a **sidecar XML** describing what to export
5. UE exports FBXs into an intermediate folder
6. Foundation/BLAM tool picks up the sidecar XML + FBXs → runs BLAM structure generation (3–5 min for collision)
7. BLAM writes binary tag data to disk
8. UE reloads the tag DataAsset with new binary bulk data
- **Failure modes at any step break the whole chain**
- Step 6 crashes if mesh exceeds 500K triangles (BLAM structure generator limit)

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

### Interview Q&A

**Q1** (Yibo, session 1): Should Blam Tags + UE Derivation be one unified study or two separate analyses?  
**A:** Unified — they are two faces of the same end-to-end pipeline.

**Q2** (Yibo, session 1): What does CVW stand for?  
**A:** Characters, Vehicles, Weapons.

**Q3** (Yibo, session 1): Can the CVW Mural post-mortem be shared?  
**A:** Link provided: https://app.mural.co/t/microsoftenterprise6294/m/microsoftenterprise6294/1774916214773/2405a997de56dd636af5ab29dd89d1b9f64b7cf0  
*(Mural content not yet extracted — pending)*

**Q4** (Yibo, session 2): What does "UE Derivation" mean in practice?  
**A:** Artists have to manually set lots of BLAM parameters for assets like Banshee. Scope boundary still being investigated via codebase.  
*(Now resolved from code: UE Derivation = exporting UE content into BLAM tag binary via sidecar XML + Foundation tool)*

**Q5** (Yibo, session 2): For M2/M3, do both legacy Reach asset updates AND new-from-scratch assets apply?  
**A:** Yes — both are in scope.

**Q6** (Yibo, session 3): How many CVW assets have been UE-derived so far?  
**A:** 50+, enough to ship M1. All important CVW assets (hero and non-hero) have been UE-derived — otherwise they wouldn't work in game.

**Q7** (Yibo, session 3): Where does ongoing pain live — initial setup or iteration on already-derived assets?  
**A:** Mostly initial setup. Once derived, iterations are fast.

**Q8** (Yibo, session 3): For M2/M3, what's the scale of new CVW content?  
**A:** Anything from M1 will be reused. New content scales with Halo CE→H2→H3 as proxy:  
- Weapons: M1 ~1,600 (10 types) → M2 ~2,400 (15 + dual-wield) → M3 ~2,600 (16 + 9 equip)  
- Vehicles: M1 ~3,700 (~6 types) → M2 ~5,500 (~9 + hijacking) → M3 ~7,400 (~12 types)  
- Characters: M1 ~13,600 → M2 +8–12K new → M3 +6–9K new

**Q9** (Yibo, session 3): Would Python read/write access to tag fields unlock automation of the 1–3 week UE Derivation setup?  
**A:** **YES** — the team has already done initial prototyping and it's promising. In addition to automation opportunities, they're also interested in major architecture/pipeline refactoring if there's capacity.

**Q10** (Yibo, session 3): What is "pytags"?  
**A:** Unknown — may be internal Python library, Foundation CLI wrapper, or similar. TBD.

### Key Implication for Recommendations
Python tag field access is the **primary unlock** for automating UE Derivation:
- Prototype exists → confirmed achievable investment
- Would enable Maya data scraping → auto-fill BLAM tag parameters
- Would enable batch validation, tag diffing, dependency tracking
- Team is also open to major architectural refactoring given capacity

### ST-9446 — Ben Frazier's verbatim feedback (P0)
> *"Working with, and setting up, CVW assets for use with the stitched engine have required a process we have dubbed 'UE derivation'. Where techart goes in and sets up the blueprints and Blam tag file connections for an asset to run in game."*
> 
> *"This is a complex process that has varied from asset to asset depending on the needs (player interaction level, destruction, etc). But generally my understanding was that it took **1-3 weeks to set up.**"*
> 
> *"This is a laborious process that limits innovation because the already steep cost here was one of many reasons that we would often say **any new or innovative feature to be added to an asset would need to be cut.**"*

### M1 Content Footprint (from TA Strategy Roadmap)
| Content Area | M1 Asset Count | M1 Disk |
|---|---|---|
| Characters | ~13,600 | ~11 GB |
| Vehicles | ~3,700 | ~8 GB |
| Weapons | ~1,600 | ~5 GB |
| Tags (BLAM) | **~34,300** | ~5 GB |
| Environments | ~31,300 | ~40 GB |
| VFX | ~10,000 | ~5% |
| Animations | ~11,000 clips | — |
| Total Package | — | **86 GB** (40% over 50 GB target) |

CVW total (Chars + Vehicles + Weapons): **~18,900 assets**  
BLAM tags: **~34,300 assets** (includes scenario structures, BSP data, BLAM metadata)

---

## Open Questions

1. ~~**Scope:** Treat Blam Tags and UE Derivation as unified?~~ **RESOLVED: Yes — unified analysis.**
2. ~~What does "CVW" stand for?~~ **RESOLVED: Characters, Vehicles, Weapons.**
3. Is there a Perforce query or asset count for how many Tag Data Assets (UAssets) currently exist in the project?
4. Are there any other post-mortems (Characters team, Props team) beyond CVW and Worlds that are accessible?

---

## Key Pain Points — Confirmed Signal

### P0 (CRITICAL): UE Derivation Setup = 1–3 Weeks Per CVW Asset
**Source:** ST-9446 (P0 verbatim), ST-9442, ST-9444, ST-9446  
**Scale impact:** At M2/M3 (3–4× content), greenfield CVW assets at 1–3 weeks each is untenable.  
**Root cause (from codebase):** Manual wiring of regions/permutations/bones in `UBlamCollisionModelTagDataAsset`; sidecar XML must be manually configured; each sub-tag (skeleton, collision, physics, animation) set up independently; no automation for parameter propagation from Maya rig data.

### P1: BLAM Structure Generation = 3–5 Min Per Collision Export
**Source:** Confluence — Env|HS:Collision page  
- Hard budget cap: 500K triangles → crashes structure generator  
- NavMesh depends on BSP structure → separate "Generate Pathfinding" step  
- Must re-export every iteration; no incremental update path

### P2: No Python Access to Tag Field Data
**Source:** ST-9548 (practitioner verbatim): *"due to not being able to access the actual tag _fields_ via python, you can't hook them together in any automatic way"* and *"this makes all of our animation pipelines in maya pretty well useless"*  
**Current tools:** "pytags" handles conversion/batch scripts only — cannot read/write individual tag field values

### P3: Crash on Collision Export with Asset in Level
**Source:** ST-9548 — 100% repro  
- Must unload asset from level → export → reload for every iteration

### P4: Socket/Marker Round-Trip Broken in UE 5.5
**Source:** ST-9548  
- Native UE socket workflow is broken; UE 5.5 broke socket round-tripping

### P5: Must Re-Export to BLAM Before Every PIE
**Source:** PIE+Blam Confluence page  
- Any UE edit requires re-export; local structure files never checked in  
- Structural rebuilds are slow and manual

### P6: Naming Constraints / Renaming Blocked
**Source:** Asset Updating Confluence page + codebase  
- UE asset path must match BLAM tag name 1:1  
- UE cannot do capitalization-only renames; requires workarounds  
- Renaming a tag potentially breaks all scene references

### P7: Separate Meshes for Render/Collision/Fallback/HLOD Bloats Asset Count
**Source:** Worlds Post-Mortem  
- *"Having separate meshes for Render, Collision, Fallback, and HLODs is bloating our asset count and making things more error-prone"*

### P8: "Duplicate Work to Setup Tag Data from Maya"
**Source:** ST-9548 — practitioner verbatim  
- *"We already have to localize collision and render meshes under joints in maya... Tooling to help support 'scraping' the data from maya to auto-fill these out would save both time and human error."*  
- Data already exists in Maya rig/scene but cannot be automatically propagated to BLAM tags

### P9: Collision Authoring Needs a Full Redesign
**Source:** Worlds Post-Mortem  
- *"Currently stitched collision workflows are very slow, opaque, and error prone. I suggest we go back to the drawing board on how to author, view, and generate collision"*  
- *"We need a way to instantly update collision meshes when reimporting, without having to export to Blam"*
