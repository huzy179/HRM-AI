import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin", "vietnamese"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "HRM AI Recruitment & Assistant Suite",
  description: "Hệ thống sàng lọc hồ sơ CV và Chatbot quy chế nội bộ tối ưu bằng AI",
};

export default function RootLayout({
  children,
  modal,
}: Readonly<{
  children: React.ReactNode;
  modal?: React.ReactNode;
}>) {
  return (
    <html lang="vi" className={`${plusJakartaSans.variable} dark`}>
      <body className="font-sans antialiased bg-[#0B0F19] text-[#E2E8F0] min-h-screen">
        {children}
        {modal}
      </body>
    </html>
  );
}
