import requests
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

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

hoy = pd.Timestamp.now().normalize()  # Fecha de hoy sin hora
hace_7_dias = hoy - pd.Timedelta(days=11)  # Fecha hace 7 días sin hora

# Filtrar las filas de los últimos 7 días
cruce_hoy = cruce[(cruce['obsDt'].dt.normalize() >= hace_7_dias) & 
                     (cruce['obsDt'].dt.normalize() <= hoy)]

#cruce_hoy = cruce[cruce['obsDt'].dt.normalize()==cruce_7_dias]

emails_df = pd.DataFrame({
    'email': [
    ]
})


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

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

#cruce = cruce_hoyhead(50)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               
# Agregamos una nueva columna de coordenadas
cruce_hoy["coordinates"] = cruce_hoy["lat"].astype(str) + ", " + cruce_hoy["lng"].astype(str)

# Aplicamos la función para obtener geo_tags
#cruce_hoy["geo_tag"] = cruce_hoy.apply(lambda row: get_geo_tag(row["lat"], row["lng"], driver), axis=1)
cruce_1 = cruce_hoy.groupby('Nombre comun', as_index=False)['howMany'].sum()
cruce_1 = cruce_1.rename(columns={'howMany': 'Avistamientos'})
#cruce_1 = cruce_hoy.groupby('Nombre comun').size().reset_index(name = "Avistamientos")
cruce_1 = cruce_1.nlargest(2000, 'Avistamientos')
# Cerramos el navegador
driver.quit()



def enviar_tabla_cruce_1(destinatarios, asunto, cuerpo, cruce_1):
    try:
        # Convertir cruce_1 a tabla HTML
        tabla_html = cruce_1.to_html(index=False, border=1, classes='table', justify='center')

        # Crear mensaje con la tabla incluida en el cuerpo
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = ", ".join(destinatarios)  # Destinatarios separados por comas
        msg['Subject'] = asunto

        # Adjuntar el cuerpo con la tabla
        html_cuerpo = f"""
        <html>
            <body>
                <p>{cuerpo}</p>
                {tabla_html}
            </body>
        </html>
        """
        msg.attach(MIMEText(html_cuerpo, 'html'))

        # Conexión al servidor SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL, PASSWORD)
            server.send_message(msg)

        print(f"Correo enviado a: {', '.join(destinatarios)}")

    except Exception as e:
        print(f"Error al enviar correo: {e}")



def obtener_correos_de_dataframe(emails_df):
    if len(emails_df) > 10:
        print("El DataFrame contiene más de 10 correos. Solo se usarán los primeros 10.")
    return emails_df['email'].head(10).tolist()  # Selecciona hasta los primeros 10 correos


# Convertir `cruce_1` en tabla y enviarla
asunto_cruce_1 = "Resumen de aves vistas durante la semana"
cuerpo_cruce_1 = "Adjuntamos la tabla con el conteo por especie:"
destinatarios = obtener_correos_de_dataframe(emails_df)

# Asegurarse de que haya destinatarios
if destinatarios:
    enviar_tabla_cruce_1(destinatarios, asunto_cruce_1, cuerpo_cruce_1, cruce_1)
else:
    print("No se enviará el correo ya que no se encontraron destinatarios.")
    