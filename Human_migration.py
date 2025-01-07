import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

url = 'http://127.0.0.1:5000/aves_migratorias?region=CO'
response = requests.get(url)

if response.status_code == 200:
    data = response.json()  # Convierte el JSON en una lista de diccionarios
    df = pd.DataFrame(data)
    print(df)
    
else:
    print(f"Error: {response.status_code}")

aves = pd.read_excel(r'C:\Users\DISPLBox\Downloads\AVES.xlsx', sheet_name = "Anexo 1")
    
cruce = pd.merge(df, aves[['Nombre 2022', 'Estado']], left_on='sciName', right_on='Nombre 2022')

cruce = cruce[cruce['Estado']=='Migratoria']

cruce.to_excel(r'C:\Users\DISPLBox\Downloads\AVES_result.xlsx')

cruce['email']="ddbdata35@gmail.com"

procedencias = pd.read_excel(r'C:\Users\DISPLBox\Downloads\AVES_result (1).xlsx', sheet_name = "BBDD")

cruce = pd.merge(cruce, procedencias[['Nombre cientifico','Nombre comun', 'Procedencia']], left_on='sciName', right_on='Nombre cientifico')

cruce.to_excel(r'C:\Users\DISPLBox\Downloads\AVES_resultado.xlsx')

cruce['obsDt']= pd.to_datetime(cruce['obsDt'], errors='coerce')

hoy = pd.Timestamp.now().normalize()

cruce = cruce[cruce['obsDt'].dt.normalize()==hoy]

emails_df = pd.DataFrame({
    'email': [
    ]
})

# Configuración del servidor de correo
SMTP_SERVER = "smtp.gmail.com"  # Cambia según el proveedor
SMTP_PORT = 587
# Pegar tu correo y contraseña


def get_geo_tag(lat, long, driver):
    try:
        # Armamos la coordenada
        coordinates = f"{lat}, {long}"
        
        # Abrimos Google Maps y buscamos las coordenadas
        driver.get("https://www.google.com/maps")
        time.sleep(3)
        
        # Ingresamos las coordenadas en el cuadro de búsqueda
        search_box = driver.find_element(By.CSS_SELECTOR, "#searchboxinput")
        search_box.click()
        search_box.clear()
        search_box.send_keys(coordinates)
        
        # Presionamos el botón de búsqueda
        search_button = driver.find_element(By.CSS_SELECTOR, "#searchbox-searchbutton")
        search_button.click()
        
        # Esperamos a que cargue el resultado
        time.sleep(5)
        
        # Extraemos el texto del geo_tag (ejemplo: "Piendamó, Cauca")
        result_element = driver.find_element(By.CSS_SELECTOR, "span.DkEaL")
        full_text = result_element.text  # Obtenemos el texto completo
        extracted_text = " ".join(full_text.split()[1:])  # Ignoramos el primer token (ej. "JFX6+5F4")
        
        return extracted_text  # Retornamos el geo_tag
    except Exception as e:
        print(f"Error procesando {lat}, {long}: {e}")
        return None

# Configuración del WebDriver
driver = webdriver.Chrome()  # Asegúrate de tener ChromeDriver configurado.

cruce = cruce.head(5)

# Agregamos una nueva columna de coordenadas
cruce["coordinates"] = cruce["lat"].astype(str) + ", " + cruce["lng"].astype(str)

cruce["geo_tag"] = cruce.apply(lambda row: get_geo_tag(row["lat"], row["lng"], driver), axis=1)

cruce_1 = cruce.groupby('Nombre comun').size().reset_index(name = "Avistamientos")

driver.quit()

def enviar_correo_grupos(destinatario, asunto, cuerpo, adjunto=None):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = destinatario
        msg['Subject'] = asunto

        msg.attach(MIMEText(cuerpo, 'html'))

        if adjunto:
            with open(adjunto, "rb") as file:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(file.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={adjunto}",
                )
                msg.attach(part)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Encriptar conexión
            server.login(EMAIL, PASSWORD)
            server.send_message(msg)

        print(f"Correo enviado a {destinatario}")

    except Exception as e:
        print(f"Error al enviar correo a {destinatario}: {e}")


chunk_size = 5

for i in range(0, len(cruce), chunk_size):
    cruce_chunk = cruce.iloc[i:i + chunk_size]  # Seleccionar un bloque de 5 registros

    filas_html = ""
    for _, row in cruce_chunk.iterrows():
        filas_html += f"""
        <tr>
            <td>{row['Nombre comun']}</td>
            <td>{row['sciName']}</td>
            <td>{row['Procedencia']}</td>
            <td>{row['obsDt']}</td>
            <td>{row['locName']}</td>
            <td>{row['howMany']}</td>
            <td>{row['geo_tag']}</td>
        </tr>
        """

    tabla_html = f"""
    <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr>
            <th>Nombre comun</th>
            <th>Nombre cientifico</th>
            <th>Procedencia</th>
            <th>Fecha avistado</th>
            <th>Lugar avistado</th>
            <th>Cuantos</th>
            <th>Geo tag</th>
        </tr>
        {filas_html}  
    </table>
    """

    asunto = "Últimos 5 avistamientos del dia de hoy"
    cuerpo = f"""
    <html>
        <body>
            <p>Hola,</p>
            <p>Aquí está la información de los avistamientos:</p>
            {tabla_html}
            <p>Saludos cordiales,</p>
            <p>Tu equipo</p>
        </body>
    </html>
    """


    for _, email_row in emails_df.iterrows():
        destinatario = email_row['email']  # Extraer correo electrónico
        enviar_correo_grupos(destinatario, asunto, cuerpo)    