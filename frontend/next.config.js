/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://framer-marketplace-scraper-py-production.up.railway.app',
  },
}

module.exports = nextConfig

