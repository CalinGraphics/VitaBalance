import { useEffect, useState } from 'react'
import { animate, useReducedMotion } from 'framer-motion'

interface CountUpProps {
  value: number
  decimals?: number
  locale: string
}

/** Număr care urcă de la 0 la valoare (instant când utilizatorul cere mișcare redusă). */
const CountUp = ({ value, decimals = 0, locale }: CountUpProps) => {
  const reduce = useReducedMotion()
  const [shown, setShown] = useState(reduce ? value : 0)
  useEffect(() => {
    if (reduce) {
      setShown(value)
      return
    }
    const controls = animate(0, value, { duration: 1.1, ease: [0.16, 1, 0.3, 1], onUpdate: setShown })
    return () => controls.stop()
  }, [value, reduce])
  return <>{new Intl.NumberFormat(locale, { minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(shown)}</>
}

export default CountUp
