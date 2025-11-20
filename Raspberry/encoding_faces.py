# encode_faces.py
import os
import cv2
import pickle

DATASET_DIR = "dataset"   # structure: dataset/nom_personne/image1.jpg ...
MODEL_FILE = "face_model.yml"
LABELS_FILE = "labels.pkl"

# Utilise le cascade frontal d'OpenCV pour extraire les visages d'entrainement
cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

faces = []
labels = []
label_map = {}
next_label = 0

for person in sorted(os.listdir(DATASET_DIR)):
    person_dir = os.path.join(DATASET_DIR, person)
    if not os.path.isdir(person_dir):
        continue
    print(f"[INFO] Traitement de: {person}")
    if person not in label_map:
        label_map[person] = next_label
        next_label += 1
    for filename in sorted(os.listdir(person_dir)):
        path = os.path.join(person_dir, filename)
        img = cv2.imread(path)
        if img is None:
            print(f"  [WARN] impossible de lire {path}")
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        detected = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50,50))
        if len(detected) == 0:
            # si aucun visage détecté, utilise l'image entière redimensionnée
            face_roi = cv2.resize(gray, (200, 200))
            faces.append(face_roi)
            labels.append(label_map[person])
            print(f"  [WARN] pas de face detectée, use whole image for {filename}")
            continue
        # prend le plus grand rectangle (probablement visage principal)
        x,y,w,h = max(detected, key=lambda r: r[2]*r[3])
        face_roi = gray[y:y+h, x:x+w]
        face_roi = cv2.resize(face_roi, (200, 200))
        faces.append(face_roi)
        labels.append(label_map[person])
        print(f"  [OK] ajouté {filename}")

if len(faces) == 0:
    raise RuntimeError("Aucune face trouvée dans dataset. Vérifie dataset/")

# Convert to suitable types
import numpy as np
faces_np = np.array(faces)
labels_np = np.array(labels)

# Créer et entraîner le modèle LBPH
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.train(faces_np, labels_np)
recognizer.write(MODEL_FILE)
print(f"[INFO] Modèle sauvé dans {MODEL_FILE}")

# Sauvegarder le mapping labels -> nom
with open(LABELS_FILE, "wb") as f:
    pickle.dump(label_map, f)
print(f"[INFO] Labels sauvegardés dans {LABELS_FILE}")
print("[DONE]")
