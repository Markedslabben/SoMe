# Metode: LLM-basert agentsimulering av meningsdynamikk

## 1. Metodologisk tilnærming

### 1.1 LLM som simuleringsmotor

Denne studien benytter en hybrid tilnærming der store språkmodeller (LLM) genererer agentenes ytringer, mens eksplisitte matematiske modeller styrer meningsoppdatering, emosjonell dynamikk og algoritmisk synlighet.

**Rasjonale for LLM-bruk:**
- Naturalistisk tekstgenerering som fanger retoriske mønstre
- Emergent atferd som ikke er eksplisitt programmert (f.eks. begrepssmitte)
- Evne til å respondere kontekstuelt på tidligere innlegg i debatten

**Begrensninger:**
- LLM-er er trent på menneskelig tekst og bærer implisitte mønstre fra treningsdataene
- Ikke egnet for å simulere individuelle psykologiske prosesser med presisjon
- Resultatene må tolkes som *system-nivå dynamikk*, ikke individuelle konverteringsmekanismer

### 1.2 Validitetsdomene

| Aspekt | Validitet | Begrunnelse |
|--------|-----------|-------------|
| Synlighetsforhold mellom innholdstyper | Høy | Algoritmisk forsterkning er eksplisitt modellert |
| Feedback-løkker på systemnivå | Høy | Mekanismene er matematisk spesifisert |
| Individuelle konverteringsterskler | Lav | LLM simulerer ikke autentisk psykologi |
| Emosjonell smitte-mønstre | Moderat | Delvis emergent fra LLM, delvis eksplisitt |
| Begrepsadopsjon/framing | Moderat | Emergent fra LLM-kontekstvindu |

---

## 2. Eksplisitt modellerte mekanismer

Følgende mekanismer er implementert med eksplisitte matematiske formler i simuleringskoden:

### 2.1 Algoritmisk forsterkning

**Synlighetsformel:**
```
visibility = (emotion×0.4 + provocativeness×0.4 + recency×0.2) × (1 + engagement²×0.6)
```

Den kvadratiske engasjementsmultiplikatoren skaper superlineære gevinster for provoserende innhold, konsistent med dokumenterte mønstre i sosiale medier-algoritmer (Bail et al., 2018; Brady et al., 2017).

### 2.2 Kognitiv investeringsmodell

**Formål:** Simulere at meninger blir "klebrige" gjennom akkumulert kognitiv innsats (Festinger, 1957; Brehm & Cohen, 1962).

**Implementering:**
```python
cognitive_investment += abs(delta) × 0.8  # Akkumulerer ved hver meningsendring
reversal_resistance = 1 + (cognitive_investment × reversal_resistance_trait)
```

Motstand mot å reversere retning øker eksponentielt med akkumulert investering, som modellerer "sunk cost"-effekten i meningsdannelse.

### 2.3 System 1/System 2 prosessering

**Teoretisk grunnlag:** Kahneman (2011) dual-prosess teori.

**Implementering:**
```python
system2_capacity = max(0.1, analytical_weight - temperature×0.4 - arousal×0.3)

# System 1 (emosjonell) prosessering
emotional_influence = emotional_impact × emotional_susceptibility × (1 - system2_capacity)

# System 2 (analytisk) prosessering
logical_influence = logical_coherence × analytical_weight × system2_capacity
```

**Debatt-temperatur** beregnes som gjennomsnittlig emosjonell intensitet over siste 15 innlegg. Høy temperatur reduserer System 2-kapasitet for alle agenter, som fanger hvordan opphetede debatter fremmer emosjonell tenkning.

### 2.4 Personlighetsheterogenitet

Fem personlighetstyper med distinkte trekkmultiplikatorer:

| Type | Emosjonell mottakelighet | Analytisk vekt | Sosial konformitet | Endringsrate |
|------|--------------------------|----------------|-------------------|--------------|
| Analytisk | 0.4 | 1.8 | 0.3 | 0.7 |
| Reaktiv | 1.8 | 0.4 | 0.8 | 1.4 |
| Konformist | 1.0 | 0.6 | 1.8 | 1.2 |
| Uengasjert | 0.6 | 0.8 | 0.5 | 0.4 |
| Balansert | 1.0 | 1.0 | 1.0 | 1.0 |

**Fordeling:** 4 agenter per type (20% hver) blant de 20 nøytrale.

### 2.5 Taushetsspiralen (valgfri mekanisme)

**Teoretisk grunnlag:** Noelle-Neumann (1974).

**Implementering:**
```python
perceived_majority = weighted_average(visible_post_opinions)
opinion_distance = abs(agent_opinion - perceived_majority)
participation_willingness = 1.0 - (opinion_distance × conflict_aversion × 0.5)
```

Agenter som oppfatter seg i mindretall reduserer deltakelsesvillighet, som kan føre til at mindretallsstemmer stilnes.

### 2.6 Emosjonell dynamikk

**Tilstandsvariabler:** Aktivering (arousal), valens, engasjement, sinne, angst.

**Oppdateringsmekanisme:**
- Lesing av emosjonelt innhold øker aktivering
- Provoserende innhold fra motstandere øker sinne
- Eksponentiell nedbrytning over tid (decay rate: 0.12 per runde)

### 2.7 Tillitsdynamikk

Tillit til kilder oppdateres basert på:
- Konsistens med egen mening (bekreftelsesbias)
- Innholdstype (logisk vs. emosjonelt)
- Akkumulert interaksjonshistorikk

---

## 3. Implisitte mekanismer fra LLM

Følgende mekanismer er **ikke eksplisitt programmert**, men *emergerer* fra LLM-ens språkgenerering:

### 3.1 Begrepssmitte (Framing contagion)

**Observasjon:** Kontrære agenter introduserer begreper ("backup-systemer", "svindel", "den grønne lobbyen") som senere adopteres av nøytrale agenter.

**Mekanisme:** LLM-ens kontekstvindu (memory window på 15 innlegg) gjør at agenter "husker" og gjenbruker terminologi de har blitt eksponert for.

**Implikasjon:** Dette er en realistisk simulering av hvordan framing sprer seg i faktiske debatter, men det er viktig å merke at det er en emergent egenskap ved LLM, ikke en eksplisitt modellert mekanisme.

### 3.2 Retoriske mønstre

LLM-generert tekst reproduserer naturlig:
- Retoriske spørsmål ("Hvorfor går regningen min opp hvis fornybar er billig?")
- Emosjonelle appeller og emoji-bruk
- In-group/out-group markører
- Eskalerende språk ved høy aktivering

### 3.3 Argumentativ struktur

Agentenes roller (kontrær/konsensus/nøytral) gis via systemprompt, men den spesifikke argumentasjonsstrukturen genereres av LLM basert på:
- Rolleinstruksjoner
- Emosjonell tilstandsbeskrivelse
- Kontekst fra tidligere innlegg

### 3.4 Sosial responsivitet

LLM-agenter responderer naturlig på:
- Direkte adresseringer (@mentions)
- Emosjonelle uttrykk fra andre
- Dominerende narrativer i konteksten

---

## 4. Mekanismer som IKKE er modellert

For transparens, følgende aspekter er **ikke inkludert** i simuleringen:

| Mekanisme | Status | Begrunnelse |
|-----------|--------|-------------|
| Nettverksstruktur | Ikke modellert | Alle agenter ser samme feed (forenklet) |
| Selektiv eksponering | Ikke modellert | Ingen filterbobler |
| Langtidsminne | Begrenset | Kun 15 innlegg i kontekstvindu |
| Demografiske faktorer | Ikke modellert | Kun personlighetstyper |
| Plattformbytte | Ikke modellert | Enkelt-plattform simulering |
| Bot-deteksjon | Ikke relevant | Alle agenter er "ekte" i simuleringen |
| Økonomiske insentiver | Ikke modellert | Ingen monetisering |

---

## 5. Metodologiske implikasjoner

### 5.1 Hva simuleringen kan si noe om

✅ **System-nivå dynamikk:** Hvordan algoritmisk forsterkning skaper feedback-løkker
✅ **Relativ synlighet:** Forholdet mellom innholdstyper under ulike algoritmedesign
✅ **Emergente mønstre:** Begrepssmitte, polariseringstrender, emosjonell eskalering
✅ **Mekanisme-testing:** Effekten av å slå av/på spesifikke mekanismer (f.eks. taushetsspiralen)

### 5.2 Hva simuleringen IKKE kan si noe om

❌ **Absolutte konverteringsrater:** Hvor mange mennesker som faktisk ville endre mening
❌ **Individuelle psykologiske prosesser:** Hvordan enkeltpersoner opplever meningsendring
❌ **Tidsskala:** Hvor lang tid dynamikkene ville ta i virkeligheten
❌ **Kalibrering mot empiri:** Parameterverdier er ikke empirisk validert

### 5.3 Fortolkningsramme

Resultatene bør tolkes som **kvalitative mønstre** og **mekanisme-demonstrasjoner**, ikke som **kvantitative prediksjoner**. Simuleringen viser *at* algoritmisk forsterkning kan skape asymmetriske utfall, ikke *hvor mye* dette skjer i praksis.

---

## 6. Teknisk implementering

### 6.1 Simuleringsparametre

| Parameter | Verdi | Begrunnelse |
|-----------|-------|-------------|
| Antall agenter | 25 (1+4+20) | Håndterbar størrelse for LLM-kontekst |
| Antall runder | 100 | Tilstrekkelig for dynamikk-observasjon |
| Innlegg per runde | 6 | Balanse mellom aktivitet og kostnad |
| Minnevindu | 15 innlegg | Begrenset av kontekstlengde |
| Emosjonell nedbrytning | 0.12/runde | Moderat persistens |
| Kognitiv investeringsrate | 0.8 | Rask akkumulering for observerbar effekt |

### 6.2 LLM-konfigurasjon

- **Modell:** Claude Sonnet 4 (claude-sonnet-4-20250514)
- **Maks tokens per innlegg:** 80 (~280 tegn, tweet-lengde)
- **Temperatur:** Standard (ikke justert)

### 6.3 Innholdsanalyse

Leksikalsk analyse av genererte innlegg for:
- Emosjonell intensitet (ordlister + tegnsetting)
- Provokasjonsnivå (konfrontasjonsmønstre)
- Logisk koherens (konnektorer + struktur)
- Konsensus-orientering (modererende språk)

---

## 7. Etiske betraktninger

### 7.1 Simulering vs. manipulasjon

Denne studien simulerer meningsdynamikk for å *forstå* mekanismer, ikke for å *utnytte* dem. Innsiktene kan informere:
- Plattformdesign som reduserer polarisering
- Medieforståelse og digital literacy
- Regulatoriske tilnærminger til algoritmisk kurasjon

### 7.2 Begrensninger ved LLM-simulering

LLM-agenter er ikke mennesker. De:
- Har ikke genuint emosjonelle opplevelser
- Kan ikke representere mangfoldet i menneskelig kognisjon
- Reproduserer mønstre fra treningsdata som kan inneholde skjevheter

---

## Referanser

### Algoritmisk forsterkning og sosiale medier
- Bail, C. A., et al. (2018). Exposure to opposing views on social media can increase political polarization. PNAS.
- Bail, C. A. (2021). Breaking the Social Media Prism: How to Make Our Platforms Less Polarizing. Princeton University Press.
- Brady, W. J., et al. (2017). Emotion shapes the diffusion of moralized content in social networks. PNAS.
- Sunstein, C. R. (2017). #Republic: Divided Democracy in the Age of Social Media. Princeton University Press.
- Zuboff, S. (2019). The Age of Surveillance Capitalism. PublicAffairs.

### Kognitiv prosessering og beslutningsteori
- Kahneman, D. (2011). Thinking, Fast and Slow. Farrar, Straus and Giroux.
- Petty, R. E., & Cacioppo, J. T. (1986). The Elaboration Likelihood Model of Persuasion. Advances in Experimental Social Psychology.
- Sharot, T., et al. (2011). How unrealistic optimism is maintained in the face of reality. Nature Neuroscience.

### Kognitiv dissonans og holdningspersistens
- Aronson, E., & Mills, J. (1959). The effect of severity of initiation on liking for a group. Journal of Abnormal and Social Psychology.
- Brehm, J. W., & Cohen, A. R. (1962). Explorations in Cognitive Dissonance. Wiley.
- Cialdini, R. B. (2006). Influence: The Psychology of Persuasion (rev. ed.). Harper Business.
- Festinger, L. (1957). A Theory of Cognitive Dissonance. Stanford University Press.
- Ross, L., Lepper, M. R., & Hubbard, M. (1975). Perseverance in self-perception and social perception. Journal of Personality and Social Psychology.
- Staw, B. M. (1976). Knee-deep in the big muddy: A study of escalating commitment to a chosen course of action. Organizational Behavior and Human Performance.

### Identitet og motivert resonnering
- Kahan, D. M., et al. (2012). The polarizing impact of science literacy and numeracy on perceived climate change risks. Nature Climate Change.

### Taushetsspiralen og offentlig mening
- Noelle-Neumann, E. (1974). The Spiral of Silence: A Theory of Public Opinion. Journal of Communication.

### Deliberativt demokrati
- Habermas, J. (1989). The Structural Transformation of the Public Sphere (orig. 1962). MIT Press.
