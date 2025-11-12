/**
 * API client functions for dashboard
 */

// Use local API if available, fallback to production
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : 'https://framer-marketplace-scraper-py-production.up.railway.app')

async function fetchAPI<T>(endpoint: string): Promise<T> {
  // Determine API URL - prefer localhost when running locally
  const apiUrl = typeof window !== 'undefined' && window.location.hostname === 'localhost' 
    ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
    : (process.env.NEXT_PUBLIC_API_URL || 'https://framer-marketplace-scraper-py-production.up.railway.app')
  
  const url = `${apiUrl}${endpoint}`
  console.log('Fetching:', url)
  
  try {
    const response = await fetch(url, {
      // Add timeout for better error handling (reduced for faster feedback)
      signal: AbortSignal.timeout(10000) // 10 seconds
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('API Error:', response.status, response.statusText, errorText)
      
      // Provide more user-friendly error messages
      if (response.status === 502 || response.status === 503) {
        throw new Error(`API is currently unavailable. Please check if the API server is running.`)
      } else if (response.status === 500) {
        throw new Error(`Server error: ${errorText.substring(0, 200)}`)
      } else {
        throw new Error(`API Error: ${response.status} ${response.statusText}`)
      }
    }
    
    const data = await response.json()
    console.log('API Response:', endpoint, 'OK')
    return data
  } catch (error: any) {
    console.error('Fetch error:', error)
    
    // Handle timeout
    if (error.name === 'AbortError' || error.name === 'TimeoutError') {
      throw new Error('Request timeout - API is not responding. Please check if the API server is running.')
    }
    
    // Handle network errors
    if (error.message?.includes('Failed to fetch') || error.message?.includes('NetworkError')) {
      throw new Error('Cannot connect to API. Please check if the API server is running at ' + apiUrl)
    }
    
    throw error
  }
}

// Creators API
export async function getCreators(params?: {
  limit?: number
  offset?: number
  sort?: string
}): Promise<{ data: any[]; meta?: any }> {
  const queryParams = new URLSearchParams()
  if (params?.limit) queryParams.set('limit', params.limit.toString())
  if (params?.offset) queryParams.set('offset', params.offset.toString())
  if (params?.sort) queryParams.set('sort', params.sort)
  
  const query = queryParams.toString()
  return fetchAPI(`/api/creators${query ? `?${query}` : ''}`)
}

export async function getCreator(username: string): Promise<{ data: any; meta?: any }> {
  return fetchAPI(`/api/creators/${username}`)
}

export async function getCreatorProducts(
  username: string,
  params?: { type?: string; limit?: number }
): Promise<{ data: any[]; meta?: any }> {
  const queryParams = new URLSearchParams()
  if (params?.type) queryParams.set('type', params.type)
  if (params?.limit) queryParams.set('limit', params.limit.toString())
  
  const query = queryParams.toString()
  return fetchAPI(`/api/creators/${username}/products${query ? `?${query}` : ''}`)
}

// Products API
export async function getProducts(params?: {
  type?: string
  limit?: number
  offset?: number
  sort?: string
  order?: 'asc' | 'desc'
}): Promise<{ data: any[]; meta?: any }> {
  const queryParams = new URLSearchParams()
  if (params?.type) queryParams.set('type', params.type)
  if (params?.limit) queryParams.set('limit', params.limit.toString())
  if (params?.offset) queryParams.set('offset', params.offset.toString())
  if (params?.sort) queryParams.set('sort', params.sort)
  if (params?.order) queryParams.set('order', params.order)
  
  const query = queryParams.toString()
  return fetchAPI(`/api/products${query ? `?${query}` : ''}`)
}

export async function getProduct(productId: string): Promise<{ data: any; meta?: any }> {
  return fetchAPI(`/api/products/${productId}`)
}

export async function getProductChanges(
  productId: string,
  periodHours?: number
): Promise<{ data: any; meta?: any }> {
  const query = periodHours ? `?period_hours=${periodHours}` : ''
  return fetchAPI(`/api/products/${productId}/changes${query}`)
}

// Categories API
export async function getCategories(params?: {
  limit?: number
  offset?: number
}): Promise<{ data: any[]; meta?: any }> {
  const queryParams = new URLSearchParams()
  if (params?.limit) queryParams.set('limit', params.limit.toString())
  if (params?.offset) queryParams.set('offset', params.offset.toString())
  
  const query = queryParams.toString()
  return fetchAPI(`/api/categories${query ? `?${query}` : ''}`)
}

export async function getCategory(categoryName: string): Promise<{ data: any; meta?: any }> {
  return fetchAPI(`/api/categories/${categoryName}`)
}

// Top Creators by Template Views
// Note: Using existing endpoint and processing on frontend until new endpoint is deployed
export async function getTopCreatorsByTemplateViews(params?: {
  limit?: number
  period_hours?: number
}): Promise<{ data: any[]; meta?: any }> {
  // Get all creators and their products, then aggregate
  const limit = params?.limit || 5
  const creatorsResponse = await getCreators({ limit: 100, sort: 'username' })
  const creators = creatorsResponse.data || []
  
  // Get products for each creator and aggregate views (batch processing to limit concurrent requests)
  // Process in batches of 5 to avoid overwhelming the API
  const batchSize = 5
  const creatorsWithViews: any[] = []
  
  for (let i = 0; i < Math.min(creators.length, 20); i += batchSize) { // Limit to first 20 creators
    const batch = creators.slice(i, i + batchSize)
    const batchResults = await Promise.all(
      batch.map(async (creator) => {
        try {
          const productsResponse = await getCreatorProducts(creator.username, { type: 'template', limit: 20 })
          const templates = productsResponse.data || []
          const totalViews = templates.reduce((sum: number, p: any) => {
            return sum + (p.stats?.views?.normalized || 0)
          }, 0)
          return {
            username: creator.username,
            name: creator.name || creator.username,
            avatar_url: creator.avatar_url,
            total_views: totalViews,
            templates_count: templates.length,
            views_change_percent: null // Not available without history endpoint
          }
        } catch (error) {
          console.error(`Error fetching products for creator ${creator.username}:`, error)
          return {
            username: creator.username,
            name: creator.name || creator.username,
            avatar_url: creator.avatar_url,
            total_views: 0,
            templates_count: 0,
            views_change_percent: null
          }
        }
      })
    )
    creatorsWithViews.push(...batchResults)
    
    // Small delay between batches to avoid overwhelming the API
    if (i + batchSize < Math.min(creators.length, 20)) {
      await new Promise(resolve => setTimeout(resolve, 100)) // 100ms delay
    }
  }
  
  // Sort by total_views and return top N
  const sorted = creatorsWithViews
    .filter(c => c.total_views > 0)
    .sort((a, b) => b.total_views - a.total_views)
    .slice(0, limit)
  
  return {
    data: sorted,
    meta: { timestamp: new Date().toISOString() }
  }
}

// Top Templates by Views
// Simplified: Use dedicated endpoint if available, fallback to products endpoint
export async function getTopTemplates(params?: {
  limit?: number
  period_hours?: number
}): Promise<{ data: any[]; meta?: any }> {
  const limit = params?.limit || 5
  const periodHours = params?.period_hours || 24
  
  try {
    // Try dedicated endpoint first
    const query = `limit=${limit}&period_hours=${periodHours}`
    return await fetchAPI(`/api/products/top-templates?${query}`)
  } catch (error) {
    console.warn('Dedicated endpoint not available, using products endpoint:', error)
    // Fallback to simple products endpoint
    const response = await getProducts({
      type: 'template',
      sort: 'views_normalized',
      order: 'desc',
      limit
    })
    
    return {
      data: (response.data || []).map((product: any) => ({
        ...product,
        views_change_percent: null
      })),
      meta: response.meta
    }
  }
}

// Top Components by Views
// Simplified: Use dedicated endpoint if available, fallback to products endpoint
export async function getTopComponents(params?: {
  limit?: number
  period_hours?: number
}): Promise<{ data: any[]; meta?: any }> {
  const limit = params?.limit || 5
  const periodHours = params?.period_hours || 24
  
  try {
    // Try dedicated endpoint first
    const query = `limit=${limit}&period_hours=${periodHours}`
    return await fetchAPI(`/api/products/top-components?${query}`)
  } catch (error) {
    console.warn('Dedicated endpoint not available, using products endpoint:', error)
    // Fallback to simple products endpoint
    const response = await getProducts({
      type: 'component',
      sort: 'views_normalized',
      order: 'desc',
      limit
    })
    
    return {
      data: (response.data || []).map((product: any) => ({
        ...product,
        views_change_percent: null
      })),
      meta: response.meta
    }
  }
}

// Top Categories by Views
// Simplified: Use dedicated endpoint if available, otherwise return empty
export async function getTopCategories(params?: {
  limit?: number
  period_hours?: number
  product_type?: string
}): Promise<{ data: any[]; meta?: any }> {
  const limit = params?.limit || 5
  const periodHours = params?.period_hours || 24
  const productType = params?.product_type || 'template'
  
  try {
    // Try dedicated endpoint first
    const query = `limit=${limit}&period_hours=${periodHours}&product_type=${productType}`
    return await fetchAPI(`/api/products/categories/top-by-views?${query}`)
  } catch (error) {
    console.warn('Dedicated endpoint not available, returning empty data:', error)
    // Return empty data instead of making many requests
    return {
      data: [],
      meta: { timestamp: new Date().toISOString() }
    }
  }
}

// Top Free Templates by Views
// Simplified: Use dedicated endpoint if available, fallback to products endpoint
export async function getTopFreeTemplates(params?: {
  limit?: number
  period_hours?: number
}): Promise<{ data: any[]; meta?: any }> {
  const limit = params?.limit || 5
  const periodHours = params?.period_hours || 24
  
  try {
    // Try dedicated endpoint first
    const query = `limit=${limit}&period_hours=${periodHours}`
    return await fetchAPI(`/api/products/top-free-templates?${query}`)
  } catch (error) {
    console.warn('Dedicated endpoint not available, using products endpoint:', error)
    // Fallback: get templates and filter free ones
    const response = await getProducts({
      type: 'template',
      sort: 'views_normalized',
      order: 'desc',
      limit: 50 // Reduced limit
    })
    
    const freeTemplates = (response.data || [])
      .filter((product: any) => product.is_free === true)
      .slice(0, limit)
      .map((product: any) => ({
        ...product,
        views_change_percent: null
      }))
    
    return {
      data: freeTemplates,
      meta: { timestamp: new Date().toISOString() }
    }
  }
}

// Top Creators by Template Count
// Simplified: Use dedicated endpoint if available, otherwise return empty
export async function getTopCreatorsByTemplateCount(params?: {
  limit?: number
  period_hours?: number
}): Promise<{ data: any[]; meta?: any }> {
  const limit = params?.limit || 5
  const periodHours = params?.period_hours || 24
  
  try {
    // Try dedicated endpoint first
    const query = `limit=${limit}&period_hours=${periodHours}`
    return await fetchAPI(`/api/creators/top-by-template-count?${query}`)
  } catch (error) {
    console.warn('Dedicated endpoint not available, returning empty data:', error)
    // Return empty data instead of making many requests
    return {
      data: [],
      meta: { timestamp: new Date().toISOString() }
    }
  }
}

// Helper function to convert period to hours
export function periodToHours(period: '1d' | '7d' | '30d'): number {
  switch (period) {
    case '1d':
      return 24
    case '7d':
      return 168
    case '30d':
      return 720
    default:
      return 24
  }
}

