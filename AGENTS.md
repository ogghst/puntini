framework: langgraph. persistenza: crea un layer di astrazione, utilizza neo4j inizialmente come implementazione ma permetti di utilizzare nebulagraph senza modifiche architetturali. interfaccia fastapi e react. parti gradualmente con un approccio incrementale, crea un piano di progetto per arrivare al full feature

Sì: di seguito è riportato un file AGENTS.md pronto per strumenti come Gemini CLI o Claude Code, progettato per LangGraph, con persistenza a strato di astrazione (Neo4j iniziale, NebulaGraph intercambiabile), interfaccia FastAPI+React e un piano incrementale verso la full‑feature. [1][2] Il documento incorpora best practice diffuse per AGENTS.md e agentic coding, incluse linee guida su structured outputs, controllo del flusso e documentazione per coding assistants. [3][4]

# AGENTS.md

## Scopo
L’agente assiste nella creazione e gestione di progetti di miglioramento aziendale basati su metodologie Agile e PMI, traducendo richieste in entità/relazioni su grafo e azioni operative verificabili. [5][1]
Obiettivi principali: orchestrazione robusta con state machine, output strutturati Pydantic, persistenza idempotente e UX via FastAPI+React per collaborazione e audit. [6][7]
Non‑obiettivi: autonomia illimitata senza guardrail, mutazioni su grafo senza validazione, dipendenza rigida da un solo database o provider LLM. [5][8]

## Epics
- Creazione progetto di miglioramento: da prompt a Progetto/Epic/Issue/Utente con vincoli PMI/Agile, più piano iniziale e KPI. [5][9]
- Richiesta informazioni: QA sul grafo (text‑to‑Cypher) e generazione report sintetici su stato, rischi, dipendenze. [2][10]
- Generazione entità e relazioni: estrazione incrementale con structured outputs e validazione Pydantic, più dedup/resolve. [7][11]
- Modifica grafo via prompt: patch tipizzate (AddNode/UpdateProps/AddEdge/Delete) con MERGE idempotente e rollback. [2][6]
- Governance e audit: history delle operazioni, diffs leggibili e criteri di approvazione per cambi rilevanti. [8][3]
- Interfaccia e collaborazione: pannello FastAPI+React, notifiche e commenti su ticket ed epiche. [8][12]
- Estensioni RAG su grafo: riepiloghi gerarchici e query locali/globali quando il corpus cresce. [13][14]

## Architettura
- Librerie: LangGraph per controllo del flusso a grafo, LangChain per structured outputs e integrazioni grafiche, FastAPI, React, Pydantic, driver Neo4j e NebulaGraph. [6][2]
- Componenti: Orchestrator (state machine), Context Manager (progressive context disclosure), Tool Layer (graph store + QA), Validation Layer (Pydantic), API (FastAPI), UI (React), Telemetria/Logging. [6][15]
- Persistenza astratta: interfaccia GraphStore con implementazioni Neo4j e NebulaGraph, sostituibili senza impatti su orchestrazione e schemi. [2][16]

## Struttura cartelle
- /apps/api: backend FastAPI (routers, services, adapters GraphStore, auth). [8][12]
- /apps/web: frontend React (pages, components, services). [8][12]
- /packages/agent: logica LangGraph, nodi, prompt, validation, tool registry. [1][6]
- /packages/graphstore: interfacce, Neo4jStore, NebulaStore, mapping Cypher/nGQL. [2][10]
- /packages/models: Pydantic (Progetto, Utente, Issue, Epic) e Patch/Spec. [7][11]
- /infra: config, env, compose/k8s, migrazioni grafo. [8][3]

Esempio albero
```
.
├─ apps/
│  ├─ api/
│  └─ web/
├─ packages/
│  ├─ agent/
│  ├─ graphstore/
│  └─ models/
└─ infra/
```

## Flusso di funzionamento
- Plan→Act→Observe controllato da LangGraph: nodi Extract→Validate→Upsert→Answer con transizioni condizionali e criteri di fine/escalation. [6][17]
- Progressive context disclosure: fornire all’LLM solo contesto minimo per lo step, aggiungendo error e historical context su fallimenti ripetuti. [15][18]
- Structured outputs: Pydantic + JSON/tool mode per generare patch e entità, con retry mirati su validazione fallita. [7][11]
- Persistenza: GraphStore.upsert(patch[]) traduce in Cypher o nGQL idempotenti e restituisce errori “parlabili” con suggerimenti. [2][10]
- QA: catena NL→Cypher/nGQL per domande operative e riepiloghi con contesto dal grafo. [2][19]

## Piano di progetto
- Fase 0: scaffolding repo, modelli Pydantic base, interfaccia GraphStore e stub Neo4j/Nebula, skeleton LangGraph, FastAPI hello, React shell. [3][1]
- Fase 1 (MVP): Extract→Validate→Upsert→Answer su Progetto/Epic/Issue/Utente, JSON mode, Neo4j attivo, TODO markdown persistente. [7][2]
- Fase 2: NebulaGraph parity con adapter nGQL, feature flags, QA chain per entrambe le implementazioni. [10][16]
- Fase 3: UI evoluta (board Epic/Issue, editor relazioni), audit log e diff viewer, auth. [8][12]
- Fase 4: RAG su grafo, metriche KPI, policy escalation intelligente, test E2E e hardening. [13][6]

## Avanzamento con Todo
- La lista TODO vive in /AGENT_TODO.md in markdown, curata dall’agente e dagli sviluppatori, con tag [feat][fix][infra][doc] e priorità P0‑P2. [3][8]
- Ogni task include “Criteri di accettazione” e “Definizione di fatto” per aiutare l’LLM a concludere le attività senza ambiguità. [3][8]
- L’agente propone aggiornamenti alla TODO a fine turno (aggiunte/completamenti), chiedendo conferma in caso di cambiamenti critici di scope. [3][20]

Template
```
## TODO
- [P0][feat] Adapter Neo4j GraphStore con MERGE idempotente (DoD: upsert, relazioni, errori parlabili)  
- [P1][feat] Adapter NebulaGraph GraphStore con nGQL e parità API  
- [P1][ui] Board Epic/Issue con filtri e aggiornamenti in tempo reale  
```

## Stile di coding
- Elegante e minimale: OOP per interfacce e implementazioni, funzioni pure nei nodi, dipendenze esplicite via costruttori. [12][20]
- Scalabile: separazione netta orchestrazione/validation/persistenza/QA, iniezione dipendenze, log strutturati, test unitari su nodi e adapter. [8][1]
- LLM‑friendly: errori tool “parlabili” con suggerimenti, prompt brevi e composabili, esempi positivi/negativi nei few‑shots. [20][18]

## Data model
- Entità iniziali: Progetto, Utente, Issue, Epic, con chiavi naturali stabili e proprietà minime utili a PMI/Agile. [5][7]
- Espandibilità: aggiungere Milestone, Stakeholder, Dipendenze, KPI senza rompere contratti grazie a campi opzionali e versionamento schema. [7][3]
- Mapping grafo: label/nodi e relazioni standardizzati con upsert idempotente sia in Cypher (Neo4j) sia in nGQL (NebulaGraph). [2][10]

Esempio Pydantic
```python
from pydantic import BaseModel, Field
from typing import Optional, Literal, List

class Progetto(BaseModel):
    key: str = Field(..., description="Chiave unica progetto")
    nome: str
    descrizione: Optional[str] = None
    metodologia: Literal["Agile","PMI","Ibrido"] = "Agile"

class Utente(BaseModel):
    user_id: str
    nome: str
    ruolo: Optional[str] = None

class Epic(BaseModel):
    key: str
    titolo: str
    progetto_key: str

class Issue(BaseModel):
    key: str
    titolo: str
    stato: Literal["open","in_progress","done","blocked"] = "open"
    epic_key: Optional[str] = None
    assegnatario: Optional[str] = None
```

Patch tipizzate
```python
class NodeSpec(BaseModel):
    label: Literal["Progetto","Utente","Issue","Epic"]
    key: str
    props: dict = {}

class EdgeSpec(BaseModel):
    src_label: str; src_key: str
    rel: str
    dst_label: str; dst_key: str

class Patch(BaseModel):
    op: Literal["AddNode","UpdateProps","AddEdge","Delete"]
    node: Optional[NodeSpec] = None
    edge: Optional[EdgeSpec] = None
```

## GraphStore astratto
- Interfaccia: GraphStore.upsert(patches), query(nl|cypher|ngql), get(node), diff(snapshot) e gestione transazioni idempotenti. [2][16]  
- Neo4jStore: usa Cypher via integrazione e catene NL→Cypher per QA. [2][21]
- NebulaStore: usa nGQL con client ufficiale e catene NL→nGQL analoghe. [10][22]

Note compatibilità
- Linguaggi: Cypher vs nGQL con leggere differenze sintattiche e semantiche; mantenere mapping e test di parità. [10][2]
- Wrapper: integrazioni LangChain offrono classi Neo4jGraph/NebulaGraph e QA chain dedicate per generazione query. [2][19]

## Orchestrazione con LangGraph
- State graph: nodi plan/patch/exec/eval, edges condizionali, stato serializzabile, checkpointing opzionale. [6][17]
- Context manager: disclosure progressiva del contesto e gestione errori per retry/escalation deterministica. [15][6]
- Structured outputs: with_structured_output per schemi Pydantic e re‑ask mirati su validation error. [7][11]

## API FastAPI
- Endpoint chiave: POST /agent/act, GET /graph/query, POST /graph/patch, GET /todo, POST /todo, GET /health e auth middleware. [8][12]
- Contratti: JSON schema con descrizioni per coding assistants e esempi di richieste/risposte. [8][3]

## UI React
- Pagine: Dashboard progetto, Board epiche/issue, Editor grafo, Console agente, TODO. [8][12]
- Pattern: stato locale + cache di query, componenti tipizzati, errori user‑friendly e controlli di conferma per mutazioni. [12][8]

## Prompt e guardrail
- System prompt per ruoli, obiettivi, policy di disclosure, limiti di sicurezza e stile risposte. [20][5]
- Few‑shots: esempi di patch corrette/errate e messaggi di errore dei tool con suggerimenti. [20][18]
- Decoding: temperature bassa per fasi strutturate, più alta per spiegazioni; fallback a re‑ask su validation fail. [18][7]

## Telemetria e qualità
- Logging strutturato di richieste, patch, query e errori, con correlazione di turni e trace id. [8][12]
- Metriche: tasso di conformità schema, success rate tool, latenza per step, qualità QA. [5][8]

## Accettazione e test
- Acceptance criteria per epiche/feature con casi di prova deterministici su patch e QA. [3][8]
- Test: unit test su nodi LangGraph e adapter GraphStore, integrazione con Neo4j/Nebula in container, E2E su scenari tipici. [1][2]

## Variabili d’ambiente
- LLM_API_KEY, GRAPH_BACKEND (neo4j|nebula), NEO4J_URI/USER/PASS, NEBULA_ADDR/PORT/USER/PASS, FEATURE_FLAGS, LOG_LEVEL. [8][2]  
- Segreti in vault e mock per ambienti di sviluppo locali. [8][12]

## Note su best practices AGENTS.md
- Esplicitare scopo, capacità, limiti, struttura repo, comandi e esempi, per massimizzare eseguibilità dai coding assistants. [3][23]
- Mantenere brevi e univoche le istruzioni operative e accettazione per ridurre ambiguità dell’LLM. [24][8]

## Richieste di feedback
- Modello LLM e provider preferito per structured outputs e tool calling (es. JSON mode o function schemas). [7][25]
- Politiche di sicurezza e audit: granularità di approvazione per mutazioni su grafo e conservazione dei log. [8][5]
- Requisiti di deployment: target cloud/on‑prem, scalabilità e SLO iniziali per API/UI. [8][12]

Se queste scelte sono allineate, si può procedere con la Fase 0 (scaffolding, interfacce e stub) e attivare il circuito MVP con Neo4j, mantenendo compatibilità binaria con NebulaGraph via adapter. [1][16]

Citazioni:
[1] LangGraph https://www.langchain.com/langgraph
[2] Neo4j - Python LangChain https://python.langchain.com/docs/integrations/graphs/neo4j_cypher/
[3] AGENTS.md — a simple, open format for guiding coding agents https://github.com/openai/agents.md
[4] Structured Output - Docs by LangChain https://docs.langchain.com/oss/python/langchain-structured-output
[5] [PDF] A practical guide to building agents - OpenAI https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf
[6] state graph node - GitHub Pages https://langchain-ai.github.io/langgraph/concepts/low_level/
[7] Structured outputs | 🦜️🔗 LangChain https://python.langchain.com/docs/concepts/structured_outputs/
[8] Providing library documentation to AI coding assistants - VirtusLab https://virtuslab.com/blog/backend/providing-library-documentation/
[9] LLM Agents - Prompt Engineering Guide https://www.promptingguide.ai/research/llm-agents
[10] NebulaGraph - Python LangChain https://python.langchain.com/docs/integrations/graphs/nebula_graph/
[11] How to return structured data from a model https://python.langchain.com/docs/how_to/structured_output/
[12] How I Code With LLMs These Days - Honeycomb https://www.honeycomb.io/blog/how-i-code-with-llms-these-days
[13] Welcome - GraphRAG https://microsoft.github.io/graphrag/
[14] microsoft/graphrag: A modular graph-based Retrieval ... https://github.com/microsoft/graphrag
[15] Context overview - Docs by LangChain https://docs.langchain.com/oss/javascript/langgraph/context
[16] NebulaGraph — LangChain documentation https://python.langchain.com/api_reference/community/graphs/langchain_community.graphs.nebula_graph.NebulaGraph.html
[17] LangGraph - GitHub Pages https://langchain-ai.github.io/langgraph/
[18] Chat models | 🦜️🔗 LangChain https://python.langchain.com/docs/concepts/chat_models/
[19] NebulaGraphQAChain — LangChain documentation https://python.langchain.com/api_reference/community/chains/langchain_community.chains.graph_qa.nebulagraph.NebulaGraphQAChain.html
[20] Claude Code: Best practices for agentic coding - Anthropic https://www.anthropic.com/engineering/claude-code-best-practices
[21] LangChain Neo4j Integration - Neo4j Labs https://neo4j.com/labs/genai-ecosystem/langchain/
[22] NebulaGraph Python https://docs.nebula-graph.io/3.3.0/14.client/5.nebula-python-client/
[23] AGENTS.md Emerges as Open Standard for AI Coding Agents - InfoQ https://www.infoq.com/news/2025/08/agents-md/
[24] Agents.md: The README for Your AI Coding Agents https://research.aimultiple.com/agents-md/
[25] OpenAI Structured Outputs Guide https://platform.openai.com/docs/guides/structured-outputs
[26] vesoft-inc/nebula-python: Client API of Nebula Graph in Python https://github.com/vesoft-inc/nebula-python
[27] NebulaGraph Python Client: Class List https://vesoft-inc.github.io/nebula-python/release-3.8/annotated.html
[28] nebula2-python - PyPI https://pypi.org/project/nebula2-python/
[29] NebulaGraph Python https://docs.nebula-graph.com.cn/3.8.0/14.client/5.nebula-python-client/
[30] Best Graph Database for Enterprise: Neo4j vs TigerGraph vs Dgraph ... https://www.nebula-graph.io/posts/best-graph-database-for-enterprise
[31] NebulaGraph x LLM：Pioneering the New Paradigm of "Graph + AI ... https://www.nebula-graph.io/posts/graph-ai
[32] nebula3-python 3.8.2 - PythonFix.com https://pythonfix.com/pkg/n/nebula3-python/
[33] Graph Database Performance Comparison: Neo4j vs NebulaGraph ... https://www.nebula-graph.io/posts/performance-comparison-neo4j-janusgraph-nebula-graph
[34] langchain_community.graphs.nebula_graph - Python LangChain https://python.langchain.com/api_reference/_modules/langchain_community/graphs/nebula_graph.html
[35] 7 Best Graph Databases in 2025 - PuppyGraph https://www.puppygraph.com/blog/best-graph-databases
[36] nebula-python - PyPI https://pypi.org/project/nebula-python/
[37] Testing 6 different graph databases over a month to see which one ... https://www.reddit.com/r/programming/comments/15fcxkd/testing_6_different_graph_databases_over_a_month/
[38] How Graph Database works with fbthrift by NebulaGraph Clients https://itnext.io/how-graph-database-works-with-fbthrift-by-nebulagraph-clients-54f3131829fc
[39] Memgraph vs NebulaGraph https://memgraph.com/blog/memgraph-vs-nebulagraph
[40] NebulaGraph Database + Large Language Model (LLMs) https://www.nebula-graph.io/ai_llm
[41] [PDF] JanusGraph, Nebula Graph, Neo4j, and TigerGraph https://baes.uc.pt/bitstream/10316/113292/1/Experimental-Evaluation-of-Graph-Databases-JanusGraph-Nebula-Graph-Neo4j-and-TigerGraphApplied-Sciences-Switzerland.pdf
