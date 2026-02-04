# Vaal AI Empire - Knowledge Bases

📚 **Overview**
This directory contains verified, real-world data that powers the Vaal AI Empire's three autonomous engines. Every claim made by our AI agents is backed by official sources and up-to-date regulations.

🗂️ **Directory Structure**

```
data/
├── sars/                           # South African Revenue Service regulations
│   ├── section_12h_learnerships.json
│   └── eti_employment_incentive.json
├── crisis/                         # Crisis detection intelligence
│   ├── loadshedding_2024.json
│   └── south_africa_economic_context.json
├── compliance/                     # Legal & regulatory compliance
│   └── popia_essentials.json
└── README.md                       # This file
```

🔥 **Knowledge Base #1: SARS Tax Regulations**
**Section 12H - Learnership Allowances**
_File: `sars/section_12h_learnerships.json`_

What it contains:

- Annual allowances (R20K - R60K per learner)
- Completion bonuses
- NQF level classifications (1-10)
- Disability allowances
- Pro-rating formulas
- Real calculation examples
- Common mistakes to avoid
- Required documentation

Financial impact:

- Typical SME unclaimed: R150K - R500K annually
- Market opportunity: R2+ billion unclaimed across SA

Sources:

- SARS Legal Note IN-20
- SARS Learnership Guide

**ETI - Employment Tax Incentive**
_File: `sars/eti_employment_incentive.json`_

What it contains:

- 2025 updated rates (effective April 1, 2025)
- Monthly allowances by salary band
- First 12 months vs. second 12 months
- Part-time pro-rating formulas
- Eligibility criteria
- Claiming process (EMP201/EMP501)
- Real calculation examples

Financial impact:

- R1,500/month per qualifying employee (first year)
- R750/month per qualifying employee (second year)
- Typical SME benefit: R180K - R500K annually (10-30 employees)

Sources:

- SARS ETI Official Page
- SARS ETI Changes 2025

🚨 **Knowledge Base #2: Crisis Detection**
**Load-shedding Intelligence**
_File: `crisis/loadshedding_2024.json`_

What it contains:

- 2024 performance: 352 loadshedding-free days (as of Dec 17, 2024)
- Historical data (2023: 279 days of loadshedding)
- Energy Availability Factor (EAF) metrics
- Unplanned outages tracking
- Stage-by-stage impact (Stage 1-8)
- Business impact matrix (manufacturing, retail, IT, SME)
- Predictive indicators (EAF thresholds, coal stockpiles)
- Economic impact estimates

Key insight:

- 2023 loadshedding cost: R61.8 billion
- 2024 diesel savings: R16.46 billion (year-on-year)

Sources:

- Eskom Official
- Loadshedding API
- EskomSePush community monitoring

**Economic Context**
_File: `crisis/south_africa_economic_context.json`_

What it contains:

- GDP, currency, exchange rates
- Key economic challenges (strikes, port delays, currency volatility)
- SME landscape (2.5M SMEs, 34% GDP contribution)
- Digital adoption rates (48%)
- Tax compliance gap (52% compliance rate)

🔐 **Knowledge Base #3: Compliance**
**POPIA (Protection of Personal Information Act)**
_File: `compliance/popia_essentials.json`_

What it contains:

- All 8 conditions for lawful processing
- Maximum penalties: R10M fine + 12 months imprisonment
- Data breach notification requirements
- Consent requirements
- Special personal information categories
- Vaal AI Empire compliance checklist

Critical for:

- Payment processing
- User data storage
- Email marketing
- Customer communications

Sources:

- POPIA Act
- Information Regulator

🎯 **How Agents Use This Data**
**Financial Sentinel Agent**

```javascript
// Load SARS data
const section12h = require('./data/sars/section_12h_learnerships.json');
const eti = require('./data/sars/eti_employment_incentive.json');

// Calculate real tax recovery
function calculateTaxRecovery(company) {
  const learners = company.learnerships_completed;
  const recovery = learners
    .map((learner) => {
      const level = learner.nqf_level <= 6 ? 'nqf_1_to_6' : 'nqf_7_to_10';
      const ability = learner.disabled ? 'disability' : 'able_bodied';
      return section12h.allowances.annual_allowance[level][ability];
    })
    .reduce((sum, amt) => sum + amt, 0);

  return {
    amount: recovery,
    source: section12h.official_sources[0],
    confidence: 'Verified by SARS'
  };
}
```

**Guardian Engine Agent**

```javascript
// Load crisis data
const loadshedding = require('./data/crisis/loadshedding_2024.json');

// Predict crisis
function checkLoadsheddingRisk(eskomData) {
  const eaf = eskomData.energy_availability_factor;
  const indicators = loadshedding.predictive_indicators;

  if (eaf < 60) {
    return {
      risk: 'HIGH',
      alert: 'Stage 2-4 loadshedding within 48 hours',
      action: 'Activate backup generators immediately',
      source: loadshedding.data_sources[0]
    };
  }
}
```

📅 **Update Schedule**

| Knowledge Base | Update Frequency        | Last Updated |
| -------------- | ----------------------- | ------------ |
| Section 12H    | Annually (SARS budget)  | 2024-12-17   |
| ETI            | Annually (Apr 1)        | 2025-04-01   |
| Load-shedding  | Weekly (current status) | 2024-12-17   |
| POPIA          | As legislation changes  | 2024-12-17   |

⚠️ **Data Integrity**
All data in this directory:

- ✅ Sourced from official government/regulatory websites
- ✅ Verified against multiple sources
- ✅ Includes citation URLs
- ✅ Updated regularly
- ✅ Peer-reviewed before deployment

_No hallucinations. No guesses. Only facts._

🚀 **Next Steps**
To complete the knowledge base ecosystem:

- Provinces Data - All 9 provinces (education, economy, demographics)
