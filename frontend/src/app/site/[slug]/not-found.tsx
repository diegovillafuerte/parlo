export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-white">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Negocio no encontrado
        </h1>
        <p className="text-gray-600">
          Esta página no existe o el negocio ya no está activo.
        </p>
      </div>
    </div>
  );
}
