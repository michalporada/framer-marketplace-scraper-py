'use client'

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardAction, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { ArrowUp, ArrowDown } from 'lucide-react'
import { getTopCreatorsByTemplateViews, getTopTemplates, getTopComponents, getTopCategories, getTopFreeTemplates, getTopCreatorsByTemplateCount, periodToHours } from '@/lib/api'
import { TimePeriod } from '@/lib/types'

type TimePeriodType = '1d' | '7d' | '30d'

export default function DashboardPage() {
  const [period, setPeriod] = useState<TimePeriodType>('1d')

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Analytics and insights for Framer Marketplace
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <TopCreatorsByViews period={period} onPeriodChange={setPeriod} />
        <MostPopularTemplates period={period} onPeriodChange={setPeriod} />
        <MostPopularComponents period={period} onPeriodChange={setPeriod} />
        <MostPopularCategories period={period} onPeriodChange={setPeriod} />
        <MostPopularFreeTemplates period={period} onPeriodChange={setPeriod} />
        <CreatorsMostTemplates period={period} onPeriodChange={setPeriod} />
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
  onPeriodChange 
}: { 
  period: TimePeriodType
  onPeriodChange: (period: TimePeriodType) => void 
}) {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<any[]>([])
  const [error, setError] = useState<string | undefined>()

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      setError(undefined)

      try {
        const periodHours = periodToHours(period)
        const response = await getTopCreatorsByTemplateViews({
          limit: 5,
          period_hours: periodHours
        })

        const creators = response.data || []
        
        setData(creators.map((creator: any, index: number) => ({
          id: creator.username,
          rank: index + 1,
          name: creator.name || creator.username,
          avatar: creator.avatar_url,
          views: creator.total_views,
          templatesCount: creator.templates_count,
          change: creator.views_change_percent !== undefined && creator.views_change_percent !== null ? {
            value: Math.abs(creator.views_change_percent),
            isPositive: creator.views_change_percent >= 0
          } : undefined
        })))
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
    <Card>
      <CardHeader>
        <CardTitle>Top Creators by Total Views</CardTitle>
        <CardAction>
          <TimePeriodSelector period={period} onPeriodChange={onPeriodChange} />
        </CardAction>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
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
                <TableHead>Creator</TableHead>
                <TableHead className="text-right">Views</TableHead>
                <TableHead className="text-right">Change</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                    No data available
                  </TableCell>
                </TableRow>
              ) : (
                data.map((row, index) => (
                  <TableRow key={row.id || index}>
                    <TableCell className="font-medium">{row.rank}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        {row.avatar && (
                          <Avatar className="h-8 w-8">
                            <AvatarImage src={row.avatar} alt={row.name} />
                            <AvatarFallback>{row.name?.charAt(0)?.toUpperCase()}</AvatarFallback>
                          </Avatar>
                        )}
                        <div className="flex flex-col">
                          <span className="font-medium">{row.name}</span>
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
  onPeriodChange 
}: { 
  period: TimePeriodType
  onPeriodChange: (period: TimePeriodType) => void 
}) {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<any[]>([])
  const [error, setError] = useState<string | undefined>()

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      setError(undefined)

      try {
        const periodHours = periodToHours(period)
        const response = await getTopTemplates({
          limit: 5,
          period_hours: periodHours
        })

        const templates = response.data || []
        
        setData(templates.map((template: any, index: number) => ({
          id: template.product_id,
          rank: index + 1,
          name: template.name,
          creator: template.creator_username || template.creator_name || 'Unknown',
          views: template.views,
          isFree: template.is_free,
          price: template.price,
          change: template.views_change_percent !== undefined && template.views_change_percent !== null ? {
            value: Math.abs(template.views_change_percent),
            isPositive: template.views_change_percent >= 0
          } : undefined
        })))
      } catch (err) {
        console.error('Error fetching top templates:', err)
        setError(err instanceof Error ? err.message : 'Failed to load data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [period])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Most Popular Templates</CardTitle>
        <CardAction>
          <TimePeriodSelector period={period} onPeriodChange={onPeriodChange} />
        </CardAction>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
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
                <TableHead>Template</TableHead>
                <TableHead>Creator</TableHead>
                <TableHead className="text-right">Views</TableHead>
                <TableHead className="text-right">Change</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                    No data available
                  </TableCell>
                </TableRow>
              ) : (
                data.map((row, index) => (
                  <TableRow key={row.id || index}>
                    <TableCell className="font-medium">{row.rank}</TableCell>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium">{row.name}</span>
                        <div className="flex items-center gap-2 mt-1">
                          {row.isFree ? (
                            <Badge variant="secondary" className="text-xs">Free</Badge>
                          ) : (
                            <Badge variant="outline" className="text-xs">
                              {row.price ? `$${row.price.toFixed(2)}` : 'Paid'}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{row.creator}</TableCell>
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

function MostPopularComponents({ 
  period, 
  onPeriodChange 
}: { 
  period: TimePeriodType
  onPeriodChange: (period: TimePeriodType) => void 
}) {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<any[]>([])
  const [error, setError] = useState<string | undefined>()

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      setError(undefined)

      try {
        const periodHours = periodToHours(period)
        const response = await getTopComponents({
          limit: 5,
          period_hours: periodHours
        })

        const components = response.data || []
        
        setData(components.map((component: any, index: number) => ({
          id: component.product_id,
          rank: index + 1,
          name: component.name,
          creator: component.creator_username || component.creator_name || 'Unknown',
          views: component.views,
          isFree: component.is_free,
          price: component.price,
          change: component.views_change_percent !== undefined && component.views_change_percent !== null ? {
            value: Math.abs(component.views_change_percent),
            isPositive: component.views_change_percent >= 0
          } : undefined
        })))
      } catch (err) {
        console.error('Error fetching top components:', err)
        setError(err instanceof Error ? err.message : 'Failed to load data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [period])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Most Popular Components</CardTitle>
        <CardAction>
          <TimePeriodSelector period={period} onPeriodChange={onPeriodChange} />
        </CardAction>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
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
                <TableHead>Component</TableHead>
                <TableHead>Creator</TableHead>
                <TableHead className="text-right">Views</TableHead>
                <TableHead className="text-right">Change</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                    No data available
                  </TableCell>
                </TableRow>
              ) : (
                data.map((row, index) => (
                  <TableRow key={row.id || index}>
                    <TableCell className="font-medium">{row.rank}</TableCell>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium">{row.name}</span>
                        <div className="flex items-center gap-2 mt-1">
                          {row.isFree ? (
                            <Badge variant="secondary" className="text-xs">Free</Badge>
                          ) : (
                            <Badge variant="outline" className="text-xs">
                              {row.price ? `$${row.price.toFixed(2)}` : 'Paid'}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{row.creator}</TableCell>
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
  onPeriodChange 
}: { 
  period: TimePeriodType
  onPeriodChange: (period: TimePeriodType) => void 
}) {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<any[]>([])
  const [error, setError] = useState<string | undefined>()

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      setError(undefined)

      try {
        const periodHours = periodToHours(period)
        const response = await getTopCategories({
          limit: 5,
          period_hours: periodHours
        })

        const categories = response.data || []
        
        setData(categories.map((category: any, index: number) => ({
          id: category.category_name,
          rank: index + 1,
          name: category.category_name,
          views: category.total_views,
          productsCount: category.products_count,
          change: category.views_change_percent !== undefined && category.views_change_percent !== null ? {
            value: Math.abs(category.views_change_percent),
            isPositive: category.views_change_percent >= 0
          } : undefined
        })))
      } catch (err) {
        console.error('Error fetching top categories:', err)
        setError(err instanceof Error ? err.message : 'Failed to load data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [period])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Most Popular Categories</CardTitle>
        <CardAction>
          <TimePeriodSelector period={period} onPeriodChange={onPeriodChange} />
        </CardAction>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
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
                <TableHead>Category</TableHead>
                <TableHead className="text-right">Products</TableHead>
                <TableHead className="text-right">Views</TableHead>
                <TableHead className="text-right">Change</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                    No data available
                  </TableCell>
                </TableRow>
              ) : (
                data.map((row, index) => (
                  <TableRow key={row.id || index}>
                    <TableCell className="font-medium">{row.rank}</TableCell>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium">{row.name}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">{row.productsCount?.toLocaleString() || '-'}</TableCell>
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
  onPeriodChange 
}: { 
  period: TimePeriodType
  onPeriodChange: (period: TimePeriodType) => void 
}) {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<any[]>([])
  const [error, setError] = useState<string | undefined>()

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      setError(undefined)

      try {
        const periodHours = periodToHours(period)
        const response = await getTopFreeTemplates({
          limit: 5,
          period_hours: periodHours
        })

        const templates = response.data || []
        
        setData(templates.map((template: any, index: number) => ({
          id: template.product_id,
          rank: index + 1,
          name: template.name,
          creator: template.creator_username || template.creator_name || 'Unknown',
          views: template.views,
          isFree: template.is_free,
          change: template.views_change_percent !== undefined && template.views_change_percent !== null ? {
            value: Math.abs(template.views_change_percent),
            isPositive: template.views_change_percent >= 0
          } : undefined
        })))
      } catch (err) {
        console.error('Error fetching top free templates:', err)
        setError(err instanceof Error ? err.message : 'Failed to load data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [period])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Most Popular Free Templates</CardTitle>
        <CardAction>
          <TimePeriodSelector period={period} onPeriodChange={onPeriodChange} />
        </CardAction>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
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
                <TableHead>Template</TableHead>
                <TableHead>Creator</TableHead>
                <TableHead className="text-right">Views</TableHead>
                <TableHead className="text-right">Change</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                    No data available
                  </TableCell>
                </TableRow>
              ) : (
                data.map((row, index) => (
                  <TableRow key={row.id || index}>
                    <TableCell className="font-medium">{row.rank}</TableCell>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium">{row.name}</span>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="secondary" className="text-xs">Free</Badge>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{row.creator}</TableCell>
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
  onPeriodChange 
}: { 
  period: TimePeriodType
  onPeriodChange: (period: TimePeriodType) => void 
}) {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<any[]>([])
  const [error, setError] = useState<string | undefined>()

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      setError(undefined)

      try {
        const periodHours = periodToHours(period)
        const response = await getTopCreatorsByTemplateCount({
          limit: 5,
          period_hours: periodHours
        })

        const creators = response.data || []
        
        setData(creators.map((creator: any, index: number) => ({
          id: creator.username,
          rank: index + 1,
          name: creator.name || creator.username,
          avatar: creator.avatar_url,
          templatesCount: creator.templates_count,
          totalProducts: creator.total_products,
          change: creator.templates_change_percent !== undefined && creator.templates_change_percent !== null ? {
            value: Math.abs(creator.templates_change_percent),
            isPositive: creator.templates_change_percent >= 0
          } : undefined
        })))
      } catch (err) {
        console.error('Error fetching top creators by template count:', err)
        setError(err instanceof Error ? err.message : 'Failed to load data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [period])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Creators with Most Templates</CardTitle>
        <CardAction>
          <TimePeriodSelector period={period} onPeriodChange={onPeriodChange} />
        </CardAction>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
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
                <TableHead>Creator</TableHead>
                <TableHead className="text-right">Templates</TableHead>
                <TableHead className="text-right">Total Products</TableHead>
                <TableHead className="text-right">Change</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                    No data available
                  </TableCell>
                </TableRow>
              ) : (
                data.map((row, index) => (
                  <TableRow key={row.id || index}>
                    <TableCell className="font-medium">{row.rank}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        {row.avatar && (
                          <Avatar className="h-8 w-8">
                            <AvatarImage src={row.avatar} alt={row.name} />
                            <AvatarFallback>{row.name?.charAt(0)?.toUpperCase()}</AvatarFallback>
                          </Avatar>
                        )}
                        <div className="flex flex-col">
                          <span className="font-medium">{row.name}</span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">{row.templatesCount?.toLocaleString() || '-'}</TableCell>
                    <TableCell className="text-right">{row.totalProducts?.toLocaleString() || '-'}</TableCell>
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
