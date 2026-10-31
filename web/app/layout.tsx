import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "Flamingo Next Studio",
  description:
    "Your private creative workspace. Independent, local, and thoughtfully made.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
