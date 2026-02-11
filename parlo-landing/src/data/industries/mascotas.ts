import type { IndustryConfig } from './index';

export const mascotasConfig: IndustryConfig = {
  seo: {
    title: 'Parlo - Asistente Inteligente para Veterinarias y Estéticas de Mascotas',
    description: 'Conecta Parlo a tu WhatsApp en 2 minutos. Tu asistente 24/7 que agenda citas de grooming y veterinaria, gestiona tu agenda y manda recordatorios — todo desde WhatsApp.',
  },
  hero: {
    badge: '🐾 Tu asistente por WhatsApp',
    headline: '¿Quieres crecer tu negocio de mascotas?<br />Conoce a <span class="gradient-text">Parlo</span>, el asistente que tus clientes (y sus peludos) van a amar',
    subheadline: 'Tu asistente 24/7 que agenda citas de grooming y consultas veterinarias, gestiona y actualiza tu agenda, manda recordatorios de vacunas y baños — <strong>todo desde WhatsApp</strong>. Sin apps complicadas, sin perder citas mientras bañas a un lomito.',
    cta: 'Únete a la lista de espera exclusiva',
    promoLine: '🎁 Primera versión <strong class="text-secondary">totalmente gratis</strong> para grupo exclusivo',
  },
  howItWorks: {
    subtitle: 'Cinco formas en que Parlo transforma tu negocio',
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
          text: '¡Hola! 👋 Soy Parlo, tu nuevo asistente.<br><br>Voy a ayudarte a organizar tus citas. Cuéntame sobre tu negocio.',
          time: '9:41',
        },
        { role: 'bot', text: '¿Cómo se llama tu negocio?', time: '9:41' },
        { role: 'owner', text: 'Patitas Felices - Estética Canina', time: '9:42' },
        {
          role: 'bot',
          text: 'Perfecto, Patitas Felices 🐾<br><br>¿Qué servicios ofreces?',
          time: '9:42',
        },
        {
          role: 'owner',
          text: '- Baño chico $250<br>- Baño mediano $350<br>- Baño grande $450<br>- Corte + baño $500<br>- Consulta veterinaria $400',
          time: '9:43',
        },
        {
          role: 'bot',
          text: '¡Listo! 🎉<br><br>Ya estoy configurado. Los dueños de mascotas ya pueden agendar citas conmigo.',
          time: '9:44',
        },
      ],
    },

    // ── Slide 2: Pet Booking ──
    {
      tabLabel: 'Agendar',
      stepNumber: 2,
      slideTitle: 'Tus clientes agendan solos',
      chatHeader: {
        name: 'Patitas Felices',
        subtitle: 'en línea',
        avatarEmoji: '🐕',
        avatarStyle: 'business',
      },
      messages: [
        { role: 'client', text: 'Hola! Necesito cita para bañar a mi perrita', time: '10:23' },
        {
          role: 'bot',
          text: '¡Hola Sofía! 🐾<br><br>Claro, con gusto. ¿Cómo se llama tu perrita y de qué tamaño es?',
          time: '10:23',
        },
        { role: 'client', text: 'Se llama Luna, es golden retriever', time: '10:24' },
        {
          role: 'bot',
          text: 'Aww Luna 🐕 Para golden necesitamos baño grande.<br><br>Horarios disponibles:<br><br>• Mañana 10:00 AM<br>• Mañana 3:00 PM<br>• Jueves 11:00 AM',
          time: '10:24',
        },
        { role: 'client', text: 'Mañana a las 10!', time: '10:25' },
        {
          role: 'bot',
          text: '✅ ¡Confirmado!<br><br><strong>Mañana miércoles</strong><br>🕒 10:00 AM<br>🐕 Baño grande - Luna<br>💰 $450<br><br>Luna va a salir guapísima 🛁✨',
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
          time: '8:00',
          voiceNote: { duration: '0:03', transcript: '"Parlo, qué mascotas tengo hoy?"' },
        },
        {
          role: 'bot',
          text: 'Agenda del miércoles 12 feb:<br><br><strong>10:00 AM</strong> - Luna (Golden)<br>Baño grande - Sofía Herrera ($450)<br><br><strong>12:00 PM</strong> - Max (Schnauzer)<br>Corte + baño - Pedro Ruiz ($500)<br><br><strong>3:00 PM</strong> - Mía (Chihuahua)<br>Baño chico - Ana Torres ($250)<br><br>🐾 3 peludos hoy | 💰 Total: $1,200',
          time: '8:00',
        },
        { role: 'owner', text: 'El schnauzer de las 12 necesita corte especial, tarda más. Bloquea hasta las 2', time: '8:01' },
        {
          role: 'bot',
          text: '✅ Listo. Bloqueé de 12:00 a 2:00 PM para Max el schnauzer 🐕✂️',
          time: '8:01',
        },
      ],
    },

    // ── Slide 4: Reminders ──
    {
      tabLabel: 'Recordatorios',
      stepNumber: 4,
      slideTitle: 'Recordatorios automáticos',
      chatHeader: {
        name: 'Patitas Felices',
        subtitle: 'en línea',
        avatarEmoji: '🐕',
        avatarStyle: 'business',
      },
      messages: [
        {
          role: 'bot',
          text: 'Hola Sofía! 🐾<br><br>Te recuerdo que mañana tienes cita para Luna a las 10:00 AM.<br><br>🐕 Baño grande<br><br>Por favor trae su correa y una toalla extra. ¿Nos vemos mañana?',
          time: '18:00',
        },
        { role: 'client', text: 'Sí! Luna ya está lista jaja, puedo agregar corte de uñas?', time: '18:10' },
        {
          role: 'bot',
          text: '¡Claro! Agrego corte de uñas a la cita de Luna.<br><br>🐕 Baño grande + corte de uñas<br>💰 $450 + $80 = $530<br><br>¡Las dos las esperamos mañana! 🐾',
          time: '18:10',
        },
      ],
    },

    // ── Slide 5: Payments ──
    {
      tabLabel: 'Pagos',
      stepNumber: 5,
      slideTitle: 'Cobra por adelantado',
      chatHeader: {
        name: 'Patitas Felices',
        subtitle: 'en línea',
        avatarEmoji: '🐕',
        avatarStyle: 'business',
      },
      messages: [
        { role: 'client', text: 'Quiero agendar corte + baño para Max', time: '16:45' },
        {
          role: 'bot',
          text: 'Perfecto! ✨<br><br>Para confirmar la cita de Max, realiza el pago por WhatsApp:<br><br><strong>Sábado 11:00 AM</strong><br>🐕 Corte + baño (Schnauzer)<br>💰 $500 MXN<br><br><em>*Reembolso completo si cancelas con 4+ horas de anticipación</em>',
          time: '16:46',
        },
        {
          role: 'bot',
          text: '',
          time: '16:47',
          paymentLink: { label: '💳 Pagar $500 MXN', amount: '$500' },
        },
        {
          role: 'bot',
          text: '✅ ¡Pago recibido!<br><br>La cita de Max está confirmada 🎉<br><br><strong>Sábado 11:00 AM</strong><br>🐕 Corte + baño<br>💰 Pagado: $500<br><br>¡Max va a quedar guapísimo! 🐾✨',
          time: '16:48',
        },
      ],
    },

    // ── Slide 6: Follow-up ──
    {
      tabLabel: 'Seguimiento',
      stepNumber: 6,
      slideTitle: 'Recordatorios de cuidado',
      chatHeader: {
        name: 'Patitas Felices',
        subtitle: 'en línea',
        avatarEmoji: '🐕',
        avatarStyle: 'parlo',
      },
      messages: [
        {
          role: 'bot',
          text: 'Hola Sofía! 🐾<br><br>Ya pasó un mes desde el último baño de Luna. Las golden necesitan baño cada 4-6 semanas para mantener su pelo sano.<br><br>¿Quieres que te agende?',
        },
        { role: 'client', text: 'Sí! Luna ya huele a perro mojado jaja' },
        {
          role: 'bot',
          text: 'Jaja 😄 Horarios disponibles:<br><br><strong>Viernes</strong><br>• 10:00 AM<br>• 2:00 PM<br><br><strong>Sábado</strong><br>• 9:00 AM<br>• 12:00 PM',
        },
        { role: 'client', text: 'El sábado a las 9! tempranito' },
        {
          role: 'bot',
          text: '✅ ¡Agendado!<br><br><strong>Sábado 9:00 AM</strong><br>🐕 Baño grande - Luna<br>💰 $450<br><br>Como clienta frecuente, le incluimos <strong>perfume gratis</strong> a Luna 🐾💜',
        },
      ],
    },
  ],
  benefits: [
    {
      icon: '📱',
      stat: 'Cero',
      title: 'Llamadas perdidas',
      text: 'Los dueños agendan por WhatsApp mientras tú atiendes peludos. No más llamadas perdidas con las manos mojadas.',
    },
    {
      icon: '📈',
      title: 'Más mascotas al día',
      text: 'Agenda organizada = más mascotas atendidas. Tu asistente nunca pierde una cita ni olvida un cliente.',
    },
    {
      icon: '💳',
      title: 'Pago anticipado',
      text: 'Cobra por WhatsApp antes de la cita. Menos cancelaciones de último momento, más seguridad para tu negocio.',
    },
    {
      icon: '🔄',
      title: 'Peludos que regresan',
      text: 'Recordatorios automáticos de baños, vacunas y desparasitaciones. Parlo sabe cuándo le toca servicio a cada mascota.',
    },
  ],
  waitlist: {
    heading: 'Únete a la lista de espera exclusiva',
    subtitle: 'Acceso anticipado para un número limitado de negocios de mascotas',
    businessPlaceholder: 'Patitas Felices',
    activityPlaceholder: 'Estética canina, veterinaria, pet shop, pensión...',
    fuente: 'landing-parlo-mascotas',
  },
  footer: {
    tagline: 'Hecho en México 🐕🐱🐾',
  },
};
