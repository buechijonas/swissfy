try {
  const mode = localStorage.getItem('theme')
  if (mode === 'light') document.documentElement.setAttribute('data-theme', 'swissfy')
  if (mode === 'dark') document.documentElement.setAttribute('data-theme', 'dark')
  if (localStorage.getItem('design') === 'glass') {
    document.documentElement.setAttribute('data-design', 'glass')
  }
} catch {}
