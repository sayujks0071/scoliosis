import numpy as np
import timeit

def orig(coords, plddt_scores):
    mask_hc = plddt_scores >= 70
    is_hc = mask_hc.astype(int)
    bounded = np.hstack(([0], is_hc, [0]))
    d = np.diff(bounded)
    starts = np.where(d == 1)[0]
    ends = np.where(d == -1)[0]

    max_len = 0
    best_segment = None

    for s, e in zip(starts, ends):
        length = e - s
        if length > max_len:
            max_len = length
            best_segment = (s, e)

    if best_segment:
        s, e = best_segment
        seg_coords = coords[s:e]
        if len(seg_coords) > 1:
            end_to_end = np.linalg.norm(seg_coords[-1] - seg_coords[0])
        else:
            end_to_end = 0.0
    else:
        end_to_end = 0.0
    return float(end_to_end)

def opt(coords, plddt_scores):
    mask_hc = plddt_scores >= 70
    bounded = np.empty(len(mask_hc) + 2, dtype=bool)
    bounded[0] = False
    bounded[-1] = False
    bounded[1:-1] = mask_hc

    d = np.diff(bounded.astype(np.int8))
    starts = np.where(d == 1)[0]
    ends = np.where(d == -1)[0]

    lengths = ends - starts
    if len(lengths) == 0:
        return 0.0

    best_idx = np.argmax(lengths)
    s = starts[best_idx]
    e = ends[best_idx]

    if e - s > 1:
        return float(np.linalg.norm(coords[e-1] - coords[s]))
    return 0.0

coords = np.random.rand(5000, 3)
plddt_scores = np.random.rand(5000) * 100

print(orig(coords, plddt_scores))
print(opt(coords, plddt_scores))
