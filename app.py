import requests
from flask import Flask, send_from_directory, request, jsonify
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Ruta para servir el index.html desde la carpeta dist
@app.route('/', methods=["GET", "POST"])
def serve_index():
    return send_from_directory('dist', 'index.html')

# Ruta para servir los archivos estáticos generados
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('dist', path)


@app.route('/analizar-riesgos', methods=['POST'])
def analizar_riesgos():
    data = request.get_json()
    activo = data.get('activo')
    if not activo:
        return jsonify({"error": "El campo 'activo' es necesario"}), 400

    riesgos, impactos = obtener_riesgos(activo)
    return jsonify({"activo": activo, "riesgos": riesgos, "impactos": impactos})


@app.route('/sugerir-tratamiento', methods=['POST'])
def sugerir_tratamiento():
    data = request.get_json()
    activo = data.get('activo')
    riesgo = data.get('riesgo')
    impacto = data.get('impacto')

    if not activo or not riesgo or not impacto:
        return jsonify({"error": "Los campos 'activo', 'riesgo' e 'impacto' son necesarios"}), 400

    entrada = f"{activo};{riesgo};{impacto}"
    tratamiento = obtener_tratamiento(entrada)

    return jsonify({
        "activo": activo,
        "riesgo": riesgo,
        "impacto": impacto,
        "tratamiento": tratamiento
    })


# --------------------------
# Funciones de interacción con Ollama
# --------------------------
def ollama_generate(model, prompt):
    """Llamada genérica a Ollama"""
    url = "http://localhost:11434/api/generate"
    response = requests.post(url, json={
        "model": model,
        "prompt": prompt,
        "stream": False
    })

    if response.status_code == 200:
        return response.json()["response"]
    else:
        raise Exception(f"Ollama error: {response.text}")


def obtener_riesgos(activo):
    prompt = f"""
    Eres una herramienta de gestión de riesgos basada en ISO 27001.
    El usuario te dará un activo tecnológico y debes responder con 5 riesgos en formato:
    • **Riesgo**: Impacto.
    
    Activo: {activo}
    """
    texto = ollama_generate("llama2:7b", prompt)

    # Extraer riesgos e impactos con regex
    patron = r'\*\*(.+?)\*\*:\s*(.+?)(?=\n|$)'
    resultados = re.findall(patron, texto)

    riesgos = [r[0].strip() for r in resultados]
    impactos = [r[1].strip() for r in resultados]

    return riesgos, impactos


def obtener_tratamiento(entrada):
    prompt = f"""
    Eres una herramienta de gestión de riesgos ISO 27001.
    El usuario te dará un activo, un riesgo y un impacto.
    Responde en máximo 200 caracteres con un tratamiento posible.

    Entrada: {entrada}
    """
    texto = ollama_generate("llama2:7b", prompt)
    return texto.strip()


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5500)
