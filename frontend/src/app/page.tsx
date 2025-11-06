export default function Home() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  return (
    <main style={{ padding: '2rem', fontFamily: 'system-ui' }}>
      <h1>Framer Marketplace Scraper</h1>
      <p>Frontend is running!</p>
      <p>API URL: {apiUrl}</p>
      <p>
        <a href={`${apiUrl}/docs`} target="_blank" rel="noopener noreferrer">
          View API Docs
        </a>
      </p>
    </main>
  )
}

