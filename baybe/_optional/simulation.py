"""Optional xyzpy import."""

from baybe.exceptions import OptionalImportError

try:
    import xyzpy
    from joblib.externals.loky.backend.context import set_start_method
    set_start_method("spawn", force=True)

except ModuleNotFoundError as ex:
    raise OptionalImportError(name="xyzpy", group="simulation") from ex

__all__ = [
    "xyzpy",
]
