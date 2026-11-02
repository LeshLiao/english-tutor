/** 字詞層級的 diff（LCS），給詳情頁高亮原句與修正句的差異。 */

export type DiffOp = 'same' | 'removed' | 'added'
export interface DiffToken {
  op: DiffOp
  text: string
}

function tokenize(text: string): string[] {
  // 保留空白與標點為獨立 token，重組時才不會改變原文
  return text.match(/\s+|[A-Za-z0-9']+|[^\sA-Za-z0-9']/g) ?? []
}

export function wordDiff(a: string, b: string): DiffToken[] {
  const x = tokenize(a)
  const y = tokenize(b)
  const n = x.length
  const m = y.length
  const lcs: number[][] = Array.from({ length: n + 1 }, () => new Array<number>(m + 1).fill(0))
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      lcs[i][j] = x[i] === y[j] ? lcs[i + 1][j + 1] + 1 : Math.max(lcs[i + 1][j], lcs[i][j + 1])
    }
  }
  const out: DiffToken[] = []
  let i = 0
  let j = 0
  while (i < n && j < m) {
    if (x[i] === y[j]) {
      out.push({ op: 'same', text: x[i] })
      i++
      j++
    } else if (lcs[i + 1][j] >= lcs[i][j + 1]) {
      out.push({ op: 'removed', text: x[i] })
      i++
    } else {
      out.push({ op: 'added', text: y[j] })
      j++
    }
  }
  while (i < n) out.push({ op: 'removed', text: x[i++] })
  while (j < m) out.push({ op: 'added', text: y[j++] })
  return out
}
