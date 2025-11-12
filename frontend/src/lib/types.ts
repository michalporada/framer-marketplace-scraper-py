/**
 * TypeScript types and interfaces for dashboard
 */

export type TimePeriod = '1d' | '7d' | '30d'

export interface PercentageChange {
  value: number
  isPositive: boolean
  period: TimePeriod
}

export interface Creator {
  username: string
  name?: string
  avatar?: string
  total_views?: number
  templates_count?: number
  products_count?: number
}

export interface Product {
  product_id: string
  name: string
  product_type: 'template' | 'component' | 'vector' | 'plugin'
  creator_username: string
  views_normalized?: number
  is_free: boolean
  price?: number
  categories?: string[]
}

export interface Category {
  name: string
  total_views: number
  products_count: number
}

export interface DashboardBlockData {
  title: string
  period: TimePeriod
  data: DashboardRow[]
  loading?: boolean
  error?: string
}

export interface DashboardRow {
  id: string
  rank: number
  name: string
  value: number | string
  percentageChange?: PercentageChange
  metadata?: Record<string, any>
}

// API Response types
export interface APIResponse<T> {
  data: T
  meta?: {
    total?: number
    limit?: number
    offset?: number
    timestamp?: string
  }
}

export interface CreatorListResponse extends APIResponse<Creator[]> {}
export interface ProductListResponse extends APIResponse<Product[]> {}
export interface CategoryListResponse extends APIResponse<Category[]> {}

