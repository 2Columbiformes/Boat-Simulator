import numpy as np

# ── Window & grid ──────────────────────────────────────────────────────────────
WIDTH,  HEIGHT  = 800, 600          # screen / viewport size
WORLD_W, WORLD_H = WIDTH, HEIGHT    # world matches screen (no scrolling)
GRID_W, GRID_H  = 100*2, 75*2
CELL_W  = WORLD_W // GRID_W         # 8 px per grid cell
CELL_H  = WORLD_H // GRID_H         # 8 px per grid cell
FPS     = 60

# ── Wave physics ───────────────────────────────────────────────────────────────
WAVE_SPEED   = 0.4   # CFL: must stay below 1/sqrt(2) ≈ 0.707
DAMPING      = 0.99  # faster energy dissipation
SPLASH_AMP   = 0.005
SPLASH_R     = 2

# Numerical stabilization
VISCOSITY    = 0.1   # Laplacian-based diffusion to damp short wavelengths
# Hard clamp — must stay above any single-frame injection to avoid h vs h_prev divergence
MAX_H        = 0.05

# ── Entity–water coupling ──────────────────────────────────────────────────────
WAVE_GRAD_K  = 1.0    # wave gradient force on entities (was 0.01)
DRAG_K       = 0.05   #0.02
DISPLACE_AMP = 0.0001   # was 0.01 — large values caused constant saturation
RIPPLE_AMP   = 0.0005   # was 0.012 — scaled down to stay well below MAX_H

# ── Rendering palette ──────────────────────────────────────────────────────────
COLOR_DEEP    = np.array([8,   24,  80],  dtype=np.float32)
COLOR_MID     = np.array([24,  80,  150], dtype=np.float32)
COLOR_SHALLOW = np.array([60,  170, 230], dtype=np.float32)
COLOR_FOAM    = np.array([220, 245, 255], dtype=np.float32)
COLOR_CREST   = np.array([200, 230, 255], dtype=np.float32)


class WaterGrid:
    """Height-field shallow-water simulator on a torus (periodic BCs)."""

    def __init__(self, grid_h: int = GRID_H, grid_w: int = GRID_W):
        self.grid_h = grid_h
        self.grid_w = grid_w
        self.c2     = WAVE_SPEED ** 2
        self.h      = np.zeros((grid_h, grid_w), dtype=np.float32)
        self.h_prev = np.zeros((grid_h, grid_w), dtype=np.float32)
        self.fixed  = np.zeros((grid_h, grid_w), dtype=bool)

    @staticmethod
    def _laplacian(h: np.ndarray) -> np.ndarray:
        return (
            np.roll(h, -1, axis=0) + np.roll(h, 1, axis=0) +
            np.roll(h, -1, axis=1) + np.roll(h, 1, axis=1) -
            4.0 * h
        )

    def step(self):
        lap = self._laplacian(self.h)
        h_new = 2.0 * self.h - self.h_prev + self.c2 * lap

        # apply small Laplacian-based viscosity to damp nyquist/short waves
        if VISCOSITY > 0.0:
            h_new -= VISCOSITY * lap

        # global damping
        h_new *= DAMPING

        # clamp extreme values to prevent numerical blowup
        if MAX_H is not None:
            np.clip(h_new, -MAX_H, MAX_H, out=h_new)

        h_new[self.fixed] = 0.0
        self.h_prev = self.h
        self.h      = h_new

    def splash(self, gx: float, gy: float, amplitude: float, radius: float):
        gx = gx % self.grid_w
        gy = gy % self.grid_h
        ys, xs = np.ogrid[:self.grid_h, :self.grid_w]
        dx = (xs - gx).astype(np.float32);  dx -= self.grid_w * np.round(dx / self.grid_w)
        dy = (ys - gy).astype(np.float32);  dy -= self.grid_h * np.round(dy / self.grid_h)
        dist2  = (dx * dx + dy * dy).astype(np.float32)
        r2     = max(radius, 0.5) ** 2
        sigma2 = (radius / 2.0) ** 2 if radius > 0.5 else 0.25
        mask   = dist2 < r2
        self.h[mask] += amplitude * np.exp(-dist2[mask] / (2.0 * sigma2))
        self.h[self.fixed] = 0.0
        # Keep h in bounds immediately so h_prev never diverges from h
        if MAX_H is not None:
            np.clip(self.h, -MAX_H, MAX_H, out=self.h)

    def set_obstacle(self, gx: float, gy: float, radius: float):
        gx = gx % self.grid_w
        gy = gy % self.grid_h
        ys, xs = np.ogrid[:self.grid_h, :self.grid_w]
        dx = (xs - gx).astype(np.float32);  dx -= self.grid_w * np.round(dx / self.grid_w)
        dy = (ys - gy).astype(np.float32);  dy -= self.grid_h * np.round(dy / self.grid_h)
        self.fixed[dx * dx + dy * dy < radius ** 2] = True
        self.h[self.fixed]      = 0.0
        self.h_prev[self.fixed] = 0.0

    def unset_obstacle(self, gx: float, gy: float, radius: float):
        gx = gx % self.grid_w
        gy = gy % self.grid_h
        ys, xs = np.ogrid[:self.grid_h, :self.grid_w]
        dx = (xs - gx).astype(np.float32);  dx -= self.grid_w * np.round(dx / self.grid_w)
        dy = (ys - gy).astype(np.float32);  dy -= self.grid_h * np.round(dy / self.grid_h)
        self.fixed[dx * dx + dy * dy < radius ** 2] = False

    def height_at(self, gx: float, gy: float) -> float:
        x = int(gx % self.grid_w)
        y = int(gy % self.grid_h)
        return float(self.h[y, x])

    def gradient_at(self, gx: float, gy: float):
        gx = gx % self.grid_w
        gy = gy % self.grid_h
        x0, y0 = int(gx), int(gy)
        x1 = (x0 + 1) % self.grid_w
        y1 = (y0 + 1) % self.grid_h
        fx, fy = gx - x0, gy - y0

        def _cd(xi: int, yi: int):
            xp = (xi + 1) % self.grid_w;  xm = (xi - 1) % self.grid_w
            yp = (yi + 1) % self.grid_h;  ym = (yi - 1) % self.grid_h
            return (
                float((self.h[yi, xp] - self.h[yi, xm]) * 0.5),
                float((self.h[yp, xi] - self.h[ym, xi]) * 0.5),
            )

        dx00, dy00 = _cd(x0, y0)
        dx10, dy10 = _cd(x1, y0)
        dx01, dy01 = _cd(x0, y1)
        dx11, dy11 = _cd(x1, y1)
        w00 = (1 - fx) * (1 - fy);  w10 = fx * (1 - fy)
        w01 = (1 - fx) * fy;        w11 = fx * fy
        return (dx00*w00 + dx10*w10 + dx01*w01 + dx11*w11,
                dy00*w00 + dy10*w10 + dy01*w01 + dy11*w11)
