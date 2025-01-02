import time
import requests
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk
from tkinter import Toplevel
import threading
import webbrowser
from flask import Flask, request, redirect
from urllib.parse import urlencode

from utils import *
from auth import *
from gui import *

next_meetings_cache = []

# URL de l'API (le user_id sera défini dynamiquement)
GRAPH_API_URL = (
    f"https://graph.microsoft.com/v1.0/users/{{user_id}}/calendar/events"
    f"?$orderby=start/dateTime&$filter=start/dateTime ge '{datetime.utcnow().isoformat()}Z'"
)

# Variable pour savoir si l'utilisateur est connecté
is_logged_in = False
is_widget_open = False

# Fonction pour gérer l'action de connexion
def on_login():
    global is_logged_in, access_token
    user_id = user_id_entry.get()
    password_id = password_entry.get()

    if user_id:
        if password_id:
            try:
                # Étape 3: Échanger le code contre un token d'accès
                access_token = get_access_token(user_id,password_id)
                events = get_events(user_id, access_token)

                is_logged_in = True
                update_gui(user_id)
                login_button.config(state=tk.DISABLED)
                logout_button.config(state=tk.NORMAL)
                user_id_entry.delete(0, tk.END)
                password_entry.delete(0, tk.END)

            except Exception as e:
                error_message = str(e)  # L'erreur renvoyée par la fonction get_access_token
                meeting_label.config(text=error_message, font=("Arial", 14, "bold"), foreground="red")
                countdown_label.config(text="")
                for row in treeview.get_children():
                    treeview.delete(row)
                login_button.config(state=tk.NORMAL)
                logout_button.config(state=tk.DISABLED)

        else:
            meeting_label.config(text="Code Manquant.")

    else:
        meeting_label.config(text="Veuillez entrer votre adresse mail et votre mot de passe.")  # Message à l'utilisateur pour lui demander un ID
        countdown_label.config(text="")
        for row in treeview.get_children():
            treeview.delete(row)
        login_button.config(state=tk.NORMAL)  # Réactiver le bouton de connexion
        logout_button.config(state=tk.DISABLED)  # Désactiver le bouton de déconnexion

# Fonction pour gérer l'action de déconnexion
def on_logout():
    global is_logged_in

    # Arrêter le thread de mise à jour
    is_logged_in = False  # Stoppe la boucle de récupération des événements
    user_id_entry.delete(0, tk.END)  # Effacer l'ID utilisateur
    password_entry.delete(0, tk.END) # Effacer le mot de passe
    meeting_label.config(text="Deconnecte.", font=("Arial", 30, "bold"))
    countdown_label.config(text="")
    login_button.config(state=tk.NORMAL)  # Réactiver le bouton de connexion
    logout_button.config(state=tk.DISABLED)  # Désactiver le bouton de déconnexion

    # Vider le tableau après déconnexion
    for row in treeview.get_children():
        treeview.delete(row)

    # Fermer la widget si elle est ouverte
    if is_widget_open:
        widget_window.destroy()

# Récupérer les événements du calendrier
def get_events(user_id, access_token):

    headers = {'Authorization': f'Bearer {access_token}'}

    # Spécifiez une plage temporelle pour calendarView
    start_date = datetime.utcnow().isoformat() + "Z"
    end_date = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"

    url = f"https://graph.microsoft.com/v1.0/users/{user_id}/calendarView?startDateTime={start_date}&endDateTime={end_date}"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        events = [event for event in data.get('value', []) if not event.get('isCancelled', False)]
        
        for event in events:
            online_meeting = event.get('onlineMeeting', {})
            if online_meeting and 'joinUrl' in online_meeting:
                print(f"Lien Teams pour l'evenement '{event['subject']}': {online_meeting['joinUrl']}")

        print("Evenements recuperes :", events)  # Log des événements
        return events
    else:
        raise Exception(f"Erreur lors de la recuperation des evenements : {response.status_code}")

# Trouver les prochains meetings
def get_next_meetings(events, num_meetings=3):
    now = datetime.utcnow()
    upcoming_events = [
        event for event in events
        if datetime.strptime(remove_microseconds(event['start']['dateTime']), '%Y-%m-%dT%H:%M:%S') > now
    ]
    # Trier les événements par heure de début
    upcoming_events.sort(key=lambda x: datetime.strptime(remove_microseconds(x['start']['dateTime']), '%Y-%m-%dT%H:%M:%S'))
    return upcoming_events[:num_meetings]

# Trouver les prochains meetings fin
def get_next_meetings_end(events, num_meetings=3):
    now = datetime.utcnow()
    upcoming_events_end = [
        event for event in events
        if datetime.strptime(remove_microseconds(event['end']['dateTime']), '%Y-%m-%dT%H:%M:%S') > now
    ]
    # Trier les événements par heure de début
    upcoming_events_end.sort(key=lambda x: datetime.strptime(remove_microseconds(x['end']['dateTime']), '%Y-%m-%dT%H:%M:%S'))
    return upcoming_events_end[:num_meetings]

def show_meetings_widget():
    """Affiche une fenetre independante avec le tableau des meetings."""

    global is_widget_open, widget_window, treeview_widget

    if not is_widget_open:
        # Créer une nouvelle fenêtre
        widget_window = Toplevel(root)
        widget_window.title("Tableau des Meetings")
        widget_window.geometry("600x230")
        widget_window.configure(bg="#34495e")

        # Rendre la fenêtre toujours au-dessus
        widget_window.attributes("-topmost", True)
        
        # Ajouter un titre
        title_label = ttk.Label(widget_window, text="Prochains Meetings", font=("Helvetica", 16, "bold"), background="#34495e", foreground="white")
        title_label.pack(pady=10)
        
        # Créer un Treeview pour afficher les meetings
        columns = ("Meeting Name", "Heure", "Duree", "Temps restant")
        treeview_widget = ttk.Treeview(widget_window, columns=columns, show="headings", height=4)
        treeview_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Définir les titres des colonnes
        treeview_widget.heading("Meeting Name", text="Nom du meeting")
        treeview_widget.heading("Heure", text="Heure")
        treeview_widget.heading("Duree", text="Duree")
        treeview_widget.heading("Temps restant", text="Temps restant")
        
        treeview_widget.column("Meeting Name", width=200, anchor="center")
        treeview_widget.column("Heure", width=100, anchor="center")
        treeview_widget.column("Duree", width=100, anchor="center")
        treeview_widget.column("Temps restant", width=100, anchor="center")
        
        # Bouton pour fermer la fenêtre
        def close_widget():
            global is_widget_open
            is_widget_open = False
            widget_window.destroy()
            root.deiconify() # Affiche la page root

        close_button = ttk.Button(widget_window, text="Fermer", command=close_widget)
        close_button.pack(pady=10)

        # Marquer le widget comme ouvert
        is_widget_open = True
    
    # Lancer la mise à jour du tableau
    refresh_widget_table()

def refresh_widget_table():
    """Rafraichit les donnees affichees dans le Treeview."""
    global treeview_widget

    if not is_widget_open:
        return

    # Vider le tableau avant de le remplir à nouveau
    for row in treeview_widget.get_children():
        treeview_widget.delete(row)

    # Ajouter les événements dans le tableau
    for meeting in next_meetings_cache:
        meeting_name = meeting['subject']
        start_time = datetime.strptime(remove_microseconds(meeting['start']['dateTime']), '%Y-%m-%dT%H:%M:%S')
        end_time = datetime.strptime(remove_microseconds(meeting['end']['dateTime']), '%Y-%m-%dT%H:%M:%S')
        duration = get_duration(start_time, end_time)  # Calcul de la durée
        remaining_time = get_remaining_time(start_time)

        start_time_local = convert_utc_to_local(start_time)
        
        teams_link = None
        if 'onlineMeeting' in meeting and meeting['onlineMeeting'] is not None:
            teams_link = meeting['onlineMeeting'].get('joinUrl', None)

        # Insérer les nouvelles informations dans le tableau
        treeview_widget.insert("", "end", values=(meeting_name, start_time_local.strftime('%H:%M'), duration, remaining_time))

    # Planifier le rafraîchissement périodique
    widget_window.after(1000, refresh_widget_table)

    # Fonction double clic pour afficher le lien teams
    treeview_widget.bind("<Double-1>", on_double_click)

def on_double_click(event):
    """Ouvre le lien Teams si un evenement est double-clique."""
    # Obtenez l'élément sélectionné dans le tableau
    selected_item = treeview_widget.selection()
    if selected_item:
        # Récupérer les informations de la ligne sélectionnée
        item_values = treeview_widget.item(selected_item[0], 'values')
        teams_link = item_values[-1]  # Le dernier élément est le lien Teams

        if teams_link:
            # Ouvrir le lien dans le navigateur
            webbrowser.open(teams_link)
        else:
            print("Aucun lien Teams disponible pour cet evenement.")

# Fonction pour mettre à jour l'interface graphique
def update_gui_with_events(next_meeting, next_meeting_end):
      global next_meetings_cache
      next_meetings_cache = next_meeting
      if next_meeting:
           if next_meeting == next_meeting_end:
                meeting_name = next_meeting[0]['subject']
                start_time = datetime.strptime(remove_microseconds(next_meeting[0]['start']['dateTime']), '%Y-%m-%dT%H:%M:%S')
                remaining_time = start_time - datetime.utcnow()
                remaining_time_str = str(remaining_time).split('.')[0]  # Afficher uniquement l'heure et les minutes

                # Mettre à jour les labels avec les informations du prochain meeting
                meeting_label.config(text=f"{meeting_name}", font=("Arial", 30, "bold"), background="#34495e", foreground="white")
                countdown_label.config(text=f"{remaining_time_str}", font=("Arial", 30, "bold"), background="#34495e", foreground="white")

                # Vider le tableau avant de le remplir à nouveau
                for row in treeview.get_children():
                    treeview.delete(row)

                # Ajouter les nouveaux meetings dans le tableau
                for meeting in next_meeting:
                    meeting_name = meeting['subject']
                    start_time = datetime.strptime(remove_microseconds(meeting['start']['dateTime']), '%Y-%m-%dT%H:%M:%S')
                    end_time = datetime.strptime(remove_microseconds(meeting['end']['dateTime']), '%Y-%m-%dT%H:%M:%S')
                    duration = get_duration(start_time, end_time)  # Calcul de la durée
                    remaining_time = get_remaining_time(start_time)

                    start_time_local = convert_utc_to_local(start_time)
                    # Insérer les nouvelles informations dans le tableau
                    treeview.insert("", "end", values=(meeting_name, start_time_local.strftime('%H:%M'), duration, remaining_time))
           else:
                meeting_name = next_meeting_end[0]['subject']
                end_time = datetime.strptime(remove_microseconds(next_meeting_end[0]['end']['dateTime']), '%Y-%m-%dT%H:%M:%S')
                remaining_time = end_time - datetime.utcnow()
                remaining_time_str = str(remaining_time).split('.')[0]  # Afficher uniquement l'heure et les minutes

                if remaining_time.seconds > 300:
                    # Mettre à jour les labels avec les informations du prochain meeting
                    meeting_label.config(text=f"{meeting_name}", font=("Arial", 30, "bold"), background="yellow", foreground="black")
                    countdown_label.config(text=f"{remaining_time_str}", font=("Arial", 30, "bold"), background="yellow", foreground="black")

                else:
                    # Mettre à jour les labels avec les informations du prochain meeting
                    meeting_label.config(text=f"{meeting_name}", font=("Arial", 30, "bold"), background="red", foreground="black")
                    countdown_label.config(text=f"{remaining_time_str}", font=("Arial", 30, "bold"), background="red", foreground="black")


                # Vider le tableau avant de le remplir à nouveau
                for row in treeview.get_children():
                    treeview.delete(row)

                # Ajouter les nouveaux meetings dans le tableau
                for meeting in next_meeting:
                    meeting_name = meeting['subject']
                    start_time = datetime.strptime(remove_microseconds(meeting['start']['dateTime']), '%Y-%m-%dT%H:%M:%S')
                    end_time = datetime.strptime(remove_microseconds(meeting['end']['dateTime']), '%Y-%m-%dT%H:%M:%S')
                    duration = get_duration(start_time, end_time)  # Calcul de la durée
                    remaining_time = get_remaining_time(start_time)

                    start_time_local = convert_utc_to_local(start_time)
                    # Insérer les nouvelles informations dans le tableau
                    treeview.insert("", "end", values=(meeting_name, start_time_local.strftime('%H:%M'), duration, remaining_time))
      else:
            meeting_label.config(text="Aucun meeting a venir.")
            countdown_label.config(text="")

def update_gui(user_id):
    if not is_logged_in:
        return

    # Lancer le thread pour récupérer les événements
    fetch_events_in_thread(user_id)

def show_widget_only():
    """Ferme la fenetre principale et ouvre seulement le widget des meetings."""
    show_meetings_widget()  # Ouvre seulement le widget des meetings
    root.withdraw()  # Cache la fenêtre principale

def fetch_events_in_thread(user_id):
    """Thread worker pour recuperer les evenements."""
    def task():
        while is_logged_in:  # Continue seulement si l'utilisateur est connecté
            try:
                events = get_events(user_id, access_token)
                next_meeting = get_next_meetings(events)
                next_meeting_end = get_next_meetings_end(events)

                # Rafraîchir l'interface uniquement si l'utilisateur est connecté
                if is_logged_in:
                    root.after(500, update_gui_with_events, next_meeting, next_meeting_end)
            except Exception as e:
                # Afficher l'erreur seulement si l'utilisateur est encore connecté
                if is_logged_in:
                    meeting_label.config(text="Erreur", font=("Arial", 14, "bold"))
                    countdown_label.config(text=message)

            time.sleep(0.2)  # Temps d'attente entre chaque rafraîchissement

    thread = threading.Thread(target=task)
    thread.daemon = True
    thread.start()

# Créer l'interface graphique
root = tk.Tk()
root.title("Compteur jusqu'au prochain meeting")

# Définir la taille de la fenêtre et la couleur de fond
root.geometry("600x600")
root.configure(bg="#34495e")

# Créer un frame pour organiser les widgets
frame = ttk.Frame(root, padding="20")
frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Ajouter un titre avec une police plus grosse
title_label = ttk.Label(frame, text="Prochain Meeting", font=("Helvetica", 18, "bold"), background="#34495e", foreground="white")
title_label.grid(row=0, column=0, columnspan=2, pady=10)  # Titre qui occupe les deux colonnes

# Champ de saisie pour l'user_id
user_id_label = ttk.Label(frame, text="Entrez votre adresse mail", font=("Arial", 12))
user_id_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")

user_id_entry = ttk.Entry(frame, font=("Arial", 12), width=25)
user_id_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

#Champ de saisie du code
password_label = ttk.Label(frame, text="Entrez votre mot de passe", font=("Arial", 12))
password_label.grid(row=2, column=0, padx=10, pady=5, sticky="e")

password_entry = ttk.Entry(frame, font=("Arial", 12), width=25, show='*')
password_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

# Bouton pour se connecter
login_button = ttk.Button(frame, text="Se connecter", command=on_login)
login_button.grid(row=3, column=0, padx=10, pady=15, sticky="e")  # Le bouton occupe les deux colonnes

# Bouton de déconnexion
logout_button = ttk.Button(frame, text="Se deconnecter", command=on_logout, state=tk.DISABLED)  # Désactivé par défaut
logout_button.grid(row=3, column=1, padx=10, pady=15, sticky="w") 

# Créer les labels pour afficher le nom du meeting et le temps restant
meeting_label = ttk.Label(frame, text="Chargement...", font=("Arial", 14), background="#34495e", foreground="white")
meeting_label.grid(row=4, column=0, columnspan=2, pady=15)  

countdown_label = ttk.Label(frame, text="Chargement...", font=("Arial", 30, "bold"), background="#34495e", foreground="white")
countdown_label.grid(row=5, column=0, columnspan=2, pady=15)  

# Créer un Canvas pour l'horloge
canvas = tk.Canvas(root, width=300, height=300, bg="#ecf0f1")
canvas.pack(pady=15)

# Créer un tableau à gauche pour afficher les 3 prochains meetings
table_frame = ttk.Frame(frame, padding="20")
table_frame.grid(row=6, column=0, columnspan=2, pady=10) 

# Ajouter un titre pour la liste des meetings
meeting_label2 = ttk.Label(table_frame, text="Prochains Meetings", font=("Helvetica", 14, "bold"))
meeting_label2.grid(row=7, column=0, columnspan=2, pady=10)

# Créér le tableau
columns = ("Meeting Name", "Heure", "Duree", "Temps restant")
treeview = ttk.Treeview(table_frame, columns=columns, show="headings", height=5)
treeview.grid(row=8, column=0, columnspan=2, pady=10) 

treeview.column("Meeting Name", width=200, anchor="center")  
treeview.column("Heure", width=100, anchor="center")  
treeview.column("Duree", width=100, anchor="center")
treeview.column("Temps restant", width=100, anchor="center")

# Définir les titres des colonnes
treeview.heading("Meeting Name", text="Nom du meeting")
treeview.heading("Heure", text="Heure")
treeview.heading("Duree", text="Duree")  
treeview.heading("Temps restant", text="Temps restant")

# Bouton pour ouvrir le widget des meetings
show_widget_button = ttk.Button(frame, text="Meetings Widget", command=show_meetings_widget)
show_widget_button.grid(row=9, column=0, pady=5, padx=10, sticky="e")

# Bouton Widget Only 
widget_only_button = ttk.Button(frame, text="Widget Only", command=show_widget_only)
widget_only_button.grid(row=9, column=1,pady=5, padx=10, sticky="w")

# Configurer les colonnes pour qu'elles s'étendent
frame.grid_columnconfigure(0, weight=1, uniform="equal")
frame.grid_columnconfigure(1, weight=1, uniform="equal")

# Centrer le contenu verticalement
frame.grid_rowconfigure(0, weight=0)  # Titre
frame.grid_rowconfigure(1, weight=1)  # User ID
frame.grid_rowconfigure(2, weight=1)  # Mot de passe
frame.grid_rowconfigure(3, weight=0)  # Bouton

# Mettre à jour l'horloge toutes les secondes
root.after(500, lambda: draw_clock(canvas, root))

root.mainloop()
