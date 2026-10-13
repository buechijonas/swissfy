try {
  const mode = localStorage.getItem('theme')
  if (mode === 'light') document.documentElement.setAttribute('data-theme', 'swissfy')
  if (mode === 'dark') document.documentElement.setAttribute('data-theme', 'dark')
} catch {}
