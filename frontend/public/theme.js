try {
  const mode = localStorage.getItem('theme')
  if (mode === 'light') document.documentElement.setAttribute('data-theme', 'swissfy')
  if (mode === 'dark') document.documentElement.setAttribute('data-theme', 'dark')
  const design = localStorage.getItem('design')
  if (design === 'glass' || design === 'cyberpunk') {
    document.documentElement.setAttribute('data-design', design)
  }
} catch {}
