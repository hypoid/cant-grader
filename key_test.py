import cv2


def mouse_handler(event, x, y, flags, param):
    """Update the mouse position as mouse move events call this function."""
    global mouseX, mouseY, Clicked
    if event == cv2.EVENT_LBUTTONDOWN:
        if k == 225:
            print("shift clicking")
    elif event == cv2.EVENT_MOUSEMOVE:
        mouseX, mouseY = x, y


cv2.namedWindow('img')
cv2.setMouseCallback('img', mouse_handler)


img = cv2.imread('Calibration/12.png', -1)
while True:
    cv2.imshow('img', img)
    k = cv2.waitKey(1) & 0xFF
    if k != 255:
        print(k)
    if k == 27:
        print("Esc key pressed: Exiting")
        break
