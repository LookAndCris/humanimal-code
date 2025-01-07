from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# Cargar la API Key desde una variable de entorno
EBIRD_API_KEY = ''

# Endpoint para obtener las aves que migran a una región
@app.route('/aves_migratorias', methods=['GET'])
def obtener_aves_migratorias():
    region = request.args.get('region', 'CO')  # Código ISO del país (CO = Colombia por defecto)

    # Verificación simple del código de país
    if len(region) != 2:
        return jsonify({'error': 'Invalid region code. Must be a 2-character ISO country code.'}), 400
    
    if not EBIRD_API_KEY:
        return jsonify({'error': 'API Key not found. Please set the EBIRD_API_KEY environment variable.'}), 500

    url = f'https://api.ebird.org/v2/data/obs/{region}/recent'
    headers = {
        'X-eBirdApiToken': EBIRD_API_KEY
    }

    params = {
        'cat': 'species',  # Solo especies
        'back': 30  # Los últimos 30 días
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Manejar errores HTTP

        data = response.json()
        return jsonify(data)
    
    except requests.exceptions.HTTPError as http_err:
        return jsonify({'error': f'HTTP error occurred: {http_err}'}), response.status_code
    except Exception as err:
        return jsonify({'error': f'Other error occurred: {err}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
