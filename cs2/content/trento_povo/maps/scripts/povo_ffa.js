// Native free-for-all for the Povo campus.
// Start the map in Deathmatch (game_type 1, game_mode 2) and everyone is an
// enemy, respawning at the campus-wide info_deathmatch_spawn points. Other
// modes (Classic, Wingman: the two-player duel) are left untouched.
import { Instance, Console } from "cs_script/point_script";

const DEATHMATCH = { type: 1, mode: 2 };

const FREE_FOR_ALL = [
    ["mp_teammates_are_enemies", 1],
    ["mp_autoteambalance", 0],
    ["mp_limitteams", 0],
    ["mp_respawn_on_death_t", 1],
    ["mp_respawn_on_death_ct", 1],
    ["mp_respawn_immunitytime", 3],
    // Random picks among the map's authored campus-wide spawns, never one
    // in an enemy's line of sight.
    ["mp_randomspawn", 1],
    ["mp_randomspawn_los", 1],
    ["mp_freezetime", 0],
    ["mp_roundtime", 20],
    ["mp_timelimit", 20],
    ["mp_maxrounds", 0],
    // Friends only; the map's default config would otherwise fill with bots.
    ["bot_quota_mode", "normal"],
    ["bot_quota", 0],
];

function isDeathmatch() {
    return Instance.GetGameType() === DEATHMATCH.type && Instance.GetGameMode() === DEATHMATCH.mode;
}

// CS2 also generates unnamed Deathmatch spawns from the nav mesh. Keep only
// the map's named ones, each checked for floor support and standing room.
const CAMPUS_SPAWN = "povo_dm_spawn";

function keepCampusSpawns() {
    let kept = 0, disabled = 0;
    for (const spawn of Instance.FindEntitiesByClass("info_deathmatch_spawn")) {
        if (spawn.GetEntityName() === CAMPUS_SPAWN) {
            kept++;
        } else {
            Instance.EntFireAtTarget({ target: spawn, input: "SetDisabled" });
            disabled++;
        }
    }
    Console.Log(`povo_ffa: ${kept} campus spawns kept, ${disabled} generated spawns disabled`);
}

function applyFreeForAll() {
    if (!isDeathmatch()) return;
    for (const [name, value] of FREE_FOR_ALL) Console.SetConvar(name, value);
    keepCampusSpawns();
    // Generated spawns can appear just after activation or a restart.
    Instance.Delay(1).then(keepCampusSpawns);
}

// Mode and map configs run around map load and again at restarts, so
// reapply at activation, at each round start and when a player arrives.
Instance.OnActivate(applyFreeForAll);
Instance.OnRoundStart(applyFreeForAll);
Instance.OnPlayerActivate(applyFreeForAll);
