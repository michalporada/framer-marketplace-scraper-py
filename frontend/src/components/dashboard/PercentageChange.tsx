'use client'

import { Badge } from '@/components/ui/badge'
import { PercentageChange as PercentageChangeType } from '@/lib/types'
import { ArrowUp, ArrowDown } from 'lucide-react'

interface PercentageChangeProps {
  change?: PercentageChangeType
  className?: string
}

export function PercentageChange({ change, className }: PercentageChangeProps) {
  if (!change) {
    return <span className={className}>-</span>
  }

  const isPositive = change.isPositive
  const value = Math.abs(change.value)
  const formattedValue = value.toFixed(1)

  return (
    <Badge
      variant={isPositive ? 'default' : 'destructive'}
      className={`flex items-center gap-1 ${className}`}
    >
      {isPositive ? (
        <ArrowUp className="h-3 w-3" />
      ) : (
        <ArrowDown className="h-3 w-3" />
      )}
      {formattedValue}%
    </Badge>
  )
}

