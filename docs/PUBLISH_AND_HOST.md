# Publish the map and play it with friends

The two-player profile is installed on the Windows development PC. The map was
uploaded successfully as [Povo campus - friends playtest](https://steamcommunity.com/sharedfiles/filedetails/?id=3827904476)
with Friends only visibility on 26 October 2026. The user confirmed Workshop
approval and their friend's subscription. The host is subscribed. A successful
connection from a second PC has not yet been verified.

## Free-for-all session

Free-for-all is built into the map. Start the campus in **Deathmatch** (game
type 1, mode 2) and a `point_script` (`maps/scripts/povo_ffa.js`) makes
everyone an enemy. It turns on automatic respawns, three seconds of spawn
protection, no bots and a 20-minute match. Players respawn at random among 64
`info_deathmatch_spawn` points spread over the whole campus: both buildings,
the wings, the bridge, Povo 2, the parking, the yard and the streets. They
never respawn where an enemy can see them. Classic and Wingman are unchanged.

The spawns come from `tools/povo_spawns.py`. It uses only floor cells that the
clearance audits show are reachable with standing room, plus the audited
outdoor routes. It keeps them at least 7 m apart and turns each one toward its
longest clear sightline.

To host: in normal CS2 with Open Party enabled, start the Povo map in
Deathmatch. Friends join through the Steam friends list. Console fallback:
`exec povo_ffa_start`, installed by `host_campus.cmd`. No command is needed
after the map loads. For a local tools-mode check, use
`play_campus.cmd -Deathmatch`.

The Workshop item needs a new upload with this map. It also needs the
**Deathmatch** tag, so Workshop Maps offers that mode.

## Two-player session through Steam

Run `host_campus.cmd` to install `povo_duel.cfg` and open normal CS2 through Steam.
It is separate from `play_campus.cmd`, which launches a tools-mode solo playtest.
To install the profile without opening CS2:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/host_povo_campus.ps1 -SetupOnly
```

After the campus has a Workshop item:

1. Both players subscribe to that same item and finish downloading it.
2. The host starts normal CS2, opens **Play > Workshop Maps**, enables **Open
   Party**, selects the campus and starts the match.
3. Once the map has loaded, the host enters `exec povo_duel` in the developer
   console. Run it after each map load, because map/mode defaults can override
   settings applied earlier.
4. The friend joins through the Steam/CS2 friends list. Pick opposite teams.

The profile removes bots, disables automatic team balancing and instant
respawns, and sets 3-minute rounds, a 5-second freeze time, 30-second buy time,
800 starting money and 24 maximum rounds. It restarts the round when applied.
It does not cap player slots; Open Party can allow other friends to join.
The host PC must stay awake and keep CS2 running.

Valve documents the Open Party joining flow in its
[18 March 2026 update](https://www.counter-strike.net/newsentry/532126482488623353).
The Steam route does not require a separate dedicated server or GSLT setup.

## How it works

- **Steam Workshop is only a file host.** Publishing uploads the compiled map
  (a VPK, ~43 MB: 44,979,765 bytes at the 24 October 2026 build). It does not
  run a server.
- **The server is whoever hosts the match.** In a normal friends game that is
  the host's own PC (a *listen server*: the game runs the server and the host
  plays on it). Friends connect to it; nothing runs on Valve's or GitHub's side
  for you.
- **Friends' games download the map automatically** when they subscribe to the
  Workshop item or join a server running it. The download is about 43 MB.
- An always-on map needs a dedicated server (a VPS or home machine running the
  CS2 dedicated server); that is optional and separate.

## 1. Publish (Windows)

1. Build: `python tools/cs2_project.py compile --target all`, then check the
   package (`python tools/verify_cs2_package.py`, see CS2_PACKAGE_CHECK.md).
2. **After the build finishes**, run:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File tools/prepare_povo_workshop.ps1
   ```

   This copies the last completed campus VPK into the separate
   `trento_povo_friends` addon and checks every entry CRC. The source build time
   and SHA-256 are recorded in `build/workshop/snapshot.json`. It also prepares
   `build/workshop/preview.png` and `description.txt`. Running it during a build
   stages the previous completed package; rerun it when the new build finishes.
   It never uploads anything.
3. Open CS2 Workshop Tools, launch an addon with **Launch Tools**, then open
   **Counter-Strike 2 Workshop Manager** from the Asset Browser toolbar. Choose
   **New** and select addon folder **trento_povo_friends**. This keeps the
   development addon and the winter map out of this initial upload.
4. Use title **Povo campus - friends playtest**, the prepared description and
   preview, **Classic** and **Wingman** tags, and **Friends only** visibility
   (**Solo amici** in the Italian UI). Review **Contents** before submitting.
5. Submit the completed package and record the Workshop item ID from its URL.
   Accept the Steam Workshop agreement if Steam requires it. Both players must
   be able to subscribe and finish downloading before testing the invite.

Preparation on 26 October 2026: the signed-in Workshop Manager has no published
maps. The friends addon now contains the latest completed standard package:
59,965,101 bytes, 790 entries, SHA-256
`3d00c5472c192f963cf1f9d89e92d5408f8c16a426b8cc55daf226a9e7e6b093`.
Every entry CRC passes. The older snapshot and metadata were backed up under
`build/workshop-backup-*/` before replacement. The installed `povo_duel.cfg`
profile is ready. The new submission has its title, description, preview,
Classic/Wingman tags and Friends only visibility filled in.
With the user's confirmation, the submission completed successfully. Workshop
Manager lists Published File ID **3827904476**. The signed-in Steam item page
confirms the title, Classic/Wingman tags and Friends only visibility, and reports
**pending moderator approval**. No approval or second-client access is claimed.
The fields, package identity and result are saved under `build/workshop/`.
The host account is subscribed. The running game is the solo tools playtest;
restart in normal CS2 to host through Open Party after the item is available.

Licensing: some reference material has no redistribution licence (see
DATA_SOURCES.md). Do not make the item public until that is resolved.

## 2. Play with friends

1. Everyone subscribes to the Workshop item (friends need the link if unlisted).
2. The host opens CS2, creates a lobby and invites friends, then picks the
   Workshop map; or in the console: `host_workshop_map <workshop_id>`.
3. Friends join through the Steam invite/lobby. Joining by IP
   (`connect <host-ip>`) needs the host to forward UDP port 27015.
4. Add bots from the console for a first solo test.

## 3. Before inviting anyone

Run the first milestone from the README: one friend on a separate PC joins and
you finish a round (spawns, buy zones, bomb, navigation). Log the result in
WORKLOG.md.
