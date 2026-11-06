# AI for Business

AI research in business and economics, grouped by research question.

Data cutoff 2026-11-04. The catalogue contains 193 independent papers from 18 journals. The target pool is the 51-journal union of UTD24 and the April 2026 FT50 list, with retrospective coverage starting in 2020. Journal archives, online-first articles, missing abstracts and candidates remain under review. The website documents actual coverage and the sources for each paper.

## Website

https://charlottexinyu.github.io/ai-for-business/

## Rebuild

Python 3.9 or later, from the repository root.

    python3 source/ai-for-business/build.py --papers source/ai-for-business/papers.json --coverage source/ai-for-business/coverage.json --journals source/ai-for-business/journals.md --output ai-for-business --as-of 2026-11-04

Use the actual data cutoff when updating. Keep assets/site.css and assets/site.js with the generated pages.

## Monthly maintenance

The owner's Codex research automation updates verified records and coverage, rebuilds the site, checks links and counts, commits the project changes, pushes to main, and verifies the deployed version. The schedule is maintained in Codex. Paper publication, reading status and site deployment are tracked independently.
