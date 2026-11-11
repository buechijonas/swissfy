try {
  const cookie = document.cookie.match(/(?:^|; )theme=([^;]*)/)
  const mode = cookie ? cookie[1] : localStorage.getItem('theme')
  if (mode === 'light') document.documentElement.setAttribute('data-theme', 'swissfy')
  if (mode === 'dark') document.documentElement.setAttribute('data-theme', 'dark')
} catch {}
