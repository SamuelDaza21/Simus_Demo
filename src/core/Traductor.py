import json
import os

class Traductor:
    def __init__(self, idioma="es"):
        ruta = os.path.join(os.path.dirname(__file__), "Locales", f"{idioma}.json")
        self.idioma=idioma
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                self.textos = json.load(f)
        except FileNotFoundError:
            # Fallback a español si no existe
            ruta_es = os.path.join(os.path.dirname(__file__), "Locales", "es.json")
            with open(ruta_es, "r", encoding="utf-8") as f:
                self.textos = json.load(f)
    
    def t(self, llave):
        return self.textos.get(llave, llave)
    
    def get_direction(self):
        return self.textos.get("direction", "ltr")
    
    def get_date_format(self):
        return self.textos.get("date_format", "DD/MM/YYYY")
    
    def get_currency_symbol(self):
        return self.textos.get("currency_symbol", "COP")

    def get_current_language(self):
        return self.idioma  # suponiendo que guardas el idioma en __init__


if __name__ == "__main__":
    traductor = Traductor("es")
    print(traductor.t("Welcome"))
    traductor2 = Traductor("en")
    print(traductor2.t("Welcome"))