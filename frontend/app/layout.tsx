import "@/app/styles/globals.css";
import Sidebar from "@/app/components/SideBar";
import { PolygonProvider } from "./context/PolygonContext";

export const metadata = {
  title: 'Agricultura de Precisión | Centro de Procesamiento de Imágenes',
  description: 'Plataforma de análisis satelital para agricultura de precisión. Monitorea y optimiza la salud de tus cultivos con tecnología Sentinel-2 e inteligencia artificial.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className="m-0 p-0 overflow-x-hidden">
        <PolygonProvider>
          <div className="flex min-h-screen bg-slate-50">
            <Sidebar />
            <main className="flex-1 p-8 overflow-y-auto bg-gradient-to-b from-slate-50 to-slate-100 relative">
              {/* Decorative gradient */}
              <div className="fixed top-0 right-0 w-1/2 h-1/2 pointer-events-none z-0 decorative-radial-gradient" />
              <div className="relative z-10">
                {children}
              </div>
            </main>
          </div>
        </PolygonProvider>
      </body>
    </html>
  );
}