# face_recognizer.py

import cv2
import pickle
import os
from config import MODEL_FILE, LABELS_FILE, RECOGNITION_THRESHOLD

# --- INITIALISATION AU NIVEAU DU MODULE (PAS DE 'global' ICI) ---
recognizer = None
cascade = None
label_to_name = {}

# --- CHARGEMENT DU MODÈLE ---
try:
    if not os.path.exists(MODEL_FILE) or not os.path.exists(LABELS_FILE):
        raise FileNotFoundError("Modèles faciaux manquants. Exécutez encode_faces.py.")

    # Chargement des labels
    with open(LABELS_FILE, "rb") as f:
        name_to_label = pickle.load(f)
    
    # ASSIGNATION: Pylance ne voit plus d'avertissement ici
    label_to_name = {v: k for k, v in name_to_label.items()}

    # Chargement du recognizer
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_FILE)

    # Chargement du classificateur en cascade
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    print("[RECOGNIZER] Modèles de reconnaissance chargés.")

except FileNotFoundError as e:
    print(f"[FATAL] {e}")
    # Ne pas quitter ici, mais marquer les modèles comme non chargés pour les éviter plus tard
    recognizer = None
    cascade = None
    label_to_name = {}
    
except Exception as e:
    print(f"[FATAL] Erreur lors du chargement des modèles: {e}")
    recognizer = None
    cascade = None
    label_to_name = {}


def process_frame(frame):
    """
    Détecte et reconnaît les visages dans une trame.
    Les variables de module (recognizer, cascade, label_to_name) sont ACCESSIBLES sans 'global'.
    Retourne une liste de résultats de détection valide.
    """
    # Pas besoin de 'global' car on ne réassigne pas les variables ici.
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