import type { IndustryConfig } from './index';

export const talleresConfig: IndustryConfig = {
  seo: {
    title: 'Parlo - Asistente Inteligente para Talleres Mecánicos',
    description: 'Conecta Parlo a tu WhatsApp en 2 minutos. Tu asistente 24/7 que agenda servicios automotrices, gestiona citas del taller y manda recordatorios — todo desde WhatsApp.',
  },
  hero: {
    badge: '🔧 Tu asistente por WhatsApp',
    headline: '¿Quieres crecer tu taller mecánico?<br />Conoce a <span class="gradient-text">Parlo</span>, el asistente que organiza todo por ti',
    subheadline: 'Tu asistente 24/7 que agenda servicios, gestiona y actualiza tu agenda del taller, manda recordatorios de mantenimiento y te ayuda a que tus clientes regresen — <strong>todo desde WhatsApp</strong>. Sin apps, sin sistemas complicados, sin perder llamadas mientras estás debajo de un carro.',
    cta: 'Únete a la lista de espera exclusiva',
    promoLine: '🎁 Primera versión <strong class="text-secondary">totalmente gratis</strong> para grupo exclusivo',
  },
  howItWorks: {
    subtitle: 'Cinco formas en que Parlo transforma tu taller',
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
          text: '¡Hola! 👋 Soy Parlo, tu nuevo asistente.<br><br>Voy a ayudarte a organizar tu taller. Cuéntame sobre tu negocio.',
          time: '9:41',
        },
        { role: 'bot', text: '¿Cómo se llama tu taller?', time: '9:41' },
        { role: 'owner', text: 'Taller Mecánico Los Hermanos', time: '9:42' },
        {
          role: 'bot',
          text: 'Perfecto, Taller Los Hermanos 🔧<br><br>¿Qué servicios manejan?',
          time: '9:42',
        },
        {
          role: 'owner',
          text: '- Cambio de aceite $450<br>- Afinación mayor $2,800<br>- Frenos $1,500<br>- Diagnóstico $300',
          time: '9:43',
        },
        {
          role: 'bot',
          text: '¡Listo! 🎉<br><br>Ya estoy configurado. Tus clientes ya pueden agendar servicios conmigo.',
          time: '9:44',
        },
      ],
    },

    // ── Slide 2: Client Booking ──
    {
      tabLabel: 'Agendar',
      stepNumber: 2,
      slideTitle: 'Tus clientes agendan solos',
      chatHeader: {
        name: 'Taller Los Hermanos',
        subtitle: 'en línea',
        avatarEmoji: '🔧',
        avatarStyle: 'business',
      },
      messages: [
        { role: 'client', text: 'Hola, necesito un cambio de aceite', time: '10:23' },
        {
          role: 'bot',
          text: '¡Hola Ricardo! 👋<br><br>Claro, un cambio de aceite. ¿Qué tipo de vehículo es?',
          time: '10:23',
        },
        { role: 'client', text: 'Honda Civic 2020', time: '10:24' },
        {
          role: 'bot',
          text: 'Perfecto. Horarios disponibles:<br><br>• Mañana 9:00 AM<br>• Mañana 2:00 PM<br>• Jueves 10:00 AM',
          time: '10:24',
        },
        { role: 'client', text: 'Mañana a las 9', time: '10:25' },
        {
          role: 'bot',
          text: '✅ ¡Confirmado!<br><br><strong>Mañana miércoles</strong><br>🕒 9:00 AM<br>🔧 Cambio de aceite<br>🚗 Honda Civic 2020<br>💰 $450<br><br>Te enviaré un recordatorio antes 😊',
          time: '10:25',
        },
      ],
    },

    // ── Slide 3: Owner Management ──
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
          time: '7:45',
          voiceNote: { duration: '0:03', transcript: '"Parlo, qué carros tengo agendados hoy?"' },
        },
        {
          role: 'bot',
          text: 'Agenda del miércoles 12 feb:<br><br><strong>9:00 AM</strong> - Ricardo Vega<br>Cambio de aceite - Honda Civic ($450)<br><br><strong>11:00 AM</strong> - Laura Torres<br>Frenos delanteros - Toyota RAV4 ($1,500)<br><br><strong>3:00 PM</strong> - Miguel Ángel<br>Afinación mayor - VW Jetta ($2,800)<br><br>💰 Total: $4,750',
          time: '7:45',
        },
        { role: 'owner', text: 'El de las 3 va a tardar, bloquea las 5 también', time: '7:46' },
        {
          role: 'bot',
          text: '✅ Listo. Bloqueé el horario de 3:00 a 6:00 PM para la afinación mayor de Miguel Ángel 👍',
          time: '7:46',
        },
      ],
    },

    // ── Slide 4: Reminders ──
    {
      tabLabel: 'Recordatorios',
      stepNumber: 4,
      slideTitle: 'Recordatorios automáticos',
      chatHeader: {
        name: 'Taller Los Hermanos',
        subtitle: 'en línea',
        avatarEmoji: '🔧',
        avatarStyle: 'business',
      },
      messages: [
        {
          role: 'bot',
          text: 'Hola Ricardo! 👋<br><br>Te recuerdo que mañana tienes tu cita para cambio de aceite a las 9:00 AM.<br><br>🚗 Honda Civic 2020<br><br>¿Nos vemos mañana?',
          time: '18:00',
        },
        { role: 'client', text: 'Se me complicó en la mañana, puedo en la tarde?', time: '18:10' },
        {
          role: 'bot',
          text: 'Claro! Tengo estos horarios por la tarde:<br><br>• 2:00 PM<br>• 4:00 PM',
          time: '18:10',
        },
        { role: 'client', text: 'A las 2 está bien', time: '18:12' },
        {
          role: 'bot',
          text: '✅ ¡Listo! Reagendé tu cita:<br><br><strong>Mañana miércoles</strong><br>🕒 2:00 PM<br>🔧 Cambio de aceite<br>🚗 Honda Civic 2020<br><br>¡Te esperamos! 🛞',
          time: '18:12',
        },
      ],
    },

    // ── Slide 5: Payments ──
    {
      tabLabel: 'Pagos',
      stepNumber: 5,
      slideTitle: 'Cobra por adelantado',
      chatHeader: {
        name: 'Taller Los Hermanos',
        subtitle: 'en línea',
        avatarEmoji: '🔧',
        avatarStyle: 'business',
      },
      messages: [
        { role: 'client', text: 'Necesito una afinación mayor para mi Jetta', time: '16:45' },
        {
          role: 'bot',
          text: 'Perfecto! Para confirmar tu cita, te pido un anticipo:<br><br><strong>Viernes 10:00 AM</strong><br>🔧 Afinación mayor<br>🚗 VW Jetta<br>💰 Anticipo: $500 MXN<br><br><em>*Se aplica al total de $2,800</em>',
          time: '16:46',
        },
        {
          role: 'bot',
          text: '',
          time: '16:47',
          paymentLink: { label: '💳 Pagar anticipo $500', amount: '$500' },
        },
        {
          role: 'bot',
          text: '✅ ¡Anticipo recibido!<br><br>Tu cita está confirmada 🎉<br><br><strong>Viernes 10:00 AM</strong><br>🔧 Afinación mayor<br>🚗 VW Jetta<br>💰 Pagado: $500 / $2,800<br><br>¡Te esperamos!',
          time: '16:48',
        },
      ],
    },

    // ── Slide 6: Maintenance Reminders ──
    {
      tabLabel: 'Mantenimiento',
      stepNumber: 6,
      slideTitle: 'Recordatorios de mantenimiento',
      chatHeader: {
        name: 'Taller Los Hermanos',
        subtitle: 'en línea',
        avatarEmoji: '🔧',
        avatarStyle: 'parlo',
      },
      messages: [
        {
          role: 'bot',
          text: 'Hola Ricardo! 🚗<br><br>Ya pasaron 6 meses desde tu último cambio de aceite en tu Honda Civic. ¡Es hora del siguiente!<br><br>¿Quieres que te agende?',
        },
        { role: 'client', text: 'Sí, esta semana si se puede' },
        {
          role: 'bot',
          text: 'Tengo estos horarios disponibles:<br><br><strong>Jueves</strong><br>• 9:00 AM<br>• 1:00 PM<br><br><strong>Viernes</strong><br>• 10:00 AM<br>• 3:00 PM',
        },
        { role: 'client', text: 'El jueves a la 1 PM' },
        {
          role: 'bot',
          text: '✅ ¡Agendado!<br><br><strong>Jueves 1:00 PM</strong><br>🔧 Cambio de aceite<br>🚗 Honda Civic 2020<br>💰 $450<br><br>Como cliente frecuente, te incluyo revisión de niveles <strong>sin costo</strong> 🛞',
        },
      ],
    },
  ],
  benefits: [
    {
      icon: '📱',
      stat: 'Cero',
      title: 'Llamadas perdidas',
      text: 'Tus clientes agendan por WhatsApp mientras tú trabajas. No más llamadas perdidas cuando estás debajo de un carro.',
    },
    {
      icon: '📈',
      title: 'Más servicios al mes',
      text: 'Agenda organizada = más carros atendidos. Tu asistente nunca olvida una cita ni pierde un cliente.',
    },
    {
      icon: '💳',
      title: 'Anticipo asegurado',
      text: 'Cobra anticipos por WhatsApp para servicios grandes. Menos cancelaciones, más compromiso del cliente.',
    },
    {
      icon: '🔄',
      title: 'Clientes que regresan',
      text: 'Recordatorios automáticos de mantenimiento. Parlo sabe cuándo le toca servicio a cada vehículo.',
    },
  ],
  waitlist: {
    heading: 'Únete a la lista de espera exclusiva',
    subtitle: 'Acceso anticipado para un número limitado de talleres mecánicos',
    businessPlaceholder: 'Taller Mecánico Los Hermanos',
    activityPlaceholder: 'Taller mecánico, agencia automotriz, llantera...',
    fuente: 'landing-parlo-talleres',
  },
  footer: {
    tagline: 'Hecho en México 🔧🚗🛞',
  },
};
