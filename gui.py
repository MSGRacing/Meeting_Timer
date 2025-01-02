import math
from tzlocal import get_localzone
from datetime import datetime
import tkinter as tk


 # Fonction pour dessiner l'horloge analogique
def draw_clock(canvas,root):
    # Obtenir l'heure locale (en utilisant pytz pour gérer le fuseau horaire)
    
    timezone = get_localzone()  # Récupère le fuseau horaire local
    now_local = datetime.now(timezone)

    hours = now_local.hour % 12  # Format 12 heures
    minutes = now_local.minute
    seconds = now_local.second

    # Effacer le canvas
    canvas.delete("all")

    # Dimensions du cadran
    center = 150
    radius = 100

    # Tracer le cercle de l'horloge
    canvas.create_oval(center - radius, center - radius, center + radius, center + radius, outline="black", width=4)

    # Tracer les numéros autour du cadran
    for i in range(1, 13):
        angle = math.radians((i - 3) * 30)  # 30° entre chaque numéro (3 heures = 90°)
        x = center + radius * 0.8 * math.cos(angle)
        y = center + radius * 0.8 * math.sin(angle)
        canvas.create_text(x, y, text=str(i), font=("Arial", 12, "bold"), fill="black")

    # Calculer les angles pour les aiguilles
    second_angle = (seconds / 60) * 360
    minute_angle = (minutes / 60) * 360
    hour_angle = (hours / 12) * 360 + (minutes / 60) * 30  # Ajouter l'effet des minutes à l'aiguille des heures

    # Calculer les positions des aiguilles
    second_x = center + radius * 0.9 * math.sin(math.radians(second_angle))
    second_y = center - radius * 0.9 * math.cos(math.radians(second_angle))

    minute_x = center + radius * 0.7 * math.sin(math.radians(minute_angle))
    minute_y = center - radius * 0.7 * math.cos(math.radians(minute_angle))

    hour_x = center + radius * 0.5 * math.sin(math.radians(hour_angle))
    hour_y = center - radius * 0.5 * math.cos(math.radians(hour_angle))

    # Tracer les aiguilles
    canvas.create_line(center, center, second_x, second_y, width=2, fill="red", arrow=tk.LAST)
    canvas.create_line(center, center, minute_x, minute_y, width=4, fill="blue", arrow=tk.LAST)
    canvas.create_line(center, center, hour_x, hour_y, width=6, fill="black", arrow=tk.LAST)

    # Mettre à jour l'horloge toutes les secondes
    root.after(500, lambda: draw_clock(canvas, root))
