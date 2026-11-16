/** Workflow counters shared by the shell and every workspace view. */
import { createContext, useContext } from 'react'
import type { Stats } from './api'

interface StatsValue {
  stats: Stats | null
  /** Re-fetch the counters after an action that changes them. */
  reloadStats: () => void
}

export const StatsContext = createContext<StatsValue>({ stats: null, reloadStats: () => {} })

export const useStats = () => useContext(StatsContext)
