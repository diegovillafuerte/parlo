import type { IndustryConfig } from './industries/index';
import { clinicasConfig } from './industries/clinicas';
import { talleresConfig } from './industries/talleres';
import { fitnessConfig } from './industries/fitness';
import { mascotasConfig } from './industries/mascotas';

export interface VariantConfig extends IndustryConfig {
  slug: string; // URL path: "clinicas", "clinicas/pagos", etc.
}

export const variants: VariantConfig[] = [
  // ═══════════════════════════════════════════════════════════════
  // BASE INDUSTRY VARIANTS (4)
  // ═══════════════════════════════════════════════════════════════
  { slug: 'clinicas', ...clinicasConfig },
  { slug: 'talleres', ...talleresConfig },
  { slug: 'fitness',  ...fitnessConfig },
  { slug: 'mascotas', ...mascotasConfig },

  // ═══════════════════════════════════════════════════════════════
  // FEATURE VARIANTS: PAGOS (4)
  // Lead angle: advance payments, deposits, reducing cancellations
  // ═══════════════════════════════════════════════════════════════
  {
    slug: 'clinicas/pagos',
    ...clinicasConfig,
    seo: {
      title: 'Parlo - Cobra Anticipos por WhatsApp en tu Clínica',
      description: 'Cobra anticipos automáticos por WhatsApp antes de cada consulta. Protege tratamientos costosos y asegura tus ingresos con Parlo.',
    },
    hero: {
      ...clinicasConfig.hero,
      headline: '¿Tratamientos de $5,000 que se cancelan sin previo aviso?<br />Con <span class="gradient-text">Parlo</span>, cobra anticipos antes de cada consulta',
      subheadline: 'Tu asistente cobra un depósito automático por WhatsApp al momento de agendar. Tratamientos costosos protegidos, menos consultas vacías, más ingresos seguros — <strong>todo desde WhatsApp</strong>.',
    },
    waitlist: { ...clinicasConfig.waitlist, fuente: 'landing-clinicas-pagos' },
  },
  {
    slug: 'talleres/pagos',
    ...talleresConfig,
    seo: {
      title: 'Parlo - Cobra Anticipos por WhatsApp en tu Taller',
      description: 'Cobra anticipos por WhatsApp antes de cada servicio. Que no te dejen colgado con refacciones compradas y rampa apartada. Parlo lo resuelve.',
    },
    hero: {
      ...talleresConfig.hero,
      headline: '¿Ya compraste refacciones y el cliente no llegó?<br />Con <span class="gradient-text">Parlo</span>, cobra anticipos antes de cada servicio',
      subheadline: 'Tu asistente cobra un depósito automático por WhatsApp al agendar. Refacciones cubiertas, rampas que no se desperdician, servicios grandes asegurados — <strong>sin perseguir a nadie para el pago</strong>.',
    },
    waitlist: { ...talleresConfig.waitlist, fuente: 'landing-talleres-pagos' },
  },
  {
    slug: 'fitness/pagos',
    ...fitnessConfig,
    seo: {
      title: 'Parlo - Vende Paquetes de Clases por WhatsApp',
      description: 'Vende paquetes y membresías por WhatsApp sin dejar de entrenar. Tus alumnos compran solos con Parlo.',
    },
    hero: {
      ...fitnessConfig.hero,
      headline: '¿Pierdes ventas de paquetes por estar dando clase?<br /><span class="gradient-text">Parlo</span> los vende por WhatsApp mientras tú entrenas',
      subheadline: 'Tu asistente ofrece paquetes, cobra y activa las clases automáticamente por WhatsApp. Más ingresos recurrentes sin pausar tu entrenamiento — <strong>vendes hasta a las 11 PM</strong>.',
    },
    waitlist: { ...fitnessConfig.waitlist, fuente: 'landing-fitness-pagos' },
  },
  {
    slug: 'mascotas/pagos',
    ...mascotasConfig,
    seo: {
      title: 'Parlo - Cobra por Adelantado en tu Estética o Veterinaria',
      description: 'Cobra depósitos por WhatsApp antes de cada baño o consulta. Que no te dejen plantado con el shampoo listo. Parlo lo resuelve.',
    },
    hero: {
      ...mascotasConfig.hero,
      headline: '¿Preparaste todo para el baño y el dueño no llegó?<br />Con <span class="gradient-text">Parlo</span>, cobra un depósito antes de cada cita',
      subheadline: 'Tu asistente cobra automáticamente por WhatsApp al agendar. Baños, cortes y consultas aseguradas con anticipo — <strong>sin perder tiempo ni dinero con plantones</strong>.',
    },
    waitlist: { ...mascotasConfig.waitlist, fuente: 'landing-mascotas-pagos' },
  },

  // ═══════════════════════════════════════════════════════════════
  // FEATURE VARIANTS: RECORDATORIOS (4)
  // Lead angle: reduce no-shows, automatic reminders
  // ═══════════════════════════════════════════════════════════════
  {
    slug: 'clinicas/recordatorios',
    ...clinicasConfig,
    seo: {
      title: 'Parlo - Reduce Inasistencias en tu Clínica con Recordatorios',
      description: 'Tus pacientes agendan y luego no llegan. Parlo les manda recordatorios automáticos por WhatsApp, confirma asistencia y reagenda si no pueden.',
    },
    hero: {
      ...clinicasConfig.hero,
      headline: '¿Consultorio listo y el paciente no llegó?<br /><span class="gradient-text">Parlo</span> manda recordatorios automáticos por WhatsApp',
      subheadline: 'Cada inasistencia es un horario que pudiste llenar con otro paciente. Tu asistente envía recordatorios 24 horas antes, confirma asistencia y reagenda al instante si el paciente no puede — <strong>sin que tu recepción haga una sola llamada</strong>.',
    },
    waitlist: { ...clinicasConfig.waitlist, fuente: 'landing-clinicas-recordatorios' },
  },
  {
    slug: 'talleres/recordatorios',
    ...talleresConfig,
    seo: {
      title: 'Parlo - Recordatorios Automáticos para tu Taller Mecánico',
      description: 'Tu mecánico listo, la rampa apartada, y el cliente no llega. Parlo manda recordatorios por WhatsApp y reagenda al instante.',
    },
    hero: {
      ...talleresConfig.hero,
      headline: '¿Rampa apartada y el cliente nunca llegó?<br /><span class="gradient-text">Parlo</span> les manda recordatorios automáticos por WhatsApp',
      subheadline: 'Cada cita que falla es una rampa parada y un mecánico sin producir. Tu asistente les recuerda la cita un día antes, confirma que van a llegar y reagenda al momento si no pueden — <strong>sin que dejes de trabajar para hacer llamadas</strong>.',
    },
    waitlist: { ...talleresConfig.waitlist, fuente: 'landing-talleres-recordatorios' },
  },
  {
    slug: 'fitness/recordatorios',
    ...fitnessConfig,
    seo: {
      title: 'Parlo - Reduce Faltas en tus Clases con Recordatorios',
      description: 'Alumnos que reservan y no llegan a clase. Parlo les manda recordatorios automáticos por WhatsApp y reagenda si no pueden asistir.',
    },
    hero: {
      ...fitnessConfig.hero,
      headline: '¿Alumnos que reservan y no se presentan?<br /><span class="gradient-text">Parlo</span> les recuerda cada clase por WhatsApp',
      subheadline: 'Cada alumno que falta es un lugar que otro pudo usar. Tu asistente les manda recordatorio antes de cada clase, confirma asistencia y reagenda si no pueden — <strong>más alumnos cumpliendo, más clases aprovechadas</strong>.',
    },
    waitlist: { ...fitnessConfig.waitlist, fuente: 'landing-fitness-recordatorios' },
  },
  {
    slug: 'mascotas/recordatorios',
    ...mascotasConfig,
    seo: {
      title: 'Parlo - Recordatorios Automáticos para tu Veterinaria o Estética',
      description: 'El shampoo listo, la mesa preparada, y el dueño no trae a su mascota. Parlo manda recordatorios por WhatsApp y reagenda al instante.',
    },
    hero: {
      ...mascotasConfig.hero,
      headline: '¿Mesa lista y el dueño no trajo a su mascota?<br /><span class="gradient-text">Parlo</span> les recuerda la cita por WhatsApp',
      subheadline: 'Preparaste todo para el baño y el dueño se le olvidó. Tu asistente les manda recordatorio un día antes, confirma que van a traer a su peludo y reagenda al momento si no pueden — <strong>sin perseguir a nadie por teléfono</strong>.',
    },
    waitlist: { ...mascotasConfig.waitlist, fuente: 'landing-mascotas-recordatorios' },
  },

  // ═══════════════════════════════════════════════════════════════
  // FEATURE VARIANTS: AGENDA (4)
  // Lead angle: 24/7 automated booking, no more missed calls
  // ═══════════════════════════════════════════════════════════════
  {
    slug: 'clinicas/agenda',
    ...clinicasConfig,
    seo: {
      title: 'Parlo - Agenda Pacientes 24/7 por WhatsApp',
      description: 'Tus pacientes agendan citas solos por WhatsApp a cualquier hora. Tu recepción deja de contestar llamadas con Parlo.',
    },
    hero: {
      ...clinicasConfig.hero,
      headline: '¿Tu recepción no da abasto con las llamadas?<br /><span class="gradient-text">Parlo</span> agenda pacientes 24/7 por WhatsApp',
      subheadline: 'Tus pacientes escriben por WhatsApp, eligen horario y quedan agendados — a las 3 AM del domingo o a las 9 AM del lunes. Tu recepción se enfoca en atender, no en contestar el teléfono — <strong>Parlo nunca descansa</strong>.',
    },
    waitlist: { ...clinicasConfig.waitlist, fuente: 'landing-clinicas-agenda' },
  },
  {
    slug: 'talleres/agenda',
    ...talleresConfig,
    seo: {
      title: 'Parlo - Agenda Servicios 24/7 por WhatsApp en tu Taller',
      description: 'Tus clientes agendan servicios por WhatsApp mientras tú trabajas en el taller. Sin perder llamadas con Parlo.',
    },
    hero: {
      ...talleresConfig.hero,
      headline: '¿Pierdes llamadas cuando estás debajo de un carro?<br /><span class="gradient-text">Parlo</span> agenda servicios por ti 24/7',
      subheadline: 'Tus clientes mandan WhatsApp, eligen horario y quedan agendados — mientras tú cambias frenos o haces una afinación. Tu taller no para de recibir citas aunque tú no puedas contestar — <strong>Parlo atiende por ti</strong>.',
    },
    waitlist: { ...talleresConfig.waitlist, fuente: 'landing-talleres-agenda' },
  },
  {
    slug: 'fitness/agenda',
    ...fitnessConfig,
    seo: {
      title: 'Parlo - Reserva de Clases 24/7 por WhatsApp',
      description: 'Tus alumnos reservan clase a cualquier hora por WhatsApp. Sin grupos caóticos ni llamadas con Parlo.',
    },
    hero: {
      ...fitnessConfig.hero,
      headline: '¿Grupos de WhatsApp caóticos para reservar clase?<br /><span class="gradient-text">Parlo</span> organiza reservas 24/7 automáticamente',
      subheadline: 'Tus alumnos escriben por WhatsApp, ven horarios disponibles y reservan al instante — a las 11 PM del domingo para la clase del lunes. Sin grupos, sin confusiones, sin "ya no hay lugar" — <strong>todo organizado automáticamente</strong>.',
    },
    waitlist: { ...fitnessConfig.waitlist, fuente: 'landing-fitness-agenda' },
  },
  {
    slug: 'mascotas/agenda',
    ...mascotasConfig,
    seo: {
      title: 'Parlo - Agenda Citas 24/7 para tu Veterinaria o Estética',
      description: 'Los dueños agendan citas para sus mascotas por WhatsApp a cualquier hora. Sin perder llamadas con Parlo.',
    },
    hero: {
      ...mascotasConfig.hero,
      headline: '¿Con las manos mojadas y el teléfono sonando?<br /><span class="gradient-text">Parlo</span> agenda citas para tu negocio de mascotas 24/7',
      subheadline: 'Los dueños escriben por WhatsApp, eligen servicio y horario, y quedan agendados — mientras tú sigues atendiendo peludos. De noche, en domingo o entre cita y cita — <strong>tu agenda siempre abierta</strong>.',
    },
    waitlist: { ...mascotasConfig.waitlist, fuente: 'landing-mascotas-agenda' },
  },

  // ═══════════════════════════════════════════════════════════════
  // FEATURE VARIANTS: MARKETING (4)
  // Lead angle: follow-up, retention, getting clients back
  // ═══════════════════════════════════════════════════════════════
  {
    slug: 'clinicas/marketing',
    ...clinicasConfig,
    seo: {
      title: 'Parlo - Recupera Pacientes que No Han Regresado',
      description: 'Parlo contacta por WhatsApp a pacientes que no han vuelto y los invita a reagendar. Más consultas recurrentes sin esfuerzo.',
    },
    hero: {
      ...clinicasConfig.hero,
      headline: '¿Pacientes que vienen una vez y no regresan?<br /><span class="gradient-text">Parlo</span> los contacta y los trae de vuelta',
      subheadline: 'Tu asistente detecta pacientes que llevan meses sin venir y les escribe por WhatsApp para invitarlos a reagendar. Limpiezas cada 6 meses, chequeos anuales, seguimientos post-tratamiento — <strong>Parlo convierte pacientes únicos en pacientes frecuentes</strong>.',
    },
    waitlist: { ...clinicasConfig.waitlist, fuente: 'landing-clinicas-marketing' },
  },
  {
    slug: 'talleres/marketing',
    ...talleresConfig,
    seo: {
      title: 'Parlo - Recupera Clientes que Ya No Regresan a tu Taller',
      description: 'Parlo detecta clientes que llevan meses sin venir y los contacta por WhatsApp para traerlos de vuelta. Más servicios al mes.',
    },
    hero: {
      ...talleresConfig.hero,
      headline: '¿Clientes que no han vuelto en meses?<br /><span class="gradient-text">Parlo</span> los contacta y los trae de vuelta al taller',
      subheadline: 'Tu asistente detecta clientes inactivos — el que lleva 6 meses sin cambio de aceite, el que nunca volvió después de la afinación — y les escribe por WhatsApp para invitarlos a agendar. Ingresos que estabas perdiendo, recuperados — <strong>sin que tú hagas nada</strong>.',
    },
    waitlist: { ...talleresConfig.waitlist, fuente: 'landing-talleres-marketing' },
  },
  {
    slug: 'fitness/marketing',
    ...fitnessConfig,
    seo: {
      title: 'Parlo - Recupera Alumnos que Dejaron de Entrenar',
      description: 'Parlo detecta alumnos inactivos y los contacta por WhatsApp para que regresen a entrenar. Menos deserciones con Parlo.',
    },
    hero: {
      ...fitnessConfig.hero,
      headline: '¿Alumnos que dejaron de venir y no regresan?<br /><span class="gradient-text">Parlo</span> los contacta y los trae de vuelta',
      subheadline: 'Tu asistente registra quién dejó de asistir, les escribe por WhatsApp y los invita a retomar sus clases. Rescata alumnos inactivos, reduce deserciones — <strong>motivación automática que funciona</strong>.',
    },
    waitlist: { ...fitnessConfig.waitlist, fuente: 'landing-fitness-marketing' },
  },
  {
    slug: 'mascotas/marketing',
    ...mascotasConfig,
    seo: {
      title: 'Parlo - Recupera Clientes que Ya No Traen a su Mascota',
      description: 'Parlo detecta dueños que llevan semanas sin traer a su mascota y los contacta por WhatsApp. Más visitas recurrentes.',
    },
    hero: {
      ...mascotasConfig.hero,
      headline: '¿Dueños que trajeron a su mascota una vez y no volvieron?<br /><span class="gradient-text">Parlo</span> los contacta y los trae de vuelta',
      subheadline: 'Tu asistente detecta clientes que llevan semanas sin venir y les escribe por WhatsApp para invitarlos a agendar. El baño mensual de Luna, la vacuna pendiente de Max — <strong>ingresos recurrentes en automático</strong>.',
    },
    waitlist: { ...mascotasConfig.waitlist, fuente: 'landing-mascotas-marketing' },
  },
];

// Guard: fail at build time if two variants share the same slug
const slugs = variants.map((v) => v.slug);
const dupes = slugs.filter((s, i) => slugs.indexOf(s) !== i);
if (dupes.length > 0) {
  throw new Error(`Duplicate variant slugs: ${dupes.join(', ')}`);
}
