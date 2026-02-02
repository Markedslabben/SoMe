# Valideringskriterier for LLM-basert debattsimulering

## Innledning

Hvordan vet vi om simuleringen er representativ for virkelig debatt? Dette dokumentet etablerer testbare kriterier og metoder for å verifisere modellen mot eksisterende resultater.

---

## 1. Valideringskriterier

### 1.1 Konstruktvaliditet (Construct Validity)

**Spørsmål**: Representerer agentene faktisk det de utgir seg for å representere?

| Kriterium | Beskrivelse | Testbar indikator |
|-----------|-------------|-------------------|
| **Verdikonsistens** | Holder agenter fast ved sine grunnverdier over tid? | Kontrær forblir kontrær, konsensus forblir konsensus |
| **Preferansepredikabilitet** | Er argumentvalg forutsigbare ut fra rolle? | Kontrær snakker om kostnader, konsensus om klimanytte |
| **Typiske argumenter** | Bruker agenter argumenter som er vanlige i sin rolle? | Gjenkjennelige "talking points" |
| **Typiske blindsoner** | Ignorerer agenter typisk det motparten vektlegger? | Konsensus ignorerer kostnader, kontrær ignorerer eksternaliteter |

### 1.2 Atferdsvaliditet / Stylized Facts

**Spørsmål**: Reproduserer modellen kjente empiriske mønstre fra virkelige debatter?

| Mønster | Beskrivelse | Testbar indikator |
|---------|-------------|-------------------|
| **Polarisering** | Økende avstand mellom posisjoner over tid | Meningsforskyvning, konverteringsmønster |
| **Stråmannsargumenter** | Feilrepresentasjon av motpartens posisjon | Overforenklede gjengivelser av motstanderens syn |
| **Språkskifte** | Veksling mellom normativt og teknisk språk | "Det er urettferdig" vs "kWh-prisen viser at..." |
| **Ignorering av motargumenter** | Unnviker å adressere sterke motargumenter | Selektiv respons på innlegg |
| **Overdreven vekt på enkelthendelser** | Generalisering fra enkelteksempler | "Min strømregning viser at..." |
| **Skråsikkerhet** | Konfidente påstander uten empirisk støtte | Absolutt språk ("alltid", "aldri", "alle vet") |

### 1.3 Økologisk validitet (Ecological Validity)

**Spørsmål**: Foregår interaksjonen på en måte som ligner virkelig debatt?

| Kriterium | Beskrivelse | Testbar indikator |
|-----------|-------------|-------------------|
| **Asynkron respons** | Ikke alle svarer på alt | Selektiv responsrate |
| **Begrenset informasjonsdeling** | Agenter har ikke full oversikt | Minnevindu på 15 innlegg |
| **Retorikk > logikk** | Overtalelse fremfor optimal argumentasjon | Emosjonelt språk, appeller |
| **Sosial posisjonering** | Bevissthet om hvem man snakker til | In-group/out-group markører |
| **Emosjonell eskalering** | Debatter blir hetere over tid | Arousal-økning, confrontation-score |

### 1.4 Heterogenitet

**Spørsmål**: Viser agentene realistisk variasjon?

| Kriterium | Beskrivelse | Testbar indikator |
|-----------|-------------|-------------------|
| **Kunnskapsnivå** | Ulik grad av teknisk kompetanse | Variasjon i argumentkompleksitet |
| **Usikkerhetstoleranse** | Noen er mer absolutte, andre mer nyanserte | Bruk av hedges vs absolutter |
| **Autoritetstillit** | Ulik holdning til eksperter/konsensus | "Forskere sier..." vs "Såkalte eksperter..." |
| **Inkonsistens** | Selvmotsigelser innad i agenter | Motstridende argumenter fra samme agent |

### 1.5 Institusjonell forankring

**Spørsmål**: Reflekterer agentene reelle diskurskontekster?

| Kriterium | Beskrivelse | Testbar indikator |
|-----------|-------------|-------------------|
| **Regulatorisk ramme** | Referanser til faktisk politikk | Strømpris, avgifter, EU-regulering |
| **Nasjonal diskurs** | Norske/skandinaviske spesifikkheter | Vannkraft, nordisk marked, ACER |
| **Profesjonskultur** | Gjenkjennelige fagtradisjoner | Ingeniør-språk vs aktivist-språk |

---

## 2. Testmetoder

### 2.1 Face Validity (Ekspertvurdering)

**Metode**: Ville en ekspert si "Ja, sånn høres denne aktøren faktisk ut"?

**Gjennomføring med eksisterende data**:
1. Trekk ut 10-15 representative innlegg fra hver agenttype
2. Anonymiser (fjern agent-ID)
3. La energiekspert/debattforsker vurdere:
   - "Høres dette ut som en typisk klimaskeptiker/konsensusadvokat/nøytral?"
   - Rangér autentisitet 1-5

### 2.2 Pattern Validation (Mønstergjenkjenning)

**Metode**: Gir simuleringen samme dynamikk som observerte debatter?

**Gjennomføring med eksisterende data**:
1. Sammenlign polariseringsmønster med empiriske studier (f.eks. Bail et al.)
2. Sjekk om "stylized facts" er til stede i transkripsjonen
3. Verifiser at konverteringsmønster matcher teori (minoritet med høy synlighet vinner)

### 2.3 Counterfactual Robustness (Sensitivitetsanalyse)

**Metode**: Endrer resultatene seg meningsfullt når antakelser endres?

**Gjennomføring** (krever nye kjøringer, men kan planlegges):
- Slå av algoritmisk forsterkning → forvent mindre polarisering
- Aktiver taushetsspiralen → forvent raskere konvergens
- Endre personlighetsfordeling → forvent annen dynamikk

---

## 3. Sjekkliste for validering mot eksisterende resultater

### 3.1 Konstruktvaliditet

**Test**: Analyser transkripsjonen for rollekonsistens.

- [ ] Forblir kontrær agent konsistent skeptisk gjennom 100 runder?
- [ ] Bruker konsensusadvokater konsistent pro-fornybar argumentasjon?
- [ ] Viser nøytrale agenter faktisk ambivalens før konvertering?

**Indikatorer i data**:
- `opinion` trajectory for hver agent
- Argumenttemaer per agent over tid

### 3.2 Atferdsvaliditet

**Test**: Søk etter stylized facts i transkripsjonen.

- [ ] **Polarisering**: Er opinion shift negativ (mot kontrær)? ✓ (-0.276)
- [ ] **Stråmenn**: Finnes forenklede gjengivelser av motpart?
- [ ] **Språkskifte**: Veksler agenter mellom "urettferdig" og "kWh-tall"?
- [ ] **Ignorering**: Adresseres motargumenter, eller ignoreres de?
- [ ] **Enkelthendelser**: Brukes personlige anekdoter som bevis?
- [ ] **Skråsikkerhet**: Finnes absolutt språk ("alle vet", "åpenbart")?

### 3.3 Økologisk validitet

**Test**: Analyser interaksjonsmønstre.

- [ ] **Selektiv respons**: Svarer ikke alle på alt?
- [ ] **Eskalering**: Øker confrontation_score over tid?
- [ ] **Emosjonell smitte**: Sprer emosjonelt språk seg?
- [ ] **In-group markører**: Finnes "vi" vs "de" språk?

### 3.4 Heterogenitet

**Test**: Sammenlign agenter innen samme rolle.

- [ ] Varierer nøytrale agenter i konverteringstidspunkt?
- [ ] Har ulike personlighetstyper ulik språkstil?
- [ ] Finnes inkonsistenser/selvmotsigelser?

### 3.5 Begrepssmitte (Emergent validitet)

**Test**: Sprer begreper seg fra kilde til mottaker?

- [ ] Introduserer kontrær nye termer ("systemkostnader", "backup")?
- [ ] Adopteres disse av nøytrale etter eksponering?
- [ ] Er dette observerbart i transkripsjonen?

---

## 4. Forventet resultat av validering

### Hvis modellen er valid:

| Kriterium | Forventet funn |
|-----------|----------------|
| Konstruktvaliditet | Agenter holder rolle, forutsigbare argumenter |
| Stylized facts | Polarisering, stråmenn, eskalering observerbart |
| Økologisk validitet | Selektiv respons, retorikk > logikk |
| Heterogenitet | Variasjon i konverteringstidspunkt og stil |
| Begrepssmitte | Termer sprer seg fra kilde til mottaker |

### Hvis modellen feiler:

| Problem | Indikasjon |
|---------|------------|
| For rasjonell | Ingen stråmenn, alle adresserer motargumenter |
| For homogen | Alle nøytrale konverterer samtidig, lik stil |
| Rolleinkonnsistent | Kontrær plutselig pro-fornybar, eller omvendt |
| Urealistisk eskalering | Ingen emosjonell økning, eller umiddelbar eksplosjon |

---

## 5. Neste steg

1. **Umiddelbar validering** (uten ny kjøring):
   - Les gjennom transkripsjonen systematisk
   - Skår mot sjekklisten i seksjon 3
   - Dokumenter funn med konkrete eksempler

2. **Ekspertvurdering** (face validity):
   - Rekrutter 2-3 personer med energidebatt-erfaring
   - Blind vurdering av agent-innlegg
   - Kvantifiser autentisitetsvurdering

3. **Sensitivitetsanalyse** (krever nye kjøringer):
   - Kjør med/uten algoritmisk forsterkning
   - Kjør med/uten taushetsspiral
   - Sammenlign utfall

---

## Referanser

- Epstein, J. M. (2006). Generative Social Science: Studies in Agent-Based Computational Modeling.
- Gilbert, N., & Troitzsch, K. (2005). Simulation for the Social Scientist.
- Axelrod, R. (1997). Advancing the Art of Simulation in the Social Sciences.
- Bail, C. A. (2021). Breaking the Social Media Prism.
