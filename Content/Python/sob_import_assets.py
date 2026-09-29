"""Importiert die generierten Assets aus Art/Generated in das Unreal-Projekt.

Manuell ausfuehren (z.B. nach erneutem Generieren mit Tools/ArtGen):
    Editor -> Tools -> Execute Python Script... -> Content/Python/sob_import_assets.py
oder in der Python-Konsole des Editors:
    import sob_import_assets, importlib; importlib.reload(sob_import_assets); sob_import_assets.run(only_missing=False)

Erzeugt:
    /Game/Sprites/<Ordner>/Textures/T_<Name>   Texturen (UI-Kompression, keine Mipmaps)
    /Game/Sprites/<Ordner>/<Name>              Paper2D-Sprites
    /Game/Audio/<Name>                         Sounds (Musik loopt)
    /Game/Maps/Stage1                          leere Map (der GameMode baut alles zur Laufzeit)
"""
import json
import os

import unreal

MAP_PATH = "/Game/Maps/Stage1"
SPRITE_MATERIAL = "/Paper2D/TranslucentUnlitSpriteMaterial"


def _art_dir():
    project = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
    return os.path.join(project, "Art", "Generated")


def _exists(path):
    return unreal.EditorAssetLibrary.does_asset_exist(path)


def _import(files_and_targets):
    tasks = []
    for filename, dest_path, dest_name in files_and_targets:
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", filename)
        task.set_editor_property("destination_path", dest_path)
        task.set_editor_property("destination_name", dest_name)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("save", False)
        tasks.append(task)
    if tasks:
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)


def _configure_texture(tex):
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property("never_stream", True)
    tex.set_editor_property("srgb", True)


def _ensure_map():
    if _exists(MAP_PATH):
        return
    try:
        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        if les.new_level(MAP_PATH):
            les.save_current_level()
            unreal.log("Streets of Berlin: Map %s angelegt." % MAP_PATH)
    except Exception as exc:  # noqa: BLE001
        unreal.log_warning("Map konnte nicht angelegt werden (%s). Bitte manuell eine leere Map %s anlegen." %
                           (exc, MAP_PATH))


def run(only_missing=True):
    art = _art_dir()
    manifest_path = os.path.join(art, "manifest.json")
    if not os.path.exists(manifest_path):
        unreal.log_warning("Streets of Berlin: %s fehlt. Bitte zuerst 'python Tools/ArtGen/generate_all.py' "
                           "ausfuehren." % manifest_path)
        return

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    sprites = [s for s in manifest["sprites"]
               if not only_missing or not _exists(s["package"] + "/" + s["name"])]
    sounds = [s for s in manifest["sounds"]
              if not only_missing or not _exists(s["package"] + "/" + s["name"])]

    if sprites or sounds:
        unreal.log("Streets of Berlin: importiere %d Sprites und %d Sounds ..." % (len(sprites), len(sounds)))

    material = unreal.load_asset(SPRITE_MATERIAL)
    total = len(sprites) + len(sounds)
    with unreal.ScopedSlowTask(max(1, total * 2), "Streets of Berlin: Assets importieren") as slow:
        slow.make_dialog(True)

        # 1) Texturen in Paketen zu 40 importieren
        for i in range(0, len(sprites), 40):
            chunk = sprites[i:i + 40]
            slow.enter_progress_frame(len(chunk), "Texturen %d/%d" % (i + len(chunk), len(sprites)))
            _import([(os.path.join(art, s["file"]), s["package"] + "/Textures", "T_" + s["name"]) for s in chunk])

        # 2) Sprites erzeugen
        for s in sprites:
            if slow.should_cancel():
                break
            slow.enter_progress_frame(1, s["name"])
            tex = unreal.load_asset(s["package"] + "/Textures/T_" + s["name"])
            if tex is None:
                unreal.log_warning("Textur fehlt: " + s["name"])
                continue
            _configure_texture(tex)
            unreal.BrawlerEditorLibrary.create_sprite_from_texture(tex, s["package"], s["name"], material)

        # 3) Sounds
        if sounds:
            slow.enter_progress_frame(len(sounds), "Sounds")
            _import([(os.path.join(art, s["file"]), s["package"], s["name"]) for s in sounds])
            for s in sounds:
                wave = unreal.load_asset(s["package"] + "/" + s["name"])
                if wave is not None and s["name"].startswith("MUS_"):
                    wave.set_editor_property("looping", True)

    if sprites or sounds:
        unreal.EditorAssetLibrary.save_directory("/Game/Sprites", only_if_is_dirty=True, recursive=True)
        unreal.EditorAssetLibrary.save_directory("/Game/Audio", only_if_is_dirty=True, recursive=True)
        unreal.log("Streets of Berlin: Import abgeschlossen.")

    _ensure_map()


if __name__ == "__main__":
    run(only_missing=False)
