'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { TimePeriodSelector } from './TimePeriodSelector'
import { TimePeriod } from '@/lib/types'
import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface DashboardBlockProps {
  title: string
  period: TimePeriod
  onPeriodChange: (period: TimePeriod) => void
  loading?: boolean
  error?: string
  children: ReactNode
  className?: string
  disabledPeriods?: TimePeriod[]
}

export function DashboardBlock({
  title,
  period,
  onPeriodChange,
  loading = false,
  error,
  children,
  className,
  disabledPeriods,
}: DashboardBlockProps) {
  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-lg font-semibold">{title}</CardTitle>
        <TimePeriodSelector
          period={period}
          onPeriodChange={onPeriodChange}
          disabledPeriods={disabledPeriods}
        />
      </CardHeader>
      <CardContent>
        {loading && (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        )}
        {error && (
          <div className="text-center py-8 text-destructive">
            <p>Error loading data</p>
            <p className="text-sm text-muted-foreground">{error}</p>
          </div>
        )}
        {!loading && !error && children}
      </CardContent>
    </Card>
  )
}

