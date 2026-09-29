"""Wird von Unreal beim Editor-Start automatisch ausgefuehrt.

Prueft einmalig (nach dem ersten Editor-Tick), ob alle generierten Sprites,
Sounds und die Map existieren, und importiert fehlende Assets.
"""
import unreal

_handle = None


def _run_once(_delta):
    global _handle
    if _handle is not None:
        unreal.unregister_slate_post_tick_callback(_handle)
        _handle = None
    try:
        import sob_import_assets
        sob_import_assets.run(only_missing=True)
    except Exception as exc:  # noqa: BLE001
        unreal.log_error("Streets of Berlin: Asset-Import fehlgeschlagen: %s" % exc)


_handle = unreal.register_slate_post_tick_callback(_run_once)
