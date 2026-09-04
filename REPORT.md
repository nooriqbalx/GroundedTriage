# GroundedTriage: Evidence-Dependent Hallucination in LLM-Based Malware Triage

**Noor-ul-ain Iqbal**
Beaconhouse National University, Lahore
iamnooriqbal@gmail.com

---

## Abstract

Large language models are increasingly proposed as assistants for security analysts, promising to accelerate malware triage by reasoning over technical evidence that would otherwise require manual correlation across static and dynamic analysis tools. This raises a basic but underexamined question: does giving a model more evidence make its judgments more reliable, or merely more confidently stated? I investigate this by evaluating three open-weight LLMs (GPT-OSS-20B, GPT-OSS-120B, Qwen3.6-27B) on malware family classification across 56 real-world samples spanning seven families, systematically varying the evidence provided from sparse static file metadata to full dynamic behavioral analysis. Across 504 total model responses, I find that classification accuracy remains statistically indistinguishable across this progression (2.4% under static evidence, 4.8% under dynamic, 4.2% under combined evidence; chi-square test not significant, p = 0.49), while abstention, a model's willingness to decline rather than guess, collapses sharply as evidence richness increases (59.5% to 12.5%, p < 0.0001, Cramer's V = 0.515). To understand this gap between confidence and correctness, I conducted a stratified human review of 45 model justifications, evaluating whether each cited claim actually traces back to evidence present in the input. Grounding quality collapses in step with abstention: from 73.3% of justifications being fully evidence-grounded under static conditions to just 6.7% under combined evidence (Fisher's exact test, p < 0.001). I find no instances of evidence fabricated from nothing. Instead, the dominant failure mode is models weaving real, present evidence into an unsupported narrative, a family attribution the evidence does not actually establish. These results suggest that, in this setting, richer context does not improve LLM reasoning. It expands the surface area for constructing plausible-sounding but ungrounded conclusions. I discuss implications for LLM-assisted security tooling and release the full dataset, evaluation pipeline, and a live interactive demonstration.

**Keywords:** LLM hallucination, malware triage, evidence grounding, model calibration, security automation, human evaluation

---

## 1. Introduction

LLM-generated malware is projected to account for roughly half of detected threats by 2025, up from approximately 2% in 2021 [1], a shift that has driven rapid, parallel interest in using LLMs defensively, including as assistants for the human analysts responsible for triaging the resulting volume of suspicious files. Security operations centers face a persistent bottleneck under this volume: the number of files flagged for review routinely exceeds the capacity of human analysts to triage them individually. A typical malware triage workflow requires an analyst to synthesize evidence from multiple disjoint sources: static file characteristics such as headers, imports, and code signing certificates; dynamic sandbox behavior such as process activity, network connections, and registry modifications; and increasingly, structured threat intelligence mappings such as MITRE ATT&CK. This synthesis must be combined into a single family classification and confidence judgment. This synthesis step is exactly the kind of multi-source reasoning task large language models are now being proposed to accelerate, either as autonomous triage agents or as copilots that draft an initial assessment for human review.

This proposition rests on an assumption that is rarely tested directly: that giving a model more evidence produces a more reliable judgment. The assumption is intuitive. A human analyst presented with both static and dynamic evidence is generally better equipped than one working from static evidence alone. Whether the same holds for an LLM is a separate empirical question, and one with direct practical stakes. If richer evidence inputs do not proportionally improve model reliability, then LLM-assisted triage tooling built on the premise that more context is strictly better may be systematically overconfident in exactly the cases, rich, detailed sandbox reports, where an analyst is most likely to defer to the model's judgment.

A closely related concern is the reliability of a model's stated justification as a signal of its actual reasoning quality. An LLM that outputs a wrong classification alongside a confident, evidence-citing explanation is a more dangerous failure mode for a human-in-the-loop workflow than one that visibly hedges. A fluent, specific-sounding justification is difficult for a time-pressured analyst to distinguish from a genuinely well-reasoned one without independently re-deriving the conclusion, at which point the model has provided no time savings at all. Evaluating whether a model's justification is grounded, meaning whether its cited claims actually trace back to the evidence shown, is therefore a necessary complement to evaluating raw classification accuracy.

### 1.1 Research Questions

This work investigates two connected questions.

First, does classification accuracy improve as evidence richness increases, moving from static file metadata alone, to dynamic behavioral evidence alone, to both combined?

Second, does the grounding quality of model justifications track classification accuracy, or can models become more confident, meaning less likely to abstain, without becoming more correct or more evidence-grounded?

### 1.2 Contributions

This paper makes three contributions.

I construct and release a dataset of 56 real-world malware samples across seven families, each independently verified to contain non-empty, genuinely usable static and dynamic behavioral evidence. This filters out the substantial fraction of nominally analyzed samples whose sandbox reports are empty, errored, or architecturally incompatible with the analysis environment (Section 3.2).

I evaluate three open-weight LLMs across three evidence conditions, static, dynamic, and combined, reporting both classification accuracy and abstention behavior across all 504 resulting responses, with statistical testing of the observed patterns (Section 4).

I conduct a stratified human evaluation of model justification grounding, applying a strict rule under which an unsupported family-specific attribution disqualifies an otherwise evidence-accurate justification from being counted as grounded, and report the resulting grounding rates by model and evidence condition (Section 5).

I release the full dataset, evidence-construction pipeline, evaluation code, and a live interactive demonstration of the triage system at github.com/nooriqbalx/GroundedTriage.

---

## 2. Related Work

### 2.1 LLM-Assisted Malware Analysis and Triage

A growing body of work explores using LLMs to accelerate malware analysis workflows. Apvrille and Nakov [2] evaluated AI-assisted analysis of Linux and IoT malware using Radare2's LLM extension, finding that analysis quality matched or exceeded unassisted analysis when a human analyst remained in the loop, but noting that gains in speed were partially offset by time spent identifying the model's hallucinations, exaggerations, and omissions. This is a tension the present paper investigates systematically rather than anecdotally. Saul et al. [3] introduced Trident, a system combining a decision tree over static features with LLM-derived behavioral detection rules and direct LLM analysis of sandbox reports, and found the resulting combination more robust to concept drift than static-feature methods alone, though their evaluation centers on detection performance rather than the reliability of the model's stated reasoning. Sun et al. [4] applied LLMs to fine-grained localization of malicious payloads within Android applications, demonstrating the breadth of tasks to which LLMs are now being applied in this domain.

Most closely related to the present work is MalEval [5], a diagnostic framework for fine-grained Android malware behavior auditing that decomposes the auditing process into function prioritization, evidence attribution, behavior synthesis, and sample discrimination stages, evaluated across seven LLMs. That work finds that decisive-evidence-missing and attack-chain-composition failures together account for the majority of auditing errors, and separately reports that stronger models improve behavior-level synthesis more consistently than precise evidence grounding, a finding broadly consistent with the model-size effects observed here (Section 4.3). MalEval does not, however, isolate evidence type, static versus dynamic, as an experimental variable, nor does it report a human-verified grounding rate stratified by evidence condition, and its evaluation is scoped to Android applications rather than the general-purpose Windows malware evaluated here. Ryan et al. [6] evaluated 13 LLMs on malicious Python package detection, finding a substantial "granularity gap": near-perfect performance (F1 approximately 0.99) on binary malicious-package detection degrading by approximately 41% when the task shifted to identifying specific malicious indicators, a pattern of coarse-task success alongside fine-grained justification failure consistent with what this paper finds in the malware triage setting. The present work differs from all three in treating evidence richness itself, rather than task type or model choice, as the primary experimental manipulation, holding task and models fixed.

### 2.2 Hallucination, Calibration, and Abstention in LLMs

Separately from the security-specific literature, a substantial body of work studies whether LLMs' expressed confidence tracks their actual correctness. Kadavath et al. [7] showed that LLM self-assessed confidence correlates with accuracy to a meaningful degree, but that overconfidence increases on harder tasks. Lin et al. [8] demonstrated that models can learn to express calibrated confidence in natural language, while cautioning that surface-level confidence expressions do not necessarily reflect a model's true internal uncertainty absent explicit calibration training. More recent work frames abstention explicitly as a trainable, evaluable capability rather than an incidental behavior. Zong et al. [9] proposed I-CALM, a prompt-based framework that elicits verbal confidence and explicitly rewards abstention on error-prone cases, finding this reduces false-answer rates by shifting uncertain cases toward abstention rather than by improving forced-answer accuracy, a distinction the present paper's own accuracy-versus-abstention results echo directly. Karge [10] formalizes a related idea at the level of collective decision-making, showing that agents who calibrate confidence and selectively abstain can approach classical jury-theorem guarantees even though no individual agent's underlying competence improves, framing improved group reliability as an artifact of selective participation rather than of better individual reasoning.

This literature largely evaluates abstention and calibration in general-domain factual question-answering settings with a single, fixed context. The present work extends this line of inquiry to a setting where the context itself is systematically varied in richness and type, allowing me to ask not just whether a model's confidence tracks its correctness, but whether that relationship holds, or breaks down, as the evidence available to the model changes.

### 2.3 Positioning of This Work

No prior work I am aware of jointly satisfies three conditions: varying evidence type, static versus dynamic versus combined, as a controlled experimental condition in an LLM-based malware triage task; reporting both classification accuracy and abstention behavior across that manipulation; and pairing this with a stratified, rule-governed human evaluation of justification grounding rather than an automated or purely accuracy-based proxy. This combination is what allows me to distinguish two outcomes that are conflated in a purely accuracy-based evaluation: a model becoming more accurate with more evidence, versus a model becoming more confident without becoming more accurate. The latter is the pattern found throughout this dataset.

---

## 3. Methodology

### 3.1 Dataset Construction

I constructed a dataset of malware samples with verified static and dynamic behavioral evidence, sourced from two independent public platforms to separate ground truth labeling from evidence collection and avoid circularity between the two.

Sample metadata and family ground truth were obtained from MalwareBazaar [11], a public malware sample repository operated by abuse.ch that aggregates family classifications as a consensus across multiple detection engines and community contributors. I queried MalwareBazaar's API by family signature to retrieve historical samples for a target list of malware families, rather than relying on the platform's most-recent-submissions feed, since recently submitted samples are substantially less likely to have completed behavioral analysis on a third-party sandbox at the time of collection.

Static and dynamic behavioral evidence for each sample was obtained from Hybrid Analysis [12], a public sandbox platform. For each candidate sample hash, I queried Hybrid Analysis's hash-search endpoint to determine whether a completed analysis report existed, and if so, retrieved the full report through its detailed report endpoint.

### 3.2 Evidence Verification and Filtering

An early version of the dataset construction pipeline treated the mere existence of a Hybrid Analysis report as sufficient evidence that a sample was usable. This proved to be an incorrect assumption. Manual inspection of a sample's full report revealed that many reports with a completed search result nonetheless contained a `state` field of `ERROR`, with zero recorded processes, network connections, and behavioral signatures. Systematically auditing an initial 60-sample batch under this criterion found that 11 of 60 samples (18.3%) had reports that existed but contained no usable evidence. All 8 Mirai-family samples in that batch failed for the same underlying reason: Mirai targets embedded and IoT architectures (observed submission types included Motorola m68k and ARM binaries), which cannot execute in the Windows-based sandbox environment used by Hybrid Analysis, producing a `FILE_TYPE_BAD_ERROR` on every submission.

Following this finding, the dataset construction pipeline was revised to require both a successful analysis state (`state == "SUCCESS"`) and at least one non-zero evidence field among process count, network connection count, and behavioral signature count, before a sample was accepted into the dataset. The Mirai family was dropped from the target family list entirely, since its incompatibility with the analysis environment is systematic rather than incidental, and including a family with a near-zero yield rate would have both wasted API quota and introduced a confound between family identity and evidence availability.

Under the revised criterion, the final dataset comprises 56 samples across seven families, capped at 8 samples per family to prevent any single family from dominating the evaluation: Vidar, njRAT, WannaCry, NanoCore, CoinMiner, ConnectWise, and NetSupport. This spans infostealers, remote access trojans, ransomware, cryptocurrency miners, and legitimate remote-administration tools repurposed for malicious use, providing meaningful diversity in both malware category and evidence profile.

### 3.3 Evidence Construction Pipeline

For each of the 56 verified samples, I constructed three evidence bundles from the same underlying Hybrid Analysis report: a static-only bundle, a dynamic-only bundle, and a combined bundle concatenating both.

The static evidence bundle includes file type and architecture, the submitted filename, file size, import hash, entry point and containing section, image base address, subsystem, PE image and DLL characteristics flags, and any code signing certificate metadata present in the report. These fields are derivable from the file itself without execution.

The dynamic evidence bundle includes the list of observed processes with their names, file paths, and command lines; contacted domains and IP addresses; the total recorded network connection count; behavioral signatures with their category, severity, and human-readable description; and MITRE ATT&CK [13] technique identifiers with their associated tactic and technique names, deduplicated across the report.

Critically, several fields present in the raw Hybrid Analysis report were deliberately excluded from both bundles: the platform's own multi-engine verdict, its `vx_family` field (a heuristic family-name-adjacent tag), antivirus detection counts, and pre-assigned classification tags. Including any of these fields would have allowed a model to read the answer directly from the input rather than reason over genuine evidence, undermining the validity of the evaluation.

### 3.4 Models

I evaluated three open-weight instruction-tuned language models, all accessed through the Groq inference API [14] at zero cost under its free tier: `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, and `qwen/qwen3.6-27b`. This selection spans roughly a six-fold range in parameter count and includes models from two distinct model families, allowing observed effects to be checked for consistency across both scale and architecture rather than being an artifact of a single model family.

The original model selection targeted a different set of three models, chosen to match those used in a related prior evaluation for methodological continuity. Two of these three models were deprecated by the inference provider during the course of this project, requiring a substitution to the three models reported here. I note this not as an incidental detail but because it reflects a genuine, undocumented constraint of building on rapidly evolving free-tier LLM infrastructure: model availability at evaluation time cannot be assumed stable even across the timeframe of a single project, and reproducibility of LLM evaluation work is correspondingly more fragile than in domains where model artifacts are fixed and versioned.

### 3.5 Evaluation Protocol

Each of the 56 samples was evaluated under each of the three evidence conditions (static, dynamic, combined) by each of the three models, yielding 56 x 3 x 3 = 504 total model responses. Each model was prompted with a fixed instruction template requesting a family classification, a confidence level (low, medium, or high), and a justification citing specific evidence, with an explicit instruction not to invent evidence not present in the input and to state explicitly when available evidence was insufficient for a confident classification. Temperature was fixed at 0.2 across all calls to reduce response variance while still allowing natural language variation. Because one model (Qwen3.6-27B) emits an internal reasoning trace before its final answer, the maximum output token budget was set high enough (4096 tokens) to allow this reasoning to complete without truncating the final structured answer, and responses were post-processed to extract only the content following the reasoning trace before parsing.

Each response was parsed to extract the stated family, confidence level, and justification. A response was scored as **correct** if the true family name appeared, case-insensitively, within the model's stated family field; this is a deliberately conservative matching rule that does not attempt to resolve family aliases or informal naming variants, since a stricter, more literal standard is more defensible for a first-pass accuracy measure than a rule that could be seen as generous to the models under evaluation. A response was scored as **abstained** if its stated family field contained an explicit marker of non-commitment (for example, "unknown," "insufficient evidence," or "unable to determine"), distinguishing an honest refusal to guess from an incorrect guess.

### 3.6 Human Grounding Evaluation Protocol

Classification accuracy and abstention rate describe what a model concluded, but not whether its stated reasoning for that conclusion was actually supported by the evidence it was given. To evaluate this directly, I conducted a manual, human-reviewed grounding assessment on a stratified sample of model responses.

Five responses were randomly sampled (fixed random seed, for reproducibility) from each of the nine model-by-condition cells (3 models x 3 conditions), yielding 45 responses for review, representing 8.9% of the full 504-response dataset. This proportion is comparable to, and somewhat larger than, the 2.4% human-validation sample used for automated-judge reliability checking in related prior work on multilingual LLM safety evaluation, which I take as a reasonable precedent for the scale of manual review appropriate to a project of this scope.

Each of the 45 sampled responses was reviewed by reading the underlying evidence bundle shown to the model alongside its full justification text, and assigning one of three verdicts: **GROUNDED**, meaning every specific claim in the justification traces back to something genuinely present in the evidence; **FABRICATED**, meaning the justification asserts evidence that is not actually present in the input; or **PARTIAL**, meaning the justification is a mixture of accurate evidence description and unsupported claims. A deliberately strict rule was applied throughout this review: a justification that accurately describes real evidence but then attributes that evidence to a specific named family without the evidence itself establishing that attribution (for example, describing real behavioral signatures accurately, then asserting that this combination is "characteristic of" or "a known pattern for" a specific family without that claim being derivable from the evidence shown) was scored as PARTIAL rather than GROUNDED, even when the underlying evidence description was itself accurate and even when the model's final classification happened to be correct. This rule was applied uniformly regardless of whether the model's ultimate classification was scored as correct or incorrect under the accuracy metric in Section 3.5, to avoid inadvertently grading grounding more leniently on responses that happened to reach the right answer.

All 45 reviews were conducted by the author. I note this as a limitation in Section 7 rather than eliding it: a single-reviewer evaluation cannot report inter-annotator agreement, and grounding judgments, particularly on the PARTIAL category, involve an element of subjective interpretation.

---

## 4. Results

### 4.1 Overall Model Performance

Table 1 reports classification accuracy and abstention rate for each model, pooled across all three evidence conditions (N = 168 responses per model).

**Table 1: Overall accuracy and abstention by model (N = 168 per model)**

| Model | Accuracy | Abstention Rate |
|---|---|---|
| GPT-OSS-120B | 10.7% (18/168) | 45.8% (77/168) |
| GPT-OSS-20B | 0.0% (0/168) | 14.3% (24/168) |
| Qwen3.6-27B | 0.6% (1/168) | 21.4% (36/168) |

GPT-OSS-120B is the clear outlier on both metrics: it is both the most accurate model by a substantial margin and the most willing to abstain rather than guess. A chi-square test of accuracy by model confirms this difference is statistically significant (chi-square = 33.58, df = 2, p < 0.0001, Cramer's V = 0.258). Abstention rate also differs significantly by model (chi-square = 46.45, df = 2, p < 0.0001, Cramer's V = 0.304). These two patterns co-occurring in the same model, higher accuracy alongside higher abstention, is consistent with GPT-OSS-120B being better calibrated: it is not simply guessing correctly more often by chance, but appears more able to recognize when available evidence is insufficient for a confident judgment, and to decline accordingly.

### 4.2 Accuracy and Abstention by Evidence Condition

Table 2 reports the same two metrics broken down by evidence condition, pooled across all three models (N = 168 responses per condition).

**Table 2: Accuracy and abstention by evidence condition (N = 168 per condition)**

| Condition | Accuracy | Abstention Rate |
|---|---|---|
| Static | 2.4% (4/168) | 59.5% (100/168) |
| Dynamic | 4.8% (8/168) | 9.5% (16/168) |
| Combined | 4.2% (7/168) | 12.5% (21/168) |

This is the central empirical finding of the paper. Accuracy does not increase monotonically, or in any statistically distinguishable way, across the progression from static to dynamic to combined evidence: a chi-square test of accuracy by condition is not significant (chi-square = 1.42, df = 2, p = 0.49, Cramer's V = 0.053, a negligible effect size). Abstention rate, in sharp contrast, collapses from 59.5% under static evidence to single-digit or low-double-digit rates once dynamic evidence is introduced, a difference that is highly significant with a large effect size (chi-square = 133.54, df = 2, p < 0.0001, Cramer's V = 0.515, the largest effect observed anywhere in this study).

In other words, richer evidence makes these models dramatically more willing to commit to an answer, without making them any more likely to be right when they do.

### 4.3 Model-by-Condition Interaction

Examining accuracy and abstention jointly by model and condition clarifies that the abstention collapse is not driven by a single outlier model. GPT-OSS-120B's abstention rate falls from 92.9% under static evidence to 21.4% under combined evidence; GPT-OSS-20B's falls from 39.3% to 3.6%; Qwen3.6-27B's falls from 46.4% to 12.5%. All three models exhibit the same qualitative pattern, at different absolute levels, which strengthens confidence that this is a property of the evidence-condition manipulation itself rather than an artifact specific to any one model's training or prompting sensitivity.

### 4.4 Statistical Robustness

Table 3 summarizes all chi-square tests of independence conducted on the full 504-response dataset.

**Table 3: Chi-square tests of independence, full dataset (N = 504)**

| Comparison | chi-square | df | p | Cramer's V |
|---|---|---|---|---|
| Accuracy x Condition | 1.42 | 2 | 0.49 | 0.053 |
| Accuracy x Model | 33.58 | 2 | < 0.0001 | 0.258 |
| Abstention x Condition | 133.54 | 2 | < 0.0001 | 0.515 |
| Abstention x Model | 46.45 | 2 | < 0.0001 | 0.304 |

The pattern across these four tests is internally consistent: model identity is a significant predictor of both accuracy and abstention, indicating real differences in model capability and calibration, while evidence condition is a significant predictor of abstention but not of accuracy, indicating that the manipulation changes models' willingness to answer without changing their likelihood of answering correctly.

---

## 5. Justification Grounding Evaluation

### 5.1 Grounding Rate by Evidence Condition

Table 4 reports the human-reviewed grounding verdict distribution by evidence condition, based on the stratified 45-response sample described in Section 3.6.

**Table 4: Grounding verdict by evidence condition (N = 45, 15 per condition)**

| Condition | Grounded | Partial | Fabricated |
|---|---|---|---|
| Static | 73.3% (11/15) | 26.7% (4/15) | 0.0% (0/15) |
| Dynamic | 13.3% (2/15) | 86.7% (13/15) | 0.0% (0/15) |
| Combined | 6.7% (1/15) | 93.3% (14/15) | 0.0% (0/15) |

The grounding rate collapses in the same direction, and nearly as sharply, as the abstention rate reported in Section 4.2, falling from 73.3% under static evidence to 6.7% under combined evidence. A chi-square test on this table is significant (chi-square = 18.87, df = 2, p < 0.0001, Cramer's V = 0.648), though the smallest expected cell count in this table falls below 5, meaning the chi-square approximation should be treated with some caution at this sample size. As a robustness check, I additionally computed pairwise Fisher's exact tests, which do not rely on the same large-sample approximation. These confirm the finding: static evidence differs significantly from both dynamic evidence (odds ratio = 17.88, p = 0.0025) and combined evidence (odds ratio = 38.50, p = 0.0005), while dynamic and combined evidence do not differ significantly from each other (odds ratio = 2.15, p = 1.0). This last result is itself informative: it indicates that the grounding collapse occurs specifically once evidence moves beyond sparse static metadata, and that adding further evidence richness beyond that point does not meaningfully change grounding quality one way or the other.

### 5.2 Grounding Rate by Model

**Table 5: Grounding verdict by model (N = 45, 15 per model)**

| Model | Grounded | Partial | Fabricated |
|---|---|---|---|
| GPT-OSS-120B | 53.3% (8/15) | 46.7% (7/15) | 0.0% (0/15) |
| GPT-OSS-20B | 13.3% (2/15) | 86.7% (13/15) | 0.0% (0/15) |
| Qwen3.6-27B | 26.7% (4/15) | 73.3% (11/15) | 0.0% (0/15) |

GPT-OSS-120B again outperforms the other two models on this metric, consistent with its stronger showing on both accuracy and abstention. A chi-square test on this table approaches but does not clear the conventional 0.05 significance threshold (chi-square = 5.81, df = 2, p = 0.055, Cramer's V = 0.359), which given the small sample size is best read as a suggestive rather than conclusive model difference on this specific metric.

### 5.3 The Absence of Fabrication From Nothing

Across all 45 manually reviewed responses, zero were assigned a FABRICATED verdict under the strict definition used here (evidence asserted that is not present in the input at all). This is a substantively important finding in its own right. The dominant failure mode observed throughout this review is not a model inventing evidence that does not exist, but a model accurately describing evidence that does exist and then attaching an unsupported family-specific narrative to it. A representative example, drawn from the live deployed demonstration of this system rather than the formal evaluation set: given evidence including process injection, token impersonation, registry modification, and contact with a Telegram-associated domain, one model correctly cited all of these as observed behaviors, then added that a named family "has been observed using custom domains... and Telegram's infrastructure... for command-and-control," a claim about a specific family's typical infrastructure that is not derivable from the evidence shown, despite every individual evidence item cited in the sentence being real.

This distinction matters practically. A model that fabricates evidence from nothing is comparatively easy to catch, since a reviewer checking a specific claimed indicator against the underlying report will find nothing there. A model that accurately restates real evidence and then appends a plausible but unsupported inference is considerably harder to catch under time pressure, because the surrounding factual claims check out. This is precisely the failure mode most likely to survive casual human review in a real triage workflow.

---

## 6. Discussion

The two central findings of this study, that accuracy remains flat while abstention and grounding both collapse as evidence increases, are not independent observations but two views of the same underlying phenomenon. When evidence is sparse, these models appear to correctly recognize the limits of what can be concluded, and either decline to answer or, when they do answer, ground their reasoning in what is actually present. When evidence becomes richer, in particular once dynamic behavioral evidence is introduced, models shift toward answering more often, but the content of their answers increasingly draws on background knowledge about malware families in general, invoked to explain the observed evidence, rather than on inferences the evidence itself supports. The evidence does not become less informative as it grows richer; if anything, real behavioral evidence such as observed process activity and contacted domains is more diagnostically useful than static file metadata alone. What appears to change is not the informational value of the evidence but the model's apparent threshold for treating pattern-matched, plausible-sounding association as sufficient grounds for a confident, specific claim.

This has a direct implication for the design of LLM-assisted security tooling. Abstention rate, or its inverse, the rate at which a system produces a definite answer, is sometimes treated as a rough proxy for how much a system can be trusted at a given confidence threshold. This study's results caution against that proxy specifically in exactly the scenario where it is most tempting to rely on it: when a system is given the richest, most detailed evidence available. A tool that answers confidently 90% of the time on rich sandbox reports is not obviously safer than one that abstains 60% of the time on sparse metadata, and this study's evidence suggests the opposite relationship may hold. This finding echoes a related conclusion in a prior evaluation of multilingual LLM safety behavior, where explicit refusal was found to be an imperfect proxy for actual safety outcomes, with some refusals still leaking harmful content and some non-refusals remaining safe; the throughline across both projects is that a model's willingness to answer, and its style of answering, is a distinct property from whether that answer is actually well-founded, and neither should be inferred from the other without direct verification.

Practically, this suggests that an LLM-assisted triage system should not treat its own confidence or willingness to answer as a reliability signal on its own terms. A verification step that checks whether a model's stated justification actually cites real, present evidence, of the kind manually performed in Section 5 of this study, appears necessary rather than optional if such a system's outputs are to be trusted without independent re-verification by a human analyst, which would defeat the efficiency purpose of using the tool in the first place. The deployed demonstration accompanying this paper includes an explicit warning to this effect for exactly this reason, but a production system would need this check automated and enforced rather than left as a caveat for the human reader.

---

## 7. Limitations

This study has several limitations that should be considered when interpreting its results.

**Sample size.** The dataset comprises 56 samples across seven families. While this is comparable in scale to the manually verified portion of several related evaluations in this literature, a larger sample would provide tighter statistical estimates, particularly for the per-family accuracy breakdown, where family-level cell counts are small.

**Grounding evaluation scale and reviewer count.** The grounding evaluation in Section 5 covers a stratified 45-response sample, 8.9% of the full dataset, reviewed by a single author. This is a larger proportion than some comparable prior work uses for human-validation subsets, but a single-reviewer evaluation cannot report inter-annotator agreement, and the PARTIAL category in particular involves judgment calls that a second independent reviewer might resolve differently in some individual cases, even under the same stated rule.

**Sandbox environment and generalization.** All behavioral evidence in this dataset originates from a single, Windows-based sandbox platform. This is a hard constraint on which malware families could be included at all; the Mirai family was excluded in its entirety for this reason (Section 3.2). Findings here should not be assumed to generalize to malware targeting non-Windows or embedded architectures, nor to sandboxes with different evasion-detection characteristics than the one used here.

**Model availability and reproducibility.** The final model selection was constrained by, and changed partway through the project in response to, deprecations on the free inference platform used. This is disclosed in Section 3.4 as a methodological note rather than hidden, but it also means that exact reproduction of these specific results at a later date may require substituting different models than those named here, since the ones evaluated may themselves no longer be available.

**Classification matching rule.** Accuracy is scored using case-insensitive substring matching between the model's stated family and the ground-truth label, without resolving known family aliases or informal naming variants. This is a deliberately conservative choice, but it means the reported accuracy figures should be read as a lower bound under a strict standard rather than an attempt to maximize apparent model performance.

**Single-turn, zero-shot evaluation.** All model queries in this study are single-turn and use a fixed zero-shot prompt template. This study does not evaluate whether few-shot examples, iterative self-verification, or explicit chain-of-thought prompting would alter the accuracy-abstention-grounding relationships observed here; these remain open questions for future work.

---

## 8. Conclusion

This study set out to answer a simple question with a real practical stake: does giving a large language model more evidence make it a more reliable malware triage assistant? Across 504 evaluated responses spanning three models, three evidence conditions, and 56 real-world malware samples, the answer found here is no, at least not straightforwardly. Classification accuracy remains flat regardless of how much evidence a model is given. What changes, sharply and consistently across all three models tested, is the model's willingness to commit to a confident answer rather than acknowledge uncertainty, and a human-verified evaluation of 45 model justifications shows that this growing confidence is largely unearned: grounding of model justifications in the actual evidence shown collapses from 73.3% to 6.7% across the same progression from sparse to rich evidence.

The dominant failure mode identified here, real evidence accurately described but woven into an unsupported family-specific narrative, is a genuinely difficult one for a time-pressured human reviewer to catch, since the surrounding facts check out even when the conclusion does not. This suggests that LLM-assisted security tooling built on the assumption that richer context straightforwardly improves reliability should be evaluated directly on this assumption before being trusted in a workflow where a human analyst is expected to defer to the model's stated reasoning.

I release the full dataset, evidence construction pipeline, evaluation code, and a live interactive demonstration incorporating an explicit grounding-skepticism prompt at github.com/nooriqbalx/GroundedTriage, with the goal of making both replication and extension of this evaluation, to additional models, larger sample sizes, or automated grounding-verification mechanisms, straightforward for future work.

---

## Data, Code, and Ethics Statement

This research involved no execution of malware on any system controlled by the author. All dynamic behavioral evidence used in this study was obtained through completed, publicly accessible analysis reports retrieved from Hybrid Analysis, a third-party sandbox platform; at no point did the local research environment execute, store persistently, or otherwise directly handle a live malware sample or binary. All malware sample metadata and family ground-truth labels were sourced from MalwareBazaar, a public malware intelligence repository intended for security research use. Only sample hashes, metadata, and pre-computed analysis reports were retrieved and processed; no executable file content was downloaded, run, or distributed as part of this project. The full dataset released alongside this paper accordingly contains structured evidence text and metadata only, not executable content. All three language models evaluated in this study were accessed through their respective providers' standard API terms of service, at zero financial cost under free-tier access. This project was conducted independently by the author and was not funded, commissioned, or formally supervised by Beaconhouse National University; the university affiliation given reflects the author's academic institution at the time of the work.

---

## References

[1] Ahi, K. and Valizadeh, S. Large Language Models (LLMs) and Generative AI in Cybersecurity and Privacy: A Survey of Dual-Use Risks, AI-Generated Malware, Explainability, and Defensive Strategies. In *Proceedings of the IEEE 6th Silicon Valley Cybersecurity Conference (SVCC)*, San Francisco, CA, USA, 2025. arXiv:2607.06963.

[2] Apvrille, A. and Nakov, D. Malware analysis assisted by AI with R2AI. arXiv:2504.07574, 2025.

[3] Saul, R., Jiang, J., Chia, E., and Wagner, D. Trident: Improving Malware Detection with LLMs and Behavioral Features. arXiv:2605.00297, 2026.

[4] Sun, T., Alecci, M., Pilgun, A., Song, Y., Tang, X., Samhi, J., Bissyande, T.F., and Klein, J. MalLoc: Toward Fine-grained Android Malicious Payload Localization via LLMs. arXiv:2508.17856, 2025.

[5] Zheng, X., Qian, X., He, Y., Yang, S., and Cavallaro, L. Beyond Classification: Evaluating LLMs for Fine-Grained Automatic Malware Behavior Auditing. arXiv:2509.14335, 2025.

[6] Ryan, A., Khalil, I., Al Jahid, A., Erfan, M., Park, S., Rahman, A.A.U., and Rahman, M.R. Mind the Gap: Evaluating LLMs for High-Level Malicious Package Detection vs. Fine-Grained Indicator Identification. arXiv:2602.16304, 2026.

[7] Kadavath, S., Conerly, T., Askell, A., Henighan, T., Drain, D., Perez, E., Schiefer, N., et al. Language Models (Mostly) Know What They Know. arXiv:2207.05221, 2022.

[8] Lin, S., Hilton, J., and Evans, O. Teaching Models to Express Their Uncertainty in Words. arXiv:2205.14334, 2022.

[9] Zong, H., Li, B., Long, Y., Chang, S., Wu, J., and Hadfield, G.K. I-CALM: Incentivizing Confidence-Aware Abstention for LLM Hallucination Mitigation. arXiv:2604.03904, 2026.

[10] Karge, J. Epistemic Filtering and Collective Hallucination: A Jury Theorem for Confidence-Calibrated Agents. arXiv:2602.22413, 2026.

[11] MalwareBazaar. abuse.ch. https://bazaar.abuse.ch/

[12] Hybrid Analysis. CrowdStrike Falcon Sandbox. https://www.hybrid-analysis.com/

[13] MITRE ATT&CK. https://attack.mitre.org/

[14] Groq API. https://groq.com/