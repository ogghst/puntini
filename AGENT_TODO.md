# TODO

| ID | Fase | Priorità | Tipo | Descrizione | Stato |
|---|---|---|---|---|---|
| F0-1 | 0 | P0 | infra | Scaffolding del repository | ✅ |
| F0-2 | 0 | P0 | feat | Definire l'interfaccia per GraphStore | ✅ |
| F0-3 | 0 | P0 | feat | Creare i modelli Pydantic di base (Progetto, Utente, Epic, Issue) | ✅ |
| F0-4 | 0 | P0 | infra | Creare lo skeleton dell'applicazione LangGraph | ✅ |
| F0-5 | 0 | P0 | feat | Endpoint `hello world` in FastAPI | ✅ |
| F0-6 | 0 | P0 | ui | Creare la shell base dell'applicazione React | ✅ |
| F0-7 | 0 | P0 | feat | Implementare SessionManager per la gestione delle sessioni utente | ✅ |
| F0-8 | 0 | P0 | feat | Implementare Session class con orchestrazione runtime e message queuing | ✅ |
| F0-9 | 0 | P0 | feat | Creare endpoint API per la gestione delle sessioni | ✅ |
| F1-1 | 1 | P1 | feat | Implementare il flusso Extract→Validate→Upsert→Answer per Progetto, Epic, Issue, Utente | ⬜️ |
| F1-2 | 1 | P1 | infra | Attivare e configurare l'adapter per Neo4j | ⬜️ |
| F1-3 | 1 | P1 | doc | Creare e mantenere il file TODO.md | ⬜️ |
| F1-4 | 1 | P1 | feat | Implementare le metriche minime di base | ⬜️ |
| F1-5 | 1 | P1 | feat | Integrare SessionManager con il sistema di agenti LangGraph | ⬜️ |
| F1-6 | 1 | P1 | feat | Implementare il routing dei messaggi tra frontend e agenti | ⬜️ |
| F1-7 | 1 | P1 | test | Scrivere test unitari per SessionManager e Session | ⬜️ |
| F2-1 | 2 | P2 | feat | Raggiungere la parità funzionale con NebulaGraph creando un adapter nGQL | ⬜️ |
| F2-2 | 2 | P2 | infra | Introdurre feature flags per i backend del grafo | ⬜️ |
| F2-3 | 2 | P2 | feat | Implementare una catena di QA per entrambi i backend (Neo4j, NebulaGraph) | ⬜️ |
| F2-4 | 2 | P2 | infra | Creare script di migrazione per i dati | ⬜️ |
| F2-5 | 2 | P2 | test | Scrivere test di parità per i due backend | ⬜️ |
| F3-1 | 3 | P3 | ui | Creare una board interattiva per Epic e Issue | ⬜️ |
| F3-2 | 3 | P3 | ui | Sviluppare un editor di relazioni tra nodi | ⬜️ |
| F3-3 | 3 | P3 | feat | Implementare un visualizzatore di log e differenze per l'audit | ⬜️ |
| F3-4 | 3 | P3 | feat | Aggiungere autenticazione e autorizzazione | ⬜️ |
| F3-5 | 3 | P3 | feat | Definire policy di approvazione per le modifiche | ⬜️ |
| F4-1 | 4 | P4 | feat | Integrare RAG sul grafo per risposte più ricche | ⬜️ |
| F4-2 | 4 | P4 | feat | Definire e monitorare i KPI di progetto | ⬜️ |
| F4-3 | 4 | P4 | feat | Implementare policy di escalation intelligenti per l'agente | ⬜️ |
| F4-4 | 4 | P4 | test | Scrivere test end-to-end completi | ⬜️ |

## Legenda Fasi

- **Fase 0:** Scaffolding
- **Fase 1:** MVP
- **Fase 2:** NebulaGraph Parity & QA
- **Fase 3:** UI Avanzata e Governance
- **Fase 4:** Production Hardening