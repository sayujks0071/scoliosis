
import matplotlib.pyplot as plt
import numpy as np


def organism(x, y, t):
    k = 5 * np.cos(x / 14) * np.cos(y / 30)
    e = y / 8 - 13

    # mag(k, e) is sqrt(k^2 + e^2)
    mag_ke = np.sqrt(k**2 + e**2)
    d = (mag_ke**2) / 59 + 4

    angleTerm = np.arctan2(k, e)
    q = 60 - 3 * np.sin(angleTerm * e)

    # sin(d*d - t*2)
    wave = k * (3 + 4 / d * np.sin(d * d - t * 2))

    c = d / 2 + e / 99 - t / 18

    xCoord = (q + wave) * np.sin(c)
    yCoord = (q + d * 9) * np.cos(c)

    return xCoord, yCoord

def main():
    t = 0
    # Simulate the loop in draw()
    # for (let i = 0; i < 10000; i++)
    i_vals = np.arange(10000)
    x_input = i_vals % 80
    y_input = i_vals / 43

    # Generate points for a single frame (t=0)
    x_coords, y_coords = organism(x_input, y_input, t)

    plt.figure(figsize=(10, 10), facecolor='black')
    plt.scatter(x_coords, y_coords, s=1, c='white', alpha=0.5)
    plt.axis('equal')
    plt.axis('off')
    plt.savefig('js_creature_t0.png', facecolor='black')
    print("Saved js_creature_t0.png")

    # Generate points for another frame to see movement (t=PI)
    t = np.pi
    x_coords, y_coords = organism(x_input, y_input, t)

    plt.figure(figsize=(10, 10), facecolor='black')
    plt.scatter(x_coords, y_coords, s=1, c='white', alpha=0.5)
    plt.axis('equal')
    plt.axis('off')
    plt.savefig('js_creature_tPI.png', facecolor='black')
    print("Saved js_creature_tPI.png")

if __name__ == "__main__":
    main()
