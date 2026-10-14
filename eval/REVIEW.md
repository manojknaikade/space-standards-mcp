# Evaluation set — review sheet

Generated from `questions.yaml` by `make_review.py`. Edit the YAML, not this file.

57 questions · status: pending: 16, ok: 41, fix: 0

## fs-001 · numeric · review: ok

**Q:** Under NASA-STD-5001B, what are the minimum design and test factors for a metallic structure verified with the prototype approach?

**Answer:** Table 1: ultimate design factor 1.4, yield design factor 1.0 (structure must still be assessed to prevent detrimental yielding in service, acceptance or proof testing), qualification test factor 1.4. Proof test factor is not applicable, except 1.05 for propellant tanks and SRM cases.

**Must contain:** ultimate design factor 1.4; yield design factor 1.0, with assessment against detrimental yielding; qualification test factor 1.4; proof factor 1.05 only for propellant tanks and SRM cases

**Sources:** `NASA-STD-5001B|FSR 24`

## fs-002 · numeric · review: ok

**Q:** For a metallic payload-fairing structure qualified with a protoflight approach under NASA-STD-5001B, what yield design factor and test factor apply, and why is the yield factor higher than for prototype?

**Answer:** Table 1 protoflight row: yield design factor 1.25, ultimate design factor 1.4, qualification (protoflight) test factor 1.2. The flight article itself is tested above limit load, so the higher yield factor protects it from detrimental yielding during the test (FSR 14 requires design factors that prevent this).

**Must contain:** yield design factor 1.25; test factor 1.2 (ultimate stays 1.4); higher yield factor protects the flight article from yielding during the protoflight test

**Sources:** `NASA-STD-5001B|FSR 24`, `NASA-STD-5001B|FSR 14`

> Note: The 'why' is explanatory guidance text in 4.1.1, plus FSR 14.

## fs-003 · numeric · review: ok

**Q:** What ultimate design factor does NASA-STD-5001B require at a discontinuity area (e.g. a bolted joint or insert) of a composite structure verified by prototype test, and can it be reduced?

**Answer:** Table 2: 2.0 on concentrated stresses at discontinuity areas, with qualification test factor 1.4 and proof factor 1.05 for prototype. For non-safety-critical applications the 2.0 may be reduced to 1.4 for prototype (1.5 for protoflight).

**Must contain:** 2.0 applied to concentrated stresses at discontinuities; may drop to 1.4 (prototype) / 1.5 (protoflight) if not safety-critical

**Sources:** `NASA-STD-5001B|FSR 29`

## fs-004 · numeric · review: ok

**Q:** Under NASA-STD-5001B, which design and test factors apply to uniform (non-discontinuity) composite structure verified with the protoflight approach, and does each flight article need a proof test?

**Answer:** Table 2 protoflight, uniform material: ultimate design factor 1.5, protoflight test factor 1.2, proof test factor 1.2. Each composite/bonded flight article is proof tested unless the alternate-approach provisions of section 4.6 are met.

**Must contain:** ultimate 1.5; test factor 1.2, proof factor 1.2; every flight article proof tested unless section 4.6 alternate approach applies

**Sources:** `NASA-STD-5001B|FSR 29`

> Note: Proof-test-every-article statement is guidance text under 4.2.3.

## fs-005 · classification · review: ok

**Q:** A fairing uses aluminium honeycomb core with aluminium face sheets. Does NASA-STD-5001B treat it as composite/bonded or metallic structure for factors of safety?

**Answer:** Metallic honeycomb (face sheets and core) is considered metallic structure, so Table 1 (metallic) factors apply rather than Table 2. Note that the bonds still make it a bonded construction in other respects (e.g. fracture control under ECSS-E-ST-32-01 clause 8.4).

**Must contain:** metallic honeycomb counts as metallic structure; Table 1 factors, not Table 2

**Sources:** `NASA-STD-5001B|FSR 29`

> Note: Statement is guidance text directly under FSR 29, not a numbered requirement. The ECSS remark is Claude's addition — please confirm or delete.

## fs-006 · lookup · review: ok

**Q:** What does NASA-STD-5001B require for buckling of thin-walled shell structures such as an interstage or fairing cylinder?

**Answer:** Design loads for buckling are ultimate loads (FSR 53). Evaluation covers general and local/panel instability, crippling and creep (FSR 55). Analyses of thin-walled shells must account for differences between idealised and real geometry and boundary conditions (FSR 56); guidance points to knockdown factors in NASA-SP-8007 and warns that the 0.65 composite-shell KDF may be unconservative (NESC TB 16-01).

**Must contain:** buckling designed to ultimate loads; general, local/panel instability, crippling, creep; account for imperfections/boundary conditions (knockdown factors)

**Sources:** `NASA-STD-5001B|FSR 53`, `NASA-STD-5001B|FSR 55`, `NASA-STD-5001B|FSR 56`

## fs-007 · lookup · review: ok

**Q:** Can a metallic structure be qualified by analysis only ("no-test") under NASA-STD-5001B, and what is needed?

**Answer:** Only metallic structures may use the no-test option. Analysis must come with an acceptable engineering rationale (FSR 15), and project-specific criteria and rationale must be approved by the delegated Technical Authority (FSR 16). Guidance: higher factors alone do not justify no-test; typical justifications are simple determinate load paths, close similarity to a test-verified structure, or tested critical elements.

**Must contain:** metallic only; engineering rationale + Technical Authority approval of project criteria; higher factors alone are not sufficient justification

**Sources:** `NASA-STD-5001B|FSR 15`, `NASA-STD-5001B|FSR 16`

## fs-008 · classification · review: ok

**Q:** Under ECSS-E-ST-32-01C, can an expendable launcher (unmanned, single mission) apply a reduced fracture control programme, and which items must then be identified as PFCI?

**Answer:** Yes — unmanned, single-mission space vehicles, their payloads and GSE may use the reduced fracture control programme of clause 11 (5.1e). PFCI identification may then be limited to: pressurized systems; rotating machinery; fasteners in safe-life applications; welded, forged or cast items above 25 % of UTS at limit stress; non-metallic structural items; and metallic safe-life items above 50 % of yield at limit stress (11.2.2.1a). With customer approval the last category can be narrowed to single-point-of-failure tension items such as lugs, isostatic mounts, struts and pins.

**Must contain:** RFCP allowed for unmanned single-mission vehicles (5.1e); six PFCI categories incl. 25 % UTS (welded/forged/cast) and 50 % yield (metallic safe life); customer can narrow metallic category to single-load-path tension items

**Sources:** `ECSS-E-ST-32-01C|5.1e`, `ECSS-E-ST-32-01C|11.2.2.1a`

> Note: Both are permissions ('may'), not mandatory requirements.

## fs-009 · numeric · review: ok

**Q:** For a metallic safe-life item under ECSS-E-ST-32-01C, what life factor and initial crack-size detectability apply?

**Answer:** The worst crack must not grow to the point where minimum performance is lost using a design life factor of at least 4 (6.3.2c); the load spectrum is applied at least four times in sequence in the crack growth analysis (7.2.8c). Unless otherwise specified, the NDT method used must find the assumed initial crack with at least 90 % probability at 95 % confidence (6.3.2b).

**Must contain:** life factor 4; spectrum applied 4 times in sequence; initial crack detectable at 90 % probability / 95 % confidence

**Sources:** `ECSS-E-ST-32-01C|6.3.2b`, `ECSS-E-ST-32-01C|6.3.2c`, `ECSS-E-ST-32-01C|7.2.8c`

## fs-010 · numeric · review: ok

**Q:** What load enhancement factor and life factor does ECSS-E-ST-32-01C require for a safe-life composite or sandwich item, and what must the structure still achieve?

**Answer:** Life factor 1 with a load enhancement factor of 1.15; the worst damage must not grow within the safe-life interval and the structure must still carry ultimate load (6.3.2e). The test programme must demonstrate ultimate load capability and no defect growth after one service life with LEF 1.15, on articles representative of manufacturing, environment and loading (8.4.4.2e).

**Must contain:** LEF 1.15, life factor 1; no damage growth and ultimate load capability retained

**Sources:** `ECSS-E-ST-32-01C|6.3.2e`, `ECSS-E-ST-32-01C|8.4.4.2e`

## fs-011 · numeric · review: ok

**Q:** In a fail-safe design under ECSS-E-ST-32-01C, what load must the remaining structure carry after one element fails, for metallic versus composite parts?

**Answer:** Limit load times 1.0 for metal and glass parts, or times 1.15 for composite, bonded and sandwich parts, while still meeting the minimum specified performance (no large-scale yielding). Under the reduced programme, where fatigue is not significant, the customer may accept a factor between 1.0 and 1.15 for composites.

**Must contain:** 1.0 x limit load for metallic/glass; 1.15 x limit load for composite/bonded/sandwich; RFCP note allows lower composite factor (>= 1.0) with customer approval

**Sources:** `ECSS-E-ST-32-01C|6.3.3b`

## fs-012 · classification · review: ok

**Q:** Can a metallic fitting be classified as a low-risk fracture item under ECSS-E-ST-32-01C? Give the stress limit and the item types that are excluded.

**Answer:** Possibly, if agreed with the customer (6.3.5.2c). Maximum net-section tensile stress at limit load must not exceed 30 % of the ultimate tensile strength (6.3.5.2b). Excluded: pressure shells of crewed modules, pressure vessels, pressurized components with hazardous fluid, high-energy rotating machinery, and fasteners (6.3.5.2a). The criteria of 6.3.5.3 (material, process, 100 % visual and part-level NDT, crack growth) also apply.

**Must contain:** <= 30 % UTS net section at limit load; fasteners and pressure hardware excluded; customer agreement required

**Sources:** `ECSS-E-ST-32-01C|6.3.5.2a`, `ECSS-E-ST-32-01C|6.3.5.2b`, `ECSS-E-ST-32-01C|6.3.5.2c`

## fs-013 · numeric · review: ok

**Q:** Under the ECSS reduced fracture control programme, what proof test is required for a safe-life composite or sandwich structure such as a fairing panel, and how does it compare with the full programme?

**Answer:** Reduced programme: proof test to at least 1.1 times flight limit load per a customer-approved proof test plan, with proof loads recommended not to exceed 80 % of ultimate (11.2.2.5a). In the full programme, a proof test used for manufacturing-defect screening needs a factor of at least 1.2 on limit load, proof loads not above 80 % of ultimate, post-test NDT and customer approval (8.4.4.2g).

**Must contain:** RFCP: >= 1.1 x flight limit load; full programme screening proof: >= 1.2 x limit load; proof loads <= 80 % of ultimate

**Sources:** `ECSS-E-ST-32-01C|11.2.2.5a`, `ECSS-E-ST-32-01C|8.4.4.2g`

## fs-014 · classification · review: ok

**Q:** When may a composite item be accepted as low-risk fracture under ECSS-E-ST-32-01C without testing the damage tolerance threshold strain?

**Answer:** Strain at limit load must be below the damage tolerance threshold strain (8.4.4.3e). With customer approval this can be assumed without specific testing if, at limit load and including stress concentrations, maximum tensile stress is below 40 % and maximum compressive stress below 25 % of the material ultimate capability (8.4.4.3f).

**Must contain:** tension < 40 % of ultimate, compression < 25 % (incl. Kt); customer approval needed

**Sources:** `ECSS-E-ST-32-01C|8.4.4.3e`, `ECSS-E-ST-32-01C|8.4.4.3f`

## fs-015 · lookup · review: ok

**Q:** Can titanium or small-diameter fasteners be used in safe-life applications under ECSS-E-ST-32-01C?

**Answer:** In the full programme, fasteners below 5 mm diameter (3/16 in) and titanium alloy fasteners are not allowed in safe-life applications (8.8a, 8.8b). Under the reduced programme, titanium fasteners may be used in safe life if the 11.2.2.7a conditions are met (crack growth with a = c = 0.63 mm over four lifetimes, standard surface NDT, SCC-resistant alloy, not in a pressurized shell) or the 11.2.2.7b conditions (incl. sustained-load K below threshold or K < 0.5 KIC, customer approval). The 5 mm minimum still applies.

**Must contain:** < 5 mm not allowed in safe life (always); titanium not allowed in full programme; titanium allowed under RFCP with 11.2.2.7a or b conditions

**Sources:** `ECSS-E-ST-32-01C|8.8a`, `ECSS-E-ST-32-01C|8.8b`, `ECSS-E-ST-32-01C|11.2.2.7a`, `ECSS-E-ST-32-01C|11.2.2.7b`

## fs-016 · numeric · review: ok

**Q:** What initial crack sizes does ECSS-E-ST-32-01C assume for the low-risk approach of metallic safe-life parts under the reduced fracture control programme?

**Answer:** Surface cracks 0.63 mm deep by 1.27 mm long, 0.63 mm radius corner cracks at holes and edges, or 1.27 mm long through cracks, which must not grow to failure in less than four service lifetimes. Further conditions include standard fracture control surface NDT (X-ray not sufficient), well-characterised SCC-resistant alloy, no defect-prone process, and not pressurized hardware.

**Must contain:** 0.63 mm deep x 1.27 mm surface crack; 0.63 mm corner; 1.27 mm through; four lifetimes; standard surface NDT, SCC-resistant alloy, not pressurized

**Sources:** `ECSS-E-ST-32-01C|11.2.2.6a`

## fs-017 · lookup · review: ok

**Q:** What does ECSS-E-ST-32-08C require about fastening into composite parts and about inserts in sandwich panels?

**Answer:** Tapped screws must not be used in composite materials, to avoid damage (4.4.1b); galvanic corrosion from dissimilar-material contact must be precluded (4.4.1a); and all inserts must have corrosion-protected surfaces (4.4.4a).

**Must contain:** no tapped screws in composites; preclude galvanic corrosion; inserts corrosion protected

**Sources:** `ECSS-E-ST-32-08C|4.4.1a`, `ECSS-E-ST-32-08C|4.4.1b`, `ECSS-E-ST-32-08C|4.4.4a`

## fs-018 · lookup · review: ok

**Q:** Under ECSS-E-ST-32-08C, what must be included when deriving composite design allowables, and who approves them?

**Answer:** Allowables must account for manufacturing process control, deviation of lamina properties from nominal, failure modes (fibre, matrix, interface), cure residual strains, combined loading, scatter in compression strength, environmental susceptibility and non-linearity (4.5.2a). Allowables used in pre-dimensioning are justified to the customer for approval (4.5.2c), and the test plan states the statistical basis and how lay-up interpolation is done (4.5.2g).

**Must contain:** process control, lamina deviation, failure modes, residual strain, combined loading, compression scatter, environment; customer approval of allowables; test plan gives statistical basis

**Sources:** `ECSS-E-ST-32-08C|4.5.2a`, `ECSS-E-ST-32-08C|4.5.2c`, `ECSS-E-ST-32-08C|4.5.2g`

> Note: Source ambiguity: in 4.5.2a only five items are numbered (process control, cure residual strains, combined loading, compression scatter, environment). Lamina deviation, failure modes and non-linearity sit in NOTE-styled paragraphs between them, likely a formatting error. Please confirm whether they count as requirement items.

## fs-019 · compare · review: ok

**Q:** Compare the fatigue / service-life factor required by NASA-STD-5001B and ECSS-E-ST-32-01C for metallic structure.

**Answer:** Both use 4. NASA requires a minimum service life factor of 4.0 for fatigue and creep of well-characterised materials, with possible additional factors for composites or poorly characterised materials (FSR 51). ECSS fracture control uses a design life factor of at least 4 for metallic safe-life crack growth (6.3.2c) and for fatigue of the remaining structure of metallic fail-safe items, with mean fatigue properties (6.3.3e). Composites under ECSS instead use life factor 1 with LEF 1.15.

**Must contain:** NASA 4.0 (fatigue and creep); ECSS 4 for metallic safe-life and fail-safe fatigue; ECSS composites: life factor 1 + LEF 1.15

**Sources:** `NASA-STD-5001B|FSR 51`, `ECSS-E-ST-32-01C|6.3.2c`, `ECSS-E-ST-32-01C|6.3.3e`, `ECSS-E-ST-32-01C|6.3.2e`

## fs-020 · numeric · review: ok

**Q:** What yield and ultimate factors of safety does ECSS require for metallic parts of an expendable launch vehicle, and how are they applied to the limit load?

**Answer:** Table 4-3, launch vehicle, metallic parts: FOSY 1.1 and FOSU 1.25 with test; for verification by analysis only FOSU 2.0, while FOSY has no commonly agreed value (note c). The FOS is not applied alone: per Table 4-1, for launch vehicles DLL = LL x KP x KM, then DYL = DLL x FOSY x KMP x KLD and DUL = DLL x FOSU x KMP x KLD, where the margin policy factor KMP is mandatory for launch vehicles (4.1.5.3a). FOSU and FOSY on thermally induced loads are 1.0 for expendable launch vehicles (4.3.2.1d).

**Must contain:** FOSY 1.1, FOSU 1.25 (tested); analysis only: FOSU 2.0, FOSY not agreed; applied with KP, KM, KMP, KLD per Table 4-1; KMP required for launch vehicles; thermal loads: factors 1.0 for expendable launchers

**Sources:** `ECSS-E-ST-32-10C|4.3.2.1a`, `ECSS-E-ST-32-10C|4.3.2.1d`, `ECSS-E-ST-32-10C|4.2.1a`, `ECSS-E-ST-32-10C|4.1.5.3a`

> Note: Replaces the earlier not-covered trap, since ECSS-E-ST-32-10 is now loaded. Contrast with NASA-STD-5001B metallic prototype (1.0 yield / 1.4 ultimate) is a good follow-up compare question.

## fs-021 · not_covered · review: ok

**Q:** What acoustic test levels and duration apply to qualify a payload fairing?

**Answer:** Not covered by the loaded documents. Acoustic test levels and durations are in test standards (e.g. ECSS-E-ST-10-03, NASA-STD-7001), which are not loaded. The answer must not invent levels or reuse structural test factors as acoustic margins.

**Must contain:** the loaded standards do not cover this; points to a test standard such as ECSS-E-ST-10-03 / NASA-STD-7001; no invented dB levels or durations

**Sources:** none (not covered)

## hand-01 · numeric · review: ok

**Q:** What qualification and acceptance test factors does ECSS-E-ST-32-10 specify for launch vehicle structures?

**Must contain:** Table 4-2: launch vehicle global flight loads KQ 1.25, corrected per 4.2.2 / Annex A; KA 1 or the proof factor Jp (1.05 to 1.1 typical for dimensioning); local dynamic loads KQ 1.25, KA not applicable; thermal loads 1 / 1

**Sources:** `ECSS-E-ST-32-10C|4.3.1a`

## hand-02 · numeric · review: ok

**Q:** What factor of safety does ECSS-E-ST-32-10 require against buckling of launcher structure?

**Must contain:** Table 4-5: FOSU 1.25 global and local; FOSY 1.1 local, not applicable global; verification by analysis only: FOSU 2.0; knock-down factors are not included in the factor

**Sources:** `ECSS-E-ST-32-10C|4.3.2.3a`

## hand-03 · lookup · review: ok

**Q:** How does ECSS-E-ST-32-10 build the design factor from the factors of safety, the model factor and the project factor?

**Must contain:** design factor is the product of the listed factors; launch vehicles: KP x KM; yield and ultimate coefficients: FOS x KMP x KLD for launch vehicles (Table 4-1)

**Sources:** `ECSS-E-ST-32-10C|4.1.4.1a`, `ECSS-E-ST-32-10C|4.2.1a`

## hand-04 · numeric · review: ok

**Q:** Which additional factor does ECSS-E-ST-32-10 apply to joints, inserts and fasteners, and what is its value?

**Must contain:** local design factor KLD, to be justified (1.2 typical for satellites); Table 4-4 factors per sub-row: failure, gapping/sliding safety critical, other

**Sources:** `ECSS-E-ST-32-10C|4.1.5.2a`, `ECSS-E-ST-32-10C|4.3.2.2a`

## hand-05 · lookup · review: ok

**Q:** What checks must a structural finite element model pass under ECSS-E-ST-32 before it is delivered or used for coupled loads analysis?

**Must contain:** report geometry, topology, rigid-body strain energy, static, thermo-elastic and normal-mode checks; no numeric acceptance criteria in the loaded standards

**Sources:** `ECSS-E-ST-32C|I.2.1<13.1>a`, `ECSS-E-ST-32C|I.2.1<13.3>a`

## hand-06 · lookup · review: ok

**Q:** What does ECSS-E-ST-32 require about the minimum natural frequencies of a structure?

**Must contain:** stiffness requirements to be identified, often as minimum frequency; verified by modal analysis; no frequency values given

**Sources:** `ECSS-E-ST-32C|4.3.5a`, `ECSS-E-ST-32C|4.6.2.4a`

## hand-07 · lookup · review: ok

**Q:** What does ECSS-E-ST-32 require when correlating the structural mathematical model with modal survey or vibration test results?

**Must contain:** models validated by correlation with test results; test-analysis correlation reported per its DRD; numeric criteria not in the loaded set

**Sources:** `ECSS-E-ST-32C|4.6.2.2b`

## hand-08 · lookup · review: ok

**Q:** What must be done under ECSS-E-ST-32-01 when NDT detects a crack-like defect in a PFCI?

**Must contain:** customer approval before use; treat as crack-like and verify by fracture mechanics analysis or test

**Sources:** `ECSS-E-ST-32-01C|10.7.1b`, `ECSS-E-ST-32-01C|10.7.2.1.1a`

## hand-09 · numeric · review: ok

**Q:** What service life factor does NASA-STD-5019A apply in the damage tolerance (safe-life) analysis of fracture critical parts?

**Must contain:** 4 lifetimes without failure; single-event lives: lower-bound toughness at 4 lifetimes or factor 1.4 after 1 lifetime

**Sources:** `NASA-STD-5019A|FCR 12 / 7.3.2.c`

## hand-10 · classification · review: ok

**Q:** Under NASA-STD-5019A, when can a part be classified non-fracture critical because it is contained or has low release mass?

**Must contain:** hazard-based: fracture and release do not cause a catastrophic hazard; no mass threshold; external released parts only within an agreed debris-field criterion; contained: containment assessment shows the part cannot escape

**Sources:** `NASA-STD-5019A|FCR 8 / 6.2.1`, `NASA-STD-5019A|FCR 8 / 6.2.2`

## hand-11 · lookup · review: ok

**Q:** When does NASA-STD-5019A accept a proof test instead of NDE to screen flaws in fracture critical hardware?

**Must contain:** approach documented in the fracture control plan with rationale; approved by the responsible fracture control board

**Sources:** `NASA-STD-5019A|FCR 18`

## hand-12 · compare · review: ok

**Q:** Compare how ECSS-E-ST-32-01 and NASA-STD-5019A treat welds in fracture critical / safe-life metallic parts.

**Must contain:** ECSS: weld properties, residual stresses and imperfections in the safe-life analysis; NASA: post-proof NDE at critical welds

**Sources:** `ECSS-E-ST-32-01C|8.3.2e`, `NASA-STD-5019A|FCR 16`

## hand-13 · compare · review: ok

**Q:** Compare how ECSS-E-ST-32-01 and NASA-STD-5019A require fasteners in fracture critical / safe-life applications to be screened.

**Must contain:** ECSS: eddy current on shank, head fillet and threads; NASA: eddy current or proof test

**Sources:** `ECSS-E-ST-32-01C|8.8f`, `NASA-STD-5019A|FCR 11 / 7.2.8.c`

## hand-14 · lookup · review: ok

**Q:** What does ECSS-Q-ST-70 require about stress corrosion cracking when selecting metallic materials?

**Must contain:** structural materials selected per ECSS-Q-ST-70-36; others tested per ECSS-Q-ST-70-37

**Sources:** `ECSS-Q-ST-70C|5.1.10a`

## hand-15 · lookup · review: ok

**Q:** What outgassing screening criteria (RML, CVCM) must materials meet under ECSS-Q-ST-70?

**Must contain:** screening per ECSS-Q-ST-70-02; the numeric limits are not in the loaded standards

**Sources:** `ECSS-Q-ST-70C|5.1.4b`

## hand-16 · lookup · review: ok

**Q:** What does ECSS-E-ST-32-08 require for adhesive bonding and bonded joints?

**Must contain:** ECSS-E-ST-32-08 has no bonding requirements; ECSS-E-ST-32: bonded joints analysed and adhesive allowables defined per agreed standards

**Sources:** `ECSS-E-ST-32C|4.6.2.12a`, `ECSS-E-ST-32C|4.5.12a`

> Note: Names a loaded document that does not cover the topic (hand test F6).

## hand-17 · not_covered · review: ok

**Q:** What random vibration qualification level applies to a payload adapter (ECSS-E-ST-10-03)?

**Must contain:** the loaded standards do not cover this; ECSS-E-ST-10-03 is not loaded

**Sources:** none (not covered)

## hand-18 · not_covered · review: ok

**Q:** What margin over the maximum expected pyroshock environment does NASA-STD-7003 require for qualification of a fairing separation system?

**Must contain:** not covered; NASA-STD-7003 is not loaded; must not reuse the 5019A single-event 1.4 test-load factor as a shock margin

**Sources:** none (not covered)

## hand-19 · not_covered · review: ok

**Q:** What separation factor of safety does NASA-STD-5020 require for preloaded bolted joints?

**Must contain:** not covered; NASA-STD-5001B defers threaded fasteners to NASA-STD-5020, which is not loaded

**Sources:** none (not covered)

## hand-20 · not_covered · review: ok

**Q:** What torque margin does ECSS-E-ST-33-01 require for a fairing mechanism?

**Must contain:** not covered; ECSS-E-ST-33-01 is not loaded

**Sources:** none (not covered)

## fs-022 · numeric · review: pending

**Q:** What scatter factor does ECSS-E-ST-32 require in fatigue analysis, and how is it applied to the service life?

**Answer:** A scatter factor of 4 is used in fatigue analysis. It multiplies the number of cycles at a load level: the life is verified for the specified service life times the scatter factor, with the most unfavourable load sequence within each event. Notes: higher factors can apply (e.g. pressure vessels, low-cycle fatigue); for composites a factor on stress may be used instead.

**Must contain:** scatter factor 4 in fatigue analysis; applied to the number of cycles: service life x scatter factor, worst load sequence per event; notes: higher for some applications; composites may use a stress factor instead

**Sources:** `ECSS-E-ST-32C|4.5.18a`, `ECSS-E-ST-32C|4.6.2.8c`

> Note: The higher-factor and composite remarks are NOTEs to 4.5.18a, not requirements.

## fs-023 · numeric · review: pending

**Q:** Under ECSS-E-ST-32, what scatter factor applies to the number of thermal cycles in thermal cycling tests of launcher structure?

**Answer:** For launchers (low number of operational thermal cycles): 4 when cycling within the flight temperature range, 2 when cycling within the qualification temperature range. The 1.5 factor is for other spacecraft with many operational cycles, not launchers.

**Must contain:** 4 within flight temperature ranges; 2 within qualification temperature ranges; 1.5 applies only to spacecraft with a large number of cycles

**Sources:** `ECSS-E-ST-32C|4.6.3.15c`

## fs-024 · compare · review: pending

**Q:** Compare how ECSS-E-ST-32 and NASA-STD-5001B handle the design of glass and ceramic structural parts.

**Answer:** ECSS-E-ST-32 asks for probabilistically derived design allowables covering size effects, without a factor table. NASA-STD-5001B gives factors in Table 3 (robotic applications): verified by test, ultimate design factor 3.0 with proof factor 1.2 (non-pressurized) or 2.0 (pressurized); analysis only (non-pressurized, not for ceramics) ultimate 5.0.

**Must contain:** ECSS: probabilistic allowables covering size effects, no factors given; NASA Table 3 tested: ultimate 3.0, proof 1.2 non-pressurized / 2.0 pressurized; NASA analysis only: 5.0, not applicable to ceramics

**Sources:** `ECSS-E-ST-32C|4.5.10.1a`, `NASA-STD-5001B|FSR 32`

## fs-025 · numeric · review: pending

**Q:** What proof test does ECSS-E-ST-32-01 require for rotating machinery, and what is the minimum proof factor?

**Answer:** Rotating machinery is proof (spin) tested, with NDT before and after the proof test. The proof factor comes from fracture mechanics analysis and is at least 1.1. Under the reduced fracture control programme (11.2.2.4a) this may be replaced by a spin test at 1.1 times nominal speed.

**Must contain:** proof (spin) test with NDT before and after; proof factor from fracture mechanics, not below 1.1; reduced programme option: 1.1 x nominal operational speed (11.2.2.4a)

**Sources:** `ECSS-E-ST-32-01C|8.6a`, `ECSS-E-ST-32-01C|8.6b`

## fs-026 · classification · review: pending

**Q:** Under ECSS-E-ST-32-01, which potential fracture-critical items must be classified fracture critical?

**Answer:** Non-metallic (composite, bonded, sandwich) PFCI unless fail-safe, low-risk or contained; metallic PFCI needing better than standard NDT; pressure vessels and manned or other pressurized structures designated fracture critical; PFCI needing periodic re-inspection or replacement to reach their life (fracture limited-life items); rotating machinery.

**Must contain:** non-metallic PFCI unless fail-safe, low-risk or contained; metallic PFCI needing better than standard NDT; pressure vessels / pressurized structures, rotating machinery; items needing periodic NDT or replacement (FLLI)

**Sources:** `ECSS-E-ST-32-01C|6.2.2a`

## fs-027 · compare · review: pending

**Q:** Compare what ECSS-E-ST-32-01 and NASA-STD-5019A require of the remaining structure for a part to be accepted as fail-safe.

**Answer:** ECSS: after failure of any element, the remaining structure carries limit loads times 1.0 (metallic, glass) or 1.15 (composite, bonded, sandwich) without losing minimum performance, and no released fragment may create a catastrophic hazard. NASA: loss of any load path is not a catastrophic hazard and multi-site damage is not a credible concern; the remaining structure sustains all redistributed loads and environments until mission end or inspection. Composite or bonded parts hit by the failed part carry DUL with the worst impact damage (DLL for the fail-safe part's own remaining composite structure; fracture-critical ones take the damage into their DTA).

**Must contain:** ECSS: limit loads x 1.0 metallic/glass, x 1.15 composite/bonded/sandwich; ECSS: no catastrophic release of fragments; NASA: no catastrophic hazard on loss of a load path; remaining structure carries redistributed loads until end of mission; NASA: no explicit factor on the remaining structure for metallic parts

**Sources:** `ECSS-E-ST-32-01C|6.3.3b`, `ECSS-E-ST-32-01C|6.3.3c`, `NASA-STD-5019A|FCR 8 / 6.2.3.a`, `NASA-STD-5019A|FCR 8 / 6.2.3.c`

## fs-028 · classification · review: pending

**Q:** What conditions must a pressure component meet under ECSS-E-ST-32-01 to be treated as non-hazardous leak-before-burst?

**Answer:** LBB failure mode shown at MDP (per ECSS-E-ST-32-02); the leak causes no catastrophic hazard; no repressurization or further cycles while leaking; alloy not prone to sustained-load cracking and made by established processes; supporting structure meets fracture control; no impervious coating that would stop the leak. Areas that cannot be shown LBB are verified safe life.

**Must contain:** LBB demonstrated at MDP; leak not a catastrophic hazard; no repressurization while leaking; suitable alloy and established processes; no impervious barrier or coating; supporting structure under fracture control; non-LBB areas verified as safe life

**Sources:** `ECSS-E-ST-32-01C|8.2.7a`, `ECSS-E-ST-32-01C|8.2.2.2d`

## fs-029 · lookup · review: pending

**Q:** What does ECSS-Q-ST-70 require to prevent hydrogen embrittlement of mechanical parts?

**Answer:** Assess whether hydrogen embrittlement can occur in manufacture or use; implement protection and control measures for manufacture and use; parts under fatigue or sustained stress made of susceptible material are heat treated after coating.

**Must contain:** assess the possibility of hydrogen embrittlement; protection and control measures in manufacturing and use; susceptible parts under fatigue or sustained load heat treated after coating

**Sources:** `ECSS-Q-ST-70C|5.1.19a`, `ECSS-Q-ST-70C|5.1.19c`, `ECSS-Q-ST-70C|5.1.19d`

## fs-030 · lookup · review: pending

**Q:** What do the ECSS materials standards require about galvanic corrosion between dissimilar metals in a structure?

**Answer:** ECSS-E-ST-32-08: galvanic corrosion from contact of dissimilar materials is precluded. ECSS-Q-ST-70: where bimetallic contacts are used, the material pair is agreed with the customer (also metal to conductive fibre-reinforced material).

**Must contain:** 32-08: galvanic corrosion precluded; Q-ST-70: bimetallic pairs agreed with the customer, incl. metal to carbon-fibre contacts

**Sources:** `ECSS-E-ST-32-08C|4.4.1a`, `ECSS-Q-ST-70C|5.1.12a`

## fs-031 · lookup · review: pending

**Q:** What does ECSS-E-ST-32 require for venting of a structure such as a fairing or interstage?

**Answer:** Venting provisions are part of the structural design; if there are none, the structure withstands the build-up pressure including safety factors. Vent openings are compatible with the purging gas pressure and flow. No venting area or depressurisation rate values are given.

**Must contain:** design provides for venting; otherwise withstand build-up pressure including safety factors; no numeric vent area or depressurisation rate in the loaded standards

**Sources:** `ECSS-E-ST-32C|4.5.15a`, `ECSS-E-ST-32C|4.5.15b`

## fs-032 · not_covered · review: pending

**Q:** What minimum static clearance must be kept between the payload and the inner wall of the fairing?

**Must contain:** not covered by the loaded standards; envelope clearances come from the launcher user's manual / ICD; no invented clearance value

**Sources:** none (not covered)

## fs-033 · not_covered · review: pending

**Q:** What overall sound pressure level does a payload experience under the fairing at lift-off?

**Must contain:** not covered; acoustic environments are launcher-specific (user's manual) or in test standards not loaded; no invented dB level

**Sources:** none (not covered)

## fs-034 · not_covered · review: pending

**Q:** What preload uncertainty factor should be used for torque-tightened bolts in a fairing joint?

**Must contain:** not covered; ECSS-E-ST-32 only requires bolted joints to be analysed to agreed standards (points to ECSS-E-HB-32-23, not loaded); no invented preload scatter value

**Sources:** none (not covered)

> Note: Citing ECSS-E-ST-32C 4.6.2.13a as the pointer is acceptable; it gives no factor.

## fs-035 · not_covered · review: pending

**Q:** What is the A-basis ultimate tensile strength of 7075-T7351 aluminium plate?

**Must contain:** not covered; the loaded standards define A/B-basis allowables but give no material values (MMPDS or similar not loaded); no invented strength value

**Sources:** none (not covered)

## fs-036 · not_covered · review: pending

**Q:** What molecular contamination deposition limit applies to payload surfaces inside the fairing?

**Must contain:** not covered; ECSS-Q-ST-70 requires a cleanliness programme and refers to ECSS-Q-ST-70-01, not loaded; no invented deposition limit

**Sources:** none (not covered)

## fs-037 · not_covered · review: pending

**Q:** What lightning strike current waveform and peak current must a composite fairing withstand?

**Must contain:** not covered; ECSS-E-ST-32 requires lightning current diversion and testing but gives no waveform or peak current; no invented current values

**Sources:** none (not covered)
