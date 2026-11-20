# Two more Launch Darkly importer bugs

Fix branch: [`fix/ld-importer-env-segments-and-mv-rules`](https://github.com/Ayush-e4/flagsmith/tree/fix/ld-importer-env-segments-and-mv-rules). It has one commit per bug.

| Issue | Bug | Effect |
|---|---|---|
| [#9032](https://github.com/Flagsmith/flagsmith/issues/9032) | A segment override in one environment is linked to **another environment's** segment | Users are targeted with the wrong environment's segment members |
| [#9033](https://github.com/Flagsmith/flagsmith/issues/9033) | Rules on multivariate flags that serve a fixed variation import as **0% for every variation** | Matching users get the control value instead of the rule's variation |

## How we came across them

While building the sample app for [#8721](https://github.com/Flagsmith/flagsmith/issues/8721), the first version used a multivariate flag: a "Beta testers" segment, and a rule "beta testers get `new`, everyone else gets `old`".

Even with the #8721 fix in place, the imported flag still gave beta testers the wrong value. Looking at what the importer created showed two things #8721 didn't explain:

1. The **Test** environment's override was linked to `Beta testers (Override for production)`, not `(Override for test)`.
2. The override's variations were `new 0%`, `old 0%`, `legacy 0%`, when the rule says `new` should be 100%.

The #8721 sample app sidestepped both, using a feature with a plain on/off segment override, so that it only tested #8721. We noted the two bugs and traced them afterwards.

## Root cause (lines on upstream `main` @ `6e0f9da`)

**Bug 1.** [`services.py#L1102-L1112`](https://github.com/Flagsmith/flagsmith/blob/6e0f9da6f8a6aed7052a35f5f00fdeb313e7ed3b/api/integrations/launch_darkly/services.py#L1102-L1112) creates one segment per (Launch Darkly segment, environment), named `<name> (Override for <env>)`. It then stores them as `segments_by_ld_key[ld_segment["key"]] = segment`, keyed by segment key only, so each environment overwrites the previous one. When flags are imported, every environment looks up `segments_by_ld_key` ([L274](https://github.com/Flagsmith/flagsmith/blob/6e0f9da6f8a6aed7052a35f5f00fdeb313e7ed3b/api/integrations/launch_darkly/services.py#L274)) and gets the **last** environment's segment.

**Bug 2.** Launch Darkly gives a rule's variation as an integer (`"variation": 0`). [L749](https://github.com/Flagsmith/flagsmith/blob/6e0f9da6f8a6aed7052a35f5f00fdeb313e7ed3b/api/integrations/launch_darkly/services.py#L749) passes it on unchanged, with a `# type: ignore[arg-type]` that hides the mismatch. [L675](https://github.com/Flagsmith/flagsmith/blob/6e0f9da6f8a6aed7052a35f5f00fdeb313e7ed3b/api/integrations/launch_darkly/services.py#L675) then compares it with the string keys of the multivariate options (`0 == "0"`), which is never true, so every variation gets 0%. Individual targets already convert the index to a string ([L575](https://github.com/Flagsmith/flagsmith/blob/6e0f9da6f8a6aed7052a35f5f00fdeb313e7ed3b/api/integrations/launch_darkly/services.py#L575)). Rules don't.

## Proof 1: unit tests with Flagsmith's own test data

Four new tests use the existing fixtures in `api/tests/unit/integrations/launch_darkly/client_responses/`. All 4 fail on `main` and pass on the fix branch:

```
# on main
FAILED test_process_import_request__segment_match_rules__targets_segment_of_same_environment
  Extra items in the left set:
  ('Test', 'User List (Override for production)')
  ('Test', 'Dynamic List (Override for production)')
  ('Test', 'Dynamic List 2 (Override for production)')
FAILED test_process_import_request__multivariate_rule_with_variation__serves_that_variation[Reverted And-1]
  Extra items in the left set: ('1', 0.0)   Extra items in the right set: ('1', 100)
FAILED ...serves_that_variation[Regular And-2]
FAILED ...serves_that_variation[Just Not-3]
4 failed

# on the fix branch
69 passed   (all Launch Darkly tests; diff coverage 100%, mypy clean)
```

## Proof 2: sample app (this folder)

The Launch Darkly export in `ld_fixtures/` has a "Beta testers" segment with **different members per environment**: `tess-tester` in Test and `paula-prod` in Production. The flag `checkout-version` serves `old` by default and `new` to beta testers.

`import.sh` runs the **real** importer from `main` (`old`) and from the fix branch (`fixed`). Only Launch Darkly's HTTP API is stubbed. `sample_app.py` then asks the Flagsmith SDK API (`POST /api/v1/identities/`) which checkout each user gets:

```
env         user         | LaunchDarkly | old import     | fixed import
Test        tess-tester  | new          | old    ❌      | new    ✅
Test        paula-prod   | old          | None   ❌      | old    ✅
Test        dave         | old          | old    ✅      | old    ✅
Production  tess-tester  | old          | old    ✅      | old    ✅
Production  paula-prod   | new          | None   ❌      | new    ✅
Production  dave         | old          | old    ✅      | old    ✅
matches Launch Darkly: old 3/6, fixed 6/6

old import, segment overrides created:
  Production  -> Beta testers (Override for production)   {'new': 0.0, 'old': 0.0, 'legacy': 0.0}
  Test        -> Beta testers (Override for production)   {'new': 0.0, 'old': 0.0, 'legacy': 0.0}
fixed import, segment overrides created:
  Production  -> Beta testers (Override for production)   {'new': 100.0, 'old': 0.0, 'legacy': 0.0}
  Test        -> Beta testers (Override for test)         {'new': 100.0, 'old': 0.0, 'legacy': 0.0}
```

What each wrong row shows:
- **Production / paula-prod:** the correct segment matched, but she gets no value instead of `new`. This is bug 2 on its own.
- **Test / tess-tester:** Test's own beta tester isn't matched, because Test checks Production's members. This is bug 1.
- **Test / paula-prod:** Production's beta tester is matched in Test (bug 1), then gets no value (bug 2).

The full importer output is in `import_old.json` and `import_fixed.json`, and the sample app output is in `result.txt`.

### Run it

You need a local Flagsmith database, a checkout of `main` and a checkout of the fix branch.

```bash
cd sample-apps/launchdarkly-import-bugs
python3 make_fixtures.py   # optional: regenerates ld_fixtures/
export OLD_CHECKOUT=/path/to/flagsmith-main FIXED_CHECKOUT=/path/to/flagsmith-fix
export ENV_FILE=/path/to/flagsmith/api/.env-local   # optional
./import.sh old && ./import.sh fixed
# start the API on :8000 (`make serve` in either checkout), then:
python3 sample_app.py
```
