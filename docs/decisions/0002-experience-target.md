# 0002 Target what the player sees, with a floor on real frames

Date: 2026-10-21. Decided by: Fede. Supersedes the frame-rate target in 0001.
Everything else in 0001 still stands: handheld first, subscription-only budget.

## Why

The first real measurement contradicted the old target. The run was on a Steam Deck
OLED in Game Mode: Monster Hunter Wilds, Windward Plains, normal weather, open plains,
hunting a Chatacabra. Settings were Fede's own: FSR3 Balanced, mostly Low, textures
High, frame generation off. Over 5 minutes, real frames gave:

- average 24.8 fps;
- 1% low about 13 fps;
- the GPU at its maximum clock and over 90% busy for 84% of the run.

A locked 45, or even 35, from real frames alone is not reachable there.

With the in-game FSR3 frame generation, Fede reports a picture between 30 and 40 fps
that looks good and plays well. That figure comes from the in-game overlay, not a
DeckForge log. The product goal is that experience, made steady and tuned
automatically.

## Decision

1. **The target is what the player sees, with frame generation allowed.**

   | Level | What the player sees | Real frames underneath |
   |---|---|---|
   | Gold | locked 35 fps (screen at 70 Hz) | steady 17.5 |
   | Good enough | steady 30-35, 1% low >= 28 | 1% low >= 14 |
   | Fail | anything else | below the floor |

2. **Real frames are always measured and reported separately.** A result is never
   described as native when frame generation produced it.
3. **Looks, for now:** quality floors that Fede sets once, plus a cut order of "least
   visible first" for each engine. The defaults are textures High, upscaler
   Performance or better, and frame generation on. An optional 1-5 rating after a
   session lets the tool learn his taste.
4. **Looks, later:** an image-quality score computed on the Deck from the Wilds
   benchmark's fixed scene. Frames never leave the Deck.
5. **Not chosen:** sending game frames to Claude for a visual judgement. It would
   break the rule that captures stay local.

## Accepted trade-off

At a real base of 17.5 fps, input lag is higher than at a real 35. Fede judges this
playable for Monster Hunter. Other games may get a stricter real-frame floor in
their profile.
