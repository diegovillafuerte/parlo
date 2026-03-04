import { Metadata } from "next";
import { notFound } from "next/navigation";
import BusinessPage from "./BusinessPage";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface BusinessData {
  business_name: string;
  slug: string;
  location: {
    address: string | null;
    business_hours: Record<
      string,
      { open?: string; close?: string; closed?: boolean }
    >;
  };
  services: Array<{
    name: string;
    description: string | null;
    duration_minutes: number;
    price_cents: number;
    currency: string;
  }>;
  whatsapp_number: string | null;
  timezone: string;
}

async function getBusinessData(slug: string): Promise<BusinessData | null> {
  try {
    const res = await fetch(`${API_BASE}/public/site/${slug}`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const data = await getBusinessData(slug);
  if (!data) return { title: "No encontrado" };

  const description = `Agenda tu cita en ${data.business_name}. ${data.services.length} servicios disponibles. Reserva por WhatsApp.`;

  return {
    title: `${data.business_name} | Agenda tu cita`,
    description,
    openGraph: {
      title: `${data.business_name} | Agenda tu cita`,
      description,
      type: "website",
      locale: "es_MX",
      siteName: "Parlo",
    },
  };
}

export default async function SitePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const data = await getBusinessData(slug);
  if (!data) notFound();

  return <BusinessPage data={data} />;
}
