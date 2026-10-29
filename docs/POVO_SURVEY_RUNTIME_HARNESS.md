# Survey native walkthrough harness

`tools/playtest_povo_survey.py` builds 50 independent routes from the current export provenance. It does not launch CS2 or reload a map. The operator must load a fresh standard map, with one human and zero bots. The harness verifies the supplied on-disk VPK hash; status verifies the loaded map name, not the loaded package bytes.

Source-only preview:

```powershell
python -m tools.playtest_povo_survey --list-routes
```

Native run, after the operator stages and loads the package:

```powershell
python -m tools.playtest_povo_survey --package build/package/trento_povo_campus.vpk --output build/gameplay/survey-repair/full --expected-package-sha256 e08a52bbf22d4b9e668d88cd5becbb8375f34831393fb1996dc59073332af3c4
```

Use `--routes REGEX` to run a selected subset and a distinct `--output` directory for each run. Route names are shown by `--list-routes`. For example, `--routes '^p1_se_segment0_up$'` selects one corner stair ascent. Each independent route has exactly one initial placement; subsequent points use normal walking or ladder climbing, with a normal jump to detach at the upper lift ledge, with `noclip 0` at placement and cleanup. Collinear 3D tread centers are simplified but landing turns and changes in stair slope remain explicit. Povo 1 corner routes enter and leave through their metadata-owned door portals.

Intermediate stair treads allow a 42 cm height envelope because the native standing hull spans neighbouring 18 cm risers. Both terminal floor elevations, all door/hall targets on them and every non-stair target retain a strict 25 cm height tolerance. Each recorded check includes its actual tolerance. The native walk button is `+sprint`, as reported by the live binding query; the obsolete `+speed` command is not used.

The persistent console transport stops forward input after short movement pulses. Narrow courtyard routes target 6 cm horizontal tolerance; the basement portal detour targets 2.5 cm, and other routes target 15 cm. Controller steering, command timing, collision and geometry can each cause a failed traversal; a stalled route alone does not identify a geometry defect. Failure reports retain actual position, requested target, successful prior checks and console transcript. Every physical failure continues to the next independent route. A multiplayer/wrong-map guard rejection blocks remaining routes; it never moves the player. Cleanup releases forward, sprint, jump and attack inputs.

The two lift routines derive upper floor at 11.2 m from the current provenance, rather than the old 7.6 m target. They require feet at least 0.65 m above that floor before a normal jump detaches from the ladder and ordinary walking reaches the registered ledge. Routes cover four corner cores across two storeys in both directions, two courtyard storeys both ways, Povo 2's two upper modules and lower stairs, rotated basement corridor, bridge, Acquario door/aisle, A103 side aisles, library/canteen stairs and entries.

The exit status is zero only when every selected route and cleanup passes. Aggregate `survey-runtime.json`, transcript `survey-runtime.log` and individual route JSON files are written below the chosen output directory. Guard rejection, incomplete runs and unexecuted routes cannot produce a passing aggregate. The fresh-map requirement remains an operator precondition; status alone does not prove map freshness.

Controller throughput settings: `TCP_NODELAY` is enabled; position replies default to 100 ms, and stopped-input reads to 40 ms. Broad walking pulses cap at 450 ms; narrow courtyard pulses retain 250 ms. Minimum pulses default to 40 ms broad and 35 ms narrow. These change command timing, not movement physics, route coordinates or acceptance tolerances. CLI flags `--position-read`, `--pulse-max`, `--narrow-pulse-max`, `--pulse-min`, `--narrow-pulse-min` and `--stop-read` override them; an individual route may override timing keys in its `timings` dictionary. Reports record the active global timings. Missing position replies fail rather than reusing a cached position.

The repaired-package routes use full Povo 2 floor landings, the native-verified library partition detour and the basement portal detour around the lift/stair enclosure and CIBIO glazing. Original failing paths remain in their historical reports.
