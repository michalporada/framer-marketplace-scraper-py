'use client'

import { useState, useEffect } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { DashboardBlock } from '../DashboardBlock'
import { PercentageChange } from '../PercentageChange'
import { TimePeriod, Creator, DashboardRow } from '@/lib/types'
import { getCreators, getCreatorProducts, periodToHours } from '@/lib/api'
import { Skeleton } from '@/components/ui/skeleton'

interface TopCreatorsByViewsProps {
  period: TimePeriod
  onPeriodChange: (period: TimePeriod) => void
}

export function TopCreatorsByViews({
  period,
  onPeriodChange,
}: TopCreatorsByViewsProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | undefined>()
  const [data, setData] = useState<DashboardRow[]>([])

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      setError(undefined)

      try {
        // Get all creators
        const creatorsResponse = await getCreators({
          limit: 1000,
          sort: 'username',
        })

        const creators = creatorsResponse.data || []

        // For each creator, get their templates and calculate total views
        const creatorsWithViews = await Promise.all(
          creators.map(async (creator: Creator) => {
            try {
              const productsResponse = await getCreatorProducts(
                creator.username,
                { type: 'template', limit: 1000 }
              )

              const templates = productsResponse.data || []
              const totalViews = templates.reduce(
                (sum: number, template: any) =>
                  sum + (template.stats?.views?.normalized || 0),
                0
              )

              return {
                ...creator,
                totalViews,
                templatesCount: templates.length,
              }
            } catch (err) {
              console.error(`Error fetching products for ${creator.username}:`, err)
              return { ...creator, totalViews: 0, templatesCount: 0 }
            }
          })
        )

        // Sort by total views and take top 10
        const topCreators = creatorsWithViews
          .filter((c) => c.totalViews > 0)
          .sort((a, b) => b.totalViews - a.totalViews)
          .slice(0, 10)

        // Format as DashboardRow
        const rows: DashboardRow[] = topCreators.map((creator, index) => ({
          id: creator.username,
          rank: index + 1,
          name: creator.name || creator.username,
          value: creator.totalViews.toLocaleString(),
          metadata: {
            username: creator.username,
            templatesCount: creator.templatesCount,
            avatar: creator.avatar,
          },
          // TODO: Calculate percentage change when API supports it
          percentageChange: undefined,
        }))

        setData(rows)
      } catch (err) {
        console.error('Error fetching top creators:', err)
        setError(err instanceof Error ? err.message : 'Failed to load data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [period])

  return (
    <DashboardBlock
      title="Top Creators by Total Views of Templates"
      period={period}
      onPeriodChange={onPeriodChange}
      loading={loading}
      error={error}
      disabledPeriods={['7d', '30d']}
    >
      {data.length === 0 && !loading && !error && (
        <p className="text-center text-muted-foreground py-8">No data available</p>
      )}
      {data.length > 0 && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12">#</TableHead>
              <TableHead>Creator</TableHead>
              <TableHead className="text-right">Views</TableHead>
              <TableHead className="text-right">Change</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((row) => (
              <TableRow key={row.id}>
                <TableCell className="font-medium">{row.rank}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-3">
                    {row.metadata?.avatar && (
                      <Avatar className="h-8 w-8">
                        <AvatarImage src={row.metadata.avatar} alt={row.name} />
                        <AvatarFallback>
                          {row.name.charAt(0).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                    )}
                    <div className="flex flex-col">
                      <span className="font-medium">{row.name}</span>
                      {row.metadata?.templatesCount && (
                        <span className="text-xs text-muted-foreground">
                          {row.metadata.templatesCount} templates
                        </span>
                      )}
                    </div>
                  </div>
                </TableCell>
                <TableCell className="text-right">{row.value}</TableCell>
                <TableCell className="text-right">
                  <PercentageChange change={row.percentageChange} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </DashboardBlock>
  )
}

