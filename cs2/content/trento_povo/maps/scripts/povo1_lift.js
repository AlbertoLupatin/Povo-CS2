// Povo 1 reception lift. The train owns movement and reports docking.
import { Instance } from "cs_script/point_script";

const prefix = "povo1_lift_";
const leaves = [0, 1];
let floor = 0;
let destination = 0;
let phase = "starting";
let resetGeneration = 0;
const completed = new Set();

function send(name, input, value = "") {
    Instance.EntFireAtName({ name: prefix + name, input, value });
}

function doors(input) {
    for (const leaf of leaves) send(`gate_${floor}_${leaf}`, input);
}

function open() {
    phase = "opening";
    completed.clear();
    doors("Open");
}

// CS2 recreates the train and doors on round cleanup and keeps this script.
function reset() {
    const generation = ++resetGeneration;
    floor = destination = 0;
    phase = "starting";
    Instance.Delay(0.75).then(() => {
        if (generation === resetGeneration) open();
    });
}

Instance.OnActivate(reset);
Instance.OnBeginRoundRestart(reset);
Instance.OnRoundStart(() => {
    if (phase === "starting") reset();
});

Instance.OnScriptInput("Arrived", () => {
    if (phase !== "travel") return;
    floor = destination;
    phase = "docking";
    const stop = `stop_${floor}`;
    // The track train stops within a tolerance of its path node. Seat the
    // platform on the exact sill before opening either landing door.
    send("car", "TeleportToPathNode", prefix + stop);
    const generation = resetGeneration;
    Instance.Delay(0.15).then(() => {
        if (generation !== resetGeneration) return;
        const car = Instance.FindEntityByName(prefix + "car");
        const landing = Instance.FindEntityByName(prefix + stop);
        if (car && landing && Math.abs(car.GetAbsOrigin().z - landing.GetAbsOrigin().z) < 0.5) open();
    });
});

for (const stop of [0, 1, 2]) {
    Instance.OnScriptInput(`Request${stop}`, () => {
        if (phase !== "idle" || stop === floor) return;
        destination = stop;
        phase = "closing";
        completed.clear();
        doors("Close");
    });
    Instance.OnScriptInput(`Blocked${stop}`, () => {
        if (phase === "closing" && stop === floor) open();
    });
    for (const leaf of leaves) {
        Instance.OnScriptInput(`Closed${stop}${leaf}`, () => {
            if (phase !== "closing" || stop !== floor) return;
            completed.add(leaf);
            if (completed.size === leaves.length) {
                phase = "travel";
                send("car", "MoveToPathNode", prefix + `stop_${destination}`);
            }
        });
        Instance.OnScriptInput(`Opened${stop}${leaf}`, () => {
            if (phase !== "opening" || stop !== floor) return;
            completed.add(leaf);
            if (completed.size === leaves.length) phase = "idle";
        });
    }
}
