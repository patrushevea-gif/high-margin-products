import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/layout/Providers";

export const metadata: Metadata = {
  title: "Compass — Product Intelligence System",
  description: "Continuous Opportunity Mining and Product Acceleration System",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" className="dark">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
