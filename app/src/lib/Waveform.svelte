<script>
  // Draws peaks as mirrored bars, one lane per channel, in the category's color.
  // Peaks will come from Rust; the style sheet passes made-up ones.
  let { peaks, category, height = 64 } = $props();
  let canvas;

  $effect(() => {
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const width = canvas.clientWidth;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    // Canvas can't read CSS variables, so resolve the token first.
    ctx.fillStyle = getComputedStyle(canvas).getPropertyValue(`--color-cat-${category}`);
    const lane = height / peaks.length;
    peaks.forEach((channel, i) => {
      const mid = lane * i + lane / 2;
      const step = width / channel.length;
      channel.forEach((p, x) => {
        const h = Math.max(1, p * (lane / 2 - 1));
        ctx.fillRect(x * step, mid - h, Math.max(1, step - 1), h * 2);
      });
    });
  });
</script>

<canvas bind:this={canvas} class="block w-full" style:height="{height}px" aria-hidden="true"></canvas>
