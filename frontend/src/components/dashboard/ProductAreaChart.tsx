"use client"

import * as React from "react"
import { Area, AreaChart, CartesianGrid, XAxis } from "recharts"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  ChartConfig,
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

type ViewMode = "daily" | "total"

interface ProductAreaChartProps {
  data?: Array<{
    date: string
    templates: number
    vectors: number
    components: number
  }>
  loading?: boolean
}

const chartConfig = {
  templates: {
    label: "Templates",
    color: "var(--chart-1)",
  },
  vectors: {
    label: "Vectors",
    color: "var(--chart-2)",
  },
  components: {
    label: "Components",
    color: "var(--chart-3)",
  },
} satisfies ChartConfig

export function ProductAreaChart({ data = [], loading = false }: ProductAreaChartProps) {
  const [viewMode, setViewMode] = React.useState<ViewMode>("daily")

  // Transform data based on view mode
  const chartData = React.useMemo(() => {
    if (!data || data.length === 0) return []

    if (viewMode === "total") {
      // Calculate cumulative totals
      let templatesTotal = 0
      let vectorsTotal = 0
      let componentsTotal = 0

      return data.map((item) => {
        templatesTotal += item.templates
        vectorsTotal += item.vectors
        componentsTotal += item.components

        return {
          date: item.date,
          templates: templatesTotal,
          vectors: vectorsTotal,
          components: componentsTotal,
        }
      })
    }

    // Daily change mode - return data as is
    return data
  }, [data, viewMode])

  // Generate mock data if no data provided (for development)
  const mockData = React.useMemo(() => {
    if (data && data.length > 0) return null

    const dates: string[] = []
    const today = new Date()
    for (let i = 29; i >= 0; i--) {
      const date = new Date(today)
      date.setDate(date.getDate() - i)
      dates.push(date.toISOString().split("T")[0])
    }

    return dates.map((date) => ({
      date,
      templates: Math.floor(Math.random() * 50) + 10,
      vectors: Math.floor(Math.random() * 30) + 5,
      components: Math.floor(Math.random() * 40) + 8,
    }))
  }, [data])

  const displayData = chartData.length > 0 ? chartData : mockData || []

  return (
    <Card className="w-full">
      <CardHeader className="flex items-center gap-2 space-y-0 border-b py-5 sm:flex-row">
        <div className="grid flex-1 gap-1">
          <CardTitle>Product Growth</CardTitle>
          <CardDescription>
            {viewMode === "daily"
              ? "Daily change of new products"
              : "Total amount of products over time"}
          </CardDescription>
        </div>
        <Select value={viewMode} onValueChange={(value) => setViewMode(value as ViewMode)}>
          <SelectTrigger
            className="w-[180px] rounded-lg sm:ml-auto"
            aria-label="Select view mode"
          >
            <SelectValue placeholder="View mode" />
          </SelectTrigger>
          <SelectContent className="rounded-xl">
            <SelectItem value="daily" className="rounded-lg">
              Daily Change
            </SelectItem>
            <SelectItem value="total" className="rounded-lg">
              Total Amount
            </SelectItem>
          </SelectContent>
        </Select>
      </CardHeader>
      <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
        {loading ? (
          <div className="flex h-[300px] items-center justify-center">
            <p className="text-muted-foreground">Loading chart data...</p>
          </div>
        ) : (
          <ChartContainer
            config={chartConfig}
            className="aspect-auto h-[300px] w-full"
          >
            <AreaChart data={displayData}>
              <defs>
                <linearGradient id="fillTemplates" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="5%"
                    stopColor="var(--color-templates)"
                    stopOpacity={0.8}
                  />
                  <stop
                    offset="95%"
                    stopColor="var(--color-templates)"
                    stopOpacity={0.1}
                  />
                </linearGradient>
                <linearGradient id="fillVectors" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="5%"
                    stopColor="var(--color-vectors)"
                    stopOpacity={0.8}
                  />
                  <stop
                    offset="95%"
                    stopColor="var(--color-vectors)"
                    stopOpacity={0.1}
                  />
                </linearGradient>
                <linearGradient id="fillComponents" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="5%"
                    stopColor="var(--color-components)"
                    stopOpacity={0.8}
                  />
                  <stop
                    offset="95%"
                    stopColor="var(--color-components)"
                    stopOpacity={0.1}
                  />
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey="date"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                minTickGap={32}
                tickFormatter={(value) => {
                  const date = new Date(value)
                  return date.toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                  })
                }}
              />
              <ChartTooltip
                cursor={false}
                content={
                  <ChartTooltipContent
                    labelFormatter={(value) => {
                      return new Date(value).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })
                    }}
                    indicator="dot"
                  />
                }
              />
              <Area
                dataKey="templates"
                type="natural"
                fill="url(#fillTemplates)"
                stroke="var(--color-templates)"
                stackId="a"
              />
              <Area
                dataKey="vectors"
                type="natural"
                fill="url(#fillVectors)"
                stroke="var(--color-vectors)"
                stackId="a"
              />
              <Area
                dataKey="components"
                type="natural"
                fill="url(#fillComponents)"
                stroke="var(--color-components)"
                stackId="a"
              />
              <ChartLegend content={<ChartLegendContent />} />
            </AreaChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  )
}

