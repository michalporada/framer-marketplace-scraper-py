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
  
  // Get products for each creator and aggregate views (limit concurrent requests)
  const creatorsWithViews = await Promise.all(
    creators.slice(0, 50).map(async (creator) => { // Limit to first 50 creators for performance
      try {
        const productsResponse = await getCreatorProducts(creator.username, { type: 'template', limit: 50 })
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
// Using existing endpoint: /api/products?type=template&sort=views_normalized&order=desc
export async function getTopTemplates(params?: {
  limit?: number
  period_hours?: number
}): Promise<{ data: any[]; meta?: any }> {
  const limit = params?.limit || 5
  const response = await getProducts({
    type: 'template',
    sort: 'views_normalized',
    order: 'desc',
    limit
  })
  
  // Skip fetching changes for now to improve performance (can be added later)
  // The changes endpoint is slow and causes timeouts
  const templatesWithChanges = (response.data || []).map((product: any) => ({
    ...product,
    views_change_percent: null // Disabled for performance
  }))
  
  return {
    data: templatesWithChanges,
    meta: response.meta
  }
}

// Top Components by Views
// Using existing endpoint: /api/products?type=component&sort=views_normalized&order=desc
export async function getTopComponents(params?: {
  limit?: number
  period_hours?: number
}): Promise<{ data: any[]; meta?: any }> {
  const limit = params?.limit || 5
  const response = await getProducts({
    type: 'component',
    sort: 'views_normalized',
    order: 'desc',
    limit
  })
  
  // Skip fetching changes for now to improve performance (can be added later)
  // The changes endpoint is slow and causes timeouts
  const componentsWithChanges = (response.data || []).map((product: any) => ({
    ...product,
    views_change_percent: null // Disabled for performance
  }))
  
  return {
    data: componentsWithChanges,
    meta: response.meta
  }
}

// Top Categories by Views
// Using existing endpoint: /api/products?limit=100 and aggregate on frontend
export async function getTopCategories(params?: {
  limit?: number
  period_hours?: number
  product_type?: string
}): Promise<{ data: any[]; meta?: any }> {
  const limit = params?.limit || 5
  const productType = params?.product_type || 'template'
  
  // Get products of the specified type (reduced limit for performance)
  const response = await getProducts({
    type: productType,
    limit: 100,
    sort: 'views_normalized',
    order: 'desc'
  })
  
  // Aggregate by category
  const categoryMap = new Map<string, { views: number; products: number; names: string[] }>()
  
  ;(response.data || []).forEach((product: any) => {
    const categories = product.metadata?.categories || []
    const views = product.stats?.views?.normalized || 0
    
    categories.forEach((category: string) => {
      if (!categoryMap.has(category)) {
        categoryMap.set(category, { views: 0, products: 0, names: [] })
      }
      const cat = categoryMap.get(category)!
      cat.views += views
      cat.products += 1
      if (!cat.names.includes(product.name)) {
        cat.names.push(product.name)
      }
    })
  })
  
  // Convert to array and sort
  const categories = Array.from(categoryMap.entries())
    .map(([name, data]) => ({
      name,
      total_views: data.views,
      products_count: data.products,
      views_change_percent: null // Not available without history endpoint
    }))
    .sort((a, b) => b.total_views - a.total_views)
    .slice(0, limit)
  
  return {
    data: categories,
    meta: { timestamp: new Date().toISOString() }
  }
}

// Top Free Templates by Views
// Using existing endpoint: /api/products?type=template&sort=views_normalized&order=desc&limit=100
// Filter by is_free on frontend
export async function getTopFreeTemplates(params?: {
  limit?: number
  period_hours?: number
}): Promise<{ data: any[]; meta?: any }> {
  const limit = params?.limit || 5
  
  // Get templates (reduced limit for performance)
  const response = await getProducts({
    type: 'template',
    sort: 'views_normalized',
    order: 'desc',
    limit: 100 // Get more to filter free ones, but not too many
  })
  
  // Filter free templates
  const freeTemplates = (response.data || [])
    .filter((product: any) => product.is_free === true)
    .slice(0, limit)
  
  // Skip fetching changes for now to improve performance (can be added later)
  // The changes endpoint is slow and causes timeouts
  const templatesWithChanges = freeTemplates.map((product: any) => ({
    ...product,
    views_change_percent: null // Disabled for performance
  }))
  
  return {
    data: templatesWithChanges,
    meta: { timestamp: new Date().toISOString() }
  }
}

// Top Creators by Template Count
// Using existing endpoint: /api/creators?sort=total_products&order=desc&limit=5
// Filter by templates_count on frontend
export async function getTopCreatorsByTemplateCount(params?: {
  limit?: number
  period_hours?: number
}): Promise<{ data: any[]; meta?: any }> {
  const limit = params?.limit || 5
  
  // Get creators sorted by total_products (reduced limit for performance)
  const response = await getCreators({
    sort: 'total_products',
    limit: 100 // Get more to filter by template count, but not too many
  })
  
  // Get template count for each creator (limit concurrent requests)
  const creatorsWithTemplateCount = await Promise.all(
    (response.data || []).slice(0, 50).map(async (creator: any) => { // Limit to first 50 for performance
      try {
        const productsResponse = await getCreatorProducts(creator.username, { type: 'template', limit: 50 })
        const templatesCount = (productsResponse.data || []).length
        return {
          ...creator,
          templates_count: templatesCount
        }
      } catch (error) {
        console.error(`Error fetching products for creator ${creator.username}:`, error)
        return {
          ...creator,
          templates_count: 0
        }
      }
    })
  )
  
  // Sort by templates_count and return top N
  const sorted = creatorsWithTemplateCount
    .filter(c => c.templates_count > 0)
    .sort((a, b) => b.templates_count - a.templates_count)
    .slice(0, limit)
  
  return {
    data: sorted,
    meta: { timestamp: new Date().toISOString() }
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

