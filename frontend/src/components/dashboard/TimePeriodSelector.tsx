'use client'

import { Button } from '@/components/ui/button'
import { TimePeriod } from '@/lib/types'
import { cn } from '@/lib/utils'

interface TimePeriodSelectorProps {
  period: TimePeriod
  onPeriodChange: (period: TimePeriod) => void
  disabledPeriods?: TimePeriod[]
  className?: string
}

const periods: { value: TimePeriod; label: string }[] = [
  { value: '1d', label: '1d' },
  { value: '7d', label: '7d' },
  { value: '30d', label: '30d' },
]

export function TimePeriodSelector({
  period,
  onPeriodChange,
  disabledPeriods = ['7d', '30d'],
  className,
}: TimePeriodSelectorProps) {
  return (
    <div className={cn('flex gap-2', className)}>
      {periods.map((p) => {
        const isDisabled = disabledPeriods.includes(p.value)
        const isActive = period === p.value

        return (
          <Button
            key={p.value}
            variant={isActive ? 'default' : 'outline'}
            size="sm"
            onClick={() => !isDisabled && onPeriodChange(p.value)}
            disabled={isDisabled}
            className={cn(
              isDisabled && 'opacity-50 cursor-not-allowed',
              isActive && 'font-semibold'
            )}
          >
            {p.label}
          </Button>
        )
      })}
    </div>
  )
}

