import "./globals.css";

export const metadata = {
  title: "ReFound — Buy second hand, first",
  description: "Search real stock from Auckland op shops. Save money, save time, and keep good things in use.",
  icons: { icon: "/favicon.svg" },
  openGraph: {
    title: "ReFound — Buy second hand, first",
    description: "Search real stock from Auckland op shops and keep good things in use.",
    images: ["/og.png"],
  },
  twitter: { card: "summary_large_image", images: ["/og.png"] },
};

export default function RootLayout({ children }) {
  return <html lang="en"><body>{children}</body></html>;
}
