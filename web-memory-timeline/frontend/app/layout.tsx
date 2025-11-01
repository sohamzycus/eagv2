import './globals.css'
import React from 'react'

export const metadata = {
  title: 'Web Memory & Context Timeline',
  icons: {
    icon: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="%23000"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Arial" font-size="28" fill="%23fff">WM</text></svg>'
  }
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body suppressHydrationWarning className="min-h-screen bg-gray-50 text-gray-900">
        <div className="max-w-5xl mx-auto px-4 py-6">
          <header className="mb-6">
            <h1 className="text-2xl font-semibold">Web Memory & Context Timeline</h1>
          </header>
          {children}
        </div>
      </body>
    </html>
  )
}
