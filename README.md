# IT Contract Analysis Agent

Reads IT contracts (software, hardware, services, staffing), classifies them and extracts the clauses that procurement, legal and IT governance need into a validated, structured record.

**Stack:** Python · Streamlit · Azure OpenAI · Pydantic · pdfplumber · Azure Document Intelligence (OCR) · Azure AI Search
**Role:** Lead developer: design and implementation

> Built at a large Brazilian insurer. The company is replaced by the fictional **Acme Seguros**, and every name, document and data point here is fictional. Code, prompts and UI are in Portuguese, written for Brazilian business teams.

## Problem

IT contracts were read by hand to find term dates, renewal rules, costs, SLAs and data-protection clauses. The same contract was read again for every audit, renewal or cost review, and the information never ended up in one structured place.

## What I built

- **Classification:** software, hardware, services, staffing or hybrid, with a 0–1 confidence score, a justification and keywords.
- **Clause extraction** into eight sections: general data, supplier, licensing, term and termination, costs and penalties, support/SLA, LGPD (Brazil's GDPR) compliance and legal obligations.
- **Pydantic schemas** for every section, so the output is always the same shape and missing fields are explicit, not invented.
- **Q&A over an indexed contract:** a contract can be indexed in Azure AI Search and then queried in chat.
- Native text extraction with pdfplumber; OCR fallback for scanned contracts; a result cache so re-analysing the same contract costs nothing.

## Design decisions

| Decision | Why |
|---|---|
| Classification and clause extraction as separate skills, and extraction can focus on one clause type | Users often need only costs or only LGPD, and a focused prompt is cheaper and more accurate |
| Structured output validated by Pydantic | Downstream governance needs fields, not prose |
| Cache keyed on contract text and clause type | Contracts are re-opened often; repeat analysis costs nothing |

## Run it

```bash
python -m venv .venv && .venv\Scripts\activate   # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                               # add your Azure keys
streamlit run agent.py
```

Use any sample IT contract in PDF.

---
Part of my [AI engineering portfolio](https://github.com/lucasboliveirasipp).
