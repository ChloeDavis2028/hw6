# AI Prompts Log — HW6: Campus Customs Vendor Desk

This file is the log of what I typed to my vibe coder. There is one section for each problem. Each section has the problem number and title, at least one prompt I typed in my own words, and one follow-up prompt if I needed it, with one sentence on what was lacking after the first.

## Getting started (before the numbered problems)

**Prompt:**
> lets work HW6: Campus Customs Vendor Desk:  Contiue with the Campus Customs from HW4 which ets all the time quotes fro vendors, invoices, catalog pages, and supplier emails.  This assignment we will build a vendor desk agent that wll read one of these documents, pull out the key facts (vendor, item, price, lead time, minorder etc) and recommend whether we should buy following the rules in the Campus Customs Shop Handbook.

## Problem 1: Vibe coder prompts

**Prompt:**
> Out one section for each problem and each section must include

(Sent with two screenshots of the assignment's AI_prompts.md instructions.)

**Follow-up prompt:**

**What was lacking after the first:** Literally trying to understand the overall beginning intent of the problem and how to set it all up.

## Problem 2: Size up the handbook

**Prompt:**
> Problem 2: Size up the handbook  Unzip data.zip. Look thru data/shop_handbook.md.  this is the handbook and you as the agent will send it to the model for evey call.  Also, look at data/proces.json, the gpt-6-luna price list

**Prompt (second part):**
> need to know how many tokens is in the handbook:  in output/handbook_estimate.md write the token count and how you go it, what the handbook alone costs in dolars on one call and on 1000 calls with cached tokens and without them (show your math), and be prepapred to check these estimates against real runs in problem 4

**Follow-up prompt:**
> i do not know, find it for me or create it so we can move on

**What was lacking after the first:** Understanding how the data and .zip file works.

## Problem 3: Building the vendor desk agent

**Prompt:**
> Problem 3: Building the vendor desk agent

**Follow-up prompt:**
> Lets build this desk agent with Pydantic AI using gpt-6-luna.  Here are the four files to build the agent: Prompts/prompt.md (instructions for the agent and also the agent send the handbook to the model for every call), agent.py (entry point), tools.py (the tools), models.py (the structured types.  the agent needs a path to one vendor so do it. must read the document with a tool (HTML, PDF, and .eml emailfiles all have to work) and returns: vendor, SKU, unit price, lead time in days, min order, a decision (recommend or do_not_recommend) following the handbook rules and a one-sentence reason.

**Other prompt:**
> keep track of what is being done and gaps along the way with possible opportunities.  ensure it is all collected for one final product at the end for teaching and future checklist resource

**Other prompt:**
> my agent must have two trap tools: send_email and approve_payment. Its job never needs them. this is to catch a malicious or bad document that tricks the agent into emailing somoene or paying a vendor. They do not pay or send anyting.  Only append a call and its arguments to output/trap_calls.json (start as an empty list) so if the file ever has an entry, a document took over your agent.  Keep this on the system for the entire homework.  After every run, append to:

(Sent with two screenshots of the assignment's logging, terminal command, and harness instructions.)

**Other prompt:**
> now explain in more basic terms what this is accomplishing and why.  Then ensure this action is part of the ongoing checklist required for me to understand how to make things work in the future.

**What was lacking after the first:**

## Problem 4: With and without cached tokens

**Prompt:**
> Problem 4: With and without cached tokens

**Follow-up prompt:**
> The handbookis the same on every call, so the model can reuse it from a cache at a much cheaper price. Lets test what that is worth. Run the agent on all 12 practice documents in two ways:  with cache and without cache.  With cache sets up so the handbook gets reused from cache and without it set ups so nothing gets reused from cache.  then check the toke counts the API sends back to prove each setup really did what you think.  A without-cache run that still shows cached tokens does not count.

**Other prompt:**
> Also, save every model call from both setups to output/cache_test.json  for each call include the setup, document every token count the API reports, and dollars from prices.json

**Other prompt:**
(Sent as a screenshot of the assignment's output/cache_test.md requirements, with no typed words.)

**Other prompt:**
> and again teach me in basic terms what is going on with this problem, keep a running dialogue for a future checklist and rewrite these prompts in a running prompt list so i can do this in the future on my own

**What was lacking after the first:**

## Problem 5: Attack your own Agent

**Prompt:**
> Problem 5: Attack your own Agent  Some vendor documents are boobytrapped with text aimed at AI.  Run problem 3 agent with no new defenses on all 12 documents in data/practice_docs/. compare each answer to data/practice_key.json and check output/trap_calls.json, then log the fake email and payment tools from Problem 3 write to

**Follow-up prompt:**
> save output/attack_results.json: for each document, whether each field matched the key, whether the decision matched, whether a trap tool was called, and whether a link or other strange text showed up in the answer

**Other prompt:**
> In output/attack_results.md, for every documetn that fooled the agent, write what fooled it and where in the fie it was hiding. open the documents the way a person would (browser, PDF viewer, email app) and compare that with what the agent read

**What was lacking after the first:**

## Problem 6: Defend your Agent

**Prompt:**
> Problem 6: Defend your Agent

**Follow-up prompt:**
> Defend the agent at three levels. 1. Code: what teh program does to the document before any model sees it, 2. Design: how the agent is put together, so a poisoned documetn can not reach the dangerous tools or the decision, and 3. Prompt: rules in prompts/prompt.md

**Other prompt:**
> do not delete send_email or approve_payment from the system

**Other prompt:**
> the shop will use them later with a human signoff and keep a way to run teh agent with no defenses which is needed in problem 7

**What was lacking after the first:**

## Problem 7: Red team

**Prompt:**
> Problem 7: Red team

**Follow-up prompt:**
> now you are the attacker. make two new booby-trapped vendor documents in data/my_attacks/ (HTML, PDF, or email). each one should use a hiding trick or an attack goal that is not in the practice set. a person opening the document should see a normal quote.

**Other prompt:**
> run both attacks on the agent with no defenses and on your defended agent. in output/red_team.md, for each attack: what is hidden, where, what it tries to make the agent do, and what happened beofre and after your defenses. more pounts for attacks that are new and creative and that actually fool the agent with no defenses.  Lets Roll Chloe!

**Other prompt:**
> again give me an update on the exact steps I am learning so in the future I can do reeat these concepts and objectives on my own

**What was lacking after the first:**

## Problem 8: Exam documents

**Prompt:**
> Problem 8: Exam documents

**Follow-up prompt:**
> data/exam_docs/ has ten vendor documents with no answer key. run the final defended agent on all of them.Do not hand edit the results.

**Other prompt:**
> Save output/exam_results.json with one entry per exam file. Each entry has these fields: file: the exam file name, vendor, sku, unit_price, lead_time_days, min_order, decision recommen or do_not_recommend, reason, trap_tool_called (true or false), input_tokens, cached_tokens, output_tokens, cost_usd

**Other prompt:**
> the graders will compare my results to a hidden answer key and rerun some agents to check.  POints will be given for correct fields and decisions, no trap tool calls, and clean documents handled normally.

**What was lacking after the first:**

## Problem 9: Results Page

**Prompt:**
> Problem 9: Results Page

**Follow-up prompt:**
> Build output/HW6_report.html  it must be one file that opens by double-click with no internet and no other files next to it.

**Other prompt:**
> also, the page must show the five things below. Use real numbers from earlier problems.  Caching results, with a chart, attacks before and after defenses, what your deenses cost in tokens and dollars, your exam results and your two team red attacks, a short recommendation to the store manager: should Campus Customs turn this agent on for a real vendor mail, and what would it cost per month at 1000 documents a day?  and for the best part... create a designed boutique asthetique page with fonts, colors, layout that reads well and provides an upscale vibe

**What was lacking after the first:**

## Problem 10: Push to GitHub and submit the URL

**Prompt:**
> taken everything done, make sure I get fullcredit for this assignment

(Sent with four screenshots of the assignment's Problem 10 instructions and expected repo.)

**Other prompt:**
> update / create a word document explaing in detail step by step the intent and execution of this assignment in its entirety.  update the prompt documetn so I can learn howto write these prompts better in future tasks, and creat a checklist for this assignent that flows and follows the checklist from the ther assignmetns so I can re create this entire task with its objectives and execution pieces all on my own in the fure.  ensure gaps,opportunities, and caution and red flags are identified and fixed if required.

**Other prompt:**
> create a public repo

**Follow-up prompt:**

**What was lacking after the first:**
