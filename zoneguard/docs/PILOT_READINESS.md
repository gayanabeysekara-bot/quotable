# Pilot Readiness Checklist

Tick every item before monitoring a real site. Items in **bold** are blockers.

## Governance
- [ ] **Legal review of COMPLIANCE_CHECKLIST_AU.md items marked ⚖ for this customer and state**
- [ ] **Privacy Impact Assessment completed and signed off by the customer**
- [ ] **Customer has given written approval; for schools, sector/department approval obtained**
- [ ] Workplace surveillance notices issued (e.g. 14 days in NSW) and signage installed
- [ ] Surveillance-notice confirmation recorded in Settings → Privacy
- [ ] Data processing agreement signed (roles, sub-processors, breach notice, deletion on exit)
- [ ] Named incident reviewers and out-of-hours escalation contacts agreed (people, not the system, decide)

## Configuration
- [ ] Sites created with correct time zones
- [ ] Cameras use dedicated read-only accounts; credentials entered via dashboard only
- [ ] Privacy masks cover toilets/change rooms/treatment areas/neighbouring property, verified on snapshots
- [ ] Zones and approved-access periods reviewed with the site manager
- [ ] Rules reviewed: severities, schedules, suppression windows, recipients
- [ ] Weapon / face-covering modules remain **disabled** unless a documented, validated model and customer approval exist
- [ ] Retention periods set to the customer's records schedule (raw video short)

## Security
- [ ] **HTTPS everywhere; `ZG_ENVIRONMENT=production`, `ZG_COOKIE_SECURE=true`**
- [ ] **Encryption keys in a secret manager; backups encrypted**
- [ ] MFA enabled for every org admin
- [ ] Edge agent on a segmented network; outbound 443 only
- [ ] Penetration test (or at minimum an external security review) completed
- [ ] Log monitoring and alerting on failed notifications / stale edge agents

## Validation
- [ ] **Staged, consented footage recorded at the actual site for every scenario in evaluation/README.md**
- [ ] **Ground-truth annotations created and `python -m evaluation.run` executed; reports stored**
- [ ] Results reviewed with the customer, including false alerts per camera per day and failure cases (poor lighting, occlusion)
- [ ] Alert delivery latency measured end-to-end (Evaluation page)
- [ ] Camera reconnect behaviour checked by power-cycling a camera and dropping the uplink
- [ ] Documented limitations communicated to all reviewers (detections are observations, not conclusions)

## Run-time
- [ ] Two-week shadow period: incidents reviewed but no operational reliance
- [ ] Weekly review of dismissed incidents (false-positive reasons) and rule tuning
- [ ] Exit/rollback plan (disable rules, revoke edge token, delete data per contract)
