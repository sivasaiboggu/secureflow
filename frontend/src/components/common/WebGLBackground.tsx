import React, { useEffect, useRef } from 'react';

export const WebGLBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let mouseX = 0, mouseY = 0;
    let targetX = 0, targetY = 0;
    let time = 0;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const resize = () => {
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
      canvas.style.width = window.innerWidth + 'px';
      canvas.style.height = window.innerHeight + 'px';
      ctx.scale(dpr, dpr);
    };

    const onMouse = (e: MouseEvent) => {
      targetX = (e.clientX - window.innerWidth / 2) * 0.04;
      targetY = (e.clientY - window.innerHeight / 2) * 0.04;
    };

    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', onMouse);
    resize();

    const spacing = 38;
    const dotRadius = 1.4;

    const draw = () => {
      time += 0.012;
      mouseX += (targetX - mouseX) * 0.06;
      mouseY += (targetY - mouseY) * 0.06;

      const W = window.innerWidth;
      const H = window.innerHeight;

      ctx.clearRect(0, 0, W, H);

      // Soft vignette background
      const grad = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, Math.max(W, H) * 0.75);
      grad.addColorStop(0, 'rgba(10,13,20,0)');
      grad.addColorStop(1, 'rgba(8,11,18,0.85)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, W, H);

      const cols = Math.ceil(W / spacing) + 4;
      const rows = Math.ceil(H / spacing) + 4;

      for (let i = -2; i < cols; i++) {
        for (let j = -2; j < rows; j++) {
          const x = i * spacing + spacing / 2 + mouseX;
          const y = j * spacing + spacing / 2 + mouseY;

          const dx = x - W / 2;
          const dy = y - H / 2;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const maxDim = Math.max(W, H) * 0.65;
          const depth = Math.max(0, 1 - dist / maxDim);

          // Individual dot breathing using sine with spatial offset
          const wave = Math.sin(time + i * 0.3 + j * 0.5) * 0.5 + 0.5;
          const alpha = depth * wave * 0.55;

          if (alpha < 0.01) continue;

          ctx.beginPath();
          ctx.arc(x, y, dotRadius, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(231,255,114,${alpha.toFixed(3)})`;
          ctx.fill();
        }
      }

      animId = requestAnimationFrame(draw);
    };

    // Reduced motion check
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!prefersReducedMotion) {
      draw();
    } else {
      // DOM fallback: static dot grid
      ctx.fillStyle = 'rgba(231,255,114,0.08)';
      const W = window.innerWidth;
      const H = window.innerHeight;
      const cols = Math.ceil(W / spacing);
      const rows = Math.ceil(H / spacing);
      for (let i = 0; i < cols; i++) {
        for (let j = 0; j < rows; j++) {
          ctx.beginPath();
          ctx.arc(i * spacing + spacing / 2, j * spacing + spacing / 2, dotRadius, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', onMouse);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      id="laser-canvas"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        pointerEvents: 'none',
        zIndex: 0,
        backgroundColor: '#080b12',
      }}
    />
  );
};
