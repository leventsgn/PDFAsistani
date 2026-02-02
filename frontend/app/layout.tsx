export const metadata = {
  title: "Osmanlica Arsiv - PDF Soru-Cevap",
  description: "PDF yukleyin, sorular sorun ve kaynaklari gorun."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body style={{ fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif", margin: 0, padding: 0 }}>
        {children}
      </body>
    </html>
  );
}
