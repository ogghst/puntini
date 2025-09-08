# TODO

## Fase 0: Scaffolding

- [x] [P0][infra] Scaffolding del repository
- [P0][feat] Definire l'interfaccia per GraphStore
- [P0][feat] Creare i modelli Pydantic di base (Progetto, Utente, Epic, Issue)
- [P0][infra] Creare lo skeleton dell'applicazione LangGraph
- [P0][feat] Endpoint `hello world` in FastAPI
- [P0][ui] Creare la shell base dell'applicazione React

## Fase 1: MVP

- [P1][feat] Implementare il flusso Extract→Validate→Upsert→Answer per Progetto, Epic, Issue, Utente
- [P1][infra] Attivare e configurare l'adapter per Neo4j
- [P1][doc] Creare e mantenere il file TODO.md
- [P1][feat] Implementare le metriche minime di base

## Fase 2: NebulaGraph Parity & QA

- [P2][feat] Raggiungere la parità funzionale con NebulaGraph creando un adapter nGQL
- [P2][infra] Introdurre feature flags per i backend del grafo
- [P2][feat] Implementare una catena di QA per entrambi i backend (Neo4j, NebulaGraph)
- [P2][infra] Creare script di migrazione per i dati
- [P2][test] Scrivere test di parità per i due backend

## Fase 3: UI Avanzata e Governance

- [P3][ui] Creare una board interattiva per Epic e Issue
- [P3][ui] Sviluppare un editor di relazioni tra nodi
- [P3][feat] Implementare un visualizzatore di log e differenze per l'audit
- [P3][feat] Aggiungere autenticazione e autorizzazione
- [P3][feat] Definire policy di approvazione per le modifiche

## Fase 4: Production Hardening

- [P4][feat] Integrare RAG sul grafo per risposte più ricche
- [P4][feat] Definire e monitorare i KPI di progetto
- [P4][feat] Implementare policy di escalation intelligenti per l'agente
- [P4][test] Scrivere test end-to-end completi
