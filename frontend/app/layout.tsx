import "@/app/styles/globals.css"; // Asegúrate de importar CSS global
import Sidebar from "@/app/components/SideBar";

export const metadata = {
  title: 'Agricultura de Precisión',
  description: 'Explora, analiza y optimiza tus cultivos con agricultura de precisión.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className="flex">
        {/* Sidebar */}
        <Sidebar />

        {/* Main Content */}
        <div className="flex-1 bg-gray-100 p-6">{children}</div>
      </body>
    </html>
  );
}