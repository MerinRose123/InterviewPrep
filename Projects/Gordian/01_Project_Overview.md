# Gordian — project overview

## 1. Project overview

Gordian was a single-tenant document/data copying-detection application built for the client. The client maintained a large reference CSV containing industrial-equipment details and related information. Users uploaded competitor documents, and the application compared their contents against the reference data to assess the amount of copying and produce analysis/reports for the client's review and possible legal follow-up. This workflow and single-tenant scope are directly confirmed by Merin.

### Client domain: public context versus internal application

Gordian's official [November 2021 RSMeans announcement](https://www.gordian.com/press/gordian-releases-2022-rsmeans-data-construction-costs/) describes construction-cost datasets covering materials, equipment, and labor, used for construction estimating. That is consistent with the equipment-related reference data recalled here. It does not prove that the internal CSV was specifically RSMeans data or establish its columns. No public source located in this research independently documents the internal piracy-detection application.

The client company and this internal application have different scopes: Gordian supplies construction data/software; this project helped compare competitor documents with the client's proprietary reference data. The comparison output supported client review; the exact copying-score formula remains to be recalled.

**Backend and reporting correction:** Merin confirms Flask was the backend framework, Django was not involved, and WeasyPrint generated PDFs. These direct corrections supersede older project-stack attributions.

**Source correction:** Older career materials attribute a multi-tenant backend to Gordian. Merin's October 28, 2026 clarification takes precedence: this application was **single-tenant**. The original resume, LinkedIn PDF, and portfolio have not been edited.

The resume and LinkedIn profile place the relevant work under the InApp Software Engineer role, July 2020-November 2021. This is the documented employment window, not a confirmed project start/end date.

### Interview introduction

“At InApp, I worked on Gordian, a single-tenant document/data copying-detection and reporting system. The client supplied a large reference CSV with equipment-related data, and we compared uploaded competitor documents against it to assess copying for client review and possible legal follow-up. I implemented data cleaning, data analysis, and document similarity scoring using Python, Pandas, and NumPy to identify possible plagiarism, and analyzed and visualized more than 50,000 data points using Matplotlib and MongoDB. I also engineered an asynchronous Celery pipeline for PDF reports over 16 GB+ datasets under memory constraints. A shared LRU cache helped eliminate repeated data loads that took around 30 minutes. The backend used Flask, MongoDB, Redis, and Docker on AWS EC2.”

Do not describe document fingerprinting, watermark extraction, web crawling, OCR, or a particular classification algorithm as implemented features: the supplied sources do not establish those mechanisms.

## 3. Technology stack and responsibilities

| Layer | Technology | Documented role / boundary |
|---|---|---|
| UI | Angular | Listed for Gordian; specific screens and personal UI ownership unspecified |
| Backend | Python, Flask | Single-tenant Flask backend confirmed directly by Merin |
| Reverse proxy | Not confirmed | Do not attribute Nginx to Gordian without deployment evidence |
| Runtime packaging | Docker | Package services and standardize development environments |
| Hosting | AWS EC2 | Backend hosting; instance count and topology unknown |
| Database | MongoDB | Application and analysis persistence; PostgreSQL was not used |
| Data processing | Pandas, NumPy | Analyze data and implement piracy-detection processing |
| Detection | TF-IDF with cosine similarity | Fitted text representation and document similarity scoring to identify possible plagiarism |
| Visualization | Matplotlib | Visualize piracy-related data for product decisions |
| Background execution | Celery | Asynchronous PDF report tasks |
| Background infrastructure | Redis | Broker in published cache example; production settings unverified |
| Data reuse | Celery LRUCache / in-memory task cache | Avoid redundant expensive dataset loads; published pattern explained below |
| Reports | WeasyPrint | PDF report generation; exact template and delivery flow unverified |

Redis and the shared LRU cache are separate documented concepts. Do not assume Redis held the large dataset or implemented the LRU cache. Likewise, general resume skills such as Kafka, Kubernetes, S3, and scikit-learn are not established Gordian dependencies.

## 6. Single-tenant backend, persistence, and deployment

Merin confirms this application served one client as a single-tenant system. Multiple users, uploads, and reports do not imply multiple tenants. Flask, MongoDB, Redis, Celery, Docker, and EC2 are listed in the project materials; the exact service boundaries and deployment automation remain unspecified.

Authorization still needs to protect reference files, competitor uploads, and report access. A useful design discussion covers permitted users, file validation, dataset versions, and comparison-job ownership without inventing a tenant-routing layer.

MongoDB was the sole database used by Gordian. There was no PostgreSQL-backed application store.

## 7. Contributions and evidence

| Contribution / scale | Evidence | Safe interpretation |
|---|---|---|
| Python piracy detection with Pandas / NumPy | Resume, LinkedIn, portfolio | Personal implementation contribution; algorithm unspecified |
| 50,000+ data points with Matplotlib / MongoDB | All three | Analysis scale, not prediction accuracy or request throughput |
| Celery PDF pipeline for 16 GB+ datasets | All three; portfolio names Gordian | Large-data reporting; no verified final runtime or RAM figure |
| Shared LRU cache avoiding repeated 30-minute loads | LinkedIn and portfolio; resume says in-memory task cache | Data reuse optimization; published local-memory cache pattern; production pool settings unknown |
| Single-tenant Flask backend on EC2 | Stack in career materials; tenancy corrected directly by Merin | Single-client application; older multi-tenant attribution superseded |
| Docker | Project materials | Packaging contribution; reverse-proxy choice not confirmed |
| 15% operational-efficiency improvement | Resume and LinkedIn InApp role | Role-level metric; Gordian attribution and measurement need confirmation |

### STAR answer: reporting optimization

**Situation:** Gordian needed PDF reporting over 16 GB+ CSV datasets under memory constraints, with repeated data loads taking around 30 minutes.

**Task:** Support asynchronous report generation and reduce redundant data loading across concurrent tasks.

**Action:** “I engineered the Celery reporting pipeline and implemented reusable dataset caching described in my materials as a shared LRU cache.” The article supplies the base-task/local-memory pattern; recover production keys, memory limits, and worker-pool configuration for deeper follow-up.

**Result:** Repeated expensive loads were eliminated through reuse. Do not invent final report latency, memory savings, cache hit rate, or a benchmark configuration.


## Study path

- [Architecture and data flow](02_Architecture_and_Data_Flow.md)
- [Engineering challenges](03_Engineering_Challenges.md)
- [Scaling and failure scenarios](04_Scaling_and_Failure_Scenarios.md)
- [Interview Q&A](05_Interview_QA.md)
- [Comprehensive technical reference](Interview_Guide.md)
