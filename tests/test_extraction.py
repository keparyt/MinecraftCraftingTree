from recipegraph.extractors.generic import extract_recipe, extract_tag
from recipegraph.models import SourceRecord


def test_shaped_recipe_normalizes_inputs_and_output(tmp_path):
    path = tmp_path / "recipe.json"
    path.write_text(
        '{"type":"minecraft:crafting_shaped","pattern":["AA"],"key":{"A":{"tag":"c:ingots/iron"}},"result":{"id":"test:plate","count":1}}',
        encoding="utf-8",
    )
    source = SourceRecord(source_type="datapack", location=str(path), logical_path="data/test/recipe/plate.json")
    recipe = extract_recipe(source)
    assert recipe.recipe_id == "test:plate"
    assert recipe.status == "verified"
    assert len(recipe.inputs) == 2
    assert all(value.kind == "tag" and value.tag_id == "c:ingots/iron" for value in recipe.inputs)
    assert recipe.outputs[0].item_id == "test:plate"


def test_unknown_recipe_type_is_preserved(tmp_path):
    path = tmp_path / "recipe.json"
    path.write_text('{"type":"create:mixing","ingredients":[],"results":[]}', encoding="utf-8")
    source = SourceRecord(source_type="datapack", location=str(path), logical_path="data/create/recipe/mix.json")
    recipe = extract_recipe(source)
    assert recipe.status == "unsupported"
    assert recipe.raw_data["type"] == "create:mixing"
    assert recipe.warnings


def test_tag_normalization(tmp_path):
    path = tmp_path / "tag.json"
    path.write_text('{"values":["minecraft:iron_ingot","#c:ingots/iron"]}', encoding="utf-8")
    source = SourceRecord(source_type="datapack", location=str(path), logical_path="data/c/tags/item/ingots/iron.json")
    tag = extract_tag(source)
    assert tag.registry == "item"
    assert tag.tag_id == "c:ingots/iron"
    assert tag.values == ["minecraft:iron_ingot", "#c:ingots/iron"]
