---
name: write-article
description: Write SEO-optimised health and wellness articles for wellkinddaily.com from a list of primary keywords, secondary keywords, titles and optional sample content to benchmark against. Use when the user supplies keywords or titles and wants article drafts ready to paste into WordPress.
---

# Write articles for WellKind Daily

Turn the user's keyword list into original, useful articles in WellKind Daily's voice, formatted for WordPress.

## Inputs

The user provides some or all of:

- **Primary keyword**: one per article. The topic the article must rank for.
- **Secondary keywords**: related terms to work in naturally.
- **Title**: use it as given. If missing, write one that contains the primary keyword.
- **Sample content** (optional): articles that already rank. Benchmark only.

If the primary keyword is missing for an item, derive it from the title and say so. Do not stop to ask questions when the inputs are workable; state assumptions at the top of the output instead. Process every item in the list.

## Benchmarking sample content

Use samples to learn what the topic needs, never to copy:

- List the headings, questions answered and sub-topics the samples cover.
- Note what they miss: a clearer explanation, a practical step, a caveat, a newer angle.
- Cover everything readers expect, then add something the samples lack.
- Never reuse sentences, phrasing, structure verbatim or statistics you cannot source. The article must be original.

## Voice

Match the site: plain, friendly and practical. It favours "routines you can try" over "quick fixes or guarantees".

- Short sentences, everyday words, second person ("you").
- Explain a term the first time it appears.
- Specific and useful beats general and vague.
- No hype, no fear, no guilt.

## Health content rules

This is a health site. These rules override keyword and ranking goals.

- No promises of cures, treatment or prevention. No "boosts immunity", "melts fat" or "detox" claims stated as fact.
- No made-up statistics, studies, quotes, experts or reviews. Cite only sources you are confident exist, named plainly (for example "the American Heart Association recommends..."). If you cannot verify a figure, leave it out or flag it with `[VERIFY: ...]` for the user.
- Mention who should talk to a doctor first (medical conditions, medicines, pregnancy, children, older adults) where relevant.
- End with a short note: general information, not medical advice.

## Article structure

1. **Title (H1)**: the given title, or one with the primary keyword near the start.
2. **Introduction** (80 to 120 words): name the problem, say what the reader will learn, include the primary keyword in the first 100 words.
3. **Body**: 4 to 8 sections with H2 headings, H3 for sub-points. Put the primary keyword or a close variant in at least one H2. Use secondary keywords in other headings and in body text.
4. **Practical element**: a checklist, step list, sample day, or comparison table where it helps. Keep tables simple (3 or 4 columns).
5. **FAQ**: 3 to 5 real questions people ask, with 40 to 70 word answers.
6. **Conclusion**: a short recap and one small next step.
7. **Disclaimer line.**

Length: 1,200 to 2,000 words unless the user sets another target or the samples show the topic needs more.

## SEO

- Primary keyword: title, first 100 words, one H2, the meta description, and naturally 3 to 6 more times. Never stuff.
- Each secondary keyword at least once, where it fits the sentence.
- **Meta title**: up to 60 characters, includes the primary keyword.
- **Meta description**: 140 to 155 characters, includes the primary keyword, written to earn the click.
- **URL slug**: lowercase, hyphenated, 3 to 6 words, includes the primary keyword.
- **Internal links**: suggest 2 to 4 links to other wellkinddaily.com articles as `[INTERNAL LINK: topic]` placeholders, unless the user gives URLs.
- **Images**: suggest 2 to 4 images with descriptive alt text including the keyword where natural. Do not invent image files.

## Output

For each article, in this order:

1. A short **summary box**: primary keyword, secondary keywords used, word count, assumptions made.
2. **SEO fields**: meta title, meta description, slug, suggested category (Nutrition, Mental Wellbeing, Fitness, Children's Health, Senior Health, Wellbeing), tags.
3. The **article body in clean HTML** for the WordPress Custom HTML block or Code editor: `h2`, `h3`, `p`, `ul`, `ol`, `table`. No inline styles, no `h1` in the body (WordPress adds the title).
4. A list of any `[VERIFY: ...]` items and `[INTERNAL LINK: ...]` placeholders.

When there are several articles, finish one fully before starting the next, and number them. Save each to `articles/<slug>.html` in the repository when the user wants files. Otherwise present them in the reply.

## Quality check before finishing

- The primary keyword and every secondary keyword are used naturally.
- No sentence is copied from a sample.
- No health claim promises a result; every statistic is sourced or flagged.
- The disclaimer is present, headings follow H2 then H3, and no H2 is empty.
- Read the first paragraph aloud in your head. If it sounds like a template, rewrite it.
