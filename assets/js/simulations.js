/**
 * Interactive Simulation Engines for Vibrations & Dynamics Modules
 * HTML5 Canvas 2D renderers with live equation banners and synchronized sliders
 */

window.VibrationsSim = (function () {
  'use strict';

  function getColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
      bg: isDark ? '#122130' : '#ffffff',
      grid: isDark ? 'rgba(255, 255, 255, 0.08)' : '#e5e7eb',
      axis: isDark ? '#94a7ba' : '#566573',
      text: isDark ? '#f0f4f8' : '#1b2631',
      copper: isDark ? '#e0915c' : '#b4622a',
      blue: isDark ? '#58a6ff' : '#0969da',
      orange: isDark ? '#f0883e' : '#d95319',
      teal: isDark ? '#39c5bb' : '#00897b',
      crimson: isDark ? '#ff7b72' : '#cf222e'
    };
  }

  // --- Lecture 01: Washing Machine Rotating Unbalance ---
  function initLec01() {
    const cvsAnim = document.getElementById('canvas-lec01-anim');
    const cvsResp = document.getElementById('canvas-lec01-resp');
    if (!cvsAnim || !cvsResp) return;

    const ctxAnim = cvsAnim.getContext('2d');
    const ctxResp = cvsResp.getContext('2d');

    let r = 1.0;
    let zeta = 0.08;
    let t = 0;
    let animId = null;

    const rSlider = document.getElementById('slider-r');
    const rVal = document.getElementById('val-r');
    const zetaSlider = document.getElementById('slider-zeta');
    const zetaVal = document.getElementById('val-zeta');

    const kpiMd = document.getElementById('kpi-md');
    const kpiTr = document.getElementById('kpi-tr');
    const kpiPhase = document.getElementById('kpi-phase');
    const liveEqBanner = document.getElementById('live-eq-banner');

    function updateKPIs() {
      const denom = Math.sqrt(Math.pow(1 - r * r, 2) + Math.pow(2 * zeta * r, 2));
      const Md = (r * r) / (denom || 1e-6);
      const Tr = Math.sqrt(1 + Math.pow(2 * zeta * r, 2)) / (denom || 1e-6);
      let phi = Math.atan2(2 * zeta * r, 1 - r * r) * (180 / Math.PI);
      if (phi < 0) phi += 360;

      if (kpiMd) kpiMd.innerText = Md.toFixed(2);
      if (kpiTr) kpiTr.innerText = Tr.toFixed(2);
      if (kpiPhase) kpiPhase.innerText = phi.toFixed(1) + '°';

      if (liveEqBanner) {
        liveEqBanner.innerHTML = `Operating State: $r = \\omega/\\omega_n = ${r.toFixed(2)}$ | $M_d(r) = ${Md.toFixed(2)}$ | Transmissibility $T_r = ${Tr.toFixed(2)}$ | Phase Lag $\\phi = ${phi.toFixed(1)}^\\circ$`;
        if (window.renderMathInElement) {
          window.renderMathInElement(liveEqBanner, {
            delimiters: [{ left: '$', right: '$', display: false }],
            throwOnError: false
          });
        }
      }
    }

    function drawAnimation() {
      if (!cvsAnim.clientWidth || !cvsAnim.clientHeight) {
        animId = requestAnimationFrame(drawAnimation);
        return;
      }
      cvsAnim.width = cvsAnim.clientWidth * window.devicePixelRatio;
      cvsAnim.height = cvsAnim.clientHeight * window.devicePixelRatio;
      ctxAnim.scale(window.devicePixelRatio, window.devicePixelRatio);
      const width = cvsAnim.clientWidth;
      const height = cvsAnim.clientHeight;
      const colors = getColors();

      ctxAnim.fillStyle = colors.bg;
      ctxAnim.fillRect(0, 0, width, height);

      const denom = Math.sqrt(Math.pow(1 - r * r, 2) + Math.pow(2 * zeta * r, 2));
      const amp = Math.min(48, (r * r / (denom || 1e-6)) * 8);
      const phi = Math.atan2(2 * zeta * r, 1 - r * r);
      const xDisp = amp * Math.sin(r * 3.5 * t - phi);

      const centerX = width * 0.5 + xDisp;
      const centerY = height * 0.5;

      // Base / Foundation
      ctxAnim.strokeStyle = colors.axis;
      ctxAnim.lineWidth = 2;
      ctxAnim.strokeRect(width * 0.15, height * 0.85, width * 0.7, 4);

      // Springs & Dashpots
      ctxAnim.beginPath();
      ctxAnim.moveTo(width * 0.28, height * 0.85);
      const springTop = centerY + 45;
      const dy = (springTop - height * 0.85) / 8;
      for (let i = 1; i <= 8; i++) {
        const sx = width * 0.28 + (i % 2 === 1 ? -10 : 10);
        ctxAnim.lineTo(sx, height * 0.85 + dy * i);
      }
      ctxAnim.strokeStyle = colors.teal;
      ctxAnim.stroke();

      // Dashpot
      ctxAnim.beginPath();
      ctxAnim.moveTo(width * 0.72, height * 0.85);
      ctxAnim.lineTo(width * 0.72, centerY + 65);
      ctxAnim.strokeStyle = colors.orange;
      ctxAnim.stroke();

      // Washing machine outer housing
      ctxAnim.fillStyle = colors.bg;
      ctxAnim.strokeStyle = colors.text;
      ctxAnim.lineWidth = 2.5;
      ctxAnim.strokeRect(centerX - 60, centerY - 55, 120, 110);
      ctxAnim.fillRect(centerX - 60, centerY - 55, 120, 110);

      // Drum circle
      ctxAnim.beginPath();
      ctxAnim.arc(centerX, centerY, 42, 0, Math.PI * 2);
      ctxAnim.strokeStyle = colors.copper;
      ctxAnim.lineWidth = 2;
      ctxAnim.stroke();

      // Rotating unbalance mass
      const rotAngle = r * 3.5 * t;
      const unbalRadius = 30;
      const ux = centerX + unbalRadius * Math.cos(rotAngle);
      const uy = centerY + unbalRadius * Math.sin(rotAngle);

      ctxAnim.beginPath();
      ctxAnim.moveTo(centerX, centerY);
      ctxAnim.lineTo(ux, uy);
      ctxAnim.strokeStyle = colors.axis;
      ctxAnim.stroke();

      ctxAnim.beginPath();
      ctxAnim.arc(ux, uy, 7, 0, Math.PI * 2);
      ctxAnim.fillStyle = colors.crimson;
      ctxAnim.fill();

      // Text displacement
      ctxAnim.font = '12px JetBrains Mono, monospace';
      ctxAnim.fillStyle = colors.text;
      ctxAnim.fillText(`x(t) = ${xDisp.toFixed(1)} mm`, centerX - 35, centerY - 65);

      t += 0.03;
      animId = requestAnimationFrame(drawAnimation);
    }

    function drawResponseCurve() {
      if (!cvsResp.clientWidth || !cvsResp.clientHeight) return;
      cvsResp.width = cvsResp.clientWidth * window.devicePixelRatio;
      cvsResp.height = cvsResp.clientHeight * window.devicePixelRatio;
      ctxResp.scale(window.devicePixelRatio, window.devicePixelRatio);
      const width = cvsResp.clientWidth;
      const height = cvsResp.clientHeight;
      const colors = getColors();

      ctxResp.fillStyle = colors.bg;
      ctxResp.fillRect(0, 0, width, height);

      const padL = 45, padR = 20, padT = 25, padB = 35;
      const plotW = width - padL - padR;
      const plotH = height - padT - padB;

      // Grid
      ctxResp.strokeStyle = colors.grid;
      ctxResp.lineWidth = 1;
      for (let rVal = 0.5; rVal <= 3.0; rVal += 0.5) {
        const x = padL + (rVal / 3.5) * plotW;
        ctxResp.beginPath();
        ctxResp.moveTo(x, padT);
        ctxResp.lineTo(x, padT + plotH);
        ctxResp.stroke();
      }

      ctxResp.strokeStyle = colors.axis;
      ctxResp.lineWidth = 1.5;
      ctxResp.strokeRect(padL, padT, plotW, plotH);

      ctxResp.font = '11px Lora, serif';
      ctxResp.fillStyle = colors.text;
      ctxResp.fillText('Frequency Ratio r = ω/ωₙ', width * 0.4, height - 10);
      ctxResp.fillText('M_d', 10, padT + 12);

      // Plot curves
      function plotForZeta(z, color, widthLine, isDashed) {
        ctxResp.beginPath();
        if (isDashed) ctxResp.setLineDash([4, 4]);
        else ctxResp.setLineDash([]);
        for (let px = 0; px <= plotW; px += 2) {
          const rCur = (px / plotW) * 3.5;
          const denom = Math.sqrt(Math.pow(1 - rCur * rCur, 2) + Math.pow(2 * z * rCur, 2));
          const md = (rCur * rCur) / (denom || 1e-6);
          const py = padT + plotH - Math.min(plotH, (md / 6.0) * plotH);
          if (px === 0) ctxResp.moveTo(padL + px, py);
          else ctxResp.lineTo(padL + px, py);
        }
        ctxResp.strokeStyle = color;
        ctxResp.lineWidth = widthLine;
        ctxResp.stroke();
        ctxResp.setLineDash([]);
      }

      plotForZeta(0.2, colors.axis, 1.2, true);
      plotForZeta(zeta, colors.copper, 2.5, false);

      // Current operating point dot
      const opX = padL + (r / 3.5) * plotW;
      const opDenom = Math.sqrt(Math.pow(1 - r * r, 2) + Math.pow(2 * zeta * r, 2));
      const opMd = (r * r) / (opDenom || 1e-6);
      const opY = padT + plotH - Math.min(plotH, (opMd / 6.0) * plotH);

      ctxResp.beginPath();
      ctxResp.arc(opX, opY, 6, 0, Math.PI * 2);
      ctxResp.fillStyle = colors.crimson;
      ctxResp.fill();
      ctxResp.strokeStyle = '#ffffff';
      ctxResp.lineWidth = 2;
      ctxResp.stroke();

      ctxResp.font = '11px JetBrains Mono, monospace';
      ctxResp.fillStyle = colors.copper;
      ctxResp.fillText(`ζ = ${zeta.toFixed(2)}`, padL + 15, padT + 20);
    }

    if (rSlider) {
      rSlider.oninput = function (e) {
        r = parseFloat(e.target.value);
        if (rVal) rVal.innerText = r.toFixed(2);
        updateKPIs();
        drawResponseCurve();
      };
    }

    if (zetaSlider) {
      zetaSlider.oninput = function (e) {
        zeta = parseFloat(e.target.value);
        if (zetaVal) zetaVal.innerText = zeta.toFixed(2);
        updateKPIs();
        drawResponseCurve();
      };
    }

    document.querySelectorAll('[data-preset-r]').forEach(btn => {
      btn.onclick = function () {
        document.querySelectorAll('[data-preset-r]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        r = parseFloat(btn.getAttribute('data-preset-r'));
        if (rSlider) rSlider.value = r;
        if (rVal) rVal.innerText = r.toFixed(2);
        updateKPIs();
        drawResponseCurve();
      };
    });

    updateKPIs();
    drawAnimation();
    drawResponseCurve();
    window.addEventListener('resize', drawResponseCurve);
    window.addEventListener('themeChanged', drawResponseCurve);
  }

  // --- Lecture 02: Fourier Transform Synthesizer ---
  function initLec02() {
    const cvsTime = document.getElementById('canvas-lec02-time');
    const cvsFreq = document.getElementById('canvas-lec02-freq');
    if (!cvsTime || !cvsFreq) return;

    const ctxTime = cvsTime.getContext('2d');
    const ctxFreq = cvsFreq.getContext('2d');

    let waveType = 'square';
    let harmonics = 5;

    const sliderHarm = document.getElementById('slider-harmonics');
    const valHarm = document.getElementById('val-harmonics');

    function draw() {
      if (!cvsTime.clientWidth || !cvsTime.clientHeight) return;
      const colors = getColors();
      const N = 256;
      const tData = new Float32Array(N);
      const fData = new Float32Array(N / 2);

      for (let i = 0; i < N; i++) {
        const theta = (i / N) * 2 * Math.PI;
        let y = 0;
        if (waveType === 'square') {
          for (let k = 1; k <= harmonics; k++) {
            const m = 2 * k - 1;
            y += (4 / (Math.PI * m)) * Math.sin(m * theta);
          }
        } else if (waveType === 'sawtooth') {
          for (let k = 1; k <= harmonics; k++) {
            y += (2 / (Math.PI * k)) * Math.pow(-1, k + 1) * Math.sin(k * theta);
          }
        } else {
          y = Math.sin(theta) + 0.6 * Math.sin(3 * theta) + 0.3 * Math.sin(7 * theta);
        }
        tData[i] = y;
      }

      for (let k = 0; k < N / 2; k++) {
        let real = 0, imag = 0;
        for (let n = 0; n < N; n++) {
          const angle = (2 * Math.PI * k * n) / N;
          real += tData[n] * Math.cos(angle);
          imag -= tData[n] * Math.sin(angle);
        }
        fData[k] = Math.sqrt(real * real + imag * imag) / (N / 2);
      }

      cvsTime.width = cvsTime.clientWidth * window.devicePixelRatio;
      cvsTime.height = cvsTime.clientHeight * window.devicePixelRatio;
      ctxTime.scale(window.devicePixelRatio, window.devicePixelRatio);
      const wT = cvsTime.clientWidth;
      const hT = cvsTime.clientHeight;

      ctxTime.fillStyle = colors.bg;
      ctxTime.fillRect(0, 0, wT, hT);
      ctxTime.strokeStyle = colors.grid;
      ctxTime.beginPath();
      ctxTime.moveTo(0, hT / 2); ctxTime.lineTo(wT, hT / 2);
      ctxTime.stroke();

      ctxTime.strokeStyle = colors.blue;
      ctxTime.lineWidth = 2;
      ctxTime.beginPath();
      for (let i = 0; i < N; i++) {
        const x = (i / N) * wT;
        const y = hT / 2 - tData[i] * (hT * 0.35);
        if (i === 0) ctxTime.moveTo(x, y);
        else ctxTime.lineTo(x, y);
      }
      ctxTime.stroke();

      cvsFreq.width = cvsFreq.clientWidth * window.devicePixelRatio;
      cvsFreq.height = cvsFreq.clientHeight * window.devicePixelRatio;
      ctxFreq.scale(window.devicePixelRatio, window.devicePixelRatio);
      const wF = cvsFreq.clientWidth;
      const hF = cvsFreq.clientHeight;

      ctxFreq.fillStyle = colors.bg;
      ctxFreq.fillRect(0, 0, wF, hF);

      const maxK = 24;
      const barW = (wF - 60) / maxK;
      ctxFreq.fillStyle = colors.copper;
      for (let k = 0; k < maxK; k++) {
        const mag = Math.min(1.0, fData[k]);
        const bH = mag * (hF - 50);
        const bx = 40 + k * barW;
        const by = hF - 30 - bH;
        ctxFreq.fillRect(bx, by, barW - 4, bH);
      }
    }

    if (sliderHarm) {
      sliderHarm.oninput = function (e) {
        harmonics = parseInt(e.target.value, 10);
        if (valHarm) valHarm.innerText = harmonics;
        draw();
      };
    }

    document.querySelectorAll('[data-wave]').forEach(btn => {
      btn.onclick = function () {
        document.querySelectorAll('[data-wave]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        waveType = btn.getAttribute('data-wave');
        draw();
      };
    });

    draw();
    window.addEventListener('resize', draw);
    window.addEventListener('themeChanged', draw);
  }

  function runAll() {
    try { initLec01(); } catch(e) { console.error('initLec01 error:', e); }
    try { initLec02(); } catch(e) { console.error('initLec02 error:', e); }
  }

  // Run immediately
  runAll();

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runAll);
  }
  window.addEventListener('load', runAll);

  return { initLec01, initLec02, runAll };
})();
