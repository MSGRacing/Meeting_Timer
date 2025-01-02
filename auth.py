import msal
from dotenv import load_dotenv
import os

load_dotenv()

# Configuration pour l'API Microsoft Graph
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID')
SCOPES = ['https://graph.microsoft.com/.default']

# Créer une instance de ConfidentialClientApplication de MSAL
def get_msal_app():
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=f'https://login.microsoftonline.com/{TENANT_ID}',
        client_credential=CLIENT_SECRET
    )

def get_access_token(username,password):
    msal_app = get_msal_app()

    result = msal_app.acquire_token_by_username_password(username=username,password=password,scopes=SCOPES)

    if 'access_token' in result:
        return result['access_token']

    # Vérifier si une erreur a été renvoyée
    if 'error' in result:
        # Erreur d'authentification
        if result['error'] == 'invalid_grant':  # "invalid_grant" correspond souvent à un mot de passe incorrect
            raise Exception("Mot de passe ou adresse mail incorrecte")
        else:
            raise Exception(f"Erreur lors de l'obtention du token d'acces : {result['error_description']}")

    raise Exception("Erreur lors de l'obtention du token d'acces")
