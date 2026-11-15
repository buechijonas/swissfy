const NOTICE =
  'Se aplican el derecho suizo y el derecho alemán. Solo la versión alemana es vinculante; las traducciones son meramente informativas.'

export default {
  impressum: {
    illustration: 'impressum',
    notice: NOTICE,
    sections: [
      {
        lines: [
          'Responsable del contenido según el § 5 TMG (ley alemana de telemedios) y el art. 4, apdo. 7 RGPD',
          'Jonas S. Büchi',
          'Eichmatt 1',
          'CH-3324 Hindelbank',
          'Cantón de Berna',
        ],
      },
      {
        title: 'Responsabilidad por los contenidos',
        lines: [
          'Los contenidos de nuestro sitio se han elaborado con el máximo cuidado. Sin embargo, no podemos garantizar que sean correctos, completos ni actuales.',
        ],
      },
      {
        title: 'Aviso obligatorio',
        lines: [
          'Esta aplicación web está bajo la influencia de la organización Kiidle. El aviso figura aquí debido a la obligación de aviso legal vigente en la Unión Europea y en Suiza.',
        ],
      },
      {
        title: 'Fuentes de datos',
        lines: [
          'Los datos y las portadas de películas y series proceden de IMDb (imdb.com); los de juegos, de Steam (store.steampowered.com). Swissfy no está vinculado con IMDb ni con Valve.',
        ],
      },
    ],
  },
  privacy: {
    illustration: 'privacy',
    notice: NOTICE,
    sections: [
      {
        title: '1. Responsable',
        lines: ['Jonas S. Büchi', 'Berna, Suiza', 'contact@wintersehn.ch'],
      },
      {
        title: '2. Finalidad del tratamiento de datos',
        text: 'Este proyecto es una iniciativa puramente recreativa que sirve exclusivamente a la formación y a la transmisión de conocimientos. El uso de la aplicación web presupone aceptar que yo trate datos personales en el marco de su administración. Se invita a los usuarios que no deseen aceptar esta regla a dejar de usar la plataforma.',
      },
      {
        title: '3. Datos recogidos',
        text: 'Al usar nuestra aplicación web, el servidor web guarda automáticamente información en los llamados archivos de registro. Estos contienen la dirección IP, el tipo de navegador, el sistema operativo, la URL de referencia, posiblemente partes del historial de navegación, así como la fecha y la hora del acceso. Estos datos no se transmiten.',
      },
      {
        title: '4. Base jurídica',
        text: 'Los datos mencionados se tratan conforme al art. 6, apdo. 1, letra f RGPD; nuestro interés legítimo consiste en operar una aplicación web funcional y fácil de usar.',
      },
      {
        title: '5. Plazo de conservación',
        text: 'Los datos personales solo se conservan mientras sea necesario para alcanzar los fines aquí indicados y, como máximo, 10 años tras la desactivación de la cuenta.',
      },
      {
        title: '6. Cesión a terceros',
        text: 'No se ceden datos personales a terceros. Los términos de búsqueda de películas, series y juegos favoritos se envían a IMDb o Steam a través de nuestro servidor, sin relación con tu persona. Las portadas también se cargan a través de nuestro servidor, de modo que tu dirección IP no se transmite a estos servicios.',
      },
      {
        title: '7. Derechos de las personas afectadas',
        text: 'Tienes derecho a obtener información sobre los datos personales que tratamos y a solicitar su rectificación, supresión o la limitación de su tratamiento. También puedes oponerte al tratamiento de tus datos personales. Para ello, dirígete a la dirección de contacto indicada arriba.',
      },
      {
        title: '8. Modificación de la política de privacidad',
        text: 'Nos reservamos el derecho de modificar esta política de privacidad para adaptarla a los requisitos legales vigentes o a cambios en nuestros servicios. La versión actual está siempre disponible en esta aplicación web.',
      },
    ],
  },
  terms: {
    illustration: 'terms',
    notice: NOTICE,
    sections: [
      {
        title: '1. Principios generales',
        text: 'Esta aplicación web es un proyecto recreativo que sirve exclusivamente a la formación y a la transmisión de conocimientos. Su uso está sujeto a estas condiciones de uso, que los responsables pueden modificar en cualquier momento. Al usar la aplicación web aceptas estas condiciones de uso.',
      },
      {
        title: '2. Persecución penal',
        text: 'El uso de esta aplicación web presupone el cumplimiento de las leyes europeas y suizas vigentes. Las infracciones como el ciberacoso, el robo de datos u otros actos ilícitos se perseguirán penalmente con todo rigor. En tales casos se transmitirán todos los datos personales y altamente sensibles a las autoridades competentes para garantizar la persecución y sanción de dichos delitos.',
      },
      {
        title: '3. Normas de conducta',
        text: 'Para garantizar un entorno seguro y respetuoso para todos los usuarios, en esta aplicación web están estrictamente prohibidas las siguientes conductas:',
        items: [
          {
            title: 'Antisemitismo',
            description: 'Cualquier forma de declaración o acto antisemita.',
          },
          {
            title: 'Contenido de explotación',
            description: 'Contenido dirigido a explotar a personas o animales.',
          },
          { title: 'Insulto', description: 'Uso de lenguaje despectivo, ofensivo o vulgar.' },
          {
            title: 'Caza de recompensas',
            description: 'Aprovechamiento indebido de las funciones de la plataforma.',
          },
          { title: 'Acoso', description: 'Acercamiento, contacto o persecución inapropiados.' },
          { title: 'Fraude', description: 'Engaño o conducta fraudulenta con ánimo de lucro.' },
          {
            title: 'Cristianofobia',
            description: 'Hostilidad o prejuicios hacia los cristianos o el cristianismo.',
          },
          {
            title: 'Ciberacoso infantil',
            description: 'Intentos de manipular o abusar de niños en línea.',
          },
          {
            title: 'Ciberacoso',
            description: 'Acosar o intimidar a otros usuarios con contenido hiriente u ofensivo.',
          },
          {
            title: 'Discriminación',
            description:
              'Perjudicar o menospreciar a personas por su sexo, raza, religión, orientación sexual u otras características personales.',
          },
          {
            title: 'Doxxing',
            description:
              'Publicar o divulgar información privada sin el consentimiento de la persona afectada.',
          },
          {
            title: 'Amenaza',
            description: 'Amenaza de violencia, asesinato u otras consecuencias negativas.',
          },
          {
            title: 'Extorsión',
            description:
              'Cualquier acto por el que se obligue a una persona a algo bajo la amenaza de perjuicios.',
          },
          { title: 'Desinformación', description: 'Difusión de información falsa o engañosa.' },
          { title: 'Fascismo', description: 'Promoción o difusión de ideologías fascistas.' },
          {
            title: 'Xenofobia',
            description: 'Hostilidad o prejuicios hacia extranjeros o minorías étnicas.',
          },
          {
            title: 'Teorías conspirativas peligrosas',
            description:
              'Difusión o apoyo de teorías que pueden fomentar el pánico, el miedo o la violencia.',
          },
          {
            title: 'Contenido violento',
            description: 'Difusión de contenido que fomenta o representa la violencia.',
          },
          {
            title: 'Apología de la violencia',
            description:
              'Fomento o justificación de la violencia contra personas, grupos o instituciones.',
          },
          {
            title: 'Discurso de odio',
            description:
              'Declaraciones que incitan al odio o a la violencia contra determinados grupos.',
          },
          {
            title: 'Homofobia',
            description: 'Hostilidad o prejuicios hacia las personas homosexuales.',
          },
          {
            title: 'Suplantación de identidad',
            description: 'Hacerse pasar por otra persona, institución o entidad.',
          },
          {
            title: 'Contenido ilegal',
            description:
              'Difusión o puesta a disposición de contenido contrario al derecho vigente.',
          },
          {
            title: 'Islamofobia',
            description: 'Hostilidad o prejuicios hacia los musulmanes o el islam.',
          },
          {
            title: 'Apropiación cultural',
            description:
              'Uso o representación inapropiados de símbolos, tradiciones o valores culturales.',
          },
          {
            title: 'Protección de menores',
            description: 'Actos contrarios a la protección de menores, como el contacto indebido.',
          },
          {
            title: 'Abuso de privilegios',
            description:
              'Cualquier forma de aprovechamiento injustificado de derechos o derechos de acceso en esta aplicación web.',
          },
          {
            title: 'Plagio',
            description:
              'Subir o compartir contenido copiado o reproducido sin el consentimiento de terceros.',
          },
          {
            title: 'Contenido pornográfico',
            description:
              'Difusión, puesta a disposición o acceso a contenido pornográfico o sexual.',
          },
          {
            title: 'Propaganda',
            description:
              'Difusión de información política o ideológicamente sesgada con fines de manipulación.',
          },
          {
            title: 'Racismo',
            description: 'Discriminación u hostilidad hacia personas por su origen étnico.',
          },
          {
            title: 'Relativización',
            description: 'Minimizar o negar delitos o violaciones de derechos humanos.',
          },
          {
            title: 'Autolesión',
            description:
              'Contenido o conductas que alientan o fomentan la autolesión o el comportamiento suicida. En su lugar, pedimos animar a buscar ayuda y a hablar de ello con alguien.',
          },
          {
            title: 'Justicia por mano propia',
            description:
              'Fomento o glorificación de actos destinados a tomarse la justicia por su mano.',
          },
          { title: 'Sexismo', description: 'Discriminación o menosprecio por razón de sexo.' },
          {
            title: 'Sextorsión',
            description: 'Extorsión bajo la amenaza de publicar información privada o íntima.',
          },
          {
            title: 'Spam',
            description: 'Mensajes no deseados ni solicitados, en particular publicitarios.',
          },
          {
            title: 'Lenguaje inapropiado',
            description: 'Uso de expresiones irrespetuosas, ofensivas o inapropiadas.',
          },
          {
            title: 'Publicidad poco ética',
            description:
              'Promoción de productos, servicios o contenidos fraudulentos, poco éticos o dañinos.',
          },
          {
            title: 'Whataboutismo',
            description: 'Desviar una crítica señalando otras faltas en lugar de responderla.',
          },
        ],
      },
      {
        title: '4. Modificación de las condiciones de uso',
        text: 'Las condiciones de uso pueden modificarse en cualquier momento sin previo aviso. Se pide a los usuarios que las revisen periódicamente para mantenerse al día.',
      },
      {
        title: '5. Propiedad intelectual',
        text: 'Todo el contenido de esta plataforma, incluidos textos, imágenes, gráficos, logotipos y software, está protegido por derechos de autor. Queda prohibida su reproducción, distribución o uso sin autorización expresa.',
      },
      {
        title: '6. Denuncia de abusos',
        text: 'Si detectas infracciones de las condiciones de uso o conductas abusivas, estás obligado a denunciarlas de inmediato a través de los canales previstos. De lo contrario, infringes las condiciones de uso.',
      },
    ],
  },
  disclaimer: {
    illustration: 'disclaimer',
    notice: NOTICE,
    sections: [
      {
        title: '1. Contenido de la oferta en línea',
        text: 'Los contenidos de esta aplicación web se han desarrollado con el máximo cuidado posible. Sin embargo, no podemos garantizar que sean correctos, completos ni actuales. Como proveedores de servicios, somos responsables de nuestros propios contenidos en estas páginas conforme al § 7, apdo. 1 TMG y las leyes generales. Según los §§ 8 a 10 TMG, no estamos obligados a supervisar información de terceros transmitida o almacenada ni a investigar circunstancias que indiquen una actividad ilícita. Las obligaciones de eliminar o bloquear el uso de información conforme a las leyes generales no se ven afectadas. No obstante, solo cabe una responsabilidad al respecto a partir del momento en que tengamos conocimiento de una infracción concreta. En cuanto tengamos conocimiento de tales infracciones, eliminaremos estos contenidos de inmediato.',
      },
      {
        title: '2. Responsabilidad por enlaces',
        text: 'Nuestra oferta contiene enlaces a sitios web externos de terceros sobre cuyo contenido no tenemos influencia. Por ello no podemos asumir responsabilidad alguna por esos contenidos. El responsable del contenido de las páginas enlazadas es siempre su proveedor u operador. Sin embargo, no es razonable un control permanente del contenido de las páginas enlazadas sin indicios concretos de una infracción. En cuanto tengamos conocimiento de infracciones, eliminaremos dichos enlaces de inmediato.',
      },
      {
        title: '3. Derechos de autor',
        text: 'Los contenidos y obras creados por los operadores del sitio en estas páginas están sujetos al derecho de autor alemán. La reproducción, edición, distribución y cualquier tipo de explotación fuera de los límites del derecho de autor requieren el consentimiento por escrito del autor o creador correspondiente. Las descargas y copias de este sitio solo están permitidas para uso privado y no comercial. En la medida en que los contenidos de este sitio no hayan sido creados por el operador, se respetan los derechos de autor de terceros y sus contenidos se identifican como tales. Si aun así detectas una infracción de derechos de autor, te rogamos que nos lo comuniques. En cuanto tengamos conocimiento de infracciones, eliminaremos dichos contenidos de inmediato.',
      },
      {
        title: '4. Responsabilidad por daños',
        text: 'Excluimos toda responsabilidad por daños derivados directa o indirectamente del uso de esta aplicación web y de la información que contiene, salvo que se deban a dolo o negligencia grave.',
      },
      {
        title: '5. Sin requerimiento sin contacto previo',
        text: 'Si algún contenido de esta aplicación web vulnera derechos de terceros o disposiciones legales, te rogamos que nos lo comuniques sin nota de gastos. Garantizamos que los contenidos objetados con razón se analizarán y evaluarán sin necesidad de recurrir a un abogado. Rechazaremos íntegramente los gastos que ocasiones sin contacto previo y, en su caso, presentaremos una reconvención por infracción de las disposiciones mencionadas.',
      },
    ],
  },
}
