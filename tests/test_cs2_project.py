import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "cs2_project", ROOT / "tools" / "cs2_project.py"
)
cs2_project = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(cs2_project)


class CS2ProjectTests(unittest.TestCase):
    def make_cs2_root(self, root: Path) -> Path:
        cs2 = root / "cs2-install"
        (cs2 / "content" / "csgo").mkdir(parents=True)
        (cs2 / "game" / "csgo").mkdir(parents=True)
        (cs2 / "game" / "csgo" / "gameinfo.gi").write_text("game", encoding="utf-8")
        compiler = cs2 / "game" / "bin" / "win64" / "resourcecompiler.exe"
        compiler.parent.mkdir(parents=True)
        compiler.write_bytes(b"compiler")
        return cs2

    def make_repo(self, root: Path) -> Path:
        repo = root / "repo"
        content = repo / "cs2" / "content" / cs2_project.ADDON_NAME
        game = repo / "cs2" / "game" / cs2_project.ADDON_NAME
        (content / "maps").mkdir(parents=True)
        (content / "maps" / "trento_povo.vmap").write_bytes(b"vmap")
        game.mkdir(parents=True)
        (game / "addoninfo.txt").write_text("addon", encoding="utf-8")
        for source, _destination in (*cs2_project.GENERATED_CONTENT, *cs2_project.GENERATED_GAME):
            path = repo / source
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(str(source).encode("utf-8"))
        return repo

    def test_parse_steam_library_paths_deduplicates(self):
        text = r'''
        "path" "C:\\Program Files (x86)\\Steam"
        "path" "D:\\Games\\SteamLibrary"
        "path" "D:\\Games\\SteamLibrary"
        '''
        self.assertEqual(
            cs2_project.parse_steam_library_paths(text),
            [Path(r"C:\Program Files (x86)\Steam"), Path(r"D:\Games\SteamLibrary")],
        )

    def test_explicit_cs2_root_is_discovered(self):
        with tempfile.TemporaryDirectory() as temporary:
            cs2 = self.make_cs2_root(Path(temporary))
            self.assertEqual(cs2_project.discover_cs2_root(cs2), cs2.resolve())

    def test_insert_blockout_prop_is_deterministic_and_idempotent(self):
        source = '''
"$prefix_element$"
{
    "map_asset_references" "string_array"
    [
        "materials/example.vmat"
    ]
}
"CMapRootElement"
{
    "world" "CMapWorld"
    {
        "nodeID" "int" "3"
        "children" "element_array"
        [
        ]
    }
}
'''
        updated = cs2_project.insert_blockout_prop(source)
        self.assertIn(
            f'"model" "string" "{cs2_project.BLOCKOUT_MODEL}"', updated
        )
        self.assertIn(f'"{cs2_project.BLOCKOUT_MODEL}",', updated)
        self.assertIn('"nodeID" "int" "4"', updated)
        self.assertIn(
            f'"angles" "qangle" "{cs2_project.BLOCKOUT_ANGLES}"', updated
        )
        self.assertEqual(cs2_project.insert_blockout_prop(updated), updated)

    def test_relocate_playtest_entities_is_deterministic_and_idempotent(self):
        def entity(classname, origin="0 0 0", extra="", brush=False):
            child = (
                f'''\n        "CMapMesh"\n        {{\n            "origin" "vector3" "{origin}"\n            "angles" "qangle" "0 0 0"\n        }}'''
                if brush
                else ""
            )
            return f'''\n"CMapEntity"\n{{{child}\n    "entity_properties" "EditGameClassProps"\n    {{\n        "classname" "string" "{classname}"\n        {extra}\n    }}\n    "origin" "vector3" "{origin}"\n    "angles" "qangle" "0 90 0"\n}}\n'''

        source = "".join(
            entity(classname)
            for classname in (
                ["info_player_counterterrorist"] * 6
                + ["info_player_terrorist"] * 6
            )
        )
        source += entity("func_bomb_target", "512 640 32", brush=True)
        for team in ("3", "2", "0"):
            source += entity(
                "func_buyzone", "96 -320 32", f'"TeamNum" "string" "{team}"', True
            )

        updated = cs2_project.relocate_playtest_entities(source)

        for classname, layout in cs2_project.PLAYTEST_SPAWNS.items():
            for origin, angles in layout:
                self.assertIn(f'"origin" "vector3" "{origin}"', updated)
                self.assertIn(f'"angles" "qangle" "{angles}"', updated)
        self.assertEqual(updated.count(cs2_project.PLAYTEST_OBJECTIVE_ORIGIN), 4)
        for team in ("3", "2"):
            self.assertEqual(
                updated.count(cs2_project.PLAYTEST_BUYZONE_ORIGINS[team]), 2
            )
        self.assertEqual(cs2_project.relocate_playtest_entities(updated), updated)

    def test_insert_lightmap_resolution_volume_is_deterministic_and_idempotent(self):
        source = '''
"$prefix_element$"
{
    "map_asset_references" "string_array"
    [
        "materials/tools_postprocess_volume.vmat"
    ]
}
"CMapRootElement"
{
    "world" "CMapWorld"
    {
        "nodeID" "int" "1"
        "children" "element_array"
        [
            "CMapEntity"
            {
                "id" "elementid" "10000000-0000-0000-0000-000000000000"
                "nodeID" "int" "2"
                "referenceID" "uint64" "0x1"
                "children" "element_array"
                [
                    "CMapMesh"
                    {
                        "id" "elementid" "20000000-0000-0000-0000-000000000000"
                        "nodeID" "int" "3"
                        "referenceID" "uint64" "0x2"
                        "material" "string" "materials/models/props_junk/trashclusters01.vmat"
                        "meshData" "DmElement"
                        {
                            "id" "elementid" "30000000-0000-0000-0000-000000000000"
                        }
                        "origin" "vector3" "1 2 3"
                        "angles" "qangle" "1 2 3"
                        "scales" "vector3" "1 1 1"
                    }
                ]
                "entity_properties" "EditGameClassProps"
                {
                    "id" "elementid" "40000000-0000-0000-0000-000000000000"
                    "classname" "string" "post_processing_volume"
                }
                "origin" "vector3" "1 2 3"
                "angles" "qangle" "0 0 0"
                "scales" "vector3" "1 1 1"
            }
        ]
    }
}
'''
        updated = cs2_project.insert_lightmap_resolution_volume(source)
        self.assertEqual(updated.count(cs2_project.LIGHTMAP_RESOLUTION_MATERIAL), 2)
        self.assertEqual(updated.count('"CMapMesh"'), 2)
        self.assertIn('"nodeID" "int" "4"', updated)
        self.assertIn(f'"origin" "vector3" "{cs2_project.PLAYTEST_CENTER}"', updated)
        self.assertEqual(
            cs2_project.insert_lightmap_resolution_volume(updated), updated
        )

    def test_map_compile_refreshes_model_before_map(self):
        with tempfile.TemporaryDirectory() as temporary:
            cs2 = self.make_cs2_root(Path(temporary))
            content = (
                cs2 / "content" / "csgo_addons" / cs2_project.ADDON_NAME
            )
            model = content / "models" / "povo" / "povo_blockout.vmdl"
            map_source = content / "maps" / "trento_povo.vmap"
            model.parent.mkdir(parents=True)
            map_source.parent.mkdir(parents=True)
            model.write_text("model", encoding="utf-8")
            map_source.write_text("map", encoding="utf-8")
            calls = []

            def record(command, check):
                calls.append(Path(command[-1]))
                return mock.Mock(returncode=0)

            with mock.patch.object(cs2_project.subprocess, "run", side_effect=record):
                self.assertEqual(cs2_project.compile_resources(cs2, "map"), 0)
            self.assertEqual(calls, [model, map_source])

    def test_deploy_is_additive_and_records_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cs2 = self.make_cs2_root(root)
            repo = self.make_repo(root)
            installed = (
                cs2
                / "content"
                / "csgo_addons"
                / cs2_project.ADDON_NAME
                / "keep.txt"
            )
            installed.parent.mkdir(parents=True)
            installed.write_text("keep", encoding="utf-8")

            records = cs2_project.deploy(cs2, repo_root=repo)

            self.assertTrue(installed.is_file())
            deployed_map = installed.parent / "maps" / "trento_povo.vmap"
            self.assertEqual(deployed_map.read_bytes(), b"vmap")
            for source, destination in cs2_project.GENERATED_GAME:
                deployed = cs2 / "game/csgo_addons" / cs2_project.ADDON_NAME / destination
                self.assertEqual(deployed.read_bytes(), (repo / source).read_bytes())
            manifest = json.loads(
                (installed.parent / "trento_deploy_manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(manifest["addon"], cs2_project.ADDON_NAME)
            self.assertTrue(records)
            self.assertTrue(all(record["sha256"] for record in records))

    def test_deploy_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cs2 = self.make_cs2_root(root)
            repo = self.make_repo(root)
            records = cs2_project.deploy(cs2, repo_root=repo, dry_run=True)
            target = cs2 / "content" / "csgo_addons" / cs2_project.ADDON_NAME
            self.assertTrue(records)
            self.assertFalse(target.exists())
            self.assertFalse((cs2 / "game/csgo_addons" / cs2_project.ADDON_NAME).exists())

    def test_all_compile_preflights_radar_before_starting_model_build(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cs2 = self.make_cs2_root(root)
            repo = self.make_repo(root)
            cs2_project.deploy(cs2, repo_root=repo)
            content, _game = cs2_project._installed_targets(cs2)
            model = content / "models/povo/povo_blockout.vmdl"
            model.parent.mkdir(parents=True, exist_ok=True)
            model.write_text("model")
            (content / cs2_project.RADAR_TEXTURES[-1]).unlink()
            with mock.patch.object(cs2_project.subprocess, "run") as run:
                with self.assertRaisesRegex(cs2_project.ProjectError, "Deploy before compiling"):
                    cs2_project.compile_resources(cs2, "all", repo_root=repo)
            run.assert_not_called()

    def test_all_compile_restores_custom_radar_after_map_generation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cs2 = self.make_cs2_root(root)
            repo = self.make_repo(root)
            content, game = cs2_project._installed_targets(cs2)
            model = content / "models/povo/povo_blockout.vmdl"
            model.parent.mkdir(parents=True)
            model.write_text("model", encoding="utf-8")
            cs2_project.deploy(cs2, repo_root=repo)
            calls = []

            def compile_and_generate(command, check):
                resource = Path(command[-1])
                calls.append(resource)
                if resource.suffix == ".vmap":
                    (game / cs2_project.RADAR_OVERVIEW).write_text("auto-generated overview")
                return mock.Mock(returncode=0)

            with mock.patch.object(cs2_project.subprocess, "run", side_effect=compile_and_generate):
                self.assertEqual(cs2_project.compile_resources(cs2, "all", repo_root=repo), 0)
            self.assertEqual(calls, [model, content / "maps/trento_povo.vmap",
                                     *(content / texture for texture in cs2_project.RADAR_TEXTURES)])
            self.assertEqual((game / cs2_project.RADAR_OVERVIEW).read_bytes(),
                             (repo / "exports/povo_radar/trento_povo.txt").read_bytes())

    def test_radar_compile_failure_stops_and_does_not_replace_overview(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cs2 = self.make_cs2_root(root)
            repo = self.make_repo(root)
            cs2_project.deploy(cs2, repo_root=repo)
            _content, game = cs2_project._installed_targets(cs2)
            overview = game / cs2_project.RADAR_OVERVIEW
            overview.write_text("existing overview")
            with mock.patch.object(cs2_project.subprocess, "run", return_value=mock.Mock(returncode=7)) as run:
                self.assertEqual(cs2_project.compile_resources(cs2, "radar", repo_root=repo), 7)
            self.assertEqual(run.call_count, 1)
            self.assertEqual(overview.read_text(), "existing overview")


if __name__ == "__main__":
    unittest.main()

