import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Framer Marketplace Scraper',
  description: 'Dashboard for Framer Marketplace data',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  )
}

