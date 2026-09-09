export interface TableLike {
  id?: number | null
  number?: string | null
  name?: string | null
}

const SYSTEM_ID = /^T\d{6,}$/i

export function tableLabel(t?: TableLike | null, ordinal = 0): string {
  const name = (t?.name || '').trim()
  if (name) return name
  const num = (t?.number || '').trim()
  if (num && !SYSTEM_ID.test(num)) return `№${num}`
  return `№${t?.id ?? ordinal + 1}`
}