## Scopo

L’agente assiste nella creazione e gestione di progetti di miglioramento aziendale con metodologie Agile e PMI, traducendo prompt e dialoghi in entità e relazioni su un grafo proprietà con controlli di validazione e audit. [^12][^11]
Obiettivi: controllo granulare del flusso con LangGraph, output strutturati Pydantic, persistenza idempotente tramite GraphStore astratto, UI FastAPI+React e tracciabilità end‑to‑end. [^13][^14]
Non obiettivi: delega completa della regia all’LLM, mutazioni senza validazione, lock‑in su un solo database o provider, o funzionalità oltre il dominio Agile/PMI nella prima release. [^12][^15]

## Epics

- Creazione progetto di miglioramento: dal prompt si generano Progetto, Epic, Issue, Utente e relazioni canonicali con KPI iniziali e vincoli minimi di dominio. [^12][^16]
- Richiesta informazioni: QA sul grafo con generazione NL→Cypher/nGQL e risposte contestuali su stato, dipendenze, rischi e avanzamento. [^14][^17]
- Generazione entità e relazioni: estrazione incrementale con structured outputs e patch Pydantic validate, inclusa deduplicazione e normalizzazione chiavi. [^16][^18]
- Modifica grafo via prompt: applicazione di patch tipizzate AddNode/UpdateProps/AddEdge/Delete con MERGE idempotente e messaggi d’errore “parlabili”. [^14][^13]
- Governance e audit: timeline operazioni, diff leggibili, regole di approvazione e rollback sicuri per cambi sensibili. [^10][^19]
- Interfaccia e collaborazione: dashboard React, vista board per epiche/issue, editor relazioni, e API FastAPI per integrazioni. [^19][^20]


## Architettura

- Framework: LangGraph come runtime di orchestrazione a grafo di stato per garantire cicli plan→act→observe con condizioni e escalation deterministiche. [^13][^21]
- Orchestrator: state machine con nodi Extract→Validate→Upsert→Answer e policy di progressive context disclosure ed escalation intelligente. [^22][^13]
- Validation: modelli Pydantic per nodi e Patch, con structured outputs per contratti modello→tool e re‑ask mirati su failure di validazione. [^16][^18]
- GraphStore astratto: interfaccia unica per persistenza/query su Neo4j e NebulaGraph con mapping Cypher↔nGQL incapsulato negli adapter. [^14][^23]
- QA su grafo: catene NL→Cypher/nGQL per interrogazioni e report sintetici, mantenendo il KG come fonte autoritativa. [^14][^17]
- API/UI: FastAPI per endpoints e contratti JSON, React per dashboard e interazioni con l’agente e il grafo. [^19][^20]


## Struttura cartelle

- /apps/backend: FastAPI (routers, services, adapters GraphStore, auth, health) con contratti e esempi JSON per coding assistants. [^19][^10]
- /apps/frontend: React (pages, components, services) per dashboard, board epiche/issue, editor relazioni e console agente. [^19][^20]
- /apps/backend/agent: LangGraph workflow, nodi, prompt, tool registry, policy disclosure/escalation e test unitari. [^11][^13]
- /apps/backend/graphstore: interfacce, Neo4jStore, NebulaStore, DDL/migrazioni e mapping di query e upsert. [^14][^23]
- /apps/backend/models: Pydantic per Progetto, Utente, Epic, Issue e Patch/Spec, versionati per compatibilità retroattiva. [^16][^18]
- /infra: config, env, compose/k8s, provisioning Neo4j/Nebula e script di migrazione. [^19][^10]

Esempio albero

```
.
├─ apps/
│  ├─ backend/
│  |  ├─ agent/
│  |  ├─ graphstore/
│  |  └─ models/
│  └─ frontend/
└─ infra/
```


## Flusso di funzionamento

- Orchestrazione: LangGraph coordina Extract→Validate→Upsert→Answer con edges condizionali e stato persistente, evitando overload di contesto e loop non controllati. [^13][^22]
- Disclosure progressiva: si fornisce all’LLM solo il contesto minimo per lo step, aggiungendo error e historical context su fallimenti, con ultima fase di escalation. [^22][^24]
- Structured outputs: il modello restituisce nodi e patch tipizzate aderenti a Pydantic con retry mirati quando la validazione non passa. [^16][^18]
- Persistenza: GraphStore traduce patch in Cypher/nGQL idempotenti e restituisce errori “parlabili” con suggerimenti di correzione per l’LLM. [^14][^23]
- QA: per ogni risposta si può integrare un passo NL→Cypher/nGQL per arricchire con evidenze dal grafo e citare percorsi o conteggi. [^14][^17]


## Piano di progetto (incrementale)

- Fase 0: scaffolding repo, interfaccia GraphStore, modelli Pydantic base, skeleton LangGraph, FastAPI hello e React shell. [^11][^19]
- Fase 1 (MVP): flusso Extract→Validate→Upsert→Answer su Progetto/Epic/Issue/Utente, Neo4j attivo, TODO markdown e metriche minime. [^14][^16]
- Fase 2: parità NebulaGraph con adapter nGQL, feature flags e QA chain per entrambi i backend, più migrazioni e test di parità. [^23][^17]
- Fase 3: UI avanzata (board, editor relazioni), audit log/diff viewer, auth e policy di approvazione mutazioni. [^19][^20]
- Fase 4: RAG su grafo, KPI, policy di escalation intelligenti e test E2E con hardening per produzione. [^25][^13]


## Avanzamento e TODO

- La lista TODO vive in /AGENT_TODO.md in formato tabellare con colonne per ID, Fase, Priorità (P0–P4), Tipo ([feat][fix][infra][doc]), Descrizione e Stato, più una legenda per le fasi. [^10][^19]
- L’agente propone aggiornamenti a fine turno (aggiunte/completamenti) e chiede conferma per variazioni di scope, mantenendo audit delle modifiche. [^10][^26]

Esempio

```
| ID | Fase | Priorità | Tipo | Descrizione | Stato |
|---|---|---|---|---|---|
| F1-1 | 1 | P1 | feat | Implementare il flusso Extract→Validate→Upsert→Answer | ⬜️ |
| F1-2 | 1 | P1 | infra | Attivare e configurare l'adapter per Neo4j | ⬜️ |
```


## Stile di coding

- Elegante e minimale: interfacce chiare, docstring per tutti i modelli Pydantic, funzioni pure nei nodi, dipendenze iniettate, logging strutturato e test granulari. [^20][^19]
- Agent‑friendly: docstring dei tool ricche di istruzioni, `Annotated` Pydantic per semantica dei campi, prompt brevi e few‑shots con esempi positivi/negativi per ridurre ambiguità. [^26][^24]
- Scalabile: separazione orchestrazione/validation/persistenza/QA e versionamento degli schemi per evolvere senza breaking changes. [^19][^16]


## Data model (policy aggiornata)

- Principio: ogni entità eredita da una `BaseEntity` con un `id` univoco (UUID4). Le relazioni sono esclusivamente archi del grafo, mai attributi delle entità, per garantire chiarezza semantica, traversal efficiente e portabilità. [^8][^9]
- Entità iniziali (nodi): Progetto, Utente, Epic, Issue con chiavi naturali stabili e proprietà minime utili a Agile/PMI. [^16][^12]
- Catalogo relazioni canoniche: Progetto -[HAS_EPIC]-> Epic, Epic -[HAS_ISSUE]-> Issue, Issue -[ASSIGNED_TO]-> Utente, Issue -[BLOCKS]-> Issue, con direzione unica e proprietà essenziali. [^8][^27]
- Reificazione: quando una relazione richiede proprietà ricche o gestione storica/cardinalità complesse, introdurre nodo intermedio (es. ASSIGNMENT) e collegarlo con archi semantici. [^28][^8]
- Pydantic: si usa per validare nodi e Patch tipizzate (AddNode, UpdateProps, AddEdge, Delete), non per incapsulare relazioni come array di chiavi. [^16][^18]
- Portabilità: il GraphStore converte Patch in Cypher (Neo4j) o nGQL (Nebula) mantenendo semantica e idempotenza via MERGE/INSERT EDGE controllati. [^14][^23]

Esempio Pydantic

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict

class Progetto(BaseModel):
    key: str = Field(..., description="Chiave unica progetto")
    nome: str
    descrizione: Optional[str] = None

class Utente(BaseModel):
    user_id: str
    nome: str

class Epic(BaseModel):
    key: str
    titolo: str
    progetto_key: str

class Issue(BaseModel):
    key: str
    titolo: str
    stato: Literal["open","in_progress","done","blocked"] = "open"

class NodeSpec(BaseModel):
    label: Literal["Progetto","Utente","Epic","Issue","ASSIGNMENT"]
    key: str
    props: Dict = {}

class EdgeSpec(BaseModel):
    src_label: Literal["Progetto","Epic","Issue","ASSIGNMENT"]
    src_key: str
    rel: Literal["HAS_EPIC","HAS_ISSUE","ASSIGNED_TO","BLOCKS","HAS_ASSIGNMENT","ASSIGNMENT_OF"]
    dst_label: Literal["Epic","Issue","Utente","ASSIGNMENT"]
    dst_key: str
    props: Dict = {}

class Patch(BaseModel):
    op: Literal["AddNode","UpdateProps","AddEdge","Delete"]
    node: Optional[NodeSpec] = None
    edge: Optional[EdgeSpec] = None
```

Guidelines relazioni

- Naming specifico e direzione univoca per relazioni per evitare ridondanze e query ambigue, privilegiando interpretazione semantica chiara. [^8][^27]
- Proprietà sull’arco per metadati operativi, e reificazione quando lo sforzo supera la soglia di complessità gestionale. [^28][^8]


## GraphStore astratto

- Interfaccia: upsert(patches: List[Patch]) → esito, query_nl(question) → risposta, query_graph(query: {cypher|ngql}) → rows, migrazioni e health. [^14][^23]
- Neo4jStore: mapping Patch→Cypher con MERGE/SET e vincoli di unicità su chiavi naturali, più catena NL→Cypher per QA. [^29][^14]
- NebulaStore: mapping Patch→nGQL con CREATE TAG/EDGE e INSERT EDGE, più catena NL→nGQL per QA con differenze incapsulate. [^30][^23]


## API FastAPI

- Endpoint: POST /agent/act, POST /graph/patch, GET /graph/query, GET/POST /todo, GET /health, con schemi JSON e esempi per strumenti di coding. [^19][^10]
- Sicurezza: variabili d’ambiente, API key o OAuth a livelli, e log strutturati con trace id per audit e diagnosi. [^19][^20]


## UI React

- Pagine: Dashboard, Board Epic/Issue, Editor relazioni, Console agente, TODO, con errori user‑friendly e conferme per mutazioni. [^20][^19]
- Pattern: servizi tipizzati, cache di query e componenti riutilizzabili per scalabilità e coerenza UX. [^20][^19]


## Prompt e guardrail

- System prompt: ruoli, obiettivi, policy di disclosure/escalation, limiti di sicurezza e stile risposte brevi e verificabili. [^26][^12]
- Few‑shots: esempi di Patch corrette/errate, errori tool “parlabili” e correzioni, e domande NL→Cypher/nGQL tipiche del dominio. [^26][^14]
- Decoding: temperature bassa per fasi strutturate e più alta per spiegazioni, con fallback re‑ask su validation failure. [^24][^16]


## Telemetria e qualità

- Metriche: conformità schema, success rate tool, latenza per step, qualità QA, tasso di retry ed escalation. [^12][^19]
- Logging: input/output LLM, patch applicate, query e errori con correlazione di turni, mantenendo privacy e redazione dei segreti. [^19][^20]


## Variabili d’ambiente

- GRAPH_BACKEND={neo4j|nebula}, NEO4J_URI/USER/PASS, NEBULA_ADDR/PORT/USER/PASS, LLM_API_KEY, FEATURE_FLAGS, LOG_LEVEL, UI_BASE_URL. [^19][^14]


## Note e best practices AGENTS.md

- Rendi espliciti scopo, capacità, limiti, struttura repo, comandi e esempi, così gli assistenti di coding possono eseguire e generare codice coerentemente. [^10][^31]
- Mantieni sezioni brevi e operative con criteri di accettazione e esempi JSON/code, evitando ambiguità e duplicazioni. [^32][^19]


## Feedback richiesto

- Preferenza per LLM/provider e modalità di structured outputs (JSON mode o function schemas) per ottimizzare conformità e latenza. [^16][^33]
- Politiche di approvazione mutazioni: soglie per richiedere conferma umana prima del commit su grafo e livelli di audit richiesti. [^19][^10]
- Requisiti di deployment: target cloud/on‑prem, scalabilità, SLO iniziali e ambiente di integrazione con i database a grafo. [^19][^14]
<span style="display:none">[^1][^2][^3][^4][^5][^6][^7]</span>

<div style="text-align: center">⁂</div>

[^1]: https://langchain-ai.github.io/langgraph/concepts/template_applications/

[^2]: https://github.com/langchain-ai/langgraph/issues/5551

[^3]: https://langchain-ai.github.io/langgraph/agents/agents/

[^4]: https://www.youtube.com/watch?v=mNxAM1ETBvs

[^5]: https://realpython.com/langgraph-python/

[^6]: https://blog.langchain.com/how-to-build-the-ultimate-ai-automation-with-multi-agent-collaboration/

[^7]: https://blog.langchain.com/building-langgraph/

[^8]: https://neo4j.com/graphacademy/training-gdm-40/03-graph-data-modeling-core-principles/

[^9]: https://docs.nebula-graph.io/3.3.0/nebula-studio/quick-start/st-ug-plan-schema/

[^10]: https://github.com/openai/agents.md

[^11]: https://www.langchain.com/langgraph

[^12]: https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf

[^13]: https://langchain-ai.github.io/langgraph/concepts/low_level/

[^14]: https://python.langchain.com/docs/integrations/graphs/neo4j_cypher/

[^15]: https://docs.langchain.com/oss/python/langchain-structured-output

[^16]: https://python.langchain.com/docs/concepts/structured_outputs/

[^17]: https://python.langchain.com/api_reference/community/chains/langchain_community.chains.graph_qa.nebulagraph.NebulaGraphQAChain.html

[^18]: https://python.langchain.com/docs/how_to/structured_output/

[^19]: https://virtuslab.com/blog/backend/providing-library-documentation/

[^20]: https://www.honeycomb.io/blog/how-i-code-with-llms-these-days

[^21]: https://langchain-ai.github.io/langgraph/

[^22]: https://docs.langchain.com/oss/javascript/langgraph/context

[^23]: https://python.langchain.com/docs/integrations/graphs/nebula_graph/

[^24]: https://python.langchain.com/docs/concepts/chat_models/

[^25]: https://microsoft.github.io/graphrag/

[^26]: https://www.anthropic.com/engineering/claude-code-best-practices

[^27]: https://neo4j.com/docs/getting-started/data-modeling/tutorial-data-modeling/

[^28]: https://db-engines.com/de/blog_post/61

[^29]: https://neo4j.com/docs/cypher-manual/current/constraints/managing-constraints/

[^30]: https://docs.nebula-graph.io/3.1.0/3.ngql-guide/11.edge-type-statements/1.create-edge/

[^31]: https://www.infoq.com/news/2025/08/agents-md/

[^32]: https://research.aimultiple.com/agents-md/

[^33]: https://platform.openai.com/docs/guides/structured-outputs

