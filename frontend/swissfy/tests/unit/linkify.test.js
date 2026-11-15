import { describe, expect, it } from 'vitest'
import { linkParts } from '@core/lib/linkify.js'

function links(text) {
  return linkParts(text)
    .filter((part) => part.href)
    .map(({ text: label, href }) => [label, href])
}

describe('linkParts', () => {
  it('turns an email into a mailto link', () => {
    expect(links('contact@wintersehn.ch')).toEqual([
      ['contact@wintersehn.ch', 'mailto:contact@wintersehn.ch'],
    ])
  })

  it('links bare domains and keeps the brackets around them', () => {
    const parts = linkParts('von IMDb (imdb.com), zu Spielen von Steam (store.steampowered.com).')
    expect(links('von IMDb (imdb.com)')).toEqual([['imdb.com', 'https://imdb.com']])
    expect(parts.map((part) => part.text).join('')).toBe(
      'von IMDb (imdb.com), zu Spielen von Steam (store.steampowered.com).',
    )
    expect(parts.at(-1).text).toBe(').')
  })

  it('keeps full urls as they are', () => {
    expect(links('see https://swissfy.ch/terms now')).toEqual([
      ['https://swissfy.ch/terms', 'https://swissfy.ch/terms'],
    ])
  })

  it('does not end a link with the sentence period', () => {
    expect(links('Schreib an contact@wintersehn.ch.')).toEqual([
      ['contact@wintersehn.ch', 'mailto:contact@wintersehn.ch'],
    ])
  })

  it('leaves legal references alone', () => {
    expect(links('gemäss Art. 6 Abs. 1 lit. f DSGVO und § 7 Abs.1 TMG')).toEqual([])
  })
})
