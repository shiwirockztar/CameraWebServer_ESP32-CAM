# face_recognizer.py

import cv2
import pickle
import os
from config import MODEL_FILE, LABELS_FILE, RECOGNITION_THRESHOLD

# --- INITIALISATION AU NIVEAU DU MODULE ---
recognizer = None
cascade = None
label_to_name = {}

# --- DÉFINITION DES CHEMINS ABSOLUS ---
# Chemin du répertoire où se trouve ce script (face_recognizer.py)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(SCRIPT_DIR, MODEL_FILE)
LABELS_PATH = os.path.join(SCRIPT_DIR, LABELS_FILE)
HAARCASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


# --- CHARGEMENT DU MODÈLE ---
try:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Modèle LBPH '{MODEL_PATH}' manquant.")
    if not os.path.exists(LABELS_PATH):
        raise FileNotFoundError(f"Fichier de labels '{LABELS_PATH}' manquant.")

    # Chargement des labels
    with open(LABELS_PATH, "rb") as f: # Utiliser LABELS_PATH
        name_to_label = pickle.load(f)
    
    label_to_name = {v: k for k, v in name_to_label.items()}

    # Chargement du recognizer
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_PATH) # <-- Utiliser MODEL_PATH

    # Chargement du classificateur en cascade
    cascade = cv2.CascadeClassifier(HAARCASCADE_PATH)

    print("[RECOGNIZER] Modèles de reconnaissance chargés.")

except FileNotFoundError as e:
    print(f"[FATAL] {e}")
    recognizer = None
    cascade = None
    label_to_name = {}
    
except Exception as e:
    # Cette erreur est probablement ici si le chemin est correct.
    print(f"[FATAL] Erreur lors du chargement des modèles (contenu invalide?): {e}")
    print("Vérifiez l'intégrité du fichier face_model.yml.")
    recognizer = None
    cascade = None
    label_to_name = {}


def process_frame(frame):
    # ... (le reste de la fonction est inchangé) ...
    if cascade is None or recognizer is None:
        return []

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    detected_faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
    
    valid_detections = []

    for (x, y, w, h) in detected_faces:
        if w < 30 or h < 30: continue

        face_roi = gray[y:y+h, x:x+w]
        if face_roi.size == 0: continue
        face_resized = cv2.resize(face_roi, (200, 200))

        label, confidence = recognizer.predict(face_resized)
        
        # Vérification du seuil de reconnaissance
        if confidence < RECOGNITION_THRESHOLD and label in label_to_name:
            name = label_to_name[label]
            valid_detections.append({
                "name": name,
                "confidence": float(confidence),
                "bbox": (x, y, w, h)
            })

    return valid_detections