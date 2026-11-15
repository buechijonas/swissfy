const NOTICE =
  'Swiss and German law apply. The German version is authoritative; translations are provided for convenience only.'

export default {
  impressum: {
    illustration: 'impressum',
    notice: NOTICE,
    sections: [
      {
        lines: [
          'Responsible for the content according to § 5 TMG (German Telemedia Act) and Art. 4 para. 7 GDPR',
          'Jonas S. Büchi',
          'Eichmatt 1',
          'CH-3324 Hindelbank',
          'Canton of Bern',
        ],
      },
      {
        title: 'Liability for content',
        lines: [
          'The content of our site was created with the greatest care. However, we cannot guarantee that the content is correct, complete and up to date.',
        ],
      },
      {
        title: 'Mandatory notice',
        lines: [
          'This web application is under the influence of the organisation Kiidle. This notice is included because of the imprint obligation in force in the European Union and Switzerland.',
        ],
      },
      {
        title: 'Data sources',
        lines: [
          'Details and covers of movies and series come from IMDb (imdb.com), those of games from Steam (store.steampowered.com). Swissfy is not affiliated with IMDb or Valve.',
        ],
      },
    ],
  },
  privacy: {
    illustration: 'privacy',
    notice: NOTICE,
    sections: [
      {
        title: '1. Controller',
        lines: ['Jonas S. Büchi', 'Bern, Switzerland', 'contact@wintersehn.ch'],
      },
      {
        title: '2. Purpose of the data processing',
        text: 'This project is a purely recreational undertaking that serves exclusively further education and the sharing of knowledge. Using the web application requires accepting that personal data is processed as part of its administration by me. Users who do not wish to agree to this are invited to stop using the platform.',
      },
      {
        title: '3. Data collected',
        text: 'When you use our web application, the web server automatically stores information in so-called log files. These contain the IP address, the browser type, the operating system, the referrer URL, potentially parts of the browser history, and the date and time of access. This data is not passed on.',
      },
      {
        title: '4. Legal basis',
        text: 'The data mentioned is processed according to Art. 6 para. 1 lit. f GDPR, our legitimate interest being to operate a working and user-friendly web application.',
      },
      {
        title: '5. Storage period',
        text: 'Personal data is only stored for as long as necessary to achieve the purposes stated here, but after an account has been deactivated for no longer than 10 years.',
      },
      {
        title: '6. Disclosure to third parties',
        text: 'Personal data is not passed on to third parties. Search terms for favourite movies, series and games are sent to IMDb or Steam through our server without any reference to you. Covers are also loaded through our server, so your IP address is not transmitted to these services.',
      },
      {
        title: '7. Rights of the data subjects',
        text: 'You have the right to obtain information about the personal data we process and to request its correction, deletion or the restriction of its processing. You can also object to the processing of your personal data. Please use the contact address given above for this.',
      },
      {
        title: '8. Changes to the privacy policy',
        text: 'We reserve the right to change this privacy policy to adapt it to current legal requirements or to changes in our services. The current version is always available on this web application.',
      },
    ],
  },
  terms: {
    illustration: 'terms',
    notice: NOTICE,
    sections: [
      {
        title: '1. General principles',
        text: 'This web application is a recreational undertaking that serves exclusively further education and the sharing of knowledge. Using the web application is subject to these terms of use, which those responsible may adapt at any time. By using the web application, you agree to these terms of use.',
      },
      {
        title: '2. Criminal prosecution',
        text: 'Using this web application requires compliance with the applicable European and Swiss laws. Violations such as cyberbullying, data theft or other unlawful acts will be prosecuted to the full extent of the law. In such cases, all personal and highly sensitive data will be passed on to the competent authorities to ensure that such offences are prosecuted and punished.',
      },
      {
        title: '3. Rules of conduct',
        text: 'To ensure a safe and respectful environment for all users, the following behaviour is strictly prohibited on this web application:',
        items: [
          {
            title: 'Antisemitism',
            description: 'Any form of antisemitic statement or act.',
          },
          {
            title: 'Exploitative content',
            description: 'Content aimed at exploiting people or animals.',
          },
          {
            title: 'Insult',
            description: 'Use of derogatory, insulting or vulgar language.',
          },
          {
            title: 'Reward hunting',
            description: 'Unlawfully exploiting features of the platform.',
          },
          {
            title: 'Harassment',
            description: 'Inappropriate advances, contact or stalking.',
          },
          {
            title: 'Fraud',
            description: 'Deception or fraudulent behaviour for the purpose of enrichment.',
          },
          {
            title: 'Christophobia',
            description: 'Hostility or prejudice towards Christians or Christianity.',
          },
          {
            title: 'Cybergrooming',
            description: 'Attempts to manipulate or abuse children online.',
          },
          {
            title: 'Cyberbullying',
            description: 'Harassing or bullying other users with hurtful or insulting content.',
          },
          {
            title: 'Discrimination',
            description:
              'Disadvantaging or degrading people because of their sex, race, religion, sexual orientation or other personal characteristics.',
          },
          {
            title: 'Doxxing',
            description:
              'Publishing or passing on private information without the consent of the person concerned.',
          },
          {
            title: 'Threat',
            description: 'Threatening violence, murder or other negative consequences.',
          },
          {
            title: 'Extortion',
            description:
              'Any act that forces a person to do something by threatening disadvantages.',
          },
          {
            title: 'Misinformation',
            description: 'Spreading false or misleading information.',
          },
          {
            title: 'Fascism',
            description: 'Promoting or spreading fascist ideologies.',
          },
          {
            title: 'Xenophobia',
            description: 'Hostility or prejudice towards foreigners or ethnic minorities.',
          },
          {
            title: 'Dangerous conspiracy theories',
            description:
              'Spreading or supporting theories that can promote panic, fear or violence.',
          },
          {
            title: 'Violent content',
            description: 'Spreading content that promotes or depicts violence.',
          },
          {
            title: 'Glorification of violence',
            description:
              'Promoting or justifying violence against individuals, groups or institutions.',
          },
          {
            title: 'Hate speech',
            description: 'Statements that call for hatred or violence against certain groups.',
          },
          {
            title: 'Homophobia',
            description: 'Hostility or prejudice towards homosexual people.',
          },
          {
            title: 'Identity theft',
            description:
              'Misrepresenting oneself or posing as another person, institution or entity.',
          },
          {
            title: 'Illegal content',
            description: 'Spreading or providing content that violates applicable law.',
          },
          {
            title: 'Islamophobia',
            description: 'Hostility or prejudice towards Muslims or Islam.',
          },
          {
            title: 'Cultural appropriation',
            description:
              'Inappropriate use or depiction of cultural symbols, traditions or values.',
          },
          {
            title: 'Protection of minors',
            description:
              'Acts that violate the protection of minors, such as inadmissible contact.',
          },
          {
            title: 'Abuse of privileges',
            description:
              'Any form of unjustified exploitation of rights or access rights on this web application.',
          },
          {
            title: 'Plagiarism',
            description:
              'Uploading or sharing content that was copied or reproduced without the consent of third parties.',
          },
          {
            title: 'Pornographic content',
            description: 'Spreading, providing or making available pornographic or sexual content.',
          },
          {
            title: 'Propaganda',
            description:
              'Spreading politically or ideologically one-sided information for the purpose of manipulation.',
          },
          {
            title: 'Racism',
            description:
              'Discrimination or hostility towards people because of their ethnic origin.',
          },
          {
            title: 'Relativisation',
            description: 'Trivialising or denying crimes or human rights violations.',
          },
          {
            title: 'Self-harm',
            description:
              'Content or behaviour that encourages or promotes self-harm or suicidal behaviour. Instead, we ask that people be encouraged to seek help and to talk to someone about it.',
          },
          {
            title: 'Vigilantism',
            description:
              'Promoting or glorifying acts aimed at taking the law into one’s own hands.',
          },
          {
            title: 'Sexism',
            description: 'Discrimination or degradation because of sex.',
          },
          {
            title: 'Sextortion',
            description: 'Extortion by threatening to publish private or intimate information.',
          },
          {
            title: 'Spam',
            description: 'Unwanted and unsolicited messages, especially advertising messages.',
          },
          {
            title: 'Inappropriate language',
            description: 'Use of disrespectful, insulting or inappropriate expressions.',
          },
          {
            title: 'Unethical advertising',
            description:
              'Advertising products, services or content that are fraudulent, unethical or harmful.',
          },
          {
            title: 'Whataboutism',
            description:
              'Deflecting criticism by pointing to other wrongdoing instead of addressing it.',
          },
        ],
      },
      {
        title: '4. Changes to the terms of use',
        text: 'The terms of use can be changed at any time without prior notice. Users are asked to review the terms regularly to stay up to date.',
      },
      {
        title: '5. Intellectual property',
        text: 'All content on this platform, including texts, images, graphics, logos and software, is protected by copyright. Reproducing, distributing or using the content without explicit permission is prohibited.',
      },
      {
        title: '6. Reporting abuse',
        text: 'If you notice violations of the terms of use or abusive behaviour, you are obliged to report them immediately through the reporting channels provided. Failing to do so violates the terms of use.',
      },
    ],
  },
  disclaimer: {
    illustration: 'disclaimer',
    notice: NOTICE,
    sections: [
      {
        title: '1. Content of the online offer',
        text: 'The content of this web application was developed with the greatest possible care. However, we cannot guarantee that the content is correct, complete and up to date. As a service provider, we are responsible for our own content on these pages under the general laws according to § 7 para. 1 TMG. According to §§ 8 to 10 TMG, however, we are not obliged to monitor transmitted or stored third-party information or to investigate circumstances that indicate unlawful activity. Obligations to remove or block the use of information under the general laws remain unaffected. Liability in this respect is only possible from the moment we become aware of a specific infringement. As soon as we become aware of such infringements, we will remove this content immediately.',
      },
      {
        title: '2. Liability for links',
        text: 'Our offer contains links to external third-party websites whose content we have no influence on. We therefore cannot accept any liability for this third-party content. The respective provider or operator of the linked pages is always responsible for their content. However, permanent monitoring of the content of the linked pages is not reasonable without concrete indications of an infringement. As soon as we become aware of infringements, we will remove such links immediately.',
      },
      {
        title: '3. Copyright',
        text: 'The content and works created by the site operators on these pages are subject to German copyright law. Reproduction, editing, distribution and any kind of use beyond the limits of copyright require the written consent of the respective author or creator. Downloads and copies of this site are only permitted for private, non-commercial use. Insofar as the content on this site was not created by the operator, the copyrights of third parties are respected. In particular, third-party content is marked as such. Should you nevertheless become aware of a copyright infringement, please let us know. As soon as we become aware of infringements, we will remove such content immediately.',
      },
      {
        title: '4. Liability for damages',
        text: 'We exclude any liability for damages that arise directly or indirectly from the use of this web application and the information it contains, unless they are based on intent or gross negligence.',
      },
      {
        title: '5. No warning letter without prior contact',
        text: 'Should content of this web application violate the rights of third parties or legal provisions, please send us a corresponding message without a bill of costs. We guarantee that content rightly objected to will be analysed and evaluated without the need to involve legal counsel. We will nevertheless reject in full any costs you incur without contacting us first and, if necessary, file a counterclaim for violation of the aforementioned provisions.',
      },
    ],
  },
}
