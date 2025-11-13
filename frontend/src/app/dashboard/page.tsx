'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Card, CardHeader, CardTitle, CardAction, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react'
import { getTopCreatorsByTemplateViews, getTopTemplates, getTopCategories, getSmallestCategories, getTopFreeTemplates, getTopCreatorsByTemplateCount, periodToHours } from '@/lib/api'
import { TimePeriod } from '@/lib/types'

type TimePeriodType = '1d' | '7d' | '30d'
type SortDirection = 'asc' | 'desc' | null

// Helper component for sortable table headers
function SortableTableHead({
  children,
  sortKey,
  currentSort,
  onSort,
  className
}: {
  children: React.ReactNode
  sortKey: string
  currentSort: { key: string | null; direction: SortDirection }
  onSort: (key: string) => void
  className?: string
}) {
  const isActive = currentSort.key === sortKey
  const direction = isActive ? currentSort.direction : null

  return (
    <TableHead 
      className={`cursor-pointer select-none hover:bg-muted/50 transition-colors ${className || ''}`}
      onClick={() => onSort(sortKey)}
    >
      <div className="flex items-center gap-2">
        {children}
        {direction === 'asc' ? (
          <ArrowUp className="h-3 w-3 opacity-70" />
        ) : direction === 'desc' ? (
          <ArrowDown className="h-3 w-3 opacity-70" />
        ) : (
          <ArrowUpDown className="h-3 w-3 opacity-30" />
        )}
      </div>
    </TableHead>
  )
}

export default function DashboardPage() {
  const [period, setPeriod] = useState<TimePeriodType>('1d')
  const [loading, setLoading] = useState(true)
  const [dashboardData, setDashboardData] = useState<{
    topCreators: any
    topTemplates: any
    smallestCategories: any
    topCategories: any
    topFreeTemplates: any
    creatorsMostTemplates: any
  }>({
    topCreators: null,
    topTemplates: null,
    smallestCategories: null,
    topCategories: null,
    topFreeTemplates: null,
    creatorsMostTemplates: null,
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    async function loadAllData() {
      setLoading(true)
      setErrors({})
      
      const periodHours = periodToHours(period)
      
      // ✅ RÓWNOLEGŁE ŁADOWANIE - wszystkie zapytania jednocześnie
      const [
        topCreatorsResult,
        topTemplatesResult,
        smallestCategoriesResult,
        topCategoriesResult,
        topFreeTemplatesResult,
        creatorsMostTemplatesResult
      ] = await Promise.allSettled([
        getTopCreatorsByTemplateViews({ limit: 10, period_hours: periodHours }),
        getTopTemplates({ limit: 10, period_hours: periodHours }),
        getSmallestCategories({ limit: 10, product_type: 'template' }),
        getTopCategories({ limit: 10, period_hours: periodHours }),
        getTopFreeTemplates({ limit: 10, period_hours: periodHours }),
        getTopCreatorsByTemplateCount({ limit: 10, period_hours: periodHours })
      ])

      // Przetwórz wyniki
      setDashboardData({
        topCreators: topCreatorsResult.status === 'fulfilled' ? topCreatorsResult.value : null,
        topTemplates: topTemplatesResult.status === 'fulfilled' ? topTemplatesResult.value : null,
        smallestCategories: smallestCategoriesResult.status === 'fulfilled' ? smallestCategoriesResult.value : null,
        topCategories: topCategoriesResult.status === 'fulfilled' ? topCategoriesResult.value : null,
        topFreeTemplates: topFreeTemplatesResult.status === 'fulfilled' ? topFreeTemplatesResult.value : null,
        creatorsMostTemplates: creatorsMostTemplatesResult.status === 'fulfilled' ? creatorsMostTemplatesResult.value : null,
      })

      // Zapisz błędy
      const newErrors: Record<string, string> = {}
      if (topCreatorsResult.status === 'rejected') newErrors.topCreators = topCreatorsResult.reason?.message || 'Failed to load'
      if (topTemplatesResult.status === 'rejected') newErrors.topTemplates = topTemplatesResult.reason?.message || 'Failed to load'
      if (smallestCategoriesResult.status === 'rejected') newErrors.smallestCategories = smallestCategoriesResult.reason?.message || 'Failed to load'
      if (topCategoriesResult.status === 'rejected') newErrors.topCategories = topCategoriesResult.reason?.message || 'Failed to load'
      if (topFreeTemplatesResult.status === 'rejected') newErrors.topFreeTemplates = topFreeTemplatesResult.reason?.message || 'Failed to load'
      if (creatorsMostTemplatesResult.status === 'rejected') newErrors.creatorsMostTemplates = creatorsMostTemplatesResult.reason?.message || 'Failed to load'
      setErrors(newErrors)

      setLoading(false)
    }

    loadAllData()
  }, [period])

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Analytics and insights for Framer Marketplace
        </p>
      </div>

      <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        <TopCreatorsByViews 
          period={period} 
          onPeriodChange={setPeriod}
          data={dashboardData.topCreators}
          loading={loading}
          error={errors.topCreators}
        />
        <MostPopularTemplates 
          period={period} 
          onPeriodChange={setPeriod}
          data={dashboardData.topTemplates}
          loading={loading}
          error={errors.topTemplates}
        />
        <SmallestCategories 
          period={period} 
          onPeriodChange={setPeriod}
          data={dashboardData.smallestCategories}
          loading={loading}
          error={errors.smallestCategories}
        />
        <MostPopularCategories 
          period={period} 
          onPeriodChange={setPeriod}
          data={dashboardData.topCategories}
          loading={loading}
          error={errors.topCategories}
        />
        <MostPopularFreeTemplates 
          period={period} 
          onPeriodChange={setPeriod}
          data={dashboardData.topFreeTemplates}
          loading={loading}
          error={errors.topFreeTemplates}
        />
        <CreatorsMostTemplates 
          period={period} 
          onPeriodChange={setPeriod}
          data={dashboardData.creatorsMostTemplates}
          loading={loading}
          error={errors.creatorsMostTemplates}
        />
      </div>
    </div>
  )
}

function TimePeriodSelector({ 
  period, 
  onPeriodChange 
}: { 
  period: TimePeriodType
  onPeriodChange: (period: TimePeriodType) => void 
}) {
  return (
    <div className="flex gap-2">
      <Button
        variant={period === '1d' ? 'default' : 'outline'}
        size="sm"
        onClick={() => onPeriodChange('1d')}
      >
        1d
      </Button>
      <Button
        variant={period === '7d' ? 'default' : 'outline'}
        size="sm"
        onClick={() => onPeriodChange('7d')}
        disabled
      >
        7d
      </Button>
      <Button
        variant={period === '30d' ? 'default' : 'outline'}
        size="sm"
        onClick={() => onPeriodChange('30d')}
        disabled
      >
        30d
      </Button>
    </div>
  )
}

function TopCreatorsByViews({ 
  period, 
  onPeriodChange,
  data: responseData,
  loading,
  error
}: { 
  period: TimePeriodType
  onPeriodChange: (period: TimePeriodType) => void
  data: any
  loading: boolean
  error?: string
}) {
  const [sort, setSort] = useState<{ key: string | null; direction: SortDirection }>({ key: null, direction: null })

  // Mapuj dane z props
  const creators = responseData?.data || []
  const mappedData = creators.map((creator: any, index: number) => {
    // Debug: sprawdź co przychodzi z API
    if (index === 0 && typeof window !== 'undefined') {
      console.log('Creator data from API:', creator)
    }
    
    // Obsługa name - preferuj name jeśli istnieje i nie jest pusty/null/undefined
    const creatorName = (creator.name != null && creator.name !== '' && typeof creator.name === 'string' && creator.name.trim() !== '')
      ? creator.name.trim() 
      : creator.username || 'Unknown'
    
    // Obsługa avatar_url - sprawdź czy istnieje i nie jest pusty/null/undefined
    const avatarUrl = (creator.avatar_url != null && creator.avatar_url !== '' && typeof creator.avatar_url === 'string' && creator.avatar_url.trim() !== '')
      ? creator.avatar_url.trim()
      : undefined
    
    // Debug: sprawdź zmapowane dane
    if (index === 0 && typeof window !== 'undefined') {
      console.log('Mapped creator data:', { name: creatorName, avatar: avatarUrl, originalName: creator.name, originalAvatar: creator.avatar_url })
    }
    
    return {
      id: creator.username,
      rank: index + 1,
      name: creatorName,
      avatar: avatarUrl,
      views: creator.total_views,
      templatesCount: creator.templates_count,
      change: creator.views_change_percent !== undefined && creator.views_change_percent !== null ? {
        value: Math.abs(creator.views_change_percent),
        isPositive: creator.views_change_percent >= 0
      } : undefined
    }
  })

  // Sort data
  const sortedData = [...mappedData].sort((a, b) => {
    if (!sort.key || !sort.direction) return 0
    
    let aVal: any
    let bVal: any
    
    switch (sort.key) {
      case 'name':
        aVal = a.name?.toLowerCase() || ''
        bVal = b.name?.toLowerCase() || ''
        break
      case 'views':
        aVal = a.views || 0
        bVal = b.views || 0
        break
      case 'change':
        aVal = a.change?.value || 0
        bVal = b.change?.value || 0
        break
      default:
        return 0
    }
    
    if (aVal < bVal) return sort.direction === 'asc' ? -1 : 1
    if (aVal > bVal) return sort.direction === 'asc' ? 1 : -1
    return 0
  })

  const handleSort = (key: string) => {
    if (sort.key === key) {
      if (sort.direction === 'asc') {
        setSort({ key, direction: 'desc' })
      } else if (sort.direction === 'desc') {
        setSort({ key: null, direction: null })
      } else {
        setSort({ key, direction: 'asc' })
      }
    } else {
      setSort({ key, direction: 'asc' })
    }
  }

  return (
    <Card className="min-w-0 w-full">
      <CardHeader>
        <CardTitle>Top Creators by Total Views</CardTitle>
        <CardAction>
          <TimePeriodSelector period={period} onPeriodChange={onPeriodChange} />
        </CardAction>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        {loading ? (
          <div className="space-y-3">
            {[...Array(10)].map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-8 text-destructive">
            <p>Error loading data</p>
            <p className="text-sm text-muted-foreground">{error}</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">#</TableHead>
                <SortableTableHead sortKey="name" currentSort={sort} onSort={handleSort}>
                  Creator
                </SortableTableHead>
                <SortableTableHead sortKey="views" currentSort={sort} onSort={handleSort} className="text-right">
                  Views
                </SortableTableHead>
                <SortableTableHead sortKey="change" currentSort={sort} onSort={handleSort} className="text-right">
                  Change
                </SortableTableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedData.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                    No data available
                  </TableCell>
                </TableRow>
              ) : (
                sortedData.map((row: any, index: number) => (
                  <TableRow key={row.id || index}>
                    <TableCell className="font-medium">{row.rank}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="h-8 w-8">
                          <AvatarImage src={row.avatar || undefined} alt={row.name || row.id} />
                          <AvatarFallback>
                            {row.name?.charAt(0)?.toUpperCase() || row.id?.charAt(0)?.toUpperCase() || '?'}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex flex-col">
                          <Link 
                            href={`https://www.framer.com/@${row.id}/`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-medium hover:underline transition-colors"
                          >
                            {row.name || row.id}
                          </Link>
                          {row.templatesCount && (
                            <span className="text-xs text-muted-foreground">
                              {row.templatesCount} templates
                            </span>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">{row.views?.toLocaleString() || '-'}</TableCell>
                    <TableCell className="text-right">
                      {row.change ? (
                        <Badge variant={row.change.isPositive ? 'default' : 'destructive'} className="flex items-center gap-1 w-fit">
                          {row.change.isPositive ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                          {row.change.value.toFixed(1)}%
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}

function MostPopularTemplates({ 
  period, 
  onPeriodChange,
  data: responseData,
  loading,
  error
}: { 
  period: TimePeriodType
  onPeriodChange: (period: TimePeriodType) => void
  data: any
  loading: boolean
  error?: string
}) {
  const [sort, setSort] = useState<{ key: string | null; direction: SortDirection }>({ key: null, direction: null })

  // Mapuj dane z props
  const templates = responseData?.data || []
  const mappedData = templates.map((template: any, index: number) => {
    // Obsługa creator_name - preferuj name jeśli istnieje i nie jest pusty/null/undefined
    const creatorName = (template.creator_name != null && template.creator_name !== '' && typeof template.creator_name === 'string' && template.creator_name.trim() !== '')
      ? template.creator_name.trim()
      : template.creator_username || 'Unknown'
    
    // Obsługa category
    const category = (template.category != null && template.category !== '' && typeof template.category === 'string' && template.category.trim() !== '')
      ? template.category.trim()
      : null
    
    return {
      id: template.product_id,
      rank: index + 1,
      name: template.name,
      creator: creatorName,
      creatorId: template.creator_username,
      category: category,
      views: template.views,
      isFree: template.is_free === true, // Explicit check for boolean true
      price: template.price != null ? template.price : null,
      change: template.views_change_percent !== undefined && template.views_change_percent !== null ? {
        value: Math.abs(template.views_change_percent),
        isPositive: template.views_change_percent >= 0
      } : undefined
    }
  })

  // Sort data
  const sortedData = [...mappedData].sort((a, b) => {
    if (!sort.key || !sort.direction) return 0
    
    let aVal: any
    let bVal: any
    
    switch (sort.key) {
      case 'name':
        aVal = a.name?.toLowerCase() || ''
        bVal = b.name?.toLowerCase() || ''
        break
      case 'price':
        aVal = a.isFree ? 0 : (a.price || 0)
        bVal = b.isFree ? 0 : (b.price || 0)
        break
      case 'views':
        aVal = a.views || 0
        bVal = b.views || 0
        break
      case 'change':
        aVal = a.change?.value || 0
        bVal = b.change?.value || 0
        break
      default:
        return 0
    }
    
    if (aVal < bVal) return sort.direction === 'asc' ? -1 : 1
    if (aVal > bVal) return sort.direction === 'asc' ? 1 : -1
    return 0
  })

  const handleSort = (key: string) => {
    if (sort.key === key) {
      if (sort.direction === 'asc') {
        setSort({ key, direction: 'desc' })
      } else if (sort.direction === 'desc') {
        setSort({ key: null, direction: null })
      } else {
        setSort({ key, direction: 'asc' })
      }
    } else {
      setSort({ key, direction: 'asc' })
    }
  }

  return (
    <Card className="min-w-0 w-full">
      <CardHeader>
        <CardTitle>Most Popular Templates</CardTitle>
        <CardAction>
          <TimePeriodSelector period={period} onPeriodChange={onPeriodChange} />
        </CardAction>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        {loading ? (
          <div className="space-y-3">
            {[...Array(10)].map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-8 text-destructive">
            <p>Error loading data</p>
            <p className="text-sm text-muted-foreground">{error}</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">#</TableHead>
                <SortableTableHead sortKey="name" currentSort={sort} onSort={handleSort}>
                  Template
                </SortableTableHead>
                <SortableTableHead sortKey="price" currentSort={sort} onSort={handleSort} className="text-right">
                  Price
                </SortableTableHead>
                <SortableTableHead sortKey="views" currentSort={sort} onSort={handleSort} className="text-right">
                  Views
                </SortableTableHead>
                <SortableTableHead sortKey="change" currentSort={sort} onSort={handleSort} className="text-right">
                  Change
                </SortableTableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedData.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                    No data available
                  </TableCell>
                </TableRow>
              ) : (
                sortedData.map((row, index) => (
                  <TableRow key={row.id || index}>
                    <TableCell className="font-medium">{row.rank}</TableCell>
                    <TableCell>
                      <div className="flex flex-col">
                        <Link 
                          href={`https://www.framer.com/marketplace/templates/${row.id}/`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-medium hover:underline transition-colors"
                        >
                          {row.name}
                        </Link>
                        {(row.category || row.creator) && (
                          <span className="text-xs text-muted-foreground">
                            {row.category && row.creator ? `${row.category} • ${row.creator}` : row.category || row.creator}
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      {row.isFree ? (
                        <Badge variant="secondary" className="text-xs">Free</Badge>
                      ) : row.price ? (
                        <Badge variant="outline" className="text-xs">
                          ${row.price.toFixed(2)}
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-xs">Paid</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">{row.views?.toLocaleString() || '-'}</TableCell>
                    <TableCell className="text-right">
                      {row.change ? (
                        <Badge variant={row.change.isPositive ? 'default' : 'destructive'} className="flex items-center gap-1 w-fit">
                          {row.change.isPositive ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                          {row.change.value.toFixed(1)}%
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}

function SmallestCategories({ 
  period, 
  onPeriodChange,
  data: responseData,
  loading,
  error
}: { 
  period: TimePeriodType
  onPeriodChange: (period: TimePeriodType) => void
  data: any
  loading: boolean
  error?: string
}) {
  const [sort, setSort] = useState<{ key: string | null; direction: SortDirection }>({ key: null, direction: null })

  // Mapuj dane z props
  const categories = responseData?.data || []
  const mappedData = categories.map((category: any, index: number) => ({
    id: category.category_name || category.category,
    rank: index + 1,
    name: category.category_name || category.category,
    productsCount: category.products_count || 0,
    views: category.total_views || 0,
    change: category.views_change_percent !== undefined && category.views_change_percent !== null ? {
      value: Math.abs(category.views_change_percent),
      isPositive: category.views_change_percent >= 0
    } : undefined
  }))

  // Sort data
  const sortedData = [...mappedData].sort((a, b) => {
    if (!sort.key || !sort.direction) return 0
    
    let aVal: any
    let bVal: any
    
    switch (sort.key) {
      case 'name':
        aVal = a.name?.toLowerCase() || ''
        bVal = b.name?.toLowerCase() || ''
        break
      case 'productsCount':
        aVal = a.productsCount || 0
        bVal = b.productsCount || 0
        break
      case 'views':
        aVal = a.views || 0
        bVal = b.views || 0
        break
      case 'change':
        aVal = a.change?.value || 0
        bVal = b.change?.value || 0
        break
      default:
        return 0
    }
    
    if (aVal < bVal) return sort.direction === 'asc' ? -1 : 1
    if (aVal > bVal) return sort.direction === 'asc' ? 1 : -1
    return 0
  })

  const handleSort = (key: string) => {
    if (sort.key === key) {
      if (sort.direction === 'asc') {
        setSort({ key, direction: 'desc' })
      } else if (sort.direction === 'desc') {
        setSort({ key: null, direction: null })
      } else {
        setSort({ key, direction: 'asc' })
      }
    } else {
      setSort({ key, direction: 'asc' })
    }
  }

  return (
    <Card className="min-w-0 w-full">
      <CardHeader>
        <CardTitle>Smallest Categories</CardTitle>
        <CardAction>
          <TimePeriodSelector period={period} onPeriodChange={onPeriodChange} />
        </CardAction>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        {loading ? (
          <div className="space-y-3">
            {[...Array(10)].map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-8 text-destructive">
            <p>Error loading data</p>
            <p className="text-sm text-muted-foreground">{error}</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">#</TableHead>
                <SortableTableHead sortKey="name" currentSort={sort} onSort={handleSort}>
                  Category
                </SortableTableHead>
                <SortableTableHead sortKey="views" currentSort={sort} onSort={handleSort} className="text-right">
                  Views
                </SortableTableHead>
                <SortableTableHead sortKey="change" currentSort={sort} onSort={handleSort} className="text-right">
                  Change
                </SortableTableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedData.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                    No data available
                  </TableCell>
                </TableRow>
              ) : (
                sortedData.map((row, index) => (
                  <TableRow key={row.id || index}>
                    <TableCell className="font-medium">{row.rank}</TableCell>
                    <TableCell>
                      <Link 
                        href={`https://www.framer.com/marketplace/templates/category/${row.id.toLowerCase().replace(/\s+/g, '-')}/`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-medium hover:underline transition-colors"
                      >
                        {row.name}
                      </Link>
                    </TableCell>
                    <TableCell className="text-right">{row.views?.toLocaleString() || '-'}</TableCell>
                    <TableCell className="text-right">
                      {row.change ? (
                        <Badge variant={row.change.isPositive ? 'default' : 'destructive'} className="flex items-center gap-1 w-fit">
                          {row.change.isPositive ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                          {row.change.value.toFixed(1)}%
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}

function MostPopularCategories({ 
  period, 
  onPeriodChange,
  data: responseData,
  loading,
  error
}: { 
  period: TimePeriodType
  onPeriodChange: (period: TimePeriodType) => void
  data: any
  loading: boolean
  error?: string
}) {
  const [sort, setSort] = useState<{ key: string | null; direction: SortDirection }>({ key: null, direction: null })

  // Mapuj dane z props
  const categories = responseData?.data || []
  const mappedData = categories.map((category: any, index: number) => ({
    id: category.category_name,
    rank: index + 1,
    name: category.category_name,
    views: category.total_views,
    productsCount: category.products_count,
    change: category.views_change_percent !== undefined && category.views_change_percent !== null ? {
      value: Math.abs(category.views_change_percent),
      isPositive: category.views_change_percent >= 0
    } : undefined
  }))

  // Sort data
  const sortedData = [...mappedData].sort((a, b) => {
    if (!sort.key || !sort.direction) return 0
    
    let aVal: any
    let bVal: any
    
    switch (sort.key) {
      case 'name':
        aVal = a.name?.toLowerCase() || ''
        bVal = b.name?.toLowerCase() || ''
        break
      case 'productsCount':
        aVal = a.productsCount || 0
        bVal = b.productsCount || 0
        break
      case 'views':
        aVal = a.views || 0
        bVal = b.views || 0
        break
      case 'change':
        aVal = a.change?.value || 0
        bVal = b.change?.value || 0
        break
      default:
        return 0
    }
    
    if (aVal < bVal) return sort.direction === 'asc' ? -1 : 1
    if (aVal > bVal) return sort.direction === 'asc' ? 1 : -1
    return 0
  })

  const handleSort = (key: string) => {
    if (sort.key === key) {
      if (sort.direction === 'asc') {
        setSort({ key, direction: 'desc' })
      } else if (sort.direction === 'desc') {
        setSort({ key: null, direction: null })
      } else {
        setSort({ key, direction: 'asc' })
      }
    } else {
      setSort({ key, direction: 'asc' })
    }
  }

  return (
    <Card className="min-w-0 w-full">
      <CardHeader>
        <CardTitle>Most Popular Categories</CardTitle>
        <CardAction>
          <TimePeriodSelector period={period} onPeriodChange={onPeriodChange} />
        </CardAction>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        {loading ? (
          <div className="space-y-3">
            {[...Array(10)].map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-8 text-destructive">
            <p>Error loading data</p>
            <p className="text-sm text-muted-foreground">{error}</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">#</TableHead>
                <SortableTableHead sortKey="name" currentSort={sort} onSort={handleSort}>
                  Category
                </SortableTableHead>
                <SortableTableHead sortKey="views" currentSort={sort} onSort={handleSort} className="text-right">
                  Views
                </SortableTableHead>
                <SortableTableHead sortKey="change" currentSort={sort} onSort={handleSort} className="text-right">
                  Change
                </SortableTableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedData.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                    No data available
                  </TableCell>
                </TableRow>
              ) : (
                sortedData.map((row, index) => (
                  <TableRow key={row.id || index}>
                    <TableCell className="font-medium">{row.rank}</TableCell>
                    <TableCell>
                      <div className="flex flex-col">
                        <Link 
                          href={`https://www.framer.com/marketplace/templates/category/${row.id.toLowerCase().replace(/\s+/g, '-')}/`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-medium hover:underline transition-colors"
                        >
                          {row.name}
                        </Link>
                        {row.productsCount && (
                          <span className="text-xs text-muted-foreground">
                            {row.productsCount.toLocaleString()} templates
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">{row.views?.toLocaleString() || '-'}</TableCell>
                    <TableCell className="text-right">
                      {row.change ? (
                        <Badge variant={row.change.isPositive ? 'default' : 'destructive'} className="flex items-center gap-1 w-fit">
                          {row.change.isPositive ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                          {row.change.value.toFixed(1)}%
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}

function MostPopularFreeTemplates({ 
  period, 
  onPeriodChange,
  data: responseData,
  loading,
  error
}: { 
  period: TimePeriodType
  onPeriodChange: (period: TimePeriodType) => void
  data: any
  loading: boolean
  error?: string
}) {
  const [sort, setSort] = useState<{ key: string | null; direction: SortDirection }>({ key: null, direction: null })

  // Mapuj dane z props
  const templates = responseData?.data || []
  const mappedData = templates.map((template: any, index: number) => {
    // Obsługa creator_name - preferuj name jeśli istnieje i nie jest pusty/null/undefined
    const creatorName = (template.creator_name != null && template.creator_name !== '' && typeof template.creator_name === 'string' && template.creator_name.trim() !== '')
      ? template.creator_name.trim()
      : template.creator_username || 'Unknown'
    
    // Obsługa category
    const category = (template.category != null && template.category !== '' && typeof template.category === 'string' && template.category.trim() !== '')
      ? template.category.trim()
      : null
    
    return {
      id: template.product_id,
      rank: index + 1,
      name: template.name,
      creator: creatorName,
      creatorId: template.creator_username,
      creatorAvatar: template.creator_avatar_url,
      category: category,
      views: template.views,
      isFree: template.is_free === true, // Explicit check for boolean true
      change: template.views_change_percent !== undefined && template.views_change_percent !== null ? {
        value: Math.abs(template.views_change_percent),
        isPositive: template.views_change_percent >= 0
      } : undefined
    }
  })

  // Sort data
  const sortedData = [...mappedData].sort((a, b) => {
    if (!sort.key || !sort.direction) return 0
    
    let aVal: any
    let bVal: any
    
    switch (sort.key) {
      case 'name':
        aVal = a.name?.toLowerCase() || ''
        bVal = b.name?.toLowerCase() || ''
        break
      case 'views':
        aVal = a.views || 0
        bVal = b.views || 0
        break
      case 'change':
        aVal = a.change?.value || 0
        bVal = b.change?.value || 0
        break
      default:
        return 0
    }
    
    if (aVal < bVal) return sort.direction === 'asc' ? -1 : 1
    if (aVal > bVal) return sort.direction === 'asc' ? 1 : -1
    return 0
  })

  const handleSort = (key: string) => {
    if (sort.key === key) {
      if (sort.direction === 'asc') {
        setSort({ key, direction: 'desc' })
      } else if (sort.direction === 'desc') {
        setSort({ key: null, direction: null })
      } else {
        setSort({ key, direction: 'asc' })
      }
    } else {
      setSort({ key, direction: 'asc' })
    }
  }

  return (
    <Card className="min-w-0 w-full">
      <CardHeader>
        <CardTitle>Most Popular Free Templates</CardTitle>
        <CardAction>
          <TimePeriodSelector period={period} onPeriodChange={onPeriodChange} />
        </CardAction>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        {loading ? (
          <div className="space-y-3">
            {[...Array(10)].map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-8 text-destructive">
            <p>Error loading data</p>
            <p className="text-sm text-muted-foreground">{error}</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">#</TableHead>
                <SortableTableHead sortKey="name" currentSort={sort} onSort={handleSort}>
                  Template
                </SortableTableHead>
                <SortableTableHead sortKey="views" currentSort={sort} onSort={handleSort} className="text-right">
                  Views
                </SortableTableHead>
                <SortableTableHead sortKey="change" currentSort={sort} onSort={handleSort} className="text-right">
                  Change
                </SortableTableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedData.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                    No data available
                  </TableCell>
                </TableRow>
              ) : (
                sortedData.map((row, index) => (
                  <TableRow key={row.id || index}>
                    <TableCell className="font-medium">{row.rank}</TableCell>
                    <TableCell>
                      <div className="flex flex-col">
                        <Link 
                          href={`https://www.framer.com/marketplace/templates/${row.id}/`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-medium hover:underline transition-colors"
                        >
                          {row.name}
                        </Link>
                        {(row.category || row.creator) && (
                          <span className="text-xs text-muted-foreground">
                            {row.category && row.creator ? `${row.category} • ${row.creator}` : row.category || row.creator}
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">{row.views?.toLocaleString() || '-'}</TableCell>
                    <TableCell className="text-right">
                      {row.change ? (
                        <Badge variant={row.change.isPositive ? 'default' : 'destructive'} className="flex items-center gap-1 w-fit">
                          {row.change.isPositive ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                          {row.change.value.toFixed(1)}%
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}

function CreatorsMostTemplates({ 
  period, 
  onPeriodChange,
  data: responseData,
  loading,
  error
}: { 
  period: TimePeriodType
  onPeriodChange: (period: TimePeriodType) => void
  data: any
  loading: boolean
  error?: string
}) {
  const [sort, setSort] = useState<{ key: string | null; direction: SortDirection }>({ key: null, direction: null })

  // Mapuj dane z props
  const creators = responseData?.data || []
  const mappedData = creators.map((creator: any, index: number) => {
    // Debug: sprawdź co przychodzi z API
    if (index === 0 && typeof window !== 'undefined') {
      console.log('Creator data from API (Most Templates):', creator)
    }
    
    // Obsługa name - preferuj name jeśli istnieje i nie jest pusty/null/undefined
    const creatorName = (creator.name != null && creator.name !== '' && typeof creator.name === 'string' && creator.name.trim() !== '')
      ? creator.name.trim() 
      : creator.username || 'Unknown'
    
    // Obsługa avatar_url - sprawdź czy istnieje i nie jest pusty/null/undefined
    const avatarUrl = (creator.avatar_url != null && creator.avatar_url !== '' && typeof creator.avatar_url === 'string' && creator.avatar_url.trim() !== '')
      ? creator.avatar_url.trim()
      : undefined
    
    // Debug: sprawdź zmapowane dane
    if (index === 0 && typeof window !== 'undefined') {
      console.log('Mapped creator data (Most Templates):', { name: creatorName, avatar: avatarUrl, originalName: creator.name, originalAvatar: creator.avatar_url })
    }
    
    return {
      id: creator.username,
      rank: index + 1,
      name: creatorName,
      avatar: avatarUrl,
      templatesCount: creator.templates_count,
      totalProducts: creator.total_products,
      totalViews: creator.total_views || null, // Total views może nie być dostępne w API
      change: creator.templates_change_percent !== undefined && creator.templates_change_percent !== null ? {
        value: Math.abs(creator.templates_change_percent),
        isPositive: creator.templates_change_percent >= 0
      } : undefined
    }
  })

  // Sort data
  const sortedData = [...mappedData].sort((a, b) => {
    if (!sort.key || !sort.direction) return 0
    
    let aVal: any
    let bVal: any
    
    switch (sort.key) {
      case 'name':
        aVal = a.name?.toLowerCase() || ''
        bVal = b.name?.toLowerCase() || ''
        break
      case 'templatesCount':
        aVal = a.templatesCount || 0
        bVal = b.templatesCount || 0
        break
      case 'change':
        aVal = a.change?.value || 0
        bVal = b.change?.value || 0
        break
      default:
        return 0
    }
    
    if (aVal < bVal) return sort.direction === 'asc' ? -1 : 1
    if (aVal > bVal) return sort.direction === 'asc' ? 1 : -1
    return 0
  })

  const handleSort = (key: string) => {
    if (sort.key === key) {
      if (sort.direction === 'asc') {
        setSort({ key, direction: 'desc' })
      } else if (sort.direction === 'desc') {
        setSort({ key: null, direction: null })
      } else {
        setSort({ key, direction: 'asc' })
      }
    } else {
      setSort({ key, direction: 'asc' })
    }
  }

  // Calculate total views for subtitle
  const totalViews = mappedData.reduce((sum: number, creator: any) => sum + (creator.totalViews || 0), 0)

  return (
    <Card className="min-w-0 w-full">
      <CardHeader>
        <div className="flex flex-col gap-1">
          <CardTitle>Creators with Most Templates</CardTitle>
          {!loading && !error && totalViews > 0 && (
            <p className="text-sm text-muted-foreground">
              {totalViews.toLocaleString()} total views
            </p>
          )}
        </div>
        <CardAction>
          <TimePeriodSelector period={period} onPeriodChange={onPeriodChange} />
        </CardAction>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        {loading ? (
          <div className="space-y-3">
            {[...Array(10)].map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-8 text-destructive">
            <p>Error loading data</p>
            <p className="text-sm text-muted-foreground">{error}</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">#</TableHead>
                <SortableTableHead sortKey="name" currentSort={sort} onSort={handleSort}>
                  Creator
                </SortableTableHead>
                <SortableTableHead sortKey="templatesCount" currentSort={sort} onSort={handleSort} className="text-right">
                  Templates
                </SortableTableHead>
                <SortableTableHead sortKey="change" currentSort={sort} onSort={handleSort} className="text-right">
                  Change
                </SortableTableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedData.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                    No data available
                  </TableCell>
                </TableRow>
              ) : (
                sortedData.map((row, index) => (
                  <TableRow key={row.id || index}>
                    <TableCell className="font-medium">{row.rank}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="h-8 w-8">
                          <AvatarImage src={row.avatar || undefined} alt={row.name || row.id} />
                          <AvatarFallback>
                            {row.name?.charAt(0)?.toUpperCase() || row.id?.charAt(0)?.toUpperCase() || '?'}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex flex-col">
                          <Link 
                            href={`https://www.framer.com/@${row.id}/`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-medium hover:underline transition-colors"
                          >
                            {row.name || row.id}
                          </Link>
                          {row.totalViews && (
                            <span className="text-xs text-muted-foreground">
                              {row.totalViews.toLocaleString()} total views
                            </span>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">{row.templatesCount?.toLocaleString() || '-'}</TableCell>
                    <TableCell className="text-right">
                      {row.change ? (
                        <Badge variant={row.change.isPositive ? 'default' : 'destructive'} className="flex items-center gap-1 w-fit">
                          {row.change.isPositive ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                          {row.change.value.toFixed(1)}%
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}
