import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function Home() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://framer-marketplace-scraper-py-production.up.railway.app'

  return (
    <main className="container mx-auto py-16 px-4">
      <div className="max-w-2xl mx-auto text-center">
        <h1 className="text-4xl font-bold tracking-tight mb-4">
          Framer Marketplace Scraper
        </h1>
        <p className="text-muted-foreground text-lg mb-8">
          Analytics and insights for Framer Marketplace data
        </p>
        
        <div className="flex gap-4 justify-center">
          <Button asChild>
            <Link href="/dashboard">View Dashboard</Link>
          </Button>
          <Button variant="outline" asChild>
            <a href={`${apiUrl}/docs`} target="_blank" rel="noopener noreferrer">
              API Documentation
            </a>
          </Button>
        </div>

        <div className="mt-12 p-6 bg-muted rounded-lg">
          <p className="text-sm text-muted-foreground">
            API URL: <code className="text-foreground">{apiUrl}</code>
          </p>
        </div>
      </div>
    </main>
  )
}

