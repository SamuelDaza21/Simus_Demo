import json
import os
import time

# Un solo archivo de calibración en la raíz del proyecto
CALIBRATION_FILE = "calibration.json"
TUTORIAL_COMPLETED_FILE = "tutorial_completed.txt"

# Modo DEMO: no se escribe nada en disco y el tutorial se muestra siempre.
DEMO_MODE = os.environ.get("DEMO_MODE") == "true"


def get_project_root() -> str:
    """Obtiene la raíz del proyecto (directorio padre de src/)."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def load_calibration_disk(sesion_id=None):
    """Lee calibration.json de la raíz o None si no existe / error."""
    if DEMO_MODE:
        return None
    filename = f"calibration_{sesion_id}.json" if sesion_id else CALIBRATION_FILE
    path = os.path.join(get_project_root(), filename)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


class CalibrationService:
    """Persistencia de calibración y estado del tutorial."""

    def __init__(self, id_sesion: int = None):
        self.id_sesion = id_sesion

    def calibration_path(self) -> str:
        filename = f"calibration_{self.id_sesion}.json" if self.id_sesion else CALIBRATION_FILE
        return os.path.join(get_project_root(), filename)

    def completed_flag_path(self) -> str:
        filename = f"tutorial_completed_{self.id_sesion}.txt" if self.id_sesion else TUTORIAL_COMPLETED_FILE
        return os.path.join(get_project_root(), filename)

    def is_completed(self) -> bool:
        if DEMO_MODE:
            return False
        return os.path.exists(self.completed_flag_path())

    def mark_tutorial_completed(self) -> None:
        if DEMO_MODE:
            return
        with open(self.completed_flag_path(), "w", encoding="utf-8") as f:
            f.write("completed")

    def save_calibration(
        self,
        sensitivity: float,
        blink_threshold: float,
        base_face_position: tuple,
        rango_cabeza_x=None,
        rango_cabeza_y=None,
        centro_cabeza=None,
    ) -> None:
        if DEMO_MODE:
            return
        data = {
            "sensitivity": sensitivity,
            "blink_threshold": blink_threshold,
            "base_face_position": list(base_face_position),
            "timestamp": time.time(),
        }
        if rango_cabeza_x is not None and rango_cabeza_y is not None:
            data["rango_cabeza_x"] = list(rango_cabeza_x)
            data["rango_cabeza_y"] = list(rango_cabeza_y)
        if centro_cabeza is not None:
            data["centro_cabeza"] = list(centro_cabeza)
        with open(self.calibration_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self.mark_tutorial_completed()
        self._sync_tutorial_config_json(data)

    def _sync_tutorial_config_json(self, data: dict) -> None:
        """Actualiza tutorial_config.json en la raíz del proyecto si existe el directorio."""
        try:
            root = get_project_root()
            path = os.path.join(root, "tutorial_config.json")
            payload = {
                "completado": True,
                "sensibilidad": data.get("sensitivity"),
                "umbral_parpadeo": data.get("blink_threshold"),
                "timestamp": data.get("timestamp"),
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            pass

    def remove_calibration_file(self) -> None:
        try:
            os.remove(self.calibration_path())
        except OSError:
            pass
