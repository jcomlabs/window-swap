---
format: 1920x1080
message: "Window Swap preserves spatial context by cycling windows that share one screen region."
arc: "Problem → Solution → Demonstration → Build Week extension → Proof → CTA"
audience: "OpenAI Build Week judges and Windows users"
mode: autonomous
music: none
---

## Video direction

Use the remixed Blue Professional system: light `bg`, near-black `text`, blue `primary`, tinted blue cards, Arial display/body, and no content shadows. Motion is camera-static or a single purposeful move, with smooth long-tail settles and every reveal timed to its spoken cue. Frames 2 and 5 receive deliberate held reads. Never front-load then freeze; never float everything independently; no lazy breathing, bouncy entrances, personal desktop imagery, third-party marks, fabricated metrics, or content inside the bottom caption band.

## Frame 1 — Keep the region

- scene: Outcome-first kinetic statement resolves from window juggling to preserved spatial context.
- voiceover: "Your windows already have a place. Window Swap lets them share it, without losing your spatial context."
- duration: 12s
- poster: 10s
- transition_in: cut
- status: animated
- src: compositions/frames/01-keep-the-region.html
- type: hook
- persuasion: Friction reduction
- beat: recognition + relief
- blueprint: kinetic-type-beats (Adapt)
- asset_candidates:
- focal: typography
- roles: typography = cutout
- sfx: none

narrativeRole: State the user value before naming implementation details.
keyMessage: Keep a screen region useful without repeatedly rearranging windows.

Adapt: keep the in-place token-swap signature; change the rapid montage into three restrained statements and a held payoff.
Scene 1 (0.0–3.0s): “Your windows” arrives upper-left in large display type; a thin blue rule draws underneath — asymmetric 70/30, three depth layers.
Scene 2 (3.0–7.0s): “already have a place” assembles phrase-by-phrase on its spoken cues via per-word staggered reveal (`dynamic-content-sequencing`); a tinted region outline appears at right.
Scene 3 (7.0–12.0s): “Share it. Keep context.” replaces the prior line with an in-place hard-cut token cycle (`discrete-text-sequence`), then holds still; the blue progress strip completes the read.

## Frame 2 — Swap, demonstrated

- scene: The privacy-safe recording shows the real overlay and a visible B-to-A window swap.
- voiceover: "Move into the corner, choose Swap, and the next matching window takes the same position. One gesture. No hunting. No rearranging."
- duration: 20s
- poster: 16s
- transition_in: zoom-through
- status: animated
- src: compositions/frames/02-swap-demonstrated.html
- type: feature_showcase
- persuasion: Show-don't-tell proof
- beat: clarity + control
- blueprint: device-surface-showcase (Adapt)
- asset_candidates: assets/window-swap-real-demo-final.mp4 — privacy-safe B-to-A swap using disposable windows
- focal: assets/window-swap-real-demo-final.mp4
- roles: window-swap-real-demo-final.mp4 = cutout
- sfx: none

narrativeRole: Prove the core interaction on the actual shipped code path.
keyMessage: The swap is immediate and preserves the occupied region.

Adapt: keep the persistent-surface and discrete state-advance signature; replace the device mockup with the real captured application surface and keep the camera static.
Scene 1 (0.0–3.5s): “THE REAL INTERACTION” and a one-line instruction reveal above a large tinted video well — full-width strip, hero surface above the caption band.
Scene 2 (3.5–15.5s): the real video plays once, uncropped inside the well; labels “CORNER”, “SWAP”, and “B → A” reveal only as the narration reaches each cue — layered-depth, surface ≥65% of canvas.
Scene 3 (15.5–20.0s): final Workspace A state holds; “same region · next window” appears beside it via a restrained titlecard reveal; no camera drift.

## Frame 3 — Extended during Build Week

- scene: Four engineering extensions assemble as a compact evidence grid.
- voiceover: "During Build Week, the prototype became a dependable daily tool: negative-coordinate monitor support, duplicate-instance prevention, privacy-conscious diagnostics, and hardened build and release automation."
- duration: 18s
- poster: 16s
- transition_in: crossfade
- status: animated
- src: compositions/frames/03-build-week-extension.html
- type: feature_showcase
- persuasion: Value stacking
- beat: confidence
- blueprint: grid-card-assemble (Adapt)
- asset_candidates:
- focal: four verified engineering cards
- roles: four verified engineering cards = cutout
- sfx: none

narrativeRole: Distinguish the pre-event prototype from the meaningful event-period extension.
keyMessage: Build Week work made the app safer and more dependable, not merely prettier.

Adapt: keep the sequential grid-assembly signature; use four verified changes and a still final grid without ambient floating.
Scene 1 (0.0–4.0s): “EXTENDED DURING BUILD WEEK” appears with a date rail and progress line — rule-of-thirds, clear upper anchor.
Scene 2 (4.0–14.5s): four tinted cards enter one at a time on the matching spoken cue: negative coordinates, one instance, privacy-conscious diagnostics, release automation (`center-outward-expansion`, short-path direct-to-slot).
Scene 3 (14.5–18.0s): resolved 2×2 grid holds; the dominant line “DEPENDABLE DAILY TOOL” reveals below the header, safely above the caption band.

## Frame 4 — Human direction, Codex execution

- scene: A human-to-Codex collaboration rail turns decisions into implementation and validation.
- voiceover: "For the submitted session, Codex with GPT-5.6 acted as the engineering partner. I set the product decisions and privacy boundary. Codex audited the code, implemented the changes, tested the Windows behavior, and prepared the public release."
- duration: 18s
- poster: 16s
- transition_in: push-slide LEFT
- status: animated
- src: compositions/frames/04-codex-collaboration.html
- type: product_intro
- persuasion: Process transparency
- beat: trust
- blueprint: compose
- asset_candidates:
- focal: collaboration rail
- roles: collaboration rail = cutout
- sfx: none

narrativeRole: Explain exactly how the human and AI collaborated, as required by the event.
keyMessage: Product judgment stayed human; Codex executed and verified the engineering work.

Scene 1 (0.0–4.0s): two unequal columns establish “HUMAN DIRECTION” and “CODEX EXECUTION”; the human side is a single decisive block, the execution side an empty rail — asymmetric 40/60.
Scene 2 (4.0–14.5s): “privacy boundary”, “audit”, “implement”, “Windows test”, and “public release” reveal sequentially with a connecting SVG path self-draw (`svg-path-draw`) and keyword glow on each spoken cue (`asr-keyword-glow`).
Scene 3 (14.5–18.0s): the rail resolves into “DECIDE → BUILD → VERIFY”; a small “GPT-5.6 · OWNER VERIFICATION REQUIRED BEFORE UPLOAD” label remains visible, and the whole composition holds still.

## Frame 5 — Proof, not promises

- scene: Verified test, release, privacy, and CI evidence lands as a restrained proof dashboard.
- voiceover: "The result is backed by fifteen automated tests, passing continuous integration, a reproducible Windows release, and a public repository audited for photos, credentials, secrets, and machine-specific paths."
- duration: 18s
- poster: 16s
- transition_in: squeeze
- status: animated
- src: compositions/frames/05-proof.html
- type: social_proof
- persuasion: Risk reversal
- beat: assurance
- blueprint: dataviz-countup (Adapt)
- asset_candidates:
- focal: verified proof dashboard
- roles: verified proof dashboard = cutout
- sfx: none

narrativeRole: Replace marketing claims with verifiable engineering evidence.
keyMessage: The public artifact is tested, reproducible, and privacy-audited.

Adapt: keep the hero count-up and instrument-to-instrument traversal; replace speculative metrics with four repository-verifiable facts and use a short lateral focus change instead of a push-through.
Scene 1 (0.0–5.0s): the number counts 0→15 with a paired progress ring (`counting-dynamic-scale`, `stat-bars-and-fills`); “AUTOMATED TESTS” lands beneath — centered hero, large numerical hierarchy.
Scene 2 (5.0–13.5s): focus moves laterally across three tinted proof cards — “CI PASSING”, “WINDOWS RELEASE”, “PRIVACY AUDIT” — each reveals on its spoken cue; off-focus cards dim slightly (`depth-of-field-blur`).
Scene 3 (13.5–18.0s): all four facts settle into a balanced dashboard; accent glow blooms once behind “PUBLIC + REPRODUCIBLE” and then holds still.

## Frame 6 — Download and swap

- scene: Window Swap identity condenses into a single repository call to action.
- voiceover: "Window Swap. Keep the place. Change the window. Download the alpha and inspect every line on GitHub."
- duration: 12s
- poster: 10s
- transition_in: crossfade
- status: animated
- src: compositions/frames/06-download.html
- type: cta
- persuasion: Transparency-led call to action
- beat: motivation
- blueprint: cta-morph-press (Adapt)
- asset_candidates:
- focal: Window Swap lockup and GitHub path
- roles: Window Swap lockup and GitHub path = cutout
- sfx: none

narrativeRole: End on one inspectable next action.
keyMessage: Download the release or review the source at the public repository.

Adapt: keep the same-center brand-to-CTA morph and press signature; the CTA is the plain repository path, with no third-party logo.
Scene 1 (0.0–3.5s): “WINDOW SWAP” holds centered inside faint closing rings; “Keep the place. Change the window.” reveals beneath — low-density closing frame.
Scene 2 (3.5–7.0s): the lockup condenses at the same center into a solid blue “DOWNLOAD ALPHA” pill (`scale-swap-transition`).
Scene 3 (7.0–10.0s): a simple arrow cursor decelerates from off-stage and presses the pill in lockstep (`physics-press-reaction`); a restrained ripple resolves.
Scene 4 (10.0–12.0s): `github.com/jcomlabs/window-swap` appears above the progress strip and holds fully legible.
