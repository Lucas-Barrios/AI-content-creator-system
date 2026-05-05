import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SRH AI Content Creator",
  description: "Production frontend for SRH's RAG-powered content generation system"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
