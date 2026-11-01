try {
  const mode = localStorage.getItem('theme')
  if (mode === 'light') document.documentElement.setAttribute('data-theme', 'swissfy')
  if (mode === 'dark') document.documentElement.setAttribute('data-theme', 'dark')
  const design = localStorage.getItem('design')
  if (['glass', 'cyberpunk', 'ecopunk', 'romance', 'y2k'].includes(design)) {
    document.documentElement.setAttribute('data-design', design)
  }
} catch {}
