# Australian Privacy & Surveillance Compliance Checklist (pilot)

> **This is a working checklist, not legal advice.** ZoneGuard AI has **not** been assessed for legal
> compliance. Obligations depend on the customer, the state/territory and the specific site. Items marked
> **⚖ Legal review** must be confirmed by a qualified Australian privacy / employment / education lawyer
> before any pilot that involves real people other than consenting staged participants.

Legend: ✅ product capability exists · 🟡 partial / customer process needed · ⚖ legal review required

## 1. Privacy Act 1988 (Cth) & Australian Privacy Principles (APPs)

| # | Item | Status | Notes |
|---|---|---|---|
| 1.1 | Determine whether each customer (and ZoneGuard as service provider) is an APP entity (e.g. small-business exemption, state public-sector schools/health bodies covered by state law instead) | ⚖ | Public schools and public health clinics are generally under **state/territory** privacy law, not the APPs. |
| 1.2 | Is CCTV footage / event metadata "personal information"? Is any of it "sensitive information" (e.g. biometric)? | ⚖ | ZoneGuard does **not** create biometric templates or identify people; footage of identifiable people is still personal information. |
| 1.3 | APP 1 – privacy policy describing AI-assisted CCTV analysis | 🟡 | Customer and ZoneGuard need published policies. Org stores a privacy contact. |
| 1.4 | APP 3 – collection is reasonably necessary; data minimisation | ✅🟡 | Metadata-only sync, privacy masks, opt-in modules, short raw-video retention. Customer must justify zones/cameras. |
| 1.5 | APP 5 – notification of collection (signage, notices) | 🟡 | Surveillance-notice confirmation recorded per org; signage is a customer obligation. |
| 1.6 | APP 6 – use/disclosure limited to purpose; no secondary use (e.g. no model training on customer footage) | ✅⚖ | No code path sends footage to third parties or uses it for training. Contract terms needed. |
| 1.7 | APP 8 – cross-border disclosure (cloud hosting region, sub-processors, email provider) | ⚖ | Host the cloud in an Australian region; list sub-processors (SMTP provider). |
| 1.8 | APP 11 – security of personal information; destruction when no longer needed | ✅🟡 | See SECURITY_PRIVACY.md; retention sweeps. Independent pen test not yet done. |
| 1.9 | APP 12/13 – access & correction requests (incl. footage requests) | 🟡 | Exports exist (CSV/JSON metadata); a formal request workflow is not built. |
| 1.10 | Notifiable Data Breaches scheme – breach response plan | 🟡 | Audit logs support investigation; written NDB response plan required. |
| 1.11 | Privacy Impact Assessment (PIA) before deployment | ⚖ | Strongly recommended (OAIC guidance) — mandatory for many public-sector bodies. |
| 1.12 | Automated decision-making transparency (recent Privacy Act amendments) | ✅⚖ | No automated decisions with legal/significant effects: humans review every incident. Confirm disclosure duties. |

## 2. Workplace surveillance (state/territory)

| # | Item | Status | Notes |
|---|---|---|---|
| 2.1 | NSW *Workplace Surveillance Act 2005*: written notice to employees ≥14 days before camera surveillance; cameras clearly visible; signs at entrances; no surveillance in change rooms/toilets/showers | 🟡⚖ | Privacy masks support exclusion areas; the notice process is the employer's. |
| 2.2 | ACT *Workplace Privacy Act 2011*: notice and consultation requirements | ⚖ | |
| 2.3 | VIC *Surveillance Devices Act 1999*: optical surveillance of private activities; *Surveillance Devices (Workplace Privacy) Act 2006* bans surveillance in toilets, change rooms, lactation rooms | 🟡⚖ | Masks/zone placement must respect prohibitions. |
| 2.4 | Other states/territories (QLD, WA, SA, TAS, NT) surveillance devices legislation | ⚖ | Requirements differ (e.g. audio is not captured by ZoneGuard). |
| 2.5 | Enterprise agreements / union consultation obligations | ⚖ | |
| 2.6 | Use of surveillance for disciplinary purposes — policy and procedural fairness | ⚖ | Product language deliberately avoids conclusions about individuals. |

## 3. Schools

| # | Item | Status | Notes |
|---|---|---|---|
| 3.1 | Department / sector policy approval (government, Catholic, independent) | ⚖ | Many departments have CCTV policies requiring approval. |
| 3.2 | Children's privacy; parental/community notification | ⚖ | |
| 3.3 | Child-safe standards; who may view footage | 🟡 | RBAC (admin / site manager / reviewer / auditor) + audit trail. |
| 3.4 | State records legislation – retention of CCTV and incident records | ⚖ | Retention periods are configurable; set according to the applicable disposal schedule. |
| 3.5 | **Do not use real school CCTV footage for testing without explicit written approval** | ✅ | Upload attestation; evaluation guidance uses staged, consented footage only. |

## 4. Medical clinics

| # | Item | Status | Notes |
|---|---|---|---|
| 4.1 | Health records legislation (e.g. NSW HRIP Act, VIC Health Records Act); patient privacy in waiting/treatment areas | ⚖ | Never place zones or cameras over treatment areas; use masks. |
| 4.2 | Medication storage monitoring — complement, not replace, controlled-drug register obligations | 🟡 | |

## 5. AI-specific

| # | Item | Status | Notes |
|---|---|---|---|
| 5.1 | No facial recognition / biometric identification | ✅ | By design. |
| 5.2 | No demographic inference | ✅ | By design. |
| 5.3 | Weapon detection is experimental; not represented as validated | ✅ | UI, API and emails label outputs as possible / simulated. |
| 5.4 | Face covering is a neutral observation; no escalation on covering alone | ✅ | Enforced severity cap. |
| 5.5 | Accuracy claims — none made without measured evaluation on representative staged footage | ✅ | Evaluation framework; no numbers published. |
| 5.6 | Bias / disparate-impact testing across lighting, clothing, mobility aids, body types | 🟡⚖ | Include in the staged evaluation plan (evaluation/README.md). |
| 5.7 | Voluntary AI Safety Standard / Australian AI Ethics Principles alignment statement | 🟡 | |
| 5.8 | Australian Consumer Law – no misleading claims about detection capability | ⚖ | Marketing review required. |

## 6. Contracts & governance

| # | Item | Status |
|---|---|---|
| 6.1 | Customer agreement / data processing terms (roles, sub-processors, breach notice, deletion on exit) | ⚖ |
| 6.2 | Model and dependency licence review (see LICENSING.md) | 🟡⚖ |
| 6.3 | Security assessment / penetration test before production | ⚖ |
| 6.4 | Incident response and escalation procedures documented per customer (who reviews Critical Review alerts, out-of-hours contacts) | 🟡 |
