'use client';

import "@/app/styles/globals.css";
import Sidebar from "@/app/components/SideBar";
import { PolygonProvider } from "./context/PolygonContext";
import { AuthProvider } from "./context/AuthContext";
import { usePathname } from "next/navigation";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isAuthPage = pathname === '/login' || pathname === '/register';

  return (
    <html lang="es">
      <body className="m-0 p-0 overflow-x-hidden">
        <AuthProvider>
          <PolygonProvider>
            {isAuthPage ? (
              // Sin sidebar en páginas de auth
              children
            ) : (
              // Con sidebar en páginas normales
              <div className="flex min-h-screen bg-slate-50">
                <Sidebar />
                <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto bg-gradient-to-b from-slate-50 to-slate-100 relative">
                  <div className="fixed top-0 right-0 w-1/2 h-1/2 pointer-events-none z-0 decorative-radial-gradient" />
                  <div className="relative z-10 pt-16 lg:pt-0">
                    {children}
                  </div>
                </main>
              </div>
            )}
          </PolygonProvider>
        </AuthProvider>
      </body>
    </html>
  );
}