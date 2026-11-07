# Native screenshots of the povo-updates build

This is the earlier bundle review. The later
[sidewalk repair](../sidewalk_fix_20261104/README.md) now occupies the mutable
review addon and the ordinary local package; these screenshots retain the
earlier build identity recorded below.

The user was running `trento_povo_campus_test`, whose installed VPK and ordinary
`build/package` VPK both had SHA-256
`18d154a01b9cdbe554db740657cd700899dab4ebc4ac8a5541ed4eaacafcd753`
(the 2 November package). The newly built bundle had not been installed there.

For these captures CS2 was restarted into the separate `trento_povo_bundle_review`
addon, with an installed copy hash-verified against the candidate:
`98a21c01cb4fa5f6cb51f388a48a53985dba4b4bd9046002cf0e0de98fe267ea`.
The app command line confirms that addon. `mat_fullbright=0` was queried before
and after capture. These are unedited CS2-window screenshots captured through
the computer-use skill; HUD/viewmodel were hidden during capture and restored
afterward. Camera placement uses noclip and does not establish walking clearance.

- [User's original viewpoint, now on the bundle build](povo2_current_view.png)
- [Povo 1 frontage, stone panels and pavement](povo1_facade.png)
- [Via Sommarive crest](via_sommarive_crest.png)
- [Povo 2 glazing/courtyard](povo2_glazing.png)
- [Facade and glazing close-up](facade_detail.png)

The views confirm textured surfaces in the loaded candidate. Large dark shapes
remain visible in the skyline and dark patches remain below the exterior ramp;
their cause was not diagnosed in this screenshot task. This is a targeted visual
record, not a full visual acceptance or movement/multiplayer certification.

`package.json` records installation identity; `captures.json` records screenshot
hashes and camera placements. CS2 is left running the new review addon at the
user's original viewpoint. `play_review.cmd` reopens this same installed review
addon after CS2 is closed. The ordinary `play_campus.cmd` still points to the older
approved package; no default-package promotion or Workshop publication occurred.
