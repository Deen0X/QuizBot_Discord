import requests
import logging
from typing import Any, Optional

from utils import Utils  # Asumimos que existe

class LLMConnector:
    def __init__(self, config_path='config.json'):
        config_data = Utils.load_config(config_path)
        if not config_data:
            raise RuntimeError("No se pudo cargar la configuración.")
        print(f"init LLMConnector...")
        self.config: dict[str, Any] = config_data
        self.llm_info = self._get_selected_llm_config()

    def _get_selected_llm_config(self):
        selected = self.config.get("selected_llm")
        llms = self.config.get("llms", {})
        if not selected or selected not in llms:
            raise ValueError(f"LLM seleccionado '{selected}' no encontrado en configuración.")
        #print(f"llm selected: {selected}")
        return llms[selected]

    def generate(self, prompt: str) -> Optional[str]:
        tipo = self.llm_info.get("type")
        if tipo in ("local", "api"):
            return self._generate_http(prompt)
        else:
            raise ValueError(f"Tipo de LLM no soportado: {tipo}")

    def _generate_http(self, prompt: str) -> Optional[str]:
        url = self.llm_info.get("endpoint")
        method = self.llm_info.get("method", "POST").upper()
        headers = self.llm_info.get("headers", {}).copy()
        payload_template = self.llm_info.get("payload_template", {})
        api_key_info = self.llm_info.get("api_key_info", {})

        if not url:
            logging.error("No se ha configurado el endpoint para el LLM.")
            return None

        # Insertar prompt en payload
        payload = self._fill_prompt_in_payload(payload_template, prompt)

        # Insertar API key en headers, params o payload según config
        url, headers, payload = self._insert_api_key(url, headers, payload, api_key_info)

        try:
            if method == "POST":
                #print(f"post url:{url}\npayload={payload}\nheaders={headers}")
                response = requests.post(url, json=payload, headers=headers, timeout=30)
            elif method == "GET":
                #print(f"GET url:{url}\npayload={payload}\nheaders={headers}")
                response = requests.get(url, params=payload, headers=headers, timeout=30)
            else:
                logging.error(f"Método HTTP no soportado: {method}")
                return None

            print(f"raise_for_status...")
            response.raise_for_status()

            response_path = self.llm_info.get("response_path", ["response"])
            #print(f"response_path={response_path}")
            return self._extract_from_response(response.json(), response_path)
        except Exception as e:
            logging.error(f"Error al llamar API LLM: {str(e)}")
            return None

    def _fill_prompt_in_payload(self, payload_template: dict, prompt: str) -> dict:
        def recurse_fill(obj):
            if isinstance(obj, dict):
                return {k: recurse_fill(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [recurse_fill(i) for i in obj]
            elif isinstance(obj, str) and "{prompt}" in obj:
                return obj.replace("{prompt}", prompt)
            else:
                return obj
        return recurse_fill(payload_template)

    def _insert_api_key(self, url: str, headers: dict, payload: dict, api_key_info: dict):
        """
        api_key_info: dict con keys:
            - "key_name": nombre del parámetro para la API key
            - "key_value": valor de la API key
            - "location": "header" | "query" | "body"
        """
        if not api_key_info:
            return url, headers, payload

        key_name = api_key_info.get("key_name")
        key_value = api_key_info.get("key_value")
        location = api_key_info.get("location", "header").lower()

        if not key_name or not key_value:
            return url, headers, payload

        if location == "header":
            headers[key_name] = key_value
        elif location == "query":
            from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

            url_parts = urlparse(url)
            query = parse_qs(url_parts.query)
            query[key_name] = [key_value]
            new_query = urlencode(query, doseq=True)
            url = urlunparse(url_parts._replace(query=new_query))
        elif location == "body":
            # Insertar en payload (asumiendo dict)
            payload[key_name] = key_value

        return url, headers, payload

    def _extract_from_response(self, data: dict, path: list[str]) -> Optional[str]:
        current = data
        try:
            for p in path:
                if isinstance(p, int) and isinstance(current, list):
                    current = current[p]
                elif isinstance(p, str) and isinstance(current, dict):
                    current = current.get(p)
                else:
                    return None
            if isinstance(current, str):
                return current.strip()
            return str(current).strip()
        except Exception:
            return None


if __name__ == "__main__":
    print(f"connector...")
    connector = LLMConnector()

    respuesta = connector.generate("Explica la ley de Newton.")
    print("Respuesta del LLM:\n", respuesta)
