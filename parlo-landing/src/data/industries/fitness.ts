import type { IndustryConfig } from './index';

export const fitnessConfig: IndustryConfig = {
  seo: {
    title: 'Parlo - Asistente Inteligente para Gimnasios y Estudios Fitness',
    description: 'Conecta Parlo a tu WhatsApp en 2 minutos. Tu asistente 24/7 que agenda clases, gestiona horarios y manda recordatorios — todo desde WhatsApp.',
  },
  hero: {
    badge: '💪 Tu asistente por WhatsApp',
    headline: '¿Quieres crecer tu estudio o gimnasio?<br />Conoce a <span class="gradient-text">Parlo</span>, el asistente que llena tus clases',
    subheadline: 'Tu asistente 24/7 que agenda clases, gestiona y actualiza tu calendario de sesiones, manda recordatorios y te ayuda a que tus alumnos no dejen de entrenar — <strong>todo desde WhatsApp</strong>. Sin apps que nadie descarga, sin grupos de WhatsApp caóticos.',
    cta: 'Únete a la lista de espera exclusiva',
    promoLine: '🎁 Primera versión <strong class="text-secondary">totalmente gratis</strong> para grupo exclusivo',
  },
  howItWorks: {
    subtitle: 'Cinco formas en que Parlo transforma tu estudio',
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
          text: '¡Hola! 👋 Soy Parlo, tu nuevo asistente.<br><br>Voy a ayudarte a llenar tus clases. Cuéntame sobre tu estudio.',
          time: '9:41',
        },
        { role: 'bot', text: '¿Cómo se llama tu estudio o gimnasio?', time: '9:41' },
        { role: 'owner', text: 'Studio Box Fitness', time: '9:42' },
        {
          role: 'bot',
          text: 'Perfecto, Studio Box Fitness 🥊<br><br>¿Qué clases o servicios ofreces?',
          time: '9:42',
        },
        {
          role: 'owner',
          text: '- Clase de box $180<br>- Yoga $150<br>- Entrenamiento personal $400<br>- Paquete 10 clases $1,500',
          time: '9:43',
        },
        {
          role: 'bot',
          text: '¡Listo! 🎉<br><br>Ya estoy configurado. Tus alumnos ya pueden reservar clases conmigo.',
          time: '9:44',
        },
      ],
    },

    // ── Slide 2: Class Booking ──
    {
      tabLabel: 'Reservar',
      stepNumber: 2,
      slideTitle: 'Tus alumnos reservan solos',
      chatHeader: {
        name: 'Studio Box Fitness',
        subtitle: 'en línea',
        avatarEmoji: '🥊',
        avatarStyle: 'business',
      },
      messages: [
        { role: 'client', text: 'Hola! Quiero reservar clase de box para mañana', time: '20:15' },
        {
          role: 'bot',
          text: '¡Hola Daniela! 💪<br><br>Clases de box disponibles mañana:<br><br>• 7:00 AM (3 lugares)<br>• 6:00 PM (1 lugar) ⭐<br>• 8:00 PM (5 lugares)',
          time: '20:15',
        },
        { role: 'client', text: 'La de las 7 AM!', time: '20:16' },
        {
          role: 'bot',
          text: '✅ ¡Reservado!<br><br><strong>Mañana martes</strong><br>🕒 7:00 AM<br>🥊 Clase de box<br>💰 $180<br><br>Llega 10 min antes para calentar. ¡Nos vemos! 🔥',
          time: '20:16',
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
          time: '6:30',
          voiceNote: { duration: '0:04', transcript: '"Parlo, cómo van las clases de hoy?"' },
        },
        {
          role: 'bot',
          text: 'Clases del martes 11 feb:<br><br><strong>7:00 AM</strong> - Box 🥊<br>8/10 lugares reservados<br><br><strong>10:00 AM</strong> - Yoga 🧘‍♀️<br>6/8 lugares reservados<br><br><strong>6:00 PM</strong> - Box 🥊<br>10/10 ¡LLENA! ⭐<br><br><strong>8:00 PM</strong> - Box 🥊<br>5/10 lugares reservados',
          time: '6:30',
        },
        { role: 'owner', text: 'Abre 2 lugares más para la de las 6', time: '6:31' },
        {
          role: 'bot',
          text: '✅ Listo. La clase de box de las 6:00 PM ahora tiene 12 lugares (10 reservados, 2 disponibles) 👍',
          time: '6:31',
        },
      ],
    },

    // ── Slide 4: Reminders ──
    {
      tabLabel: 'Recordatorios',
      stepNumber: 4,
      slideTitle: 'Recordatorios automáticos',
      chatHeader: {
        name: 'Studio Box Fitness',
        subtitle: 'en línea',
        avatarEmoji: '🥊',
        avatarStyle: 'business',
      },
      messages: [
        {
          role: 'bot',
          text: 'Hola Daniela! 💪<br><br>Te recuerdo que mañana tienes clase de box a las 7:00 AM.<br><br>🥊 Trae guantes y toalla<br><br>¿Vas a asistir?',
          time: '20:00',
        },
        { role: 'client', text: 'Uy mañana no puedo, me la puedes cambiar?', time: '20:10' },
        {
          role: 'bot',
          text: 'Claro! Clases de box disponibles esta semana:<br><br>• Miércoles 7:00 AM (4 lugares)<br>• Jueves 6:00 PM (2 lugares)<br>• Viernes 7:00 AM (6 lugares)',
          time: '20:10',
        },
        { role: 'client', text: 'Jueves a las 6!', time: '20:11' },
        {
          role: 'bot',
          text: '✅ ¡Cambiado!<br><br><strong>Jueves</strong><br>🕒 6:00 PM<br>🥊 Clase de box<br><br>Tu lugar está apartado. ¡A darle! 🔥',
          time: '20:11',
        },
      ],
    },

    // ── Slide 5: Payments ──
    {
      tabLabel: 'Paquetes',
      stepNumber: 5,
      slideTitle: 'Vende paquetes por WhatsApp',
      chatHeader: {
        name: 'Studio Box Fitness',
        subtitle: 'en línea',
        avatarEmoji: '🥊',
        avatarStyle: 'business',
      },
      messages: [
        { role: 'client', text: 'Me interesa el paquete de 10 clases', time: '16:45' },
        {
          role: 'bot',
          text: '¡Excelente decisión! 💪<br><br>El paquete de 10 clases incluye:<br>• 10 clases de box, yoga o combinadas<br>• Válido por 2 meses<br>• Ahorro de $300 vs clases individuales<br><br>💰 $1,500 MXN',
          time: '16:45',
        },
        {
          role: 'bot',
          text: '',
          time: '16:46',
          paymentLink: { label: '💳 Comprar paquete $1,500', amount: '$1,500' },
        },
        {
          role: 'bot',
          text: '✅ ¡Paquete activado!<br><br>Tienes 10 clases disponibles 🎉<br>Vigencia: hasta el 11 de abril<br><br>¿Quieres reservar tu primera clase? 🥊',
          time: '16:47',
        },
      ],
    },

    // ── Slide 6: Re-engagement ──
    {
      tabLabel: 'Motivación',
      stepNumber: 6,
      slideTitle: 'Motiva a tus alumnos',
      chatHeader: {
        name: 'Studio Box Fitness',
        subtitle: 'en línea',
        avatarEmoji: '🥊',
        avatarStyle: 'parlo',
      },
      messages: [
        {
          role: 'bot',
          text: 'Hola Daniela! 🥊<br><br>¡Llevas 3 semanas entrenando sin faltar! 🔥<br><br>Estás en racha — no la rompas. ¿Reservo tu clase de esta semana?',
        },
        { role: 'client', text: 'Wow no sabía! sí, ponme el viernes' },
        {
          role: 'bot',
          text: 'Clases de box el viernes:<br><br>• 7:00 AM (5 lugares)<br>• 6:00 PM (3 lugares)',
        },
        { role: 'client', text: 'La de las 7 AM como siempre 💪' },
        {
          role: 'bot',
          text: '✅ ¡Reservado!<br><br><strong>Viernes 7:00 AM</strong><br>🥊 Clase de box<br><br>¡Ya son 4 semanas de racha! Sigue así campeona 🏆',
        },
      ],
    },
  ],
  benefits: [
    {
      icon: '📱',
      stat: '24/7',
      title: 'Reservas sin parar',
      text: 'Tus alumnos reservan clase a cualquier hora por WhatsApp. No más mensajes en grupo ni llamadas para apartar lugar.',
    },
    {
      icon: '📈',
      title: 'Clases más llenas',
      text: 'Parlo llena lugares vacíos avisando a alumnos interesados. Cada lugar vacío es dinero que se pierde.',
    },
    {
      icon: '💳',
      title: 'Vende paquetes fácil',
      text: 'Tus alumnos compran paquetes de clases directo por WhatsApp. Más ingresos recurrentes para tu estudio.',
    },
    {
      icon: '🔥',
      title: 'Alumnos motivados',
      text: 'Seguimiento automático y rachas de asistencia. Parlo motiva a tus alumnos a no faltar y mantener el hábito.',
    },
  ],
  waitlist: {
    heading: 'Únete a la lista de espera exclusiva',
    subtitle: 'Acceso anticipado para un número limitado de estudios y gimnasios',
    businessPlaceholder: 'Studio Box Fitness',
    activityPlaceholder: 'Gimnasio, estudio de yoga, box, crossfit, pilates...',
    fuente: 'landing-parlo-fitness',
  },
  footer: {
    tagline: 'Hecho en México 💪🧘‍♀️🥊',
  },
};
