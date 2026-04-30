This file is written by Yibo Liu to provide initial context for this project. I would like you to gather as much information as you can from all useful data sources, including codebase, bug records, confluence documentation, developer feedback and so on, to perform a deep and comprehensive analysis, then produce a high-level analysis & recommendations document on the Tag-to-Asset Pipeline. The main target audience of this document is Halo Leadership as well as the technical artists in the studio.

For timeline we are aiming for a 6-9 months plan from 7/1/2026 to 2/1/2026. The big-picture purpose is we aim to evolve our technical foundation to be better prepared for future Halo game projects, with the immediate next project being M2 & M3 which for development can be treated as a single combined project (more context in other documents later).

We're near the end of Project Meteorite (official named Halo: Campaign Evolved), which is a remake of the original Halo: CE. Our tech stack is different from all previous halo games, this time we're using a "stitched-engine with UE 5.5 + BLAM from Halo Reach".

Over the past ~2 years we've learnt a lot from successes, missteps, joys and pains. Now as the current project is winding down we start to look ahead and plan for the future.

In the immediate future, it's highly probable Meteorite 2 and 3 will be our next projects. Of course there's Nyali (codename for the next big Halo title after the Halo Infinite story line) but for our purpose let's focus on M2 & M3.

When I look at the scope of M2 & M3, it's useful to look back into the history of the original Halo trilogy. Halo 2 and Halo 3 was much bigger in feature and content compared to Halo:CE. As a back of the envelop calculation this provides a useful estimate. BTW, the Metorite Animation Pipeline analysis work included some estiamte along this line but only for animation assets. See C:\Users\yibliu\OneDrive - Microsoft\Projects\SE_Evolution\SE_Anim_Pipeline\

As the Studio Technical Art Director, I often use a thought framework of the Triangle: 
1. Visual Quality
2. Content Quantity
3. Computational Performance

For #1 Based on our Meteorite experience I'm least worried about Visual Quality as I believe we have a very talented art team and coherent art direction.

For #2 and #3 however, scale will be our main challenge going forward. Our current content + optimizaion pipeline is barely sufficient for Metoerite 1, which means for future projects we'll need to greatly improve our overall content productivity as well as optimization throughput. Again the reasoning is very similar behind our recent Animation Pipeline analysis work. In other words, our strategy and roadmap should have a greater focus on SCALE, especially content workflow productivity. This means a diverse range of efforts from better asset spec standardization, documentation, tooling, automation, test and validation coverage etc.

Regarding tech stack, a hot topic has always been the "stitched engine". Content creators generally dislike this setup because the BLAM simulation layer requires extra many steps and these steps need special training not available in the general UE community, driving down our content producitivy. On the other hand however, the stitched-engine setup does save us a lot of time to recreate the "Halo Feel" so we don't have to re-implement many legacy features and tunings such as character motion, vehicle handling, AI behaviors and so on. I think on balance we're doing well relatively to other AAA competitors in the industry, simply because from outside view we're able to produce a high-quality AAA shooter with very tight schedule.

Based on subjective feedback I gathered from various artists and tech-artists, the top 5 issues for improvements are:
1. Animation Pipeline
2. Blam tags - https://343industries.atlassian.net/browse/ST-9441
3. Dynamic Object Pipeline / Device Machines - https://343industries.atlassian.net/browse/ST-9447
4. UE Derivation - https://343industries.atlassian.net/browse/ST-9444
5. Nav/collision mesh workflow

Please note these 5 top stitch-engine issues are anecdotes and should not be treated as absolute truth. The reality may differ. Feel free to suggest new ideas/recommendations as we go with the study effort.

---

## Post-Research Findings (April 2026)

After comprehensive analysis of Jira backlogs (15+ HybridEngineDevEfficiency issues), 7 discipline post-mortems, the 38KB Tech Art/Environment Challenges document (82 versions), Animation Pipeline report, and full Meteorite source code:

### Adjusted Priority Ranking (Data-Driven)

The anecdotal top 5 has been adjusted based on cross-source evidence:

| # | Pipeline Area | Shift | Evidence |
|---|--------------|-------|----------|
| 1 | **Animation Pipeline** | — | Animation report, 3-4× scale math, blocked UE toolset |
| 2 | **Collision / Nav Mesh** | ↑ from #5 | Most-cited pain across ALL sources — Worlds PM, Challenges doc, ONI-672 |
| 3 | **Blam Tags / CVW** | ↓ from #2 | P0 Jira items, CVW post-mortem |
| 4 | **Device Machines** | ↓ from #3 | P0 Jira, Worlds PM, reparenting proposal exists |
| 5 | **Content Management & Tooling** | NEW | Cross-cutting force multiplier, cited by every discipline |
| 6 | **UE Derivation** | ↓ from #4 | P2 Jira, moderate scale impact |
| 7 | **Documentation & Standards** | NEW | Every post-mortem, outsource enabler |

### Key Discovery: Collision is Worse Than Expected

Collision authoring emerged as the #2 pain point — more severe than initially ranked:
- Separate meshes for Render/Collision/Fallback/HLOD bloat asset count
- Any collision fix requires BLAM export → 3-5 min structure generation
- 500K triangle budget cap crashes the BLAM structure generator
- Content creators "will try to avoid collision" because workflow is so cumbersome
- NavMesh auto-update is disabled in code; all rebuilds are manual

### Animation Scale Math (Validated)

- M1: ~11,000 animation assets
- M2 incremental: ~9,000-14,000 (35-45% reuse)
- M3 incremental: ~8,000-14,000 (50-65% reuse)
- Trilogy total: ~28,000-39,000 (3-4× current volume)

### Three Strategic Themes

1. **Scale Through Productivity** — Handle 3-4× volume through pipeline modernization, automation, and documentation
2. **Minimize BLAM Surface Area** — Move collision, device machines, animation toward UE-native workflows
3. **Build the Foundation** — TA tools framework, validation overhaul, content management, documentation standards

Full analysis: [TA Strategy & Roadmap 2026](TA_Strategy_Roadmap_2026.html)

