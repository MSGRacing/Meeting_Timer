from datetime import datetime
import pytz
from tzlocal import get_localzone

# Obtenir le fuseau horaire local automatiquement
local_timezone = get_localzone()  # Récupère le fuseau horaire local
utc_timezone = pytz.utc  # UTC est l'heure de référence du serveur

# Calculer le temps restant avant le prochain meeting
def get_remaining_time(meeting_time):
    remaining = meeting_time - datetime.utcnow()
    return str(remaining).split('.')[0]  # Afficher l'heure et les minutes sans les microsecondes

#Supprimer les microsecondes de la date
def remove_microseconds(date_str):
# Si la chaîne contient des microsecondes (après un point), couper les micro secondes
    if '.' in date_str:
        date_str = date_str[:date_str.find('.')]  # Couper après le point
    return date_str

#Convertit l'heure utc en local timezone
def convert_utc_to_local(utc_time):

    # Ensure the passed time is in UTC
    if utc_time.tzinfo is None:  # Check if the datetime is naive (no timezone info)
        utc_time = pytz.utc.localize(utc_time)  # Localize the naive datetime to UTC
    
    # Convert the UTC time to the local timezone
    local_time = utc_time.astimezone(local_timezone)
    
    # Return the time in 'HH:MM' format
    return local_time

# Récupérer l'heure de fin et calculer la durée
def get_duration(start_time, end_time):
    duration = end_time - start_time
    # Retourner la durée sous un format lisible (ex : "01:30" pour 1h30)
    return str(duration).split('.')[0]