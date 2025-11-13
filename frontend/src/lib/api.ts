/**
 * API client functions for dashboard
 */

// Use local API if available, fallback to production
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : 'https://framer-marketplace-scraper-py-production.up.railway.app')

async function fetchAPI<T>(endpoint: string, retries = 2): Promise<T> {
  // Determine API URL - prefer localhost when running locally
  const apiUrl = typeof window !== 'undefined' && window.location.hostname === 'localhost' 
    ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
    : (process.env.NEXT_PUBLIC_API_URL || 'https://framer-marketplace-scraper-py-production.up.railway.app')
  
  const url = `${apiUrl}${endpoint}`
  console.log('Fetching:', url)
  
  // Retry logic with exponential backoff
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 seconds timeout
      
      const response = await fetch(url, {
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('API Error:', response.status, response.statusText, errorText)
        
        // Don't retry on client errors (4xx)
        if (response.status >= 400 && response.status < 500) {
          // Provide more user-friendly error messages
          if (response.status === 404) {
            throw new Error('Resource not found')
          } else if (response.status === 429) {
            throw new Error('Too many requests. Please try again later.')
          } else {
            throw new Error(`API Error: ${response.status} ${response.statusText}`)
          }
        }
        
        // Retry on server errors (5xx) if we have retries left
        if (response.status >= 500 && attempt < retries) {
          const delay = Math.pow(2, attempt) * 1000 // Exponential backoff: 1s, 2s, 4s
          console.warn(`Server error ${response.status}, retrying in ${delay}ms... (attempt ${attempt + 1}/${retries + 1})`)
          await new Promise(resolve => setTimeout(resolve, delay))
          continue
        }
        
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
      // Handle timeout
      if (error.name === 'AbortError' || error.name === 'TimeoutError') {
        if (attempt < retries) {
          const delay = Math.pow(2, attempt) * 1000 // Exponential backoff
          console.warn(`Request timeout, retrying in ${delay}ms... (attempt ${attempt + 1}/${retries + 1})`)
          await new Promise(resolve => setTimeout(resolve, delay))
          continue
        }
        throw new Error('Request timeout - API is not responding. Please check if the API server is running.')
      }
      
      // Handle network errors
      if (error.message?.includes('Failed to fetch') || error.message?.includes('NetworkError')) {
        if (attempt < retries) {
          const delay = Math.pow(2, attempt) * 1000 // Exponential backoff
          console.warn(`Network error, retrying in ${delay}ms... (attempt ${attempt + 1}/${retries + 1})`)
          await new Promise(resolve => setTimeout(resolve, delay))
          continue
        }
        throw new Error('Cannot connect to API. Please check if the API server is running at ' + apiUrl)
      }
      
      // If it's not a retryable error, throw immediately
      if (attempt === retries) {
        console.error('Fetch error (final attempt):', error)
        throw error
      }
      
      // For other errors, retry if we have attempts left
      const delay = Math.pow(2, attempt) * 1000
      console.warn(`Error occurred, retrying in ${delay}ms... (attempt ${attempt + 1}/${retries + 1})`, error)
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }
  
  // This should never be reached, but TypeScript needs it
  throw new Error('Failed to fetch after all retries')
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
// Simplified: Use dedicated endpoint if available, otherwise return empty
export async function getTopCreatorsByTemplateViews(params?: {
  limit?: number
  period_hours?: number
}): Promise<{ data: any[]; meta?: any }> {
  const limit = params?.limit || 5
  const periodHours = params?.period_hours || 24
  
  try {
    // Try dedicated endpoint first
    const query = `limit=${limit}&period_hours=${periodHours}`
    return await fetchAPI(`/api/creators/top-by-template-views?${query}`)
  } catch (error) {
    console.warn('Dedicated endpoint not available, [returning empty data / using products endpoint]:', error)
    // Return empty data instead of making many requests
    return {
      data: [],
      meta: { timestamp: new Date().toISOString() }
    }
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
    console.warn('Dedicated endpoint not available, [returning empty data / using products endpoint]:', error)
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
    console.warn('Dedicated endpoint not available, [returning empty data / using products endpoint]:', error)
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
    console.warn('Dedicated endpoint not available, [returning empty data / using products endpoint]:', error)
    // Return empty data instead of making many requests
    return {
      data: [],
      meta: { timestamp: new Date().toISOString() }
    }
  }
}

// Smallest Categories by Product Count
// Uses the same endpoint but sorts by products_count ascending
export async function getSmallestCategories(params?: {
  limit?: number
  period_hours?: number
  product_type?: string
}): Promise<{ data: any[]; meta?: any }> {
  const limit = params?.limit || 5
  const periodHours = params?.period_hours || 24
  const productType = params?.product_type || 'template'
  
  try {
    // Get more categories than needed, then sort and take smallest
    const query = `limit=100&period_hours=${periodHours}&product_type=${productType}`
    const response = await fetchAPI(`/api/products/categories/top-by-views?${query}`)
    
    // Sort by products_count ascending and take top N
    const sorted = (response.data || []).sort((a: any, b: any) => {
      const countA = a.products_count || 0
      const countB = b.products_count || 0
      return countA - countB
    })
    
    return {
      data: sorted.slice(0, limit),
      meta: response.meta || { timestamp: new Date().toISOString() }
    }
  } catch (error) {
    console.warn('Error fetching smallest categories:', error)
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
    console.warn('Dedicated endpoint not available, [returning empty data / using products endpoint]:', error)
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
    console.warn('Dedicated endpoint not available, [returning empty data / using products endpoint]:', error)
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

