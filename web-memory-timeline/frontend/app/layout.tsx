import './globals.css'
import React from 'react'

export const metadata = {
  title: 'Web Memory & Context Timeline'
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900">
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
