export interface ChartThemeColors {
  axis: string
  split: string
  label: string
  tooltipBg: string
  tooltipText: string
  tooltipShadow: string
  border: string
  legend: string
}

export function chartThemeColors(): ChartThemeColors {
  const isLight = document.documentElement.getAttribute('data-theme') === 'light'
  return isLight
    ? {
        axis: 'rgba(0, 0, 0, 0.42)',
        split: 'rgba(0, 0, 0, 0.08)',
        label: '#5a5a68',
        tooltipBg: 'rgba(255, 255, 255, 0.98)',
        tooltipText: '#23232b',
        tooltipShadow: '0 8px 24px rgba(40, 60, 45, 0.18)',
        border: '#ffffff',
        legend: '#5a5a68'
      }
    : {
        axis: '#3a3a40',
        split: '#26262a',
        label: '#b9b9c0',
        tooltipBg: 'rgba(22, 22, 26, 0.96)',
        tooltipText: '#fff',
        tooltipShadow: '0 8px 24px rgba(0,0,0,0.4)',
        border: '#0a0a0a',
        legend: '#b9b9c0'
      }
}

export function watchThemeChange(cb: () => void): () => void {
  const observer = new MutationObserver(cb)
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
  return () => observer.disconnect()
}