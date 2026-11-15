const NOTICE =
  'Si applicano il diritto svizzero e il diritto tedesco. Fa fede unicamente la versione tedesca; le traduzioni hanno scopo puramente informativo.'

export default {
  impressum: {
    illustration: 'impressum',
    notice: NOTICE,
    sections: [
      {
        lines: [
          'Responsabile del contenuto ai sensi del § 5 TMG (legge tedesca sui telemedia) e dell’art. 4 cpv. 7 RGPD',
          'Jonas S. Büchi',
          'Eichmatt 1',
          'CH-3324 Hindelbank',
          'Canton Berna',
        ],
      },
      {
        title: 'Responsabilità per i contenuti',
        lines: [
          'I contenuti del nostro sito sono stati realizzati con la massima cura. Non possiamo tuttavia garantirne l’esattezza, la completezza e l’attualità.',
        ],
      },
      {
        title: 'Avviso obbligatorio',
        lines: [
          'Questa applicazione web è sotto l’influenza dell’organizzazione Kiidle. L’avviso è riportato qui in virtù dell’obbligo di note legali vigente nell’Unione europea e in Svizzera.',
        ],
      },
      {
        title: 'Fonti dei dati',
        lines: [
          'Le informazioni e le copertine di film e serie provengono da IMDb (imdb.com), quelle dei giochi da Steam (store.steampowered.com). Swissfy non è collegato a IMDb né a Valve.',
        ],
      },
    ],
  },
  privacy: {
    illustration: 'privacy',
    notice: NOTICE,
    sections: [
      {
        title: '1. Titolare del trattamento',
        lines: ['Jonas S. Büchi', 'Berna, Svizzera', 'contact@wintersehn.ch'],
      },
      {
        title: '2. Finalità del trattamento dei dati',
        text: 'Questo progetto è un’iniziativa puramente ricreativa che serve esclusivamente alla formazione continua e alla trasmissione di conoscenze. L’uso dell’applicazione web presuppone l’accettazione del trattamento dei dati personali nell’ambito della sua gestione da parte mia. Gli utenti che non desiderano accettare questa regola sono invitati a non utilizzare più la piattaforma.',
      },
      {
        title: '3. Dati raccolti',
        text: 'Durante l’uso della nostra applicazione web, il server web salva automaticamente informazioni nei cosiddetti file di log. Questi contengono l’indirizzo IP, il tipo di browser, il sistema operativo, l’URL di provenienza, eventualmente parti della cronologia di navigazione nonché la data e l’ora dell’accesso. Questi dati non vengono trasmessi.',
      },
      {
        title: '4. Base giuridica',
        text: 'Il trattamento dei dati citati avviene ai sensi dell’art. 6 cpv. 1 lett. f RGPD; il nostro interesse legittimo consiste nel gestire un’applicazione web funzionante e facile da usare.',
      },
      {
        title: '5. Durata della conservazione',
        text: 'I dati personali vengono conservati solo per il tempo necessario a raggiungere le finalità qui indicate, al massimo però 10 anni dopo la disattivazione dell’account.',
      },
      {
        title: '6. Trasmissione a terzi',
        text: 'I dati personali non vengono trasmessi a terzi. I termini di ricerca per film, serie e giochi preferiti vengono inviati a IMDb o Steam tramite il nostro server senza riferimento alla tua persona. Anche le copertine vengono caricate tramite il nostro server, così il tuo indirizzo IP non viene trasmesso a questi servizi.',
      },
      {
        title: '7. Diritti delle persone interessate',
        text: 'Hai il diritto di ottenere informazioni sui dati personali che trattiamo e di chiederne la rettifica, la cancellazione o la limitazione del trattamento. Puoi inoltre opporti al trattamento dei tuoi dati personali. Rivolgiti per questo all’indirizzo di contatto indicato sopra.',
      },
      {
        title: '8. Modifica dell’informativa sulla privacy',
        text: 'Ci riserviamo il diritto di modificare questa informativa per adeguarla ai requisiti legali attuali o a modifiche dei nostri servizi. La versione aggiornata è sempre disponibile su questa applicazione web.',
      },
    ],
  },
  terms: {
    illustration: 'terms',
    notice: NOTICE,
    sections: [
      {
        title: '1. Principi generali',
        text: 'Questa applicazione web è un progetto ricreativo che serve esclusivamente alla formazione continua e alla trasmissione di conoscenze. Il suo uso è soggetto alle presenti condizioni d’uso, che i responsabili possono modificare in qualsiasi momento. Utilizzando l’applicazione web accetti queste condizioni d’uso.',
      },
      {
        title: '2. Perseguimento penale',
        text: 'L’uso di questa applicazione web presuppone il rispetto delle leggi europee e svizzere vigenti. Violazioni come il cyberbullismo, il furto di dati o altri atti illeciti saranno perseguite penalmente con il massimo rigore. In tali casi tutti i dati personali e altamente sensibili saranno trasmessi alle autorità competenti per garantire il perseguimento e la punizione di questi reati.',
      },
      {
        title: '3. Regole di comportamento',
        text: 'Per garantire un ambiente sicuro e rispettoso a tutti gli utenti, su questa applicazione web sono severamente vietati i seguenti comportamenti:',
        items: [
          {
            title: 'Antisemitismo',
            description: 'Qualsiasi forma di affermazione o azione antisemita.',
          },
          {
            title: 'Contenuti di sfruttamento',
            description: 'Contenuti volti allo sfruttamento di persone o animali.',
          },
          {
            title: 'Insulto',
            description: 'Uso di un linguaggio denigratorio, offensivo o volgare.',
          },
          {
            title: 'Caccia alle ricompense',
            description: 'Sfruttamento illecito delle funzioni della piattaforma.',
          },
          {
            title: 'Molestia',
            description: 'Avvicinamento, contatto o persecuzione inappropriati.',
          },
          {
            title: 'Frode',
            description: 'Inganno o comportamento fraudolento a scopo di arricchimento.',
          },
          {
            title: 'Cristianofobia',
            description: 'Ostilità o pregiudizi nei confronti dei cristiani o del cristianesimo.',
          },
          {
            title: 'Adescamento online',
            description: 'Tentativi di manipolare o abusare di bambini online.',
          },
          {
            title: 'Cyberbullismo',
            description: 'Molestare o bullizzare altri utenti con contenuti offensivi o lesivi.',
          },
          {
            title: 'Discriminazione',
            description:
              'Svantaggiare o denigrare persone in base a sesso, razza, religione, orientamento sessuale o altre caratteristiche personali.',
          },
          {
            title: 'Doxxing',
            description:
              'Pubblicazione o divulgazione di informazioni private senza il consenso della persona interessata.',
          },
          {
            title: 'Minaccia',
            description: 'Minaccia di violenza, omicidio o altre conseguenze negative.',
          },
          {
            title: 'Estorsione',
            description:
              'Qualsiasi atto con cui una persona viene costretta a qualcosa con la minaccia di un danno.',
          },
          {
            title: 'Disinformazione',
            description: 'Diffusione di informazioni false o fuorvianti.',
          },
          { title: 'Fascismo', description: 'Promozione o diffusione di ideologie fasciste.' },
          {
            title: 'Xenofobia',
            description: 'Ostilità o pregiudizi verso stranieri o minoranze etniche.',
          },
          {
            title: 'Teorie del complotto pericolose',
            description:
              'Diffusione o sostegno di teorie che possono generare panico, paura o violenza.',
          },
          {
            title: 'Contenuti violenti',
            description: 'Diffusione di contenuti che promuovono o rappresentano la violenza.',
          },
          {
            title: 'Apologia della violenza',
            description:
              'Promozione o giustificazione della violenza contro persone, gruppi o istituzioni.',
          },
          {
            title: 'Incitamento all’odio',
            description:
              'Affermazioni che incitano all’odio o alla violenza contro determinati gruppi.',
          },
          { title: 'Omofobia', description: 'Ostilità o pregiudizi verso le persone omosessuali.' },
          {
            title: 'Furto d’identità',
            description: 'Spacciarsi per un’altra persona, istituzione o entità.',
          },
          {
            title: 'Contenuti illegali',
            description:
              'Diffusione o messa a disposizione di contenuti contrari al diritto vigente.',
          },
          {
            title: 'Islamofobia',
            description: 'Ostilità o pregiudizi verso i musulmani o l’islam.',
          },
          {
            title: 'Appropriazione culturale',
            description:
              'Uso o rappresentazione inappropriati di simboli, tradizioni o valori culturali.',
          },
          {
            title: 'Tutela dei minori',
            description: 'Azioni contrarie alla tutela dei minori, come contatti non ammessi.',
          },
          {
            title: 'Abuso di privilegi',
            description:
              'Qualsiasi forma di sfruttamento ingiustificato di diritti o diritti di accesso su questa applicazione web.',
          },
          {
            title: 'Plagio',
            description:
              'Caricamento o condivisione di contenuti copiati o riprodotti senza il consenso di terzi.',
          },
          {
            title: 'Contenuti pornografici',
            description:
              'Diffusione, messa a disposizione o accessibilità di contenuti pornografici o sessuali.',
          },
          {
            title: 'Propaganda',
            description:
              'Diffusione di informazioni politicamente o ideologicamente unilaterali a scopo di manipolazione.',
          },
          {
            title: 'Razzismo',
            description:
              'Discriminazione o ostilità verso persone a causa della loro origine etnica.',
          },
          {
            title: 'Relativizzazione',
            description: 'Minimizzazione o negazione di reati o violazioni dei diritti umani.',
          },
          {
            title: 'Autolesionismo',
            description:
              'Contenuti o comportamenti che incoraggiano o favoriscono l’autolesionismo o comportamenti suicidi. Chiediamo invece di incoraggiare a cercare aiuto e a parlarne con qualcuno.',
          },
          {
            title: 'Giustizia privata',
            description: 'Promozione o glorificazione di azioni volte a farsi giustizia da sé.',
          },
          { title: 'Sessismo', description: 'Discriminazione o denigrazione in base al sesso.' },
          {
            title: 'Sextortion',
            description: 'Estorsione con la minaccia di pubblicare informazioni private o intime.',
          },
          {
            title: 'Spam',
            description: 'Messaggi indesiderati e non richiesti, in particolare pubblicitari.',
          },
          {
            title: 'Linguaggio inappropriato',
            description: 'Uso di espressioni irrispettose, offensive o inappropriate.',
          },
          {
            title: 'Pubblicità non etica',
            description:
              'Promozione di prodotti, servizi o contenuti fraudolenti, non etici o dannosi.',
          },
          {
            title: 'Benaltrismo',
            description: 'Sviare una critica indicando altri torti invece di rispondere.',
          },
        ],
      },
      {
        title: '4. Modifica delle condizioni d’uso',
        text: 'Le condizioni d’uso possono essere modificate in qualsiasi momento senza preavviso. Gli utenti sono invitati a consultarle regolarmente per restare aggiornati.',
      },
      {
        title: '5. Proprietà intellettuale',
        text: 'Tutti i contenuti di questa piattaforma, compresi testi, immagini, grafiche, loghi e software, sono protetti dal diritto d’autore. La riproduzione, la diffusione o l’uso dei contenuti senza autorizzazione esplicita sono vietati.',
      },
      {
        title: '6. Segnalazione di abusi',
        text: 'Se noti violazioni delle condizioni d’uso o comportamenti abusivi, sei tenuto a segnalarli immediatamente tramite i canali previsti. In caso contrario violi le condizioni d’uso.',
      },
    ],
  },
  disclaimer: {
    illustration: 'disclaimer',
    notice: NOTICE,
    sections: [
      {
        title: '1. Contenuto dell’offerta online',
        text: 'I contenuti di questa applicazione web sono stati sviluppati con la massima cura. Non possiamo tuttavia garantirne l’esattezza, la completezza e l’attualità. In qualità di fornitori di servizi siamo responsabili dei nostri contenuti su queste pagine secondo il § 7 cpv. 1 TMG e le leggi generali. Secondo i §§ da 8 a 10 TMG non siamo però tenuti a sorvegliare informazioni di terzi trasmesse o memorizzate né a ricercare circostanze che indichino un’attività illecita. Gli obblighi di rimozione o di blocco dell’uso di informazioni secondo le leggi generali restano invariati. Una responsabilità in tal senso è tuttavia possibile solo dal momento in cui veniamo a conoscenza di una violazione concreta. Non appena ne veniamo a conoscenza, rimuoveremo immediatamente tali contenuti.',
      },
      {
        title: '2. Responsabilità per i link',
        text: 'La nostra offerta contiene link a siti web esterni di terzi, sui cui contenuti non abbiamo alcuna influenza. Non possiamo quindi assumerci alcuna responsabilità per tali contenuti. Il rispettivo fornitore o gestore delle pagine collegate è sempre responsabile dei loro contenuti. Un controllo permanente dei contenuti delle pagine collegate non è tuttavia ragionevole senza indizi concreti di una violazione. Non appena veniamo a conoscenza di violazioni, rimuoveremo immediatamente tali link.',
      },
      {
        title: '3. Diritto d’autore',
        text: 'I contenuti e le opere creati dai gestori del sito su queste pagine sono soggetti al diritto d’autore tedesco. La riproduzione, l’elaborazione, la diffusione e ogni forma di utilizzo al di fuori dei limiti del diritto d’autore richiedono il consenso scritto del rispettivo autore o creatore. Download e copie di questo sito sono consentiti solo per uso privato e non commerciale. Nella misura in cui i contenuti di questo sito non sono stati creati dal gestore, vengono rispettati i diritti d’autore di terzi e i contenuti di terzi sono contrassegnati come tali. Se dovessi comunque notare una violazione del diritto d’autore, ti preghiamo di segnalarcelo. Non appena veniamo a conoscenza di violazioni, rimuoveremo immediatamente tali contenuti.',
      },
      {
        title: '4. Responsabilità per danni',
        text: 'Escludiamo qualsiasi responsabilità per danni derivanti direttamente o indirettamente dall’uso di questa applicazione web e delle informazioni in essa contenute, salvo che siano dovuti a dolo o colpa grave.',
      },
      {
        title: '5. Nessuna diffida senza contatto preliminare',
        text: 'Se i contenuti di questa applicazione web dovessero violare diritti di terzi o disposizioni di legge, ti preghiamo di inviarci una comunicazione senza nota spese. Garantiamo che i contenuti contestati a ragione saranno analizzati e valutati senza che sia necessario coinvolgere un legale. Respingeremo integralmente i costi da te causati senza contatto preliminare e, se del caso, presenteremo una domanda riconvenzionale per violazione delle disposizioni sopra citate.',
      },
    ],
  },
}
