const NOTICE =
  'Le droit suisse et le droit allemand s’appliquent. Seule la version allemande fait foi ; les traductions ne sont fournies qu’à titre informatif.'

export default {
  impressum: {
    illustration: 'impressum',
    notice: NOTICE,
    sections: [
      {
        lines: [
          'Responsable du contenu selon le § 5 TMG (loi allemande sur les télémédias) et l’art. 4, al. 7 RGPD',
          'Jonas S. Büchi',
          'Eichmatt 1',
          'CH-3324 Hindelbank',
          'Canton de Berne',
        ],
      },
      {
        title: 'Responsabilité pour les contenus',
        lines: [
          'Les contenus de notre site ont été créés avec le plus grand soin. Nous ne pouvons toutefois garantir leur exactitude, leur exhaustivité ni leur actualité.',
        ],
      },
      {
        title: 'Mention obligatoire',
        lines: [
          'Cette application web est placée sous l’influence de l’organisation Kiidle. Cette mention figure ici en raison de l’obligation de mentions légales en vigueur dans l’Union européenne et en Suisse.',
        ],
      },
      {
        title: 'Sources des données',
        lines: [
          'Les informations et couvertures des films et séries proviennent d’IMDb (imdb.com), celles des jeux de Steam (store.steampowered.com). Swissfy n’est lié ni à IMDb ni à Valve.',
        ],
      },
    ],
  },
  privacy: {
    illustration: 'privacy',
    notice: NOTICE,
    sections: [
      {
        title: '1. Responsable du traitement',
        lines: ['Jonas S. Büchi', 'Berne, Suisse', 'contact@wintersehn.ch'],
      },
      {
        title: '2. Finalité du traitement des données',
        text: 'Ce projet est une démarche purement récréative qui sert exclusivement à la formation continue et à la transmission de connaissances. L’utilisation de l’application web suppose d’accepter que des données personnelles soient traitées dans le cadre de son administration par moi. Les utilisateurs qui ne souhaitent pas accepter cette règle sont invités à ne plus utiliser la plateforme.',
      },
      {
        title: '3. Données collectées',
        text: 'Lors de l’utilisation de notre application web, le serveur web enregistre automatiquement des informations dans des fichiers journaux. Celles-ci comprennent l’adresse IP, le type de navigateur, le système d’exploitation, l’URL de référence, éventuellement des parties de l’historique de navigation ainsi que la date et l’heure de l’accès. Ces données ne sont pas transmises.',
      },
      {
        title: '4. Base juridique',
        text: 'Le traitement de ces données repose sur l’art. 6, al. 1, let. f RGPD, notre intérêt légitime étant d’exploiter une application web fonctionnelle et conviviale.',
      },
      {
        title: '5. Durée de conservation',
        text: 'Les données personnelles ne sont conservées qu’aussi longtemps que nécessaire pour atteindre les finalités mentionnées ici, et au maximum 10 ans après la désactivation du compte.',
      },
      {
        title: '6. Transmission à des tiers',
        text: 'Aucune donnée personnelle n’est transmise à des tiers. Les termes de recherche pour les films, séries et jeux préférés sont envoyés à IMDb ou à Steam via notre serveur, sans lien avec ta personne. Les couvertures sont également chargées via notre serveur, de sorte que ton adresse IP n’est pas transmise à ces services.',
      },
      {
        title: '7. Droits des personnes concernées',
        text: 'Tu as le droit d’obtenir des informations sur les données personnelles que nous traitons et d’en demander la rectification, l’effacement ou la limitation du traitement. Tu peux également t’opposer au traitement de tes données personnelles. Pour cela, adresse-toi à l’adresse de contact indiquée ci-dessus.',
      },
      {
        title: '8. Modification de la politique de confidentialité',
        text: 'Nous nous réservons le droit de modifier cette politique de confidentialité afin de l’adapter aux exigences légales actuelles ou à l’évolution de nos services. La version en vigueur est disponible à tout moment sur cette application web.',
      },
    ],
  },
  terms: {
    illustration: 'terms',
    notice: NOTICE,
    sections: [
      {
        title: '1. Principes généraux',
        text: 'Cette application web est un projet récréatif qui sert exclusivement à la formation continue et à la transmission de connaissances. Son utilisation est soumise aux présentes conditions d’utilisation, que les responsables peuvent adapter à tout moment. En utilisant l’application web, tu acceptes ces conditions d’utilisation.',
      },
      {
        title: '2. Poursuites pénales',
        text: 'L’utilisation de cette application web suppose le respect des lois européennes et suisses en vigueur. Les infractions telles que le cyberharcèlement, le vol de données ou d’autres actes illicites seront poursuivies pénalement avec la plus grande fermeté. Dans de tels cas, toutes les données personnelles et hautement sensibles seront transmises aux autorités compétentes afin de garantir la poursuite et la sanction de ces infractions.',
      },
      {
        title: '3. Règles de conduite',
        text: 'Afin de garantir un environnement sûr et respectueux pour tous les utilisateurs, les comportements suivants sont strictement interdits sur cette application web :',
        items: [
          { title: 'Antisémitisme', description: 'Toute forme de propos ou d’acte antisémite.' },
          {
            title: 'Contenus d’exploitation',
            description: 'Contenus visant à exploiter des êtres humains ou des animaux.',
          },
          { title: 'Insulte', description: 'Usage d’un langage dénigrant, insultant ou vulgaire.' },
          {
            title: 'Chasse aux récompenses',
            description: 'Exploitation abusive des fonctions de la plateforme.',
          },
          {
            title: 'Harcèlement',
            description: 'Approche, prise de contact ou traque inappropriées.',
          },
          {
            title: 'Fraude',
            description: 'Tromperie ou comportement frauduleux dans un but d’enrichissement.',
          },
          {
            title: 'Christianophobie',
            description: 'Hostilité ou préjugés envers les chrétiens ou le christianisme.',
          },
          {
            title: 'Pédopiégeage en ligne',
            description: 'Tentatives de manipuler ou d’abuser des enfants en ligne.',
          },
          {
            title: 'Cyberharcèlement',
            description:
              'Harcèlement ou intimidation d’autres utilisateurs par des contenus blessants ou insultants.',
          },
          {
            title: 'Discrimination',
            description:
              'Désavantager ou dénigrer des personnes en raison de leur sexe, de leur race, de leur religion, de leur orientation sexuelle ou d’autres caractéristiques personnelles.',
          },
          {
            title: 'Doxxing',
            description:
              'Publication ou transmission d’informations privées sans le consentement de la personne concernée.',
          },
          {
            title: 'Menace',
            description: 'Menace de violence, de meurtre ou d’autres conséquences négatives.',
          },
          {
            title: 'Chantage',
            description:
              'Tout acte par lequel une personne est contrainte à quelque chose sous la menace d’un préjudice.',
          },
          {
            title: 'Désinformation',
            description: 'Diffusion d’informations fausses ou trompeuses.',
          },
          { title: 'Fascisme', description: 'Promotion ou diffusion d’idéologies fascistes.' },
          {
            title: 'Xénophobie',
            description: 'Hostilité ou préjugés envers les étrangers ou les minorités ethniques.',
          },
          {
            title: 'Théories du complot dangereuses',
            description:
              'Diffusion ou soutien de théories pouvant susciter la panique, la peur ou la violence.',
          },
          {
            title: 'Contenu violent',
            description: 'Diffusion de contenus qui promeuvent ou représentent la violence.',
          },
          {
            title: 'Apologie de la violence',
            description:
              'Promotion ou justification de la violence envers des personnes, des groupes ou des institutions.',
          },
          {
            title: 'Discours de haine',
            description: 'Propos appelant à la haine ou à la violence envers certains groupes.',
          },
          {
            title: 'Homophobie',
            description: 'Hostilité ou préjugés envers les personnes homosexuelles.',
          },
          {
            title: 'Usurpation d’identité',
            description: 'Se faire passer pour une autre personne, institution ou entité.',
          },
          {
            title: 'Contenus illégaux',
            description:
              'Diffusion ou mise à disposition de contenus contraires au droit en vigueur.',
          },
          {
            title: 'Islamophobie',
            description: 'Hostilité ou préjugés envers les musulmans ou l’islam.',
          },
          {
            title: 'Appropriation culturelle',
            description:
              'Utilisation ou représentation inappropriée de symboles, de traditions ou de valeurs culturels.',
          },
          {
            title: 'Protection des mineurs',
            description:
              'Actes contraires à la protection des mineurs, comme un contact inadmissible.',
          },
          {
            title: 'Abus de privilèges',
            description:
              'Toute forme d’exploitation injustifiée de droits ou de droits d’accès sur cette application web.',
          },
          {
            title: 'Plagiat',
            description:
              'Mise en ligne ou partage de contenus copiés ou reproduits sans le consentement de tiers.',
          },
          {
            title: 'Contenus pornographiques',
            description:
              'Diffusion, mise à disposition ou accessibilité de contenus pornographiques ou sexuels.',
          },
          {
            title: 'Propagande',
            description:
              'Diffusion d’informations politiquement ou idéologiquement partiales à des fins de manipulation.',
          },
          {
            title: 'Racisme',
            description:
              'Discrimination ou hostilité envers des personnes en raison de leur origine ethnique.',
          },
          {
            title: 'Relativisation',
            description: 'Banalisation ou négation de crimes ou de violations des droits humains.',
          },
          {
            title: 'Mise en danger de soi',
            description:
              'Contenus ou comportements qui encouragent l’automutilation ou les comportements suicidaires. Nous demandons plutôt d’encourager à chercher de l’aide et à en parler à quelqu’un.',
          },
          {
            title: 'Justice expéditive',
            description: 'Promotion ou glorification d’actes visant à se faire justice soi-même.',
          },
          { title: 'Sexisme', description: 'Discrimination ou dénigrement fondé sur le sexe.' },
          {
            title: 'Sextorsion',
            description: 'Chantage sous la menace de publier des informations privées ou intimes.',
          },
          {
            title: 'Spam',
            description: 'Messages non désirés et non sollicités, en particulier publicitaires.',
          },
          {
            title: 'Langage inapproprié',
            description: 'Usage d’expressions irrespectueuses, insultantes ou inappropriées.',
          },
          {
            title: 'Publicité contraire à l’éthique',
            description:
              'Promotion de produits, de services ou de contenus frauduleux, contraires à l’éthique ou nuisibles.',
          },
          {
            title: 'Whataboutisme',
            description: 'Détourner une critique en pointant d’autres torts au lieu d’y répondre.',
          },
        ],
      },
      {
        title: '4. Modification des conditions d’utilisation',
        text: 'Les conditions d’utilisation peuvent être modifiées à tout moment sans préavis. Les utilisateurs sont invités à les consulter régulièrement afin de rester informés.',
      },
      {
        title: '5. Propriété intellectuelle',
        text: 'Tous les contenus de cette plateforme, y compris les textes, images, graphiques, logos et logiciels, sont protégés par le droit d’auteur. Leur reproduction, diffusion ou utilisation sans autorisation expresse est interdite.',
      },
      {
        title: '6. Signalement des abus',
        text: 'Si tu constates des violations des conditions d’utilisation ou des comportements abusifs, tu es tenu de les signaler sans délai via les canaux prévus. À défaut, tu enfreins les conditions d’utilisation.',
      },
    ],
  },
  disclaimer: {
    illustration: 'disclaimer',
    notice: NOTICE,
    sections: [
      {
        title: '1. Contenu de l’offre en ligne',
        text: 'Les contenus de cette application web ont été élaborés avec le plus grand soin. Nous ne pouvons toutefois garantir leur exactitude, leur exhaustivité ni leur actualité. En tant que prestataire, nous sommes responsables de nos propres contenus selon le § 7, al. 1 TMG et les lois générales. Selon les §§ 8 à 10 TMG, nous ne sommes toutefois pas tenus de surveiller les informations de tiers transmises ou stockées, ni de rechercher des circonstances indiquant une activité illicite. Les obligations de supprimer ou de bloquer l’utilisation d’informations selon les lois générales restent inchangées. Une responsabilité à cet égard n’est toutefois possible qu’à partir du moment où nous avons connaissance d’une violation concrète. Dès que nous aurons connaissance de telles violations, nous supprimerons immédiatement ces contenus.',
      },
      {
        title: '2. Responsabilité pour les liens',
        text: 'Notre offre contient des liens vers des sites web externes de tiers sur le contenu desquels nous n’avons aucune influence. Nous ne pouvons donc assumer aucune responsabilité pour ces contenus. Le fournisseur ou l’exploitant des pages liées est toujours responsable de leur contenu. Un contrôle permanent du contenu des pages liées n’est toutefois pas raisonnable sans indice concret d’une infraction. Dès que nous aurons connaissance d’infractions, nous supprimerons immédiatement ces liens.',
      },
      {
        title: '3. Droit d’auteur',
        text: 'Les contenus et œuvres créés par les exploitants du site sont soumis au droit d’auteur allemand. La reproduction, la modification, la diffusion et toute forme d’exploitation en dehors des limites du droit d’auteur nécessitent l’accord écrit de l’auteur ou du créateur. Les téléchargements et copies de ce site ne sont autorisés que pour un usage privé et non commercial. Dans la mesure où les contenus de ce site n’ont pas été créés par l’exploitant, les droits d’auteur de tiers sont respectés et les contenus de tiers sont signalés comme tels. Si tu remarques malgré tout une violation du droit d’auteur, merci de nous le signaler. Dès que nous aurons connaissance de violations, nous supprimerons immédiatement ces contenus.',
      },
      {
        title: '4. Responsabilité pour les dommages',
        text: 'Nous excluons toute responsabilité pour les dommages résultant directement ou indirectement de l’utilisation de cette application web et des informations qu’elle contient, pour autant qu’ils ne reposent pas sur une faute intentionnelle ou une négligence grave.',
      },
      {
        title: '5. Pas de mise en demeure sans contact préalable',
        text: 'Si des contenus de cette application web portent atteinte aux droits de tiers ou à des dispositions légales, nous te prions de nous en informer sans note de frais. Nous garantissons que les contenus contestés à juste titre seront analysés et évalués sans qu’il soit nécessaire de faire appel à un avocat. Nous rejetterons intégralement les frais engagés sans prise de contact préalable et déposerons, le cas échéant, une demande reconventionnelle pour violation des dispositions susmentionnées.',
      },
    ],
  },
}
