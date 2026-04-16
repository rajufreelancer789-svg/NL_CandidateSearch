# Demo Test Sheet

Use these prompts during the demo to prove the search system handles different sectors and does not collapse into IT-only results.

Each row includes the query to ask, the expected top resume, and the category it should come from.

| ID | Sector | Query | Expected output |
| --- | --- | --- | --- |
| 1 | Healthcare | Sourced healthcare professionals for travel and contract assignments. Qualified candidates based on client requirements. Maintaining pipelines to passive candidates. Make 60-100 daily outbound calls and emails to potential candidates. | Top resume: CORPORATE REGIONAL RECRUITER. Category: Healthcare. File: [HEALTHCARE_17864043.pdf](/Users/appalaraju/Desktop/NLP/nlcs/uploads/HEALTHCARE_17864043.pdf) |
| 2 | HR | Looking for an HR manager/business partner with employee relations, workforce planning, talent acquisition, succession planning, organizational design, and HRIS Workday PeopleSoft Oracle. | Top resume: HR MANAGER/BUSINESS PARTNER. Category: Hr. File: [HR_30563572.pdf](/Users/appalaraju/Desktop/NLP/nlcs/uploads/HR_30563572.pdf) |
| 3 | Information Technology | Senior information technology manager with Office 365 migration, disaster recovery, network infrastructure, server and storage, SQL, and system center management. | Top resume: SENIOR INFORMATION TECHNOLOGY MANAGER. Category: Information Technology. File: [INFORMATION-TECHNOLOGY_18176523.pdf](/Users/appalaraju/Desktop/NLP/nlcs/uploads/INFORMATION-TECHNOLOGY_18176523.pdf) |
| 4 | Accountant | Accounting professional with twenty years of experience in inventory and manufacturing accounting, Sage 100, Syspro, financial statements, general ledger, and reconciliations. | Top resume: ACCOUNTANT. Category: Accountant. File: [ACCOUNTANT_27980446.pdf](/Users/appalaraju/Desktop/NLP/nlcs/uploads/ACCOUNTANT_27980446.pdf) |
| 5 | Banking | Investment banking summer analyst with M&A modeling, valuation, Python, Java, Excel macros, and financial analysis. | Top resume: INVESTMENT BANKING SUMMER ANALYST. Category: Banking. File: [BANKING_29839396.pdf](/Users/appalaraju/Desktop/NLP/nlcs/uploads/BANKING_29839396.pdf) |
| 6 | Chef | Chef de cuisine with culinary school training, seasonal menu development, inventory ordering, handmade pastas, and kitchen leadership. | Top resume: CHEF DE CUISINE. Category: Chef. File: [CHEF_22561438.pdf](/Users/appalaraju/Desktop/NLP/nlcs/uploads/CHEF_22561438.pdf) |
| 7 | Sales / Marketing | Digital media consultant with sales revenue generation, account management, territory management, marketing strategies, and client relations. | Top resume: DIGITAL MEDIA CONSULTANT. Category: Digital Media. File: [DIGITAL-MEDIA_14945250.pdf](/Users/appalaraju/Desktop/NLP/nlcs/uploads/DIGITAL-MEDIA_14945250.pdf) |
| 8 | Aviation | Aviation electrician with 20 years of experience on large-scale electronic systems, avionics, troubleshooting, electrical systems, and aircraft maintenance. | Top resume: ELECTRICIAN. Category: Aviation. File: [AVIATION_11752500.pdf](/Users/appalaraju/Desktop/NLP/nlcs/uploads/AVIATION_11752500.pdf) |
| 9 | Public Relations | Marketing coordinator working on advertisements, direct mail, editing, email campaigns, press releases, newsletters, and website content. | Top resume: MARKETING COORDINATOR. Category: Public Relations. File: [PUBLIC-RELATIONS_21669215.pdf](/Users/appalaraju/Desktop/NLP/nlcs/uploads/PUBLIC-RELATIONS_21669215.pdf) |

Suggested demo flow:
1. Ask the query.
2. Show the top returned resume.
3. Confirm the category and why it matched.
4. Move to the next sector.

Validation note:
- The healthcare query was checked against the current search pipeline and returns the healthcare recruiter resume first.
- The rest are curated from stored PageIndex trees and are intended for demo validation across sectors.