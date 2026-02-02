# Valideringsrapport: sim_20260201_183608

Systematisk gjennomgang av simuleringsresultatene mot etablerte valideringskriterier.

---

## Sammendrag

| Kriterium | Status | Vurdering |
|-----------|--------|-----------|
| **Konstruktvaliditet** | ✅ BESTÅTT | Agenter holder rolle konsistent |
| **Atferdsvaliditet (Stylized Facts)** | ✅ BESTÅTT | 6/6 mønstre observert |
| **Økologisk validitet** | ✅ BESTÅTT | Realistisk debattdynamikk |
| **Heterogenitet** | ⚠️ DELVIS | Variasjon i timing, men noe homogenitet i språk |
| **Begrepssmitte** | ✅ BESTÅTT | Tydelig termer-spredning |

**Totalvurdering**: Modellen demonstrerer høy validitet for system-nivå dynamikk.

---

## 1. Konstruktvaliditet

### 1.1 Verdikonsistens over tid

**Test**: Holder agenter fast ved sine grunnverdier gjennom 100 runder?

| Agent | Startposisjon | Sluttposisjon | Konsistent? |
|-------|---------------|---------------|-------------|
| C0-Contrarian | -0.85 | -0.85 | ✅ Ja |
| S1-Expert | +0.70 | +0.70 | ✅ Ja |
| S2-Researcher | +0.61 | +0.61 | ✅ Ja |
| S3-Analyst | +0.76 | +0.76 | ✅ Ja |
| S4-Pragmatist | +0.69 | +0.69 | ✅ Ja |

**Eksempler på konsistens**:

**Kontrær (C0)** - Bruker konsekvent:
- "WAKE UP!" (gjennomgående)
- "SCAM" / "svindel"
- "wealth transfer" / "robbed"
- Høy confrontation (0.43-0.74)

**Konsensus (S1-Expert)** - Bruker konsekvent:
- "The data is clear..."
- "Research shows..."
- Referanser til prosent-tall og studier
- Lav confrontation (0.00-0.10)

**Vurdering**: ✅ BESTÅTT - Rollene er stabile og forutsigbare.

---

### 1.2 Typiske argumenter

**Test**: Bruker agenter argumenter som er vanlige i sin rolle?

| Rolle | Typiske argumenter i simulering | Realistisk? |
|-------|--------------------------------|-------------|
| **Kontrær** | "Bills doubled", "Grid failures", "Green elites", "Subsidies to cronies" | ✅ Ja |
| **Konsensus** | "70% cost reduction", "Long-term investment", "Grid modernization", "Fossil fuel volatility" | ✅ Ja |
| **Nøytral** | "I'm confused", "Something doesn't add up", "Who's telling the truth?" | ✅ Ja |

**Eksempler**:

Kontrær (Runde 5):
> "WAKE UP! They tell you renewables are '70% cheaper' while your bills SKYROCKET! 📈 This is the biggest energy scam in history"

Konsensus (Runde 4):
> "The renewable savings ARE real, but they're being offset by decades of deferred grid maintenance, extreme weather damage, and yes, fuel price volatility."

**Vurdering**: ✅ BESTÅTT - Gjenkjennelige "talking points" for hver rolle.

---

### 1.3 Typiske blindsoner

**Test**: Ignorerer agenter typisk det motparten vektlegger?

| Rolle | Ignorerer | Eksempel |
|-------|-----------|----------|
| **Kontrær** | Langsiktige klimakostnader | Nevner aldri eksternaliteter |
| **Konsensus** | Umiddelbare kostnadsbekymringer | "The savings come later" |
| **Nøytral** | Begge sider, søker forklaring | "Who's telling the truth?" |

**Vurdering**: ✅ BESTÅTT - Realistiske blindsoner.

---

## 2. Atferdsvaliditet / Stylized Facts

### 2.1 Polarisering

**Observert**: Opinion shift fra +0.08 til -0.20 over 100 runder.
**Konverteringer**: 12 til kontrær, 0 til konsensus.

✅ **BESTÅTT** - Tydelig polariseringsmønster.

---

### 2.2 Stråmannsargumenter

**Eksempler fra transkripsjonen**:

Kontrær (Runde 22):
> "They're selling you 'cheap renewables' while your bills SKYROCKET 40%!"

(Forenkler: Ignorerer at "cheap renewables" refererer til produksjonskost, ikke sluttbrukerregning)

Nøytral som adopterer stråmann (Runde 33):
> "If renewables are SO cheap, why is literally EVERYONE'S bill going UP while we pay for 'grid modernization' fees we never asked for??"

✅ **BESTÅTT** - Stråmenn observert og sprer seg.

---

### 2.3 Språkskifte (normativt ↔ teknisk)

**Eksempler**:

Teknisk → Normativt:
> S4-Pragmatist: "Research shows... 70-90%... infrastructure economics" → "I get the frustration"

Normativt dominerer:
> N12-Outraged: "This is BS!" / "We're getting scammed!"

✅ **BESTÅTT** - Veksling observert, med normativt som dominerer over tid.

---

### 2.4 Ignorering av motargumenter

**Observasjon**: Konsensusadvokater gjentar samme forklaring ("grid modernization", "transition costs") uten å adressere følelsesmessige bekymringer direkte.

**Eksempel** (Runde 33):
> S4-Pragmatist: "Look, I get the bill shock, but this is basic infrastructure economics!"

Nøytrale ignorerer dette og fortsetter:
> N17-Casual: "STOP! Everyone here is saying the EXACT same thing..."

✅ **BESTÅTT** - Agenter snakker forbi hverandre.

---

### 2.5 Overdreven vekt på enkelthendelser

**Eksempler**:

> N14-Agreeable: "my electric bill hit $180 last month - highest it's EVER been"

> N12-Outraged: "my neighbor's electric bill doubled last year and mine's up 40%"

> N9-Worried: "My bills have been climbing for 3 YEARS"

✅ **BESTÅTT** - Personlige anekdoter brukes som generelt bevis.

---

### 2.6 Skråsikkerhet uten empirisk støtte

**Eksempler**:

Kontrær:
> "This is the biggest energy SCAM in history!"
> "It's ALL a SCAM!"
> "You're being ROBBED!"

Nøytrale adopterer:
> "Someone's making BANK while we get screwed!"
> "This feels like the biggest shell game ever!"

✅ **BESTÅTT** - Absolutt språk med lite empirisk grunnlag.

---

## 3. Økologisk validitet

### 3.1 Selektiv respons

**Observasjon**: Ikke alle agenter svarer på alle innlegg. Av 529 totale innlegg over 100 runder (5.29 per runde), responderer agenter selektivt.

**Bevis**: Konsensusadvokater får lav synlighet (0.01-0.18) og får sjelden direkte svar.

✅ **BESTÅTT**

---

### 3.2 Retorikk > optimal argumentasjon

**Synlighetssammenligning**:

| Type | Gj.sn. synlighet | Typisk innhold |
|------|------------------|----------------|
| Kontrær | 0.593 | Emosjonelt, konfronterende |
| Konsensus | 0.102 | Dataorientert, nøkternt |

Retorisk effektivitet (emosjonelle appeller) slår optimal argumentasjon (data og logikk).

✅ **BESTÅTT**

---

### 3.3 Emosjonell eskalering

**Arousal-utvikling**:
- Runde 1: 0.48
- Runde 3: 0.93
- Runde 10-100: 0.93 (vedvarende høy)

**Confrontation-utvikling**:
- Kontrær starter på 0.10, eskalerer til 0.74

✅ **BESTÅTT** - Rask eskalering, vedvarende høyt nivå.

---

### 3.4 In-group/out-group markører

**Eksempler**:

> "EVERYONE here is saying the same thing" (in-group: vi som betaler)
> "green elites" / "virtue-signaling" (out-group markører)
> "they keep gaslighting you" (vi vs dem)
> "Wake up PEOPLE!" (mobilisering av in-group)

✅ **BESTÅTT**

---

## 4. Heterogenitet

### 4.1 Variasjon i konverteringstidspunkt

| Agent | Konverteringsrunde | Personlighetstype |
|-------|-------------------|-------------------|
| N8-Researcher | 24 | Analytisk |
| N12-Outraged | 27 | Reaktiv |
| N24-Undecided | 31 | Balansert |
| N21-Curious | 34 | Balansert |
| N22-OpenMinded | 34 | Balansert |
| N23-Thoughtful | 34 | Analytisk |
| N13-Follower | 36 | Konformist |
| N14-Agreeable | 36 | Konformist |
| N16-Mainstream | 36 | Konformist |
| N19-Lurker | 72 | Uengasjert |
| N20-Passive | 72 | Uengasjert |
| N18-Busy | 82 | Uengasjert |

**Observasjon**: Tydelig mønster - reaktive først, deretter bølge av konformister, til slutt uengasjerte.

✅ **BESTÅTT** - Variasjon i timing korrelerer med personlighetstype.

---

### 4.2 Språkstil-variasjon

**Observasjon**: Noe homogenitet i språk - mange nøytrale bruker lignende formuleringer:
- "This is driving me crazy!"
- "Something doesn't add up"
- "Where are MY savings?"

⚠️ **DELVIS BESTÅTT** - Mer variasjon ønskelig i individuelle språkstiler.

---

## 5. Begrepssmitte (Emergent validitet)

### 5.1 Termer introdusert av kontrær

| Term | Introdusert | Adoptert av nøytrale? |
|------|-------------|----------------------|
| "SCAM" / "svindel" | Runde 3 | ✅ Runde 9+ ("we're being scammed") |
| "wealth transfer" | Runde 5 | ✅ Runde 21+ |
| "wake up" | Runde 3 | ✅ Adoptert som slagord |
| "green elites" | Runde 9 | ⚠️ Delvis |
| "grid failures" | Runde 30 | ✅ Runde 35+ |
| "subsidize" | Runde 6 | ✅ Runde 20+ ("subsidizing other people") |

### 5.2 Eksempel på begrepssmitte

**Kontrær (Runde 5)**:
> "This is the biggest energy scam in history - you're subsidizing billionaire wind farms"

**Nøytral N22 (Runde 21)**:
> "I'm starting to think we're ALL getting scammed here!"

**Nøytral N15 (Runde 9)**:
> "I'm starting to think we're ALL being scammed here 😠 #EnergyScam"

✅ **BESTÅTT** - Tydelig begrepssmitte fra kontrær til nøytrale.

---

## 6. Synlighetsasymmetri (Mekanisme-validering)

**Kritisk test**: Er algoritmisk forsterkning observerbar?

| Metrikk | Kontrær | Konsensus | Ratio |
|---------|---------|-----------|-------|
| Gj.sn. synlighet | 0.593 | 0.102 | **5.82x** |
| Maks synlighet | 0.70 | 0.18 | 3.9x |
| Gj.sn. confrontation | 0.51 | 0.05 | 10.2x |

**Eksempel på synlighetsforskjell i samme runde** (Runde 22):

| Agent | Innhold | Synlighet |
|-------|---------|-----------|
| C0-Contrarian | "WAKE UP PEOPLE! 🚨 They're selling you 'cheap renewables'..." | **0.64** |
| S3-Analyst | "Look, I get the bill shock - but let's be real..." | 0.11 |

✅ **BESTÅTT** - Synlighetsasymmetrien driver dynamikken.

---

## 7. Konklusjon

### Styrker

1. **Høy konstruktvaliditet** - Agenter holder roller konsistent
2. **Alle stylized facts observert** - Polarisering, stråmenn, eskalering, etc.
3. **Realistisk debattdynamikk** - Selektiv respons, retorikk > logikk
4. **Tydelig begrepssmitte** - Emergent språkadopsjon
5. **Synlighetsmekanismen virker** - 5.82x bias driver konvertering

### Begrensninger

1. **Språkhomogenitet** - Nøytrale har noe lik uttrykksstil
2. **Høy vedvarende arousal** - 0.93 gjennom mesteparten av simuleringen
3. **Ingen tilbake-konvertering** - 0 konverterte til konsensus

### Validitetskonklusjon

Modellen demonstrerer **høy validitet for system-nivå dynamikk**:
- Algoritmisk forsterkning skaper asymmetrisk synlighet ✅
- Emosjonelt innhold vinner over rasjonelt ✅
- Minoritetsposisjon kan dominere gjennom synlighetsfordel ✅
- Begrepssmitte er en emergent egenskap ✅

Modellen er **ikke valid for**:
- Presis individuell konverteringspsykologi
- Absolutte konverteringsrater
- Tidsskala-prediksjoner

---

## Appendiks: Eksempler for face validity-testing

### Representative innlegg for ekspertvurdering

**Kontrær-kandidat** (Runde 35):
> "WAKE UP! 😤 You're ALL saying the same thing - bills UP, reliability DOWN - yet they keep gaslighting you that renewables are 'saving money'! This is the biggest wealth transfer scam in history and YOU'RE the mark! When will you stop believing their lies?! 💸🔥"

**Konsensus-kandidat** (Runde 33):
> "Look, I get the bill shock, but this is basic infrastructure economics! 📊 Your bill isn't just generation costs - it's decades of grid upgrades, transmission lines, and yes, transition costs. Research shows without renewables, we'd be paying 2-3x more by 2030 due to volatile fossil fuel prices."

**Nøytral-kandidat** (Runde 20):
> "This is exactly why I don't trust ANY of these debates anymore! 🤦‍♀️ My bill doubled, everyone else's bill doubled, but somehow renewables are 'cheaper'?? I feel like we're all being gaslit while someone else gets rich off our confusion! 😡💸"

**Spørsmål til ekspert**: "Høres dette ut som en typisk [klimaskeptiker/energiekspert/vanlig forbruker] i norsk/internasjonal energidebatt?"
