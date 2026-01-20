# ProcureMind MVP

## What This Is

A procurement intelligence tool that transforms messy RFQ emails into structured, comparable data. It parses incoming RFQs into tables, lets you log products and supplier quotes you find, and provides a comparison dashboard to evaluate options side-by-side. Built for a solo user starting fresh with no historical data.

## Core Value

Parse RFQs into structured data and compare options (suppliers and products) to make faster, better procurement decisions.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Paste raw RFQ email text and get structured table output (item, requirements, brand, specs, links)
- [ ] Manually add RFQ items when AI parsing fails
- [ ] Add suppliers to the database (name, contact info)
- [ ] Add products with details (name, description, specs)
- [ ] Log price quotes (product, supplier, price, date)
- [ ] Compare different suppliers' quotes for the same product
- [ ] Compare different products that could fulfill the same requirement
- [ ] Search historical prices using vector similarity (semantic search)
- [ ] Dashboard view for side-by-side comparison and decision making

### Out of Scope

- Email integration / automatic inbox parsing — manual paste is fine for v1
- Multi-user / team collaboration — solo tool
- Notifications or alerts — manual workflow
- Mobile app — web/desktop Streamlit is sufficient

## Context

- Currently processing RFQs manually, a few per week
- No existing historical data — knowledge base builds as the tool is used
- Each logged quote becomes searchable history for future RFQs
- Primary goal is speed: reduce time from RFQ receipt to decision

## Constraints

- **Tech stack**: Streamlit (frontend), Python 3.10+ (backend), Supabase with pgvector (database), OpenAI API (parsing + embeddings) — user-specified
- **Deployment**: Local/simple deployment acceptable for solo use
- **Data**: Starting from zero — system must be usable without historical data

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Streamlit for UI | Rapid development, Python-native, good enough for solo tool | — Pending |
| Supabase + pgvector | Managed PostgreSQL with vector search built-in, no infra overhead | — Pending |
| OpenAI for parsing & embeddings | Proven quality for text extraction and semantic search | — Pending |
| Manual entry fallback | AI parsing may fail on unusual RFQ formats, need reliability | — Pending |

---
*Last updated: 2026-01-20 after initialization*
