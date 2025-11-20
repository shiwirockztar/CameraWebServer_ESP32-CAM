import cv2

url = 'http://192.168.1.86:81/stream' 
cap = cv2.VideoCapture(url)

WinName = 'ESP32 CAMERA'
cv2.namedWindow(WinName, cv2.WINDOW_AUTOSIZE)   

while True:
    cap.open(url)
    ret, frame = cap.read()

    if ret:
        #frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE) 
        #gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow(WinName, frame)

    tecla = cv2.waitKey(5) & 0xFF
    if tecla == 27:
        break
cv2.destroyAllWindows()
cap.release()   