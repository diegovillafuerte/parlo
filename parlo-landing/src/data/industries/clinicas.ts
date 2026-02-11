import type { IndustryConfig } from './index';

export const clinicasConfig: IndustryConfig = {
  seo: {
    title: 'Parlo - Asistente Inteligente para Clínicas y Consultorios',
    description: 'Conecta Parlo a tu WhatsApp en 2 minutos. Tu asistente 24/7 que agenda pacientes, gestiona citas médicas y manda recordatorios — todo desde WhatsApp.',
  },
  hero: {
    badge: '🏥 Tu asistente por WhatsApp',
    headline: '¿Quieres crecer tu clínica o consultorio?<br />Conoce a <span class="gradient-text">Parlo</span>, el asistente que tus pacientes van a amar',
    subheadline: 'Tu asistente 24/7 que agenda pacientes, gestiona y actualiza tu agenda médica, manda recordatorios de citas y te ayuda a reducir las inasistencias — <strong>todo desde WhatsApp</strong>. Sin apps, sin capacitaciones, sin estrés para tu recepción.',
    cta: 'Únete a la lista de espera exclusiva',
    promoLine: '🎁 Primera versión <strong class="text-secondary">totalmente gratis</strong> para grupo exclusivo',
  },
  howItWorks: {
    subtitle: 'Cinco formas en que Parlo transforma tu clínica',
  },
  slides: [
    // ── Slide 1: Onboarding ──
    {
      tabLabel: 'Configuración',
      stepNumber: 1,
      slideTitle: 'Configuración inicial (5 min)',
      chatHeader: {
        name: 'Parlo',
        subtitle: 'tu asistente',
        avatarEmoji: '💜',
        avatarStyle: 'parlo',
      },
      messages: [
        {
          role: 'bot',
          text: '¡Hola! 👋 Soy Parlo, tu nuevo asistente.<br><br>Voy a ayudarte a gestionar tus citas. Primero cuéntame sobre tu consultorio.',
          time: '9:41',
        },
        { role: 'bot', text: '¿Cómo se llama tu clínica o consultorio?', time: '9:41' },
        { role: 'owner', text: 'Consultorio Dental Sonríe', time: '9:42' },
        {
          role: 'bot',
          text: 'Perfecto, Consultorio Dental Sonríe 🦷<br><br>¿Qué servicios ofreces?',
          time: '9:42',
        },
        {
          role: 'owner',
          text: '- Limpieza dental $800<br>- Consulta general $500<br>- Blanqueamiento $3,500',
          time: '9:43',
        },
        {
          role: 'bot',
          text: '¡Listo! 🎉<br><br>Ya estoy configurado. Tus pacientes ya pueden agendar citas conmigo.',
          time: '9:44',
        },
      ],
    },

    // ── Slide 2: Patient Booking ──
    {
      tabLabel: 'Agendar',
      stepNumber: 2,
      slideTitle: 'Tus pacientes agendan solos',
      chatHeader: {
        name: 'Consultorio Sonríe',
        subtitle: 'en línea',
        avatarEmoji: '🦷',
        avatarStyle: 'business',
      },
      messages: [
        { role: 'client', text: 'Hola, necesito una cita para limpieza dental', time: '10:23' },
        {
          role: 'bot',
          text: '¡Hola María! 👋<br><br>Con gusto te agendo. Estos son los horarios disponibles esta semana:<br><br>• Martes 10:00 AM<br>• Miércoles 4:00 PM<br>• Jueves 11:00 AM',
          time: '10:23',
        },
        { role: 'client', text: 'El miércoles a las 4 por favor', time: '10:24' },
        {
          role: 'bot',
          text: '✅ ¡Confirmado!<br><br><strong>Miércoles</strong><br>🕒 4:00 PM<br>🦷 Limpieza dental<br>💰 $800<br><br>Te enviaré un recordatorio un día antes 😊',
          time: '10:24',
        },
      ],
    },

    // ── Slide 3: Doctor Management ──
    {
      tabLabel: 'Gestionar',
      stepNumber: 3,
      slideTitle: 'Gestiona todo desde WhatsApp',
      chatHeader: {
        name: 'Parlo',
        subtitle: 'tu asistente',
        avatarEmoji: '💜',
        avatarStyle: 'parlo',
      },
      messages: [
        {
          role: 'owner',
          text: '',
          time: '15:42',
          voiceNote: { duration: '0:04', transcript: '"Parlo, cuántos pacientes tengo mañana?"' },
        },
        {
          role: 'bot',
          text: 'Agenda del martes 11 feb:<br><br><strong>9:00 AM</strong> - Ana López<br>Consulta general ($500)<br><br><strong>11:00 AM</strong> - Pedro García<br>Limpieza dental ($800)<br><br><strong>4:00 PM</strong> - María Ruiz<br>Blanqueamiento ($3,500)<br><br>💰 Total: $4,800',
          time: '15:42',
        },
        { role: 'owner', text: 'Cancela la cita de las 4, me surgió algo', time: '15:43' },
        {
          role: 'bot',
          text: 'Listo, cancelé la cita de María Ruiz a las 4:00 PM.<br><br>¿Le aviso y le ofrezco reagendar?',
          time: '15:43',
        },
        { role: 'owner', text: 'Sí, dile que puede venir el jueves', time: '15:44' },
        {
          role: 'bot',
          text: '✅ Le avisé a María. Ya le ofrecí horarios del jueves para reagendar 👍',
          time: '15:45',
        },
      ],
    },

    // ── Slide 4: Reminders ──
    {
      tabLabel: 'Recordatorios',
      stepNumber: 4,
      slideTitle: 'Reduce inasistencias',
      chatHeader: {
        name: 'Consultorio Sonríe',
        subtitle: 'en línea',
        avatarEmoji: '🦷',
        avatarStyle: 'business',
      },
      messages: [
        {
          role: 'bot',
          text: 'Hola Pedro! 👋<br><br>Te recuerdo que mañana tienes tu cita de limpieza dental a las 11:00 AM.<br><br>¿Te esperamos?',
          time: '18:00',
        },
        { role: 'client', text: 'Sí ahí estaré! Necesito llevar algo?', time: '18:15' },
        {
          role: 'bot',
          text: 'Solo tu identificación y tu sonrisa 😄<br><br>Recuerda no comer nada 2 horas antes de tu cita.<br><br>¡Te esperamos mañana!',
          time: '18:15',
        },
      ],
    },

    // ── Slide 5: Payments ──
    {
      tabLabel: 'Pagos',
      stepNumber: 5,
      slideTitle: 'Cobra por adelantado',
      chatHeader: {
        name: 'Consultorio Sonríe',
        subtitle: 'en línea',
        avatarEmoji: '🦷',
        avatarStyle: 'business',
      },
      messages: [
        { role: 'client', text: 'Quiero agendar un blanqueamiento', time: '16:45' },
        {
          role: 'bot',
          text: 'Perfecto! ✨<br><br>Para confirmar tu cita, realiza el anticipo por WhatsApp:<br><br><strong>Viernes 10:00 AM</strong><br>🦷 Blanqueamiento dental<br>💰 Anticipo: $1,000 MXN<br><br><em>*Se aplica al total de $3,500</em>',
          time: '16:46',
        },
        {
          role: 'bot',
          text: '',
          time: '16:47',
          paymentLink: { label: '💳 Pagar anticipo $1,000', amount: '$1,000' },
        },
        {
          role: 'bot',
          text: '✅ ¡Anticipo recibido!<br><br>Tu cita está confirmada 🎉<br><br><strong>Viernes 10:00 AM</strong><br>🦷 Blanqueamiento dental<br>💰 Pagado: $1,000 / $3,500<br><br>¡Te esperamos!',
          time: '16:48',
        },
      ],
    },

    // ── Slide 6: Follow-up ──
    {
      tabLabel: 'Seguimiento',
      stepNumber: 6,
      slideTitle: 'Seguimiento automático',
      chatHeader: {
        name: 'Consultorio Sonríe',
        subtitle: 'en línea',
        avatarEmoji: '🦷',
        avatarStyle: 'parlo',
      },
      messages: [
        {
          role: 'bot',
          text: 'Hola Ana! 🦷<br><br>Han pasado 6 meses desde tu última limpieza dental. Los dentistas recomendamos una limpieza cada 6 meses.<br><br>¿Quieres que te agende una cita?',
        },
        { role: 'client', text: 'Sí! qué horarios tienes?' },
        {
          role: 'bot',
          text: 'Tengo estos horarios disponibles:<br><br><strong>Lunes</strong><br>• 9:00 AM<br>• 2:00 PM<br><br><strong>Martes</strong><br>• 11:00 AM<br>• 5:00 PM',
        },
        { role: 'client', text: 'El lunes a las 9 AM' },
        {
          role: 'bot',
          text: '✅ ¡Agendado!<br><br><strong>Lunes 9:00 AM</strong><br>🦷 Limpieza dental<br>💰 $800<br><br>Como paciente frecuente, tienes <strong>10% de descuento</strong> 💜',
        },
      ],
    },
  ],
  benefits: [
    {
      icon: '⏰',
      stat: '2 horas',
      title: 'Tiempo ahorrado al día',
      text: 'Tu recepción deja de contestar llamadas para agendar. Más tiempo para atender pacientes presenciales.',
    },
    {
      icon: '📉',
      title: 'Menos inasistencias',
      text: 'Recordatorios automáticos reducen las faltas. Cada cita perdida es dinero perdido — Parlo las recupera.',
    },
    {
      icon: '💳',
      title: 'Anticipo asegurado',
      text: 'Cobra anticipos por WhatsApp para tratamientos costosos. Menos cancelaciones de último momento.',
    },
    {
      icon: '🔄',
      title: 'Pacientes que regresan',
      text: 'Seguimiento automático después de cada consulta. Parlo recuerda cuándo toca la siguiente cita de cada paciente.',
    },
  ],
  waitlist: {
    heading: 'Únete a la lista de espera exclusiva',
    subtitle: 'Acceso anticipado para un número limitado de clínicas y consultorios',
    businessPlaceholder: 'Consultorio Dental Sonríe',
    activityPlaceholder: 'Consultorio dental, clínica médica, dermatología...',
    fuente: 'landing-parlo-clinicas',
  },
  footer: {
    tagline: 'Hecho en México 🏥🦷🩺',
  },
};
