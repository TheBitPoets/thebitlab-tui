# Regole operative di thebitlab-tui

Questo documento definisce il flusso stabile per roadmap, issue, pull request, review e
documentazione. È adattato alla micro-libreria Python `thebitlab-tui`: non eredita processi,
componenti o vincoli applicativi di altri progetti.

## Metodo di lavoro

- Procedere per passi piccoli, monoscopo e verificabili.
- Prima di un cambiamento non banale dichiarare obiettivo, contratto, compatibilità e trade-off.
- Non anticipare refactor, widget o configurazioni non richiesti dalla milestone corrente.
- Toccare solo i file riconducibili a una issue, un finding, un test o un aggiornamento
  documentale necessario.
- Trasferire le decisioni consolidate dalla chat o dalle Discussions alla documentazione
  versionata.
- Una modifica non banale deve aggiornare almeno uno tra test, snapshot, API reference,
  architettura, guida, esempio o decisione documentata.

## Contratti non negoziabili

- Nessuna dipendenza runtime esterna.
- Python 3.11+; comportamento supportato su Windows e Linux.
- Rendering puro: nessuna stampa o logica applicativa nei widget.
- Fallback ASCII completo e colori ANSI opzionali.
- Larghezza visibile stabile; ANSI escluso dai calcoli; nessun overflow orizzontale involontario.
- API pubblica piccola e stabile.
- Nessuna integrazione diretta con `2cornot2c`: il futuro collegamento passa da un adapter
  applicativo compatibile con `scripts/student_lab_layout.py`.

## Roadmap e tracciamento GitHub

Per un lavoro che supera un singolo micro-step usare questa gerarchia:

```text
Milestone
  `-- Issue madre
      |-- Discussion, se la decisione è ancora aperta
      |-- Issue figlie
      |   `-- Pull request dedicate
      `-- Documentazione stabile
```

La Discussion conserva alternative e ragionamento. La documentazione del repository conserva la
decisione consolidata.

Se GitHub Discussions non è abilitato, usare una issue con label `status:needs-discussion`. Non
pubblicare nel selettore delle issue un collegamento a una funzionalità disabilitata.

### Milestone

Una milestone rappresenta un risultato misurabile, per esempio `Core widgets v0.2`, `Interactive
widgets v0.3`, `Terminal adapters v0.4` o `Student TUI adapter v0.5`.

Ogni milestone non banale deve avere:

- titolo, scope e criteri di completamento;
- data di fine orientativa, aggiornata con una motivazione quando cambia;
- issue madre;
- roadmap primaria in `docs/roadmap.md` o in un documento dedicato;
- dipendenze, rischi e lavoro esplicitamente rinviato.

La milestone si chiude solo quando i criteri sono soddisfatti o il lavoro rinviato è registrato.

### Issue madre

L'issue madre è il piano operativo, non la fonte definitiva del contratto. Subito dopo il goal
deve contenere `Primary roadmap`, con link cliccabile e una frase che spiega perché quel documento
è il riferimento principale.

Deve inoltre contenere:

- scope e non-scope;
- criteri di completamento verificabili;
- checklist sintetica;
- rischi per API, ASCII/ANSI, responsive layout e portabilità;
- tabella `Implementation traceability`.

Checklist e tracciabilità devono essere aggiornate insieme:

```markdown
| Checklist item | Status | Issue / PR / Commit | Notes |
| --- | --- | --- | --- |
| Add Divider widget | Todo | #... | Public API not yet approved |
| Add snapshots | In progress | #... / PR #... | Narrow Windows case pending |
| Update Sphinx docs | Done | commit / PR | API and examples documented |
```

### Issue figlie

Ogni micro-step non banale richiede una issue figlia bounded e una PR dedicata. La issue figlia:

- collega la issue madre e la milestone;
- definisce comportamento atteso, non-scope e verifica;
- collega la PR; la PR usa `Closes #...` quando il merge deve chiuderla;
- è aggiunta come sub-issue nativa quando GitHub lo consente, altrimenti usa link bidirezionali.

La PR non deve chiudere automaticamente la issue madre.

### Label

Usare almeno una label `area:*` e una `kind:*`. Usare priorità e stato solo quando aggiungono
informazione operativa.

- `area:canvas`, `area:widgets`, `area:layout`, `area:renderer`, `area:terminal`, `area:docs`,
  `area:tests`, `area:ci`, `area:integration`;
- `kind:bug`, `kind:feature`, `kind:design`, `kind:test`, `kind:docs`, `kind:debt`,
  `kind:roadmap`;
- `priority:p0`, `priority:p1`, `priority:p2`;
- `status:needs-discussion`, `status:ready`, `status:blocked`, `status:needs-docs`.

Le label predefinite dichiarate nei template devono esistere nel repository prima del merge.
Verificarle con `gh label list` insieme alla validazione YAML dei template.

## Pull request

Una PR deve essere piccola, monoscopo, collegata a una issue figlia e inizialmente draft. Il body,
in inglese, deve indicare:

- obiettivo, issue figlia, issue madre e milestone;
- cambiamenti e motivazione;
- impatto sull'API pubblica e compatibilità;
- test, snapshot e controlli manuali;
- documentazione e docstring aggiornate;
- comportamento Windows/Linux, ASCII, ANSI e `no-color` quando rilevante;
- limiti e lavoro rinviato.

Un cambio dell'API pubblica richiede discussione esplicita, test, documentazione Sphinx e una
dichiarazione di compatibilità o breaking change. Una modifica al rendering richiede snapshot
deterministici e casi narrow. Una modifica terminale richiede casi Windows e Linux.

La PR resta draft fino a due round di review consecutivi senza nuovi finding. Prima di marcarla
ready o fare merge, chiedere al maintainer.

### Modalità operative

La modalità predefinita è supervisionata: spiegare i passaggi significativi e chiedere conferma
prima di push, apertura PR, fix di finding o decisioni che cambiano contratto, scope, architettura
o documentazione rilevante.

La modalità autonoma PR loop deve essere richiesta esplicitamente. In quel perimetro sono
autorizzati i passaggi meccanici già regolati — branch, issue figlia, commit, push, apertura o
aggiornamento PR, label, review, finding inline, fix e aggiornamento del body — fino a due review
consecutive pulite. Anche in modalità autonoma fermarsi prima del merge e quando emergono scelte di
prodotto, ampliamenti di scope, breaking change non concordate, CI non banale, limiti di permesso o
lavoro fuori milestone.

### Review round

Dopo ogni round significativo aggiornare il body della PR. Usare `Review round N`, non
`Review update #N`, perché GitHub interpreta `#N` come link.

```markdown
## Review round N

Summary:
- Scope and risks reviewed.

Clean review status:
- New findings: yes/no.
- Consecutive clean reviews: 0/1/2.
- Draft status: keep draft / ready after maintainer confirmation.

Findings:
- Finding: link to inline thread
  Fix: commit link and concise rationale, or `pending`.

Validation:
- Commands and CI status observed during this round.
```

## Finding e risoluzioni

Un finding deve essere azionabile, specifico e proporzionato. Quando esiste una riga precisa,
pubblicarlo inline. Indicare:

- severità (`P0`, `P1`, `P2`, `P3`);
- file e riga;
- evidenza o riproduzione;
- rischio e comportamento atteso;
- correzione richiesta;
- test, snapshot o documento necessario.

Severità:

- `P0`: perdita dati, vulnerabilità o rottura totale;
- `P1`: bug funzionale, overflow del frame, API incompatibile o regressione multipiattaforma;
- `P2`: caso limite concreto, copertura rilevante mancante o contratto incoerente;
- `P3`: miglioramento non bloccante, concreto e in scope.

Evitare finding estetici, speculativi, duplicati o fuori scope. Una review pura non modifica il
codice.

Per risolvere un finding:

1. usare un commit monoscopo quando possibile;
2. aggiungere un test di regressione o motivare perché non è applicabile;
3. rispondere nel thread inline con link Markdown al commit;
4. spiegare rischio originale, soluzione e contratto che impedisce la regressione;
5. aggiornare `Review round N` nel body.

Non rispondere solo `fixed`. Formato raccomandato:

```markdown
Fixed in [abc1234](https://github.com/TheBitPoets/thebitlab-tui/commit/full-sha).

The previous path counted ANSI escape sequences as visible cells and could move the right border.
The fix measures visible width independently from styling; the new snapshots cover both modes.
```

## Checklist di review specifica

Controllare almeno:

- correttezza di rendering e layout;
- clipping, ellissi e larghezza visibile stabile;
- ANSI escluso dalla geometria e output `no-color` pulito;
- fallback interamente ASCII;
- terminali stretti, dimensioni minime, responsive layout e resize;
- portabilità Windows/Linux;
- nessuna stampa nei widget e nessuna logica applicativa;
- separazione widget/layout/renderer/terminal adapter;
- API pubblica piccola, documentata e compatibile;
- compatibilità futura con l'adapter per `student_lab_layout.py`;
- test deterministici e snapshot leggibili;
- zero dipendenze runtime;
- semplicità e assenza di astrazioni speculative;
- docstring pubbliche e documentazione Sphinx aggiornate;
- coerenza tra API reference, architettura, guide, esempi e immagini;
- nessuna modifica o copia diretta da `2cornot2c`.

## Commit

Usare commit in inglese, monoscopo e con subject imperativo. Il formato Conventional Commits è
consigliato quando chiarisce il tipo (`feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `build`,
`perf`). Il body deve spiegare cosa cambia e perché; citare issue, PR e finding quando pertinenti.
Committare solo i file del passo corrente, senza log, build o esperimenti locali.

## Documentazione e docstring

Tutti i moduli, classi, funzioni, metodi e proprietà pubblici devono avere docstring. Le docstring
devono spiegare contratto, parametri, ritorno, eccezioni e casi limite rilevanti senza ripetere
ovvietà del codice.

Sphinx genera l'API reference dalle docstring. Sphinx e i relativi strumenti sono dipendenze di
sviluppo/documentazione, mai runtime. Ogni nuova API pubblica richiede:

- docstring;
- inclusione nella API reference Sphinx;
- test e snapshot quando produce rendering;
- esempio d'uso;
- aggiornamento architetturale se cambia una responsabilità.

La documentazione deve comprendere:

- guida utente;
- guida sviluppatore;
- API reference;
- architettura e flusso degli eventi;
- integrazione futura tramite adapter;
- esempi eseguibili;
- immagini o screenshot quando migliorano la comprensione.

Le immagini devono avere sorgente riproducibile e testo alternativo. Il contenuto essenziale non
deve dipendere dall'immagine. Preferire SVG, diagrammi semplici e screenshot ASCII leggibili.

## Verifiche minime

Prima di proporre una PR eseguire:

```text
git diff --check
python -m pytest
python -m compileall -q src tests examples
python -m sphinx -W --keep-going -b html docs docs/_build/html
python examples/basic_panels.py --no-color
```

Se un comando non è disponibile o fallisce, documentare la causa e non dichiarare completata la
verifica. Il processo deve essere riproducibile senza strumenti AI.

## Provenienza

Il processo deriva dalle
[regole operative di Alfred](https://github.com/kinderp/alfred/blob/main/docs/it/00-regole-operative.md),
poi ridotto e riscritto per i contratti di una libreria TUI Python. Sono stati esclusi runtime,
backend, strumenti, audit e procedure specifici di Alfred.
