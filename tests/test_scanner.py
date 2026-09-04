from pathlib import Path
from zipfile import ZipFile

from recipegraph.scanner.instance import InstanceScanner
from recipegraph.scanner.mods import inspect_mod_jar


def test_inspect_neoforge_jar(tmp_path: Path) -> None:
    mods = tmp_path / "mods"
    mods.mkdir()
    jar = mods / "example.jar"
    metadata = '''modLoader="javafml"\nloaderVersion="[4,)"\nlicense="MIT"\n\n[[mods]]\nmodId="example"\nversion="1.2.3"\ndisplayName="Example"\n'''
    with ZipFile(jar, "w") as archive:
        archive.writestr("META-INF/neoforge.mods.toml", metadata)
    info = inspect_mod_jar(jar)
    assert info.mod_id == "example"
    assert info.version == "1.2.3"
    assert info.loader == "neoforge"


def test_instance_scan_finds_recipe_and_script(tmp_path: Path) -> None:
    mods = tmp_path / "mods"
    mods.mkdir()
    jar = mods / "example.jar"
    recipe = '{"type":"minecraft:crafting_shaped","pattern":["A"],"key":{"A":{"item":"minecraft:iron_ingot"}},"result":{"id":"example:widget","count":1}}'
    metadata = 'modLoader="javafml"\nloaderVersion="[4,)"\n\n[[mods]]\nmodId="example"\nversion="1.0"\n'
    with ZipFile(jar, "w") as archive:
        archive.writestr("META-INF/neoforge.mods.toml", metadata)
        archive.writestr("data/example/recipe/widget.json", recipe)
    (tmp_path / "kubejs" / "server_scripts").mkdir(parents=True)
    (tmp_path / "kubejs" / "server_scripts" / "recipes.js").write_text("ServerEvents.recipes(e => {})", encoding="utf-8")

    result = InstanceScanner(tmp_path).scan()
    assert len(result.mods) == 1
    assert result.mods[0].mod_id == "example"
    assert result.recipe_files == 1
    assert result.script_files == 1
