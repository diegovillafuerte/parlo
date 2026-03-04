"use client";

import { formatPrice, formatDuration } from "@/lib/format";
import type { BusinessData } from "./page";

const DAY_NAMES: Record<string, string> = {
  monday: "Lunes",
  tuesday: "Martes",
  wednesday: "Miércoles",
  thursday: "Jueves",
  friday: "Viernes",
  saturday: "Sábado",
  sunday: "Domingo",
};

const DAY_ORDER = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday",
];

function getTodayKey(): string {
  const days = [
    "sunday",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
  ];
  return days[new Date().getDay()];
}

function formatTime(time24: string): string {
  const [h, m] = time24.split(":").map(Number);
  const suffix = h >= 12 ? "PM" : "AM";
  const h12 = h === 0 ? 12 : h > 12 ? h - 12 : h;
  return `${h12}:${m.toString().padStart(2, "0")} ${suffix}`;
}

function getWhatsAppLink(number: string | null, businessName: string): string {
  if (!number) return "#";
  const clean = number.replace(/[^0-9]/g, "");
  const text = encodeURIComponent(
    `Hola, quiero agendar una cita en ${businessName}`
  );
  return `https://wa.me/${clean}?text=${text}`;
}

export default function BusinessPage({ data }: { data: BusinessData }) {
  const todayKey = getTodayKey();
  const waLink = getWhatsAppLink(data.whatsapp_number, data.business_name);

  return (
    <div className="min-h-screen bg-white">
      {/* Hero */}
      <header className="bg-gradient-to-br from-green-600 to-green-700 text-white px-6 py-12 text-center">
        <h1 className="text-3xl font-bold mb-2">{data.business_name}</h1>
        <p className="text-green-100 text-lg">Agenda tu cita por WhatsApp</p>
      </header>

      <main className="max-w-lg mx-auto px-4 py-8 space-y-10 pb-28">
        {/* Services */}
        {data.services.length > 0 && (
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Servicios
            </h2>
            <div className="space-y-3">
              {data.services.map((svc, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-gray-900">{svc.name}</p>
                    <p className="text-sm text-gray-500">
                      {formatDuration(svc.duration_minutes)}
                    </p>
                  </div>
                  <p className="font-semibold text-gray-900">
                    {formatPrice(svc.price_cents, svc.currency)}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Business Hours */}
        {Object.keys(data.location.business_hours).length > 0 && (
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Horario
            </h2>
            <div className="space-y-2">
              {DAY_ORDER.map((day) => {
                const hours = data.location.business_hours[day];
                if (!hours) return null;
                const isToday = day === todayKey;
                return (
                  <div
                    key={day}
                    className={`flex justify-between py-2 px-3 rounded ${
                      isToday ? "bg-green-50 font-medium" : ""
                    }`}
                  >
                    <span className="text-gray-700">
                      {DAY_NAMES[day]}
                      {isToday && (
                        <span className="ml-2 text-xs text-green-600 font-normal">
                          Hoy
                        </span>
                      )}
                    </span>
                    <span className="text-gray-900">
                      {hours.closed
                        ? "Cerrado"
                        : hours.open && hours.close
                          ? `${formatTime(hours.open)} - ${formatTime(hours.close)}`
                          : "—"}
                    </span>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* Location */}
        {data.location.address && (
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Ubicación
            </h2>
            <p className="text-gray-700 mb-2">{data.location.address}</p>
            <a
              href={`https://maps.google.com/?q=${encodeURIComponent(data.location.address)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-green-600 hover:text-green-700 text-sm font-medium"
            >
              Ver en Google Maps &rarr;
            </a>
          </section>
        )}
      </main>

      {/* Sticky WhatsApp CTA */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-gray-200">
        <a
          href={waLink}
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full max-w-lg mx-auto bg-green-500 hover:bg-green-600 text-white text-center font-semibold py-4 rounded-xl text-lg transition-colors"
        >
          Agendar por WhatsApp
        </a>
      </div>

      {/* Footer */}
      <footer className="text-center py-4 text-xs text-gray-400 pb-24">
        Powered by Parlo
      </footer>
    </div>
  );
}
