# Publish the map and play it with friends

Not yet tried end to end in this project. Menu labels may differ in your CS2
build; treat this as a checklist, and record what you find in the worklog.

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
2. Open CS2 Workshop Tools, select the `trento_povo` addon and choose Publish.
3. Set visibility to **Friends-only or Unlisted** for the first upload.
4. Note the Workshop item ID (the number in its URL).

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
