import React from "react"
import type { Metadata } from 'next'
import Script from 'next/script'
import { Instrument_Sans, Instrument_Serif, JetBrains_Mono } from 'next/font/google'
import './globals.css'

const instrumentSans = Instrument_Sans({
  subsets: ["latin"],
  variable: '--font-instrument'
});

const instrumentSerif = Instrument_Serif({
  subsets: ["latin"],
  weight: "400",
  variable: '--font-instrument-serif'
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: '--font-jetbrains'
});

export const metadata: Metadata = {
  title: 'RORY - Pediatric Sepsis Early-Warning System',
  description: 'A tablet a nurse uses in the first 90 seconds. Enter vitals, describe what you see, get HOME / ED / 911 with citations. Named after Rory Staunton (1999-2012).',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`${instrumentSans.variable} ${instrumentSerif.variable} ${jetbrainsMono.variable} font-sans antialiased`}>
        {children}
        {/* @ts-expect-error - elevenlabs-convai is a custom element */}
        <elevenlabs-convai agent-id="agent_1501kp0wc3sdesxap05bmzdhkez1"></elevenlabs-convai>
        <Script src="https://unpkg.com/@elevenlabs/convai-widget-embed" strategy="lazyOnload" />
      </body>
    </html>
  )
}
