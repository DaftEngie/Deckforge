# Round 2 brief: red-team and rescue

You are one of several independent reviewers. Each reviewer covers different clusters of ideas.

The project goal and rules are in `brief.md`. The clustered ideas are in `round2_clusters.md`. Both files are in this scratchpad folder:
`/tmp/claude-0/-home-claude/bafac712-f1ea-5f41-b2ba-592b27d3cd05/scratchpad/`

The full Round 1 reports are in `round1/`. Read `brief.md`, `round2_clusters.md` and the Round 1 reports your clusters cite before you start.

## Your job: break the ideas, then try to rescue what broke

The owner's rule is "don't give up at walls". So a wall you find is a design input. Try to go around it before declaring an idea dead. Only call an idea DEAD if every rescue you try also fails your own attack.

Do these steps for every idea in your clusters.

1. **Is it already done?**
   - Check whether SteamOS 3.8, the Deck's default Proton, gamescope, Mesa/RADV defaults, or the game itself already does this.
   - If so, the gain over the status quo is zero or reduced.
   - Check source code, docs and changelogs. Don't rely on memory.
2. **Check the facts that matter.**
   - Find the facts the idea depends on, then fetch the primary source: the URL, the code at that file and line, or the docs.
   - Mark each one [checked], [contradicted: what the source says], or [could not verify].
   - Be especially strict with anything dated after June 2026.
3. **Redo the budget.**
   - Use your own assumptions and give pessimistic / central / optimistic values in ms or %.
   - Say what is measured and what is estimated.
   - Name any double-counting with other clusters. Two ideas that both save the same GPU milliseconds don't add up.
4. **Find the strongest ways it fails.** Consider:
   - visible artifacts;
   - stability;
   - anti-cheat;
   - SteamOS or Proton updates undoing it;
   - game patches breaking it;
   - CPU-bound vs GPU-bound mismatch;
   - power (a saving at a fixed 15 W cap may not turn into fps).
5. **Check legality and tier.**
   - Does the idea really fit its claimed tier (S or I)?
   - Does it stay within the legal lines?
6. **Give a verdict:** SURVIVES, SURVIVES WITH CHANGES (say which changes), or DEAD (say which rescues you tried).
7. **For anything that survives, write the falsification experiment.**
   - Exact steps, equipment and the measurement.
   - Numeric pass and kill thresholds.
   - It must fit in 2 weeks or less.
   - The judge is a measurement or a blind test, never an opinion.
   - Assume a dedicated bench Steam Deck OLED that the owner runs. A dev session never touches a real Deck.
   - Say what the owner, a non-engineer, has to do by hand.

## Output

Return your final message only. Do not write files: a hook blocks subagent file writes.

Stay under about 2,000 words. Cite URLs and file:line for every load-bearing claim.

End with:
- a one-line verdict table;
- "What would change my mind": one line per idea.
