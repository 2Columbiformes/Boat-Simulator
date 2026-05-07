import numpy as np

#  Window & grid
WIDTH, HEIGHT = 800, 600          # Screen resolution in pixels
WORLD_W, WORLD_H = WIDTH, HEIGHT  # World size matches screen (no camera scrolling)
GRID_W, GRID_H = 100*2, 75*2     # Simulation grid resolution (200×150)
CELL_W = WORLD_W // GRID_W        # Pixel width of each grid cell (8 px)
CELL_H = WORLD_H // GRID_H        # Pixel height of each grid cell (8 px)
FPS = 60                          # Simulation update rate

#  Wave physics
WAVE_SPEED = 0.4   # Wave propagation speed (CFL must be < 1/sqrt(2))
DAMPING = 0.99     # Global energy loss per frame
SPLASH_AMP = 0.005 # Default splash amplitude
SPLASH_R = 10      # Default splash radius (grid units)

# Numerical stabilization
VISCOSITY = 0.1  # Laplacian diffusion to damp high-frequency noise
MAX_H = 0.05     # Hard clamp on height values to prevent instability

#  Entity–water coupling
WAVE_GRAD_K = 7000.0  # Strength of water gradient force on entities
DRAG_K = 0.02         # Drag force applied to entities
DISPLACE_AMP = 0.0001 # How much entities displace water
RIPPLE_AMP = 0.0005   # Ripple amplitude caused by entity movement

#  Rendering palette
COLOR_DEEP = np.array([8, 24, 80], dtype=np.float32)
COLOR_MID = np.array([24, 80, 150], dtype=np.float32)
COLOR_SHALLOW = np.array([60, 170, 230], dtype=np.float32)
COLOR_FOAM = np.array([220, 245, 255], dtype=np.float32)
COLOR_CREST = np.array([200, 230, 255], dtype=np.float32)


class WaterGrid:
    """
    Height‑field shallow‑water simulator on a torus (periodic boundaries).

    Stores:
      - h:      current water height
      - h_prev: previous frame height (needed for 2nd‑order wave equation)
      - fixed:  boolean mask of obstacle cells (height forced to 0)
    """

    def __init__(self, grid_h: int = GRID_H, grid_w: int = GRID_W):
        self.grid_h = grid_h
        self.grid_w = grid_w
        self.c2 = WAVE_SPEED ** 2                                    # Precompute c^2 for wave equation
        self.h = np.zeros((grid_h, grid_w), dtype=np.float32)       # Current height
        self.h_prev = np.zeros((grid_h, grid_w), dtype=np.float32)  # Previous height
        self.fixed = np.zeros((grid_h, grid_w), dtype=bool)         # Obstacle mask


    # Discrete 5‑point Laplacian (periodic wrapping)
    # Measures curvature of the height field.

    @staticmethod
    def _laplacian(h: np.ndarray) -> np.ndarray:
        return (
            np.roll(h, -1, axis=0) + np.roll(h, 1, axis=0) +   # vertical neighbors
            np.roll(h, -1, axis=1) + np.roll(h, 1, axis=1) +   # horizontal neighbors
            -4.0 * h                                             # center weight
        )


    # Advance the wave simulation by one time step
    # Implements the 2nd‑order finite‑difference wave equation.

    def step(self):
        lap = self._laplacian(self.h)  # Compute curvature of height field

        # Standard wave equation update:
        # h_new = 2h - h_prev + c^2 * Laplacian(h)
        h_new = 2.0 * self.h - self.h_prev + self.c2 * lap

        # Optional viscosity: damps high‑frequency (short‑wavelength) noise
        if VISCOSITY > 0.0:
            h_new -= VISCOSITY * lap

        # Global damping to simulate energy loss
        h_new *= DAMPING

        # Clamp height to prevent numerical blowup
        if MAX_H is not None:
            np.clip(h_new, -MAX_H, MAX_H, out=h_new)

        # Enforce obstacles (height = 0)
        h_new[self.fixed] = 0.0

        # Rotate buffers for next frame
        self.h_prev = self.h
        self.h = h_new


    # Inject a Gaussian splash centered at (gx, gy)

    def splash(self, gx: float, gy: float, amplitude: float, radius: float):
        # Wrap coordinates (toroidal world)
        gx = gx % self.grid_w
        gy = gy % self.grid_h

        # Create coordinate grids
        ys, xs = np.ogrid[:self.grid_h, :self.grid_w]

        # Compute toroid distances in x and y
        dx = (xs - gx).astype(np.float32)
        dx -= self.grid_w * np.round(dx / self.grid_w)

        dy = (ys - gy).astype(np.float32)
        dy -= self.grid_h * np.round(dy / self.grid_h)

        # Squared distance from splash center
        dist2 = (dx * dx + dy * dy).astype(np.float32)

        # Splash radius and Gaussian width
        r2 = max(radius, 0.5) ** 2
        sigma2 = (radius / 2.0) ** 2 if radius > 0.5 else 0.25

        # Mask of affected cells
        mask = dist2 < r2

        # Add Gaussian bump to height field
        self.h[mask] += amplitude * np.exp(-dist2[mask] / (2.0 * sigma2))

        # Obstacles must remain at height 0
        self.h[self.fixed] = 0.0

        # Clamp immediately to avoid divergence between h and h_prev
        if MAX_H is not None:
            np.clip(self.h, -MAX_H, MAX_H, out=self.h)


    # Mark a circular region as a fixed obstacle (height = 0)

    def set_obstacle(self, gx: float, gy: float, radius: float):
        gx = gx % self.grid_w
        gy = gy % self.grid_h

        ys, xs = np.ogrid[:self.grid_h, :self.grid_w] # open grid,

        # Toroidal distances
        dx = (xs - gx).astype(np.float32)
        dx -= self.grid_w * np.round(dx / self.grid_w)

        dy = (ys - gy).astype(np.float32)
        dy -= self.grid_h * np.round(dy / self.grid_h)

        # Mark cells inside radius as fixed
        self.fixed[dx * dx + dy * dy < radius ** 2] = True
        # selects all elements where the mask is True and assigns True to them

        # Force height to zero for obstacles
        self.h[self.fixed] = 0.0
        self.h_prev[self.fixed] = 0.0


    # Remove obstacle flag from a circular region

    def unset_obstacle(self, gx: float, gy: float, radius: float):
        gx = gx % self.grid_w
        gy = gy % self.grid_h
        #general x and y location as grid
        ys, xs = np.ogrid[:self.grid_h, :self.grid_w]

        # Toroidal distances
        dx = (xs - gx).astype(np.float32) #difference between grid and center
        dx -= self.grid_w * np.round(dx / self.grid_w)

        dy = (ys - gy).astype(np.float32)
        dy -= self.grid_h * np.round(dy / self.grid_h)

        # Unmark fixed cells
        self.fixed[dx * dx + dy * dy < radius ** 2] = False


    # Return height at nearest grid cell (integer lookup)

    def height_at(self, gx: float, gy: float) -> float:
        x = int(gx % self.grid_w)
        y = int(gy % self.grid_h)
        return float(self.h[y, x])


    # Return bilinearly interpolated gradient of the height field
    # Used for water forces on entities.

    def gradient_at(self, gx: float, gy: float):
        # Wrap coordinates
        gx = gx % self.grid_w
        gy = gy % self.grid_h

        # Integer grid cell coordinates
        x0, y0 = int(gx), int(gy)
        x1 = (x0 + 1) % self.grid_w
        y1 = (y0 + 1) % self.grid_h

        # Fractional offsets for bilinear interpolation
        fx, fy = gx - x0, gy - y0

        # Central-difference gradient at a grid cell
        def _cd(xi: int, yi: int):
            xp = (xi + 1) % self.grid_w
            xm = (xi - 1) % self.grid_w
            yp = (yi + 1) % self.grid_h
            ym = (yi - 1) % self.grid_h
            return (
                float((self.h[yi, xp] - self.h[yi, xm]) * 0.5),  # ∂h/∂x
                float((self.h[yp, xi] - self.h[ym, xi]) * 0.5),  # ∂h/∂y
            )

        # Gradients at four surrounding cells
        dx00, dy00 = _cd(x0, y0)
        dx10, dy10 = _cd(x1, y0)
        dx01, dy01 = _cd(x0, y1)
        dx11, dy11 = _cd(x1, y1)

        # Bilinear interpolation weights
        w00 = (1 - fx) * (1 - fy)
        w10 = fx * (1 - fy)
        w01 = (1 - fx) * fy
        w11 = fx * fy

        # Interpolated gradient
        return (
            dx00*w00 + dx10*w10 + dx01*w01 + dx11*w11,
            dy00*w00 + dy10*w10 + dy01*w01 + dy11*w11
        )
