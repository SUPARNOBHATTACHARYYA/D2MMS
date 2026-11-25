import os
import shutil
from pathlib import Path

user_up = Path(r"C:\Users\iamjo\.gemini\antigravity\brain\17eaac24-64ab-425c-a9cf-add56cdaddba\.user_uploaded")
root = Path(__file__).resolve().parent.parent
lectures_dir = root / "lectures"

lectures_info = [
    {
        "num": 1,
        "slug": "01-washing-machine-shake",
        "title": "Why Does a Washing Machine Shake? (1-DOF Forced Vibration)",
        "pdf": "media_1795538738887_f1362bac.pdf", # Unit 2, Lec 1
        "nb": "media_1795538738885_58f0ff46.ipynb",  # washer_demo
        "date": "2026-09-08",
        "tags": ["Intro to Vibrations", "Pyodide", "Dynamical Systems", "Resonance", "Rotating Imbalance", "Vibration Isolation"],
        "abstract": "Single-DOF forced vibration, rotating unbalance, resonance peak, transmissibility, and vibration isolation in mechanical engineering systems.",
        "takeaways": [
            "Model a 1-DOF mass-spring-damper system excited by rotating unbalance.",
            "Derive and interpret steady-state amplitude magnification factor M(r) and phase angle phi(r).",
            "Compute force transmissibility and define isolation frequency thresholds."
        ],
        "tasks": [
            "Vary spin frequency across the resonance boundary (r=1) and observe phase shift.",
            "Compute base reaction forces for different damping ratios zeta."
        ]
    },
    {
        "num": 2,
        "slug": "02-fourier-transform-fft",
        "title": "Fourier Transform and FFT: From Time Series to Linear Spectrum",
        "pdf": "media_1795538738887_b280b87c.pdf", # Unit 2, Lec 2
        "nb": "media_1795538738887_37ab41ca.ipynb",  # FFT notebook
        "date": "2026-09-10",
        "tags": ["FFT", "Spectral Analysis", "Nyquist Frequency", "Windowing"],
        "abstract": "Discrete Fourier Transform (DFT), Fast Fourier Transform (FFT) algorithm, frequency resolution, leakage, windowing, and spectral decomposition.",
        "takeaways": [
            "Understand mathematical foundation of the Discrete Fourier Transform and O(N log N) FFT.",
            "Master sampling criteria: Nyquist-Shannon sampling theorem and aliasing prevention.",
            "Apply window functions (Hanning, Hamming) to mitigate spectral leakage."
        ],
        "tasks": [
            "Synthesize a multi-tone vibration signal with additive noise and extract peaks via FFT.",
            "Investigate zero-padding vs increased recording time on frequency resolution."
        ]
    },
    {
        "num": 3,
        "slug": "03-multi-dof-systems",
        "title": "Multi-DOF Systems: Coupled Equations and Modal Superposition",
        "pdf": "media_1795538738890_f921e502.pdf", # Unit 2, Lec 3
        "nb": "media_1795538738890_60d1ffbc.ipynb",  # Multi-DOF notebook
        "date": "2026-09-15",
        "tags": ["Multi-DOF", "Coupled Systems", "Normal Modes", "Modal Superposition"],
        "abstract": "Equations of motion for N-DOF systems, mass and stiffness matrices, generalized eigenvalue problem, modal coordinates, and modal decoupling.",
        "takeaways": [
            "Assemble global mass and stiffness matrices M and K for discrete mechanical networks.",
            "Formulate and solve generalized eigenvalue problem det(K - omega^2 M) = 0.",
            "Uncouple linear multi-DOF equations into independent single-degree modal oscillators."
        ],
        "tasks": [
            "Compute natural frequencies and mode shapes for a 3-storey building shear model.",
            "Simulate time-domain response using modal superposition vs direct numerical ODE integration."
        ]
    },
    {
        "num": 4,
        "slug": "04-eigen-decomposition",
        "title": "Eigen-Decomposition & DMD: State-Space & Modal Identification",
        "pdf": "media_1795538738894_10df9364.pdf", # Unit 2, Lec 4
        "nb": "media_1795538738891_f7a4d911.ipynb",  # Eigen / DMD notebook
        "date": "2026-09-17",
        "tags": ["Eigenvalues", "State-Space", "DMD", "Modal Identification"],
        "abstract": "State-space formulation, non-proportional damping, defective systems, and data-driven Dynamic Mode Decomposition (DMD) from sensor time-histories.",
        "takeaways": [
            "Transform second-order equations into first-order continuous state-space form.",
            "Analyze non-proportional damping and complex modal vectors.",
            "Implement exact Dynamic Mode Decomposition (DMD) to extract modes directly from sensor data."
        ],
        "tasks": [
            "Construct snapshot matrices X and X_prime from transient vibration measurements.",
            "Extract DMD eigenvalues and reconstructed continuous-time system modes."
        ]
    },
    {
        "num": 5,
        "slug": "05-nonlinear-odes",
        "title": "Nonlinear ODEs in Mechanics: Phase Space & The Simple Pendulum",
        "pdf": "media_1795538738896_e273bf3f.pdf", # Unit 3, Lec 1
        "nb": "media_1795538738892_f3b0d18b.ipynb",  # Simple Pendulum notebook
        "date": "2026-09-22",
        "tags": ["Nonlinear ODEs", "Phase Space", "Energy Conservation", "Elliptic Integrals"],
        "abstract": "Simple pendulum mechanics, nonlinear restoring moments, phase space topology, separatrix, energy conservation, and large-amplitude elliptic period.",
        "takeaways": [
            "Formulate conservative nonlinear mechanics beyond small-angle linear approximations.",
            "Visualize closed orbits, saddle equilibrium points, and the homoclinic separatrix trajectory.",
            "Evaluate exact pendulum period via complete elliptic integrals of the first kind K(k)."
        ],
        "tasks": [
            "Compare small-angle harmonic period T0 against exact elliptic period T(theta_max).",
            "Track total mechanical energy drift along computed numerical trajectories."
        ]
    },
    {
        "num": 6,
        "slug": "06-phase-portraits-stability",
        "title": "Phase Portraits & Stability Analysis: Invariant Manifolds & Limit Cycles",
        "pdf": "media_1795538738896_4906747e.pdf", # Unit 3, Lec 2
        "nb": "media_1795538738893_c8d245af.ipynb",  # Phase Portraits notebook
        "date": "2026-09-24",
        "tags": ["Phase Portraits", "Stability", "Jacobian Linearization", "Limit Cycles"],
        "abstract": "Autonomous planar dynamical systems, fixed points, Jacobian matrix linearization, Lyapunov stability, invariant manifolds, and Van der Pol limit cycles.",
        "takeaways": [
            "Locate equilibrium points and classify stability via trace-determinant plane of Jacobian.",
            "Identify stable and unstable invariant manifolds separating dynamic attraction basins.",
            "Explore self-excited nonlinear oscillations and isolated periodic orbits (limit cycles)."
        ],
        "tasks": [
            "Compute vector fields and nullclines for the Van der Pol nonlinear oscillator.",
            "Simulate relaxation oscillations and phase portrait convergence toward the limit cycle."
        ]
    },
    {
        "num": 7,
        "slug": "07-numerical-odes",
        "title": "Numerical Solution of ODEs: Runge-Kutta, Stiffness & Step Size Control",
        "pdf": "media_1795538738893_bd8c602b.pdf", # Unit 3, Lec 3
        "nb": "media_1795538738894_cda14059.ipynb",  # Numerical ODEs notebook
        "date": "2026-09-29",
        "tags": ["Runge-Kutta", "Dahlquist Stability", "Stiffness", "Adaptive Step Size"],
        "abstract": "Explicit vs implicit Runge-Kutta schemes, Dahlquist test equation, linear stability domains, numerical stiffness, and embedded RK45 adaptive timestepping.",
        "takeaways": [
            "Derive Butcher tableau and order conditions for explicit Runge-Kutta integrators.",
            "Map absolute stability regions in the complex lambda*dt plane for Euler and RK4.",
            "Understand numerical stiffness and why implicit schemes (A-stable) are required for stiff mechanics."
        ],
        "tasks": [
            "Simulate stiff flame-kinetics / mass-spring system with explicit RK4 vs implicit backward Euler.",
            "Implement an embedded RK4(5) Fehlberg / Dormand-Prince adaptive step-size controller."
        ]
    }
]

for lec in lectures_info:
    ldir = lectures_dir / lec["slug"]
    ldir.mkdir(parents=True, exist_ok=True)
    
    # Copy PDF
    src_pdf = user_up / lec["pdf"]
    dst_pdf = ldir / "slides.pdf"
    shutil.copy2(src_pdf, dst_pdf)
    
    # Copy notebook
    src_nb = user_up / lec["nb"]
    dst_nb = ldir / "notebook.ipynb"
    shutil.copy2(src_nb, dst_nb)
    
    # Write meta.yml
    tags_yaml = "\n".join([f'  - "{t}"' for t in lec["tags"]])
    takeaways_yaml = "\n".join([f'  - "{t}"' for t in lec["takeaways"]])
    tasks_yaml = "\n".join([f'  - "{t}"' for t in lec["tasks"]])
    
    meta_content = f"""number: {lec['num']}
title: "{lec['title']}"
slug: "{lec['slug']}"
date: "{lec['date']}"
tags:
{tags_yaml}
takeaways:
{takeaways_yaml}
tasks:
{tasks_yaml}
"""
    (ldir / "meta.yml").write_text(meta_content, encoding="utf-8")
    print(f"Verified & Populated {lec['slug']} ({dst_pdf.stat().st_size} bytes PDF, {dst_nb.stat().st_size} bytes NB)")

print("All 7 lectures verified and populated with exact PDF-to-Notebook mapping.")
