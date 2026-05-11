import csv
import math
import os

import matplotlib.pyplot as plt


def organism(x, y, t):
    k = 5 * math.cos(x / 14) * math.cos(y / 30)
    e = y / 8 - 13

    # mag(k, e) in JS is sqrt(k*k + e*e)
    mag_sq = k * k + e * e
    d = mag_sq / 59 + 4

    angleTerm = math.atan2(k, e)
    q = 60 - 3 * math.sin(angleTerm * e)

    wave = k * (3 + 4 / d * math.sin(d * d - t * 2))

    c = d / 2 + e / 99 - t / 18

    xCoord = (q + wave) * math.sin(c) + 200
    yCoord = (q + d * 9) * math.cos(c) + 200

    return xCoord, yCoord

def run_simulation(t_steps, output_file, output_dir):
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['t', 'i', 'x', 'y', 'xCoord', 'yCoord'])

        t = 0
        for step in range(t_steps):
            x_coords = []
            y_coords = []
            for i in range(10000):
                x = i % 80
                # In JS, integer division is often implicitly meant if we are indexing, but the original code:
                # let y = i / 43;
                # In JS, division is floating point unless explicitly floored. We will use floating point to match exactly.
                y = i / 43

                xCoord, yCoord = organism(x, y, t)
                writer.writerow([t, i, x, y, xCoord, yCoord])
                x_coords.append(xCoord)
                y_coords.append(yCoord)

            # Generate and save plot for each timestep
            plt.figure(figsize=(6, 6))
            plt.style.use('dark_background')
            plt.scatter(x_coords, y_coords, s=0.5, c='white', alpha=0.6)
            plt.xlim(0, 400)
            plt.ylim(0, 400)
            plt.gca().invert_yaxis()  # p5.js has y=0 at top
            plt.axis('off')
            plt.title(f"JS Creature - t={t:.2f}")
            plot_filepath = os.path.join(output_dir, f"creature_t{step}.png")
            plt.savefig(plot_filepath, dpi=150, bbox_inches='tight', facecolor='black')
            plt.close()

            t += math.pi / 20

if __name__ == "__main__":
    output_dir = "outputs/js_creature_toy_model"
    os.makedirs(output_dir, exist_ok=True)

    output_filepath = os.path.join(output_dir, "creature_coordinates.csv")
    print(f"Running toy model simulation, saving to {output_filepath}...")

    # Run for 2 timesteps to match a small snippet of time
    run_simulation(2, output_filepath, output_dir)
    print("Simulation complete.")
