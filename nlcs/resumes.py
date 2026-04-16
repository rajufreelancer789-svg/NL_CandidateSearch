
import json, os, zipfile, re, random
import json, os, zipfile, re, random
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)

# ── Colour palette ─────────────────────────────────────────────────────────
ACCENT       = colors.HexColor("#1B4F8A")
ACCENT_LIGHT = colors.HexColor("#E8F0FB")
DIVIDER      = colors.HexColor("#3A7BD5")
TEXT_DARK    = colors.HexColor("#1A1A2E")
TEXT_MID     = colors.HexColor("#4A4A6A")
TAG_BG       = colors.HexColor("#E8F0FB")
TAG_BORDER   = colors.HexColor("#3A7BD5")
WHITE        = colors.white

LEVEL_COLORS = {
    "Fresher":   colors.HexColor("#27AE60"),
    "Mid-Level": colors.HexColor("#F39C12"),
    "Senior":    colors.HexColor("#E74C3C"),
    "Lead":      colors.HexColor("#8E44AD"),
    "Intern":    colors.HexColor("#16A085"),
}

def S(name, **kw):
    defaults = dict(fontName="Helvetica", fontSize=9, leading=12,
                    textColor=TEXT_DARK)
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)

def build_styles():
    return {
        "name":        S("name", fontSize=22, textColor=WHITE,
                         fontName="Helvetica-Bold", leading=26),
        "title":       S("title", fontSize=11,
                         textColor=colors.HexColor("#BDD7FF"), leading=14),
        "contact":     S("contact", fontSize=8, textColor=WHITE, leading=11),
        "badge":       S("badge", fontSize=8, textColor=WHITE,
                         fontName="Helvetica-Bold", leading=10),
        "sh":          S("sh", fontSize=10, textColor=ACCENT,
                         fontName="Helvetica-Bold", leading=13,
                         spaceBefore=5, spaceAfter=2),
        "summary":     S("summary", fontSize=8.5, textColor=TEXT_MID,
                         fontName="Helvetica-Oblique", leading=13),
        "job_title":   S("jt", fontSize=9.5, fontName="Helvetica-Bold",
                         leading=12),
        "company":     S("co", fontSize=8.5, textColor=ACCENT,
                         fontName="Helvetica-Bold", leading=11),
        "date":        S("dt", fontSize=8, textColor=TEXT_MID,
                         fontName="Helvetica-Oblique", leading=10),
        "bullet":      S("bu", fontSize=8.5, leading=12,
                         leftIndent=10, firstLineIndent=-8),
        "body_mid":    S("bm", fontSize=8.5, textColor=TEXT_MID, leading=12),
        "tag":         S("tag", fontSize=7.5, textColor=ACCENT,
                         fontName="Helvetica-Bold", leading=10),
    }

def skill_tags(skills, styles, doc_width):
    tags, row = [], []
    for s in skills:
        row.append(Paragraph(s, styles["tag"]))
        if len(row) == 3:
            tags.append(row); row = []
    if row:
        while len(row) < 3: row.append(Paragraph("", styles["tag"]))
        tags.append(row)
    if not tags: return Spacer(1, 1)
    cw = doc_width / 3
    t = Table(tags, colWidths=[cw, cw, cw])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), TAG_BG),
        ("BOX",           (0,0),(-1,-1), 0.4, TAG_BORDER),
        ("INNERGRID",     (0,0),(-1,-1), 0.3, TAG_BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("RIGHTPADDING",  (0,0),(-1,-1), 6),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]))
    return t

def section_header(title, styles, story):
    story.append(Paragraph(title.upper(), styles["sh"]))
    story.append(HRFlowable(width="100%", thickness=0.6,
                            color=DIVIDER, spaceAfter=3))

def make_pdf(data, filepath):
    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=0, bottomMargin=12*mm)
    W = doc.width
    st = build_styles()
    story = []

    # ── Header ────────────────────────────────────────────────────────────
    lc = LEVEL_COLORS.get(data["experience_level"], DIVIDER)
    contact = (f"{data['email']}  |  {data['phone']}  |  "
               f"{data['location']}  |  {data['linkedin']}")
    hdata = [
        [Paragraph(data["name"], st["name"]), ""],
        [Paragraph(data["role_title"], st["title"]),
         Paragraph(data["experience_level"], st["badge"])],
        [Paragraph(contact, st["contact"]), ""],
    ]
    ht = Table(hdata, colWidths=[W - 28*mm, 28*mm])
    ht.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), ACCENT),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("RIGHTPADDING",  (0,0),(-1,-1), 10),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("ALIGN",         (1,0),(1,-1),  "RIGHT"),
        ("SPAN",          (0,2),(1,2)),
        ("BACKGROUND",    (1,1),(1,1),   lc),
        ("TOPPADDING",    (1,1),(1,1),   4),
        ("BOTTOMPADDING", (1,1),(1,1),   4),
    ]))
    story.append(ht)
    story.append(Spacer(1, 4*mm))

    # ── Summary ───────────────────────────────────────────────────────────
    section_header("Professional Summary", st, story)
    story.append(Paragraph(data["summary"], st["summary"]))
    story.append(Spacer(1, 3*mm))

    # ── Skills ────────────────────────────────────────────────────────────
    all_skills = data["skills"]["technical"] + data["skills"]["soft"]
    section_header("Core Skills", st, story)
    story.append(skill_tags(all_skills, st, W))
    story.append(Spacer(1, 3*mm))

    # ── Experience ────────────────────────────────────────────────────────
    if data["experience"]:
        section_header("Work Experience", st, story)
        for exp in data["experience"]:
            row = Table([[
                Paragraph(exp["title"], st["job_title"]),
                Paragraph(exp["duration"], st["date"])
            ]], colWidths=[W*0.65, W*0.35])
            row.setStyle(TableStyle([
                ("ALIGN",(1,0),(1,0),"RIGHT"),
                ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                ("LEFTPADDING",(0,0),(-1,-1),0),
                ("RIGHTPADDING",(0,0),(-1,-1),0),
            ]))
            story.append(row)
            story.append(Paragraph(
                f"{exp['company']}  —  {exp['location']}", st["company"]))
            for b in exp["bullets"]:
                story.append(Paragraph(f"• {b}", st["bullet"]))
            story.append(Spacer(1, 2.5*mm))

    # ── Projects ──────────────────────────────────────────────────────────
    if data["projects"]:
        section_header("Key Projects", st, story)
        for p in data["projects"]:
            story.append(Paragraph(p["name"], st["job_title"]))
            story.append(Paragraph(p["description"], st["body_mid"]))
            story.append(Paragraph("Tech: " + " | ".join(p["tech_stack"]),
                                   st["date"]))
            story.append(Spacer(1, 2*mm))

    # ── Education ─────────────────────────────────────────────────────────
    section_header("Education", st, story)
    for e in data["education"]:
        row = Table([[
            Paragraph(f"{e['degree']}  —  {e['institution']}", st["job_title"]),
            Paragraph(f"{e['year']}  |  GPA: {e['gpa']}", st["date"])
        ]], colWidths=[W*0.70, W*0.30])
        row.setStyle(TableStyle([
            ("ALIGN",(1,0),(1,0),"RIGHT"),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("LEFTPADDING",(0,0),(-1,-1),0),
            ("RIGHTPADDING",(0,0),(-1,-1),0),
        ]))
        story.append(row)
    story.append(Spacer(1, 2*mm))

    # ── Certs + Achievements ──────────────────────────────────────────────
    c_items, a_items = [], []
    if data.get("certifications"):
        c_items.append(Paragraph("CERTIFICATIONS", st["sh"]))
        c_items.append(HRFlowable(width="100%", thickness=0.6,
                                  color=DIVIDER, spaceAfter=3))
        for c in data["certifications"]:
            c_items.append(Paragraph(f"• {c}", st["bullet"]))
    if data.get("achievements"):
        a_items.append(Paragraph("ACHIEVEMENTS", st["sh"]))
        a_items.append(HRFlowable(width="100%", thickness=0.6,
                                  color=DIVIDER, spaceAfter=3))
        for a in data["achievements"]:
            a_items.append(Paragraph(f"• {a}", st["bullet"]))
    if c_items and a_items:
        two = Table([[c_items, a_items]],
                    colWidths=[W/2 - 3*mm, W/2 - 3*mm])
        two.setStyle(TableStyle([
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LEFTPADDING",(0,0),(-1,-1),0),
            ("RIGHTPADDING",(0,0),(-1,-1),0),
        ]))
        story.append(two)
    elif c_items:
        for i in c_items: story.append(i)
    elif a_items:
        for i in a_items: story.append(i)

    doc.build(story)


# ══════════════════════════════════════════════════════════════════════════
#  RESUME DATA  (100 candidates)
# ══════════════════════════════════════════════════════════════════════════
RESUMES = [
# ── 1. Python Developer – Fresher ──────────────────────────────────────
{"name":"Arjun Sharma","email":"arjun.sharma@gmail.com","phone":"+91-9876543210",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/arjunsharma",
 "github":"github.com/arjunsharma","role_title":"Python Developer",
 "category":"Engineering","experience_level":"Fresher",
 "summary":"Recent CS graduate with strong Python fundamentals and hands-on project experience in Django and Flask. Passionate about building scalable backend services and eager to contribute to a high-impact engineering team.",
 "skills":{"technical":["Python","Django","Flask","PostgreSQL","Git","REST APIs","HTML/CSS"],"soft":["Problem Solving","Team Collaboration","Quick Learner"]},
 "experience":[{"company":"TechSpark Solutions","title":"Python Developer Intern","duration":"Jan 2024 - Jun 2024","location":"Bangalore, India","bullets":["Built REST APIs using Flask for an e-commerce platform serving 5K+ daily users","Optimized SQL queries reducing page load time by 30%","Wrote unit tests achieving 85% code coverage"]}],
 "projects":[{"name":"Student Attendance System","description":"Web app for colleges to track attendance with automated email alerts","tech_stack":["Python","Django","SQLite","Bootstrap"],"link":"github.com/arjunsharma/attendance"},{"name":"Weather Dashboard","description":"Real-time weather app using OpenWeatherMap API","tech_stack":["Python","Flask","Chart.js"],"link":"github.com/arjunsharma/weather"}],
 "education":[{"degree":"B.Tech Computer Science","institution":"VTU Bangalore","year":"2024","gpa":"8.4/10"}],
 "certifications":["Python for Everybody – Coursera","AWS Cloud Practitioner"],
 "achievements":["Winner – HackIndia 2023 (Best Backend Project)","Dean's List 2022-23"]},

# ── 2. Python Developer – Mid-Level ────────────────────────────────────
{"name":"Priya Nair","email":"priya.nair@outlook.com","phone":"+91-9845012345",
 "location":"Hyderabad, India","linkedin":"linkedin.com/in/priyanair",
 "github":"github.com/priyanair","role_title":"Python Developer",
 "category":"Engineering","experience_level":"Mid-Level",
 "summary":"4 years of Python development experience specializing in microservices, Django REST Framework, and cloud deployments. Proven track record of delivering high-availability APIs for fintech and healthcare clients.",
 "skills":{"technical":["Python","Django","FastAPI","Celery","Redis","PostgreSQL","Docker","AWS","Kafka"],"soft":["Technical Leadership","Agile","Mentoring"]},
 "experience":[
   {"company":"Infosys Ltd","title":"Senior Software Engineer","duration":"Mar 2022 - Present","location":"Hyderabad, India","bullets":["Architected microservices platform handling 2M+ daily transactions for a banking client","Reduced API response time by 45% through Redis caching and async task queues","Led a team of 4 developers and conducted weekly code reviews"]},
   {"company":"Wipro Technologies","title":"Software Engineer","duration":"Jul 2020 - Mar 2022","location":"Pune, India","bullets":["Developed RESTful APIs for healthcare portal using Django REST Framework","Implemented JWT authentication and role-based access control","Automated deployment pipelines reducing release time by 60%"]}],
 "projects":[{"name":"Loan Processing Engine","description":"Automated loan eligibility and approval pipeline for a major bank","tech_stack":["Python","FastAPI","Celery","Redis","PostgreSQL"],"link":"github.com/priyanair/loan-engine"},{"name":"Real-time Analytics Dashboard","description":"Streaming analytics using Kafka and WebSockets","tech_stack":["Python","Kafka","WebSockets","React"],"link":"github.com/priyanair/analytics"}],
 "education":[{"degree":"B.E. Computer Science","institution":"BITS Pilani","year":"2020","gpa":"8.7/10"}],
 "certifications":["AWS Certified Developer – Associate","Certified Kubernetes Application Developer"],
 "achievements":["Employee of the Quarter – Infosys Q3 2023","Speaker at PyCon India 2022"]},

# ── 3. Python Developer – Senior ───────────────────────────────────────
{"name":"Rahul Verma","email":"rahul.verma@techcorp.com","phone":"+91-9900123456",
 "location":"Mumbai, India","linkedin":"linkedin.com/in/rahulverma",
 "github":"github.com/rahulverma","role_title":"Python Developer",
 "category":"Engineering","experience_level":"Senior",
 "summary":"8 years building large-scale Python systems for e-commerce and fintech. Expert in distributed architectures, performance optimization, and leading cross-functional teams. Open-source contributor with 2K+ GitHub stars.",
 "skills":{"technical":["Python","Django","FastAPI","Kubernetes","Kafka","Elasticsearch","AWS","Terraform","GraphQL","gRPC"],"soft":["System Design","Team Leadership","Stakeholder Management"]},
 "experience":[
   {"company":"Flipkart","title":"Principal Engineer","duration":"Jan 2021 - Present","location":"Bangalore, India","bullets":["Designed catalog search service handling 50M+ queries/day using Elasticsearch","Reduced infrastructure cost by 35% via efficient Kubernetes auto-scaling","Mentored 12 engineers and established Python best-practices guild"]},
   {"company":"Paytm","title":"Senior Engineer","duration":"Jun 2018 - Jan 2021","location":"Noida, India","bullets":["Built payment reconciliation system processing Rs 500Cr+ daily","Led migration from monolith to 15 microservices cutting deployment time by 70%","Established CI/CD pipelines using Jenkins and GitHub Actions"]},
   {"company":"Freshworks","title":"Software Engineer","duration":"Aug 2016 - Jun 2018","location":"Chennai, India","bullets":["Developed CRM automation features used by 10K+ businesses","Implemented webhook delivery system with 99.99% reliability"]}],
 "projects":[{"name":"PySearch OSS Library","description":"High-performance search abstraction layer for Django/FastAPI","tech_stack":["Python","Elasticsearch","Redis"],"link":"github.com/rahulverma/pysearch"},{"name":"Distributed Rate Limiter","description":"Token-bucket rate limiter with Redis cluster support","tech_stack":["Python","Redis","Lua"],"link":"github.com/rahulverma/ratelimiter"}],
 "education":[{"degree":"M.Tech Computer Science","institution":"IIT Bombay","year":"2016","gpa":"9.1/10"}],
 "certifications":["AWS Solutions Architect – Professional","Google Cloud Professional Developer"],
 "achievements":["Tech Lead of the Year – Flipkart 2022","PyCon India keynote speaker 2021","2,400+ GitHub stars on open-source projects"]},

# ── 4. Java Developer – Fresher ────────────────────────────────────────
{"name":"Neha Gupta","email":"neha.gupta@gmail.com","phone":"+91-8877665544",
 "location":"Delhi, India","linkedin":"linkedin.com/in/nehagupta",
 "github":"github.com/nehagupta","role_title":"Java Developer",
 "category":"Engineering","experience_level":"Fresher",
 "summary":"Motivated Java graduate with solid understanding of OOP, Spring Boot basics, and data structures. Completed academic projects in web application development and eager to grow in an enterprise Java environment.",
 "skills":{"technical":["Java","Spring Boot","MySQL","Maven","Git","REST APIs","HTML/CSS","JUnit"],"soft":["Analytical Thinking","Communication","Adaptability"]},
 "experience":[{"company":"CodeLabs Pvt Ltd","title":"Java Developer Intern","duration":"Feb 2024 - Jul 2024","location":"Delhi, India","bullets":["Developed CRUD APIs using Spring Boot for an inventory management system","Created JUnit test cases achieving 80% coverage","Assisted in database design and optimization with MySQL"]}],
 "projects":[{"name":"Library Management System","description":"Full-featured library app with book issue, return, and fine calculation","tech_stack":["Java","Spring Boot","MySQL","Thymeleaf"],"link":"github.com/nehagupta/library-mgmt"},{"name":"Student Grade Portal","description":"Grade tracking portal with role-based access for admins and students","tech_stack":["Java","Servlet","JSP","MySQL"],"link":"github.com/nehagupta/grade-portal"}],
 "education":[{"degree":"B.Tech Information Technology","institution":"DTU Delhi","year":"2024","gpa":"8.2/10"}],
 "certifications":["Java Programming – Oracle","Spring Framework Fundamentals – Udemy"],
 "achievements":["Best Final Year Project Award – DTU 2024","Top 10 – GeeksforGeeks Coding Challenge"]},

# ── 5. Java Developer – Mid-Level ──────────────────────────────────────
{"name":"Siddharth Rao","email":"siddharth.rao@tcs.com","phone":"+91-9123456780",
 "location":"Chennai, India","linkedin":"linkedin.com/in/siddharthrao",
 "github":"github.com/siddharthrao","role_title":"Java Developer",
 "category":"Engineering","experience_level":"Mid-Level",
 "summary":"4 years building enterprise Java applications in banking and insurance domains. Strong expertise in Spring ecosystem, microservices, and Apache Kafka for event-driven architectures.",
 "skills":{"technical":["Java","Spring Boot","Spring Cloud","Hibernate","Apache Kafka","Docker","PostgreSQL","Redis","Jenkins","JUnit/Mockito"],"soft":["Problem Solving","Agile/Scrum","Code Review"]},
 "experience":[
   {"company":"TCS","title":"Systems Engineer – Java","duration":"Apr 2022 - Present","location":"Chennai, India","bullets":["Built microservices for trade settlement system processing 100K+ daily transactions","Implemented event-driven architecture using Apache Kafka reducing system latency by 40%","Conducted technical interviews and onboarded 6 junior developers"]},
   {"company":"Mphasis","title":"Junior Developer","duration":"Aug 2020 - Apr 2022","location":"Bangalore, India","bullets":["Developed insurance policy management APIs using Spring Boot","Integrated third-party payment gateways (Razorpay, PayU)","Improved CI/CD pipeline execution time by 25%"]}],
 "projects":[{"name":"Trade Settlement Engine","description":"High-throughput settlement processing with Kafka streams","tech_stack":["Java","Spring Boot","Kafka","PostgreSQL"],"link":"github.com/siddharthrao/settlement"},{"name":"Claims Processing API","description":"REST API for insurance claims with document verification","tech_stack":["Java","Spring Boot","AWS S3","Redis"],"link":"github.com/siddharthrao/claims-api"}],
 "education":[{"degree":"B.E. Electronics & Communication","institution":"Anna University","year":"2020","gpa":"8.5/10"}],
 "certifications":["Oracle Java SE 11 Certified","Spring Professional Certification"],
 "achievements":["Best Innovation Award – TCS Q2 2023","Published article on Kafka optimization on Medium (5K+ reads)"]},

# ── 6. Java Developer – Senior ─────────────────────────────────────────
{"name":"Ankit Mehta","email":"ankit.mehta@amazon.in","phone":"+91-9988776655",
 "location":"Hyderabad, India","linkedin":"linkedin.com/in/ankitmehta",
 "github":"github.com/ankitmehta","role_title":"Java Developer",
 "category":"Engineering","experience_level":"Senior",
 "summary":"9 years of Java engineering expertise at scale, including distributed systems design, JVM tuning, and leading teams of 10+ engineers. Delivered mission-critical e-commerce and logistics platforms at Amazon.",
 "skills":{"technical":["Java","Spring Boot","AWS","DynamoDB","Kafka","Elasticsearch","gRPC","Kubernetes","JVM Tuning","Terraform"],"soft":["System Design","Engineering Leadership","Cross-team Coordination"]},
 "experience":[
   {"company":"Amazon India","title":"Senior Software Development Engineer","duration":"Sep 2020 - Present","location":"Hyderabad, India","bullets":["Architected order routing service handling 10M+ daily orders during sale events","Reduced P99 latency from 800ms to 120ms via JVM GC tuning and async processing","Built and led a team of 8 engineers across 2 time zones"]},
   {"company":"Walmart Labs","title":"Software Engineer III","duration":"Jun 2017 - Sep 2020","location":"Bangalore, India","bullets":["Developed pricing engine processing 2M+ SKU updates daily","Led platform migration reducing AWS costs by $1.2M annually","Established microservices patterns adopted org-wide"]},
   {"company":"Cognizant","title":"Programmer Analyst","duration":"Jul 2015 - Jun 2017","location":"Pune, India","bullets":["Built retail inventory management APIs for a Fortune 500 client","Improved batch processing speed by 3x through parallel streams"]}],
 "projects":[{"name":"Order Router v2","description":"Event-driven order routing with ML-based fulfillment center selection","tech_stack":["Java","Kafka","DynamoDB","SageMaker"],"link":"github.com/ankitmehta/order-router"},{"name":"JVM Profiler","description":"Open-source JVM profiling agent for production environments","tech_stack":["Java","JVMTI","InfluxDB"],"link":"github.com/ankitmehta/jvm-profiler"}],
 "education":[{"degree":"B.Tech Computer Science","institution":"IIT Kharagpur","year":"2015","gpa":"9.0/10"}],
 "certifications":["AWS Solutions Architect – Professional","Java Champion (nominated)"],
 "achievements":["Amazon Bar Raiser certified","Keynote at JavaOne India 2022","Open-source JVM Profiler – 1.8K GitHub stars"]},

# ── 7. .NET Developer – Fresher ────────────────────────────────────────
{"name":"Divya Pillai","email":"divya.pillai@gmail.com","phone":"+91-8866554433",
 "location":"Kochi, India","linkedin":"linkedin.com/in/divyapillai",
 "github":"github.com/divyapillai","role_title":".NET Developer",
 "category":"Engineering","experience_level":"Fresher",
 "summary":"Enthusiastic .NET graduate skilled in C# and ASP.NET Core fundamentals. Built academic projects involving web APIs and SQL Server. Looking to start a professional career in Microsoft stack development.",
 "skills":{"technical":["C#","ASP.NET Core","SQL Server","Entity Framework","Git","HTML/CSS","Blazor","REST APIs"],"soft":["Detail-Oriented","Team Player","Eager Learner"]},
 "experience":[{"company":"Softsense Technologies","title":".NET Intern","duration":"Jan 2024 - Jun 2024","location":"Kochi, India","bullets":["Developed CRUD modules for HR management system using ASP.NET Core","Wrote stored procedures in SQL Server for payroll calculation","Participated in daily standups and sprint planning meetings"]}],
 "projects":[{"name":"Employee Management Portal","description":"Web portal for HR with leave management and attendance tracking","tech_stack":["C#","ASP.NET Core","SQL Server","Bootstrap"],"link":"github.com/divyapillai/emp-portal"},{"name":"Quiz Application","description":"Online quiz app with timer and leaderboard functionality","tech_stack":["C#","Blazor","SQLite"],"link":"github.com/divyapillai/quiz-app"}],
 "education":[{"degree":"B.Tech Computer Science","institution":"Cochin University of Science and Technology","year":"2024","gpa":"8.0/10"}],
 "certifications":["Microsoft Certified: Azure Fundamentals (AZ-900)","C# Programming – SoloLearn"],
 "achievements":["Best Project – Cochin University Tech Fest 2024","Top 5% in HackerRank C# Assessment"]},

# ── 8. .NET Developer – Mid-Level ──────────────────────────────────────
{"name":"Karan Singh","email":"karan.singh@hcltech.com","phone":"+91-9765432109",
 "location":"Noida, India","linkedin":"linkedin.com/in/karansingh",
 "github":"github.com/karansingh","role_title":".NET Developer",
 "category":"Engineering","experience_level":"Mid-Level",
 "summary":"5 years of .NET development across healthcare and retail domains. Proficient in .NET 6/8, microservices with gRPC, and Azure cloud services. Strong focus on clean architecture and SOLID principles.",
 "skills":{"technical":["C#",".NET 8","ASP.NET Core","Azure","gRPC","SQL Server","Redis","Docker","SignalR","Entity Framework Core"],"soft":["Clean Code Advocate","Agile","Technical Documentation"]},
 "experience":[
   {"company":"HCL Technologies","title":"Software Engineer","duration":"Mar 2022 - Present","location":"Noida, India","bullets":["Built patient management microservices for NHS UK client using .NET 6 and gRPC","Implemented real-time notifications with SignalR for 50K+ concurrent users","Reduced database query time by 50% through EF Core optimizations and indexing"]},
   {"company":"Persistent Systems","title":"Associate Engineer","duration":"Aug 2019 - Mar 2022","location":"Pune, India","bullets":["Developed retail POS integrations using .NET Core Web APIs","Migrated legacy .NET Framework 4.5 apps to .NET 5","Implemented Azure Service Bus for async messaging between services"]}],
 "projects":[{"name":"Patient Portal API","description":"Secure healthcare APIs with HL7 FHIR compliance","tech_stack":["C#","ASP.NET Core","Azure","SQL Server"],"link":"github.com/karansingh/patient-api"},{"name":"Real-time Chat Service","description":"Scalable chat using SignalR and Azure Service Bus","tech_stack":["C#","SignalR","Redis","Azure"],"link":"github.com/karansingh/chat-service"}],
 "education":[{"degree":"B.Tech Information Technology","institution":"Amity University Noida","year":"2019","gpa":"8.3/10"}],
 "certifications":["Microsoft Certified: Azure Developer Associate (AZ-204)","Microsoft Certified: .NET Developer"],
 "achievements":["HCL Star Performer Award 2023","Published .NET performance blog with 8K monthly readers"]},

# ── 9. .NET Developer – Senior ─────────────────────────────────────────
{"name":"Meera Krishnan","email":"meera.k@microsoft.com","phone":"+91-9944332211",
 "location":"Hyderabad, India","linkedin":"linkedin.com/in/meerakrishnan",
 "github":"github.com/meerakrishnan","role_title":".NET Developer",
 "category":"Engineering","experience_level":"Senior",
 "summary":"10 years of expertise in .NET ecosystem building enterprise solutions across BFSI and enterprise SaaS. Architect-level experience with Azure, microservices, and domain-driven design. Led teams delivering $50M+ revenue products.",
 "skills":{"technical":["C#",".NET 8","Azure Service Fabric","Dapr","Cosmos DB","Azure DevOps","Kubernetes","CQRS","Event Sourcing","Terraform"],"soft":["Architecture Design","Team Leadership","Executive Communication"]},
 "experience":[
   {"company":"Microsoft India","title":"Principal Software Engineer","duration":"Jul 2019 - Present","location":"Hyderabad, India","bullets":["Architected Azure-native SaaS platform serving 200+ enterprise customers","Led adoption of Dapr for service mesh reducing cross-service complexity by 60%","Managed team of 15 engineers across 3 product squads"]},
   {"company":"Citi Bank Technology","title":"Senior .NET Developer","duration":"Apr 2016 - Jul 2019","location":"Mumbai, India","bullets":["Built trading platform components handling $2B+ daily volume","Implemented CQRS pattern improving read performance by 200%","Established .NET coding standards adopted across 300-person org"]},
   {"company":"Accenture","title":".NET Developer","duration":"Jun 2014 - Apr 2016","location":"Bangalore, India","bullets":["Developed insurance claims processing system for AXA Group","Migrated legacy VB.NET system to modern .NET stack"]}],
 "projects":[{"name":"Enterprise ESB Framework","description":"Internal .NET-based enterprise service bus reducing integration effort by 70%","tech_stack":["C#","Azure Service Bus","Dapr","Cosmos DB"],"link":"github.com/meerakrishnan/esb-framework"},{"name":"CQRS Toolkit","description":"Open-source .NET library for CQRS/ES patterns","tech_stack":["C#","MediatR","EventStoreDB"],"link":"github.com/meerakrishnan/cqrs-toolkit"}],
 "education":[{"degree":"M.Tech Software Engineering","institution":"JNTU Hyderabad","year":"2014","gpa":"9.2/10"}],
 "certifications":["Microsoft Certified: Azure Solutions Architect Expert","Microsoft MVP – .NET (2021, 2022, 2023)"],
 "achievements":["Microsoft MVP Award – 3 consecutive years","Speaker at .NET Conf 2022","Open-source .NET library – 3.1K GitHub stars"]},

# ── 10. Full-Stack Developer – Fresher ─────────────────────────────────
{"name":"Aditya Kumar","email":"aditya.kumar@gmail.com","phone":"+91-8899001122",
 "location":"Pune, India","linkedin":"linkedin.com/in/adityakumar",
 "github":"github.com/adityakumar","role_title":"Full-Stack Developer",
 "category":"Engineering","experience_level":"Fresher",
 "summary":"Fresh CS graduate with hands-on full-stack project experience using React and Node.js. Comfortable working across the entire stack and passionate about building user-friendly web applications.",
 "skills":{"technical":["JavaScript","React","Node.js","Express","MongoDB","HTML/CSS","Git","Tailwind CSS","REST APIs"],"soft":["Creative Thinking","Fast Learner","Collaboration"]},
 "experience":[{"company":"WebNova Labs","title":"Full-Stack Intern","duration":"Feb 2024 - Jul 2024","location":"Pune, India","bullets":["Built a client feedback portal using React and Node.js from scratch","Integrated Stripe payment gateway for subscription management","Deployed application to AWS EC2 with Nginx reverse proxy"]}],
 "projects":[{"name":"Job Board Platform","description":"Full-stack job portal with real-time notifications and resume parsing","tech_stack":["React","Node.js","MongoDB","Socket.io"],"link":"github.com/adityakumar/job-board"},{"name":"E-Commerce Store","description":"MERN stack online store with cart, checkout, and order tracking","tech_stack":["MongoDB","Express","React","Node.js"],"link":"github.com/adityakumar/mern-store"}],
 "education":[{"degree":"B.Tech Computer Engineering","institution":"Pune University","year":"2024","gpa":"8.6/10"}],
 "certifications":["Meta Front-End Developer – Coursera","MongoDB Developer Certification"],
 "achievements":["1st place – Smart India Hackathon 2023 (Web Track)","Full Scholarship – Masai School Bootcamp"]},

# ── 11. Full-Stack Developer – Mid-Level ───────────────────────────────
{"name":"Sneha Patil","email":"sneha.patil@thoughtworks.com","phone":"+91-9812345670",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/snehapatil",
 "github":"github.com/snehapatil","role_title":"Full-Stack Developer",
 "category":"Engineering","experience_level":"Mid-Level",
 "summary":"5 years of full-stack development with React, TypeScript, and Node.js. Experienced in building SaaS products from 0 to 1 and scaling them to thousands of users. Strong focus on performance and accessibility.",
 "skills":{"technical":["React","TypeScript","Node.js","GraphQL","PostgreSQL","Redis","AWS","Docker","Next.js","Cypress"],"soft":["Product Thinking","Agile","Mentoring"]},
 "experience":[
   {"company":"Thoughtworks","title":"Senior Consultant","duration":"Aug 2022 - Present","location":"Bangalore, India","bullets":["Led front-end architecture for a healthcare SaaS serving 100K+ patients","Improved Core Web Vitals score from 45 to 92 through SSR and code splitting","Mentored 3 junior developers and drove adoption of TypeScript across the project"]},
   {"company":"Zoho Corporation","title":"Software Developer","duration":"Jul 2019 - Aug 2022","location":"Chennai, India","bullets":["Developed CRM dashboards consumed by 500K+ business users","Built reusable React component library reducing dev time by 35%","Integrated 15+ third-party APIs including Salesforce and HubSpot"]}],
 "projects":[{"name":"HealthTrack SaaS","description":"Patient monitoring dashboard with real-time vitals and alerts","tech_stack":["Next.js","GraphQL","PostgreSQL","AWS Lambda"],"link":"github.com/snehapatil/healthtrack"},{"name":"UI Component Library","description":"Accessible React component library with Storybook documentation","tech_stack":["React","TypeScript","Rollup","Storybook"],"link":"github.com/snehapatil/ui-lib"}],
 "education":[{"degree":"B.E. Computer Science","institution":"College of Engineering Pune","year":"2019","gpa":"8.8/10"}],
 "certifications":["AWS Certified Developer – Associate","Google UX Design Certificate"],
 "achievements":["Thoughtworks Spotlight Award Q1 2023","Conference talk – ReactConf India 2022"]},

# ── 12. Full-Stack Developer – Senior ──────────────────────────────────
{"name":"Vikram Bhatia","email":"vikram.bhatia@google.com","phone":"+91-9700112233",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/vikrambhatia",
 "github":"github.com/vikrambhatia","role_title":"Full-Stack Developer",
 "category":"Engineering","experience_level":"Senior",
 "summary":"9 years of full-stack engineering at Google and fast-growing startups. Expert in scalable front-end architectures, Node.js microservices, and developer tooling. Led 3 successful product launches with 1M+ users.",
 "skills":{"technical":["React","TypeScript","Node.js","Go","GCP","Kubernetes","GraphQL","Redis","BigQuery","Webpack"],"soft":["Technical Vision","Cross-functional Leadership","Open Source Contribution"]},
 "experience":[
   {"company":"Google India","title":"Senior Software Engineer, L5","duration":"Mar 2020 - Present","location":"Bangalore, India","bullets":["Built Google Workspace add-ons used by 5M+ enterprise users","Led migration of legacy AngularJS codebase to React, improving performance 4x","Designed API gateway handling 100M+ daily requests"]},
   {"company":"Swiggy","title":"Staff Engineer","duration":"Jan 2017 - Mar 2020","location":"Bangalore, India","bullets":["Architected real-time order tracking system across mobile and web","Scaled front-end platform from 100K to 5M daily active users","Established engineering blog driving 50K+ monthly readers"]},
   {"company":"InMobi","title":"Software Engineer","duration":"Jul 2015 - Jan 2017","location":"Bangalore, India","bullets":["Developed ad-serving dashboard processing 500M+ daily impressions","Built A/B testing framework used across 20+ product teams"]}],
 "projects":[{"name":"Micro Frontend Framework","description":"OSS framework for composing independent React apps","tech_stack":["React","Webpack Module Federation","TypeScript"],"link":"github.com/vikrambhatia/micro-fe"},{"name":"GQL Gateway","description":"Auto-generated GraphQL gateway from REST APIs","tech_stack":["Node.js","GraphQL","Redis"],"link":"github.com/vikrambhatia/gql-gateway"}],
 "education":[{"degree":"B.Tech Computer Science","institution":"IIT Delhi","year":"2015","gpa":"9.3/10"}],
 "certifications":["Google Cloud Professional Cloud Architect","CKA – Certified Kubernetes Administrator"],
 "achievements":["Google Eng Excellence Award 2022","React India keynote 2021","Micro Frontend Framework – 4.2K GitHub stars"]},

# ── 13. Mobile Developer iOS – Mid-Level ───────────────────────────────
{"name":"Tanvi Shah","email":"tanvi.shah@swiggy.in","phone":"+91-9823456701",
 "location":"Mumbai, India","linkedin":"linkedin.com/in/tanvishah",
 "github":"github.com/tanvishah","role_title":"Mobile Developer (iOS)",
 "category":"Engineering","experience_level":"Mid-Level",
 "summary":"4 years of iOS development delivering consumer-facing apps with millions of downloads. Proficient in Swift, SwiftUI, and Combine. Strong focus on performance, smooth animations, and accessibility.",
 "skills":{"technical":["Swift","SwiftUI","UIKit","Combine","Core Data","XCTest","Firebase","REST APIs","Instruments","App Store Connect"],"soft":["User Empathy","Detail Orientation","Collaboration"]},
 "experience":[
   {"company":"Swiggy","title":"iOS Engineer","duration":"Jun 2022 - Present","location":"Mumbai, India","bullets":["Developed new restaurant discovery feature increasing order conversion by 18%","Optimized app launch time from 3.2s to 1.1s using lazy loading","Published 6 app updates with zero critical crashes"]},
   {"company":"Nykaa","title":"Junior iOS Developer","duration":"Aug 2020 - Jun 2022","location":"Mumbai, India","bullets":["Built beauty product AR try-on feature using ARKit","Migrated UIKit views to SwiftUI reducing code by 40%","Maintained 4.8-star App Store rating"]}],
 "projects":[{"name":"FitTrack iOS App","description":"Workout tracking app with HealthKit integration and custom animations","tech_stack":["Swift","SwiftUI","HealthKit","Core Data"],"link":"github.com/tanvishah/fittrack"},{"name":"AR Beauty App","description":"Real-time makeup AR try-on using ARKit","tech_stack":["Swift","ARKit","Vision","Core ML"],"link":"github.com/tanvishah/ar-beauty"}],
 "education":[{"degree":"B.E. Information Technology","institution":"Mumbai University","year":"2020","gpa":"8.4/10"}],
 "certifications":["Apple Developer Certification","SwiftUI Masterclass – Udemy"],
 "achievements":["App featured in App Store 'Best New Apps' – 2021","Speaker at SwiftConf India 2022"]},

# ── 14. Mobile Developer Android – Mid-Level ───────────────────────────
{"name":"Rohan Desai","email":"rohan.desai@ola.com","phone":"+91-9712345678",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/rohandesai",
 "github":"github.com/rohandesai","role_title":"Mobile Developer (Android)",
 "category":"Engineering","experience_level":"Mid-Level",
 "summary":"5 years building Android apps with Kotlin and Jetpack Compose. Experienced in complex navigation flows, offline-first architectures, and performance tuning for low-end devices.",
 "skills":{"technical":["Kotlin","Jetpack Compose","Android SDK","Room","Retrofit","Hilt","Coroutines","Firebase","CI/CD","Material Design 3"],"soft":["User-Centric Design","Systematic Testing","Agile"]},
 "experience":[
   {"company":"Ola Cabs","title":"Senior Android Engineer","duration":"Jul 2022 - Present","location":"Bangalore, India","bullets":["Built driver app features used by 2M+ drivers across India","Implemented offline mode with Room database and sync engine","Reduced app size by 30% through ProGuard optimizations and WebP images"]},
   {"company":"Practo","title":"Android Developer","duration":"Sep 2019 - Jul 2022","location":"Bangalore, India","bullets":["Developed video consultation feature during COVID-19 within 3 weeks","Improved app rating from 3.9 to 4.6 by fixing top user-reported issues","Built reusable Kotlin Multiplatform modules shared with iOS team"]}],
 "projects":[{"name":"Offline Navigation SDK","description":"Turn-by-turn navigation with offline maps for low-connectivity regions","tech_stack":["Kotlin","Android SDK","SQLite","MapLibre"],"link":"github.com/rohandesai/offline-nav"},{"name":"Compose UI Kit","description":"Custom Material 3 components for enterprise Android apps","tech_stack":["Kotlin","Jetpack Compose","Material 3"],"link":"github.com/rohandesai/compose-kit"}],
 "education":[{"degree":"B.Tech Electronics & Telecom","institution":"VJTI Mumbai","year":"2019","gpa":"8.0/10"}],
 "certifications":["Associate Android Developer – Google","Kotlin Coroutines – JetBrains"],
 "achievements":["Google Play Indie Award Nominee 2022","Android GDE (Google Developer Expert) community mentor"]},

# ── 15. DevOps Engineer – Fresher ──────────────────────────────────────
{"name":"Pooja Iyer","email":"pooja.iyer@gmail.com","phone":"+91-9654321098",
 "location":"Hyderabad, India","linkedin":"linkedin.com/in/poojaiyer",
 "github":"github.com/poojaiyer","role_title":"DevOps Engineer",
 "category":"DevOps & Cloud","experience_level":"Fresher",
 "summary":"Recent IT graduate with hands-on experience in Linux administration, Docker containerization, and CI/CD pipeline automation. Completed multiple cloud practitioner certifications and eager to contribute to DevOps teams.",
 "skills":{"technical":["Linux","Docker","Git","Jenkins","AWS (basic)","Bash Scripting","YAML","Nginx","Ansible (basics)"],"soft":["Troubleshooting","Documentation","Continuous Learning"]},
 "experience":[{"company":"Accenture","title":"DevOps Intern","duration":"Jan 2024 - Jun 2024","location":"Hyderabad, India","bullets":["Set up Jenkins CI/CD pipelines for 3 microservices teams","Containerized 5 legacy apps using Docker reducing environment issues","Created Bash automation scripts saving 4 hours of weekly manual work"]}],
 "projects":[{"name":"CI/CD Pipeline Template","description":"Reusable Jenkins pipeline templates for Node.js and Python apps","tech_stack":["Jenkins","Docker","Git","Bash"],"link":"github.com/poojaiyer/cicd-templates"},{"name":"Server Monitoring Dashboard","description":"Prometheus + Grafana monitoring setup for college lab servers","tech_stack":["Prometheus","Grafana","Linux","Docker"],"link":"github.com/poojaiyer/monitoring"}],
 "education":[{"degree":"B.Tech Information Technology","institution":"JNTU Hyderabad","year":"2024","gpa":"8.1/10"}],
 "certifications":["AWS Cloud Practitioner","Docker Certified Associate – Study Path"],
 "achievements":["Best Intern Project – Accenture Hyderabad 2024","Linux Foundation Scholarship Recipient"]},

# ── 16. DevOps Engineer – Mid-Level ────────────────────────────────────
{"name":"Suresh Nambiar","email":"suresh.nambiar@razorpay.com","phone":"+91-9555666777",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/sureshnambiar",
 "github":"github.com/sureshnambiar","role_title":"DevOps Engineer",
 "category":"DevOps & Cloud","experience_level":"Mid-Level",
 "summary":"5 years of DevOps experience at high-growth fintech companies. Expert in Kubernetes, Terraform, and building zero-downtime deployment pipelines. Reduced infrastructure costs by 40% through right-sizing and automation.",
 "skills":{"technical":["Kubernetes","Terraform","AWS","Helm","ArgoCD","Prometheus","Grafana","GitLab CI","Python","ELK Stack"],"soft":["Reliability Mindset","Incident Management","Knowledge Sharing"]},
 "experience":[
   {"company":"Razorpay","title":"DevOps Engineer","duration":"May 2022 - Present","location":"Bangalore, India","bullets":["Managed Kubernetes clusters processing 10M+ payment transactions daily","Implemented GitOps with ArgoCD achieving fully declarative infrastructure","Built on-call runbooks reducing MTTR from 45 minutes to 8 minutes"]},
   {"company":"Urban Company","title":"Cloud Engineer","duration":"Aug 2019 - May 2022","location":"Gurugram, India","bullets":["Migrated on-premise workloads to AWS saving Rs 1.2Cr annually","Automated infrastructure provisioning with Terraform for 50+ environments","Set up ELK stack for centralized logging across 30 microservices"]}],
 "projects":[{"name":"GitOps Platform","description":"ArgoCD-based GitOps platform with multi-cluster support","tech_stack":["Kubernetes","ArgoCD","Helm","Terraform"],"link":"github.com/sureshnambiar/gitops"},{"name":"Cost Optimizer","description":"Automated AWS cost optimization tool with scheduled scaling","tech_stack":["Python","AWS","Lambda","Cost Explorer"],"link":"github.com/sureshnambiar/cost-opt"}],
 "education":[{"degree":"B.Tech Computer Science","institution":"NIT Calicut","year":"2019","gpa":"8.5/10"}],
 "certifications":["CKA – Certified Kubernetes Administrator","AWS Solutions Architect – Associate","HashiCorp Terraform Associate"],
 "achievements":["DevOps Engineer of the Year – Razorpay 2023","Speaker at KubeCon India 2022"]},

# ── 17. DevOps Engineer – Senior ───────────────────────────────────────
{"name":"Amit Joshi","email":"amit.joshi@flipkart.com","phone":"+91-9600789012",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/amitjoshi",
 "github":"github.com/amitjoshi","role_title":"DevOps Engineer",
 "category":"DevOps & Cloud","experience_level":"Senior",
 "summary":"10 years leading platform engineering and DevOps at Flipkart and HDFC Tech. Built and operated Kubernetes platforms serving 100M+ users. Expert in SRE practices, cost optimization, and building high-performing DevOps cultures.",
 "skills":{"technical":["Kubernetes","AWS/GCP","Terraform","Istio","Prometheus/Grafana","Kafka","ArgoCD","Ansible","Python","FinOps"],"soft":["Platform Vision","SRE Practices","Team Building"]},
 "experience":[
   {"company":"Flipkart","title":"Principal DevOps Engineer","duration":"Jan 2020 - Present","location":"Bangalore, India","bullets":["Designed multi-region Kubernetes platform handling 500K+ RPS during Big Billion Days","Achieved 99.999% uptime SLA through chaos engineering and automated failover","Built DevOps Center of Excellence coaching 200+ engineers"]},
   {"company":"HDFC Bank Technology","title":"Senior DevOps Lead","duration":"Jun 2016 - Jan 2020","location":"Mumbai, India","bullets":["Established cloud-first strategy migrating 80% workloads to AWS in 18 months","Implemented FinOps practices saving $3M annually","Built incident management framework reducing P1 incidents by 70%"]},
   {"company":"Sapient Corporation","title":"DevOps Engineer","duration":"Aug 2014 - Jun 2016","location":"Gurgaon, India","bullets":["Set up Jenkins-based CI/CD for 15 development teams","Automated infrastructure provisioning reducing setup time from days to minutes"]}],
 "projects":[{"name":"Platform-as-a-Service Framework","description":"Internal PaaS on Kubernetes with self-service developer portal","tech_stack":["Kubernetes","Backstage","Crossplane","Terraform"],"link":"github.com/amitjoshi/paas-framework"},{"name":"FinOps Toolkit","description":"Open-source AWS cost optimization and allocation toolkit","tech_stack":["Python","AWS","Terraform","Grafana"],"link":"github.com/amitjoshi/finops"}],
 "education":[{"degree":"B.E. Information Technology","institution":"Pune University","year":"2014","gpa":"8.7/10"}],
 "certifications":["CKA + CKAD + CKS","AWS DevOps Engineer – Professional","Google SRE Certificate"],
 "achievements":["Flipkart Platform Engineering Award 2022","KubeCon keynote speaker 2021","FinOps Toolkit – 2.7K GitHub stars"]},

# ── 18. AI/ML Engineer – Fresher ───────────────────────────────────────
{"name":"Shreya Agarwal","email":"shreya.agarwal@gmail.com","phone":"+91-9765012345",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/shreyaagarwal",
 "github":"github.com/shreyaagarwal","role_title":"AI/ML Engineer",
 "category":"AI & Data","experience_level":"Fresher",
 "summary":"AI/ML enthusiast with strong foundations in Python, scikit-learn, and deep learning. Published ML research as an undergraduate and completed Kaggle competitions. Looking to apply ML skills to real-world product problems.",
 "skills":{"technical":["Python","scikit-learn","TensorFlow","PyTorch","Pandas","NumPy","SQL","Jupyter","Git","Hugging Face"],"soft":["Research Mindset","Critical Thinking","Communication"]},
 "experience":[{"company":"Fractal Analytics","title":"ML Intern","duration":"Feb 2024 - Jul 2024","location":"Bangalore, India","bullets":["Built churn prediction model achieving 84% accuracy for telecom client","Created feature engineering pipeline reducing model training time by 40%","Deployed model as REST API using FastAPI on AWS EC2"]}],
 "projects":[{"name":"Sentiment Analysis Engine","description":"BERT-based sentiment classifier for product reviews with 92% accuracy","tech_stack":["Python","Hugging Face","FastAPI","Docker"],"link":"github.com/shreyaagarwal/sentiment"},{"name":"Image Classifier","description":"Custom CNN for plant disease detection with 89% test accuracy","tech_stack":["Python","PyTorch","OpenCV","Streamlit"],"link":"github.com/shreyaagarwal/plant-disease"}],
 "education":[{"degree":"B.Tech Computer Science (AI Specialization)","institution":"PES University Bangalore","year":"2024","gpa":"9.0/10"}],
 "certifications":["Deep Learning Specialization – Coursera (Andrew Ng)","TensorFlow Developer Certificate – Google"],
 "achievements":["Kaggle Competitions Expert (Top 5%)","Best UG Thesis – PES University 2024","Published paper in IEEE ICML Student Workshop"]},

# ── 19. AI/ML Engineer – Mid-Level ─────────────────────────────────────
{"name":"Nikhil Jain","email":"nikhil.jain@mu-sigma.com","phone":"+91-9811122233",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/nikhiljain",
 "github":"github.com/nikhiljain","role_title":"AI/ML Engineer",
 "category":"AI & Data","experience_level":"Mid-Level",
 "summary":"5 years building and deploying production ML systems for FMCG, retail, and finance clients. Strong expertise in MLOps, feature stores, and LLM fine-tuning. Delivered models generating $20M+ in quantifiable business value.",
 "skills":{"technical":["Python","PyTorch","XGBoost","MLflow","Kubeflow","SageMaker","Spark","Feature Stores","LangChain","Databricks"],"soft":["Business Acumen","Stakeholder Communication","Research-to-Production"]},
 "experience":[
   {"company":"Mu Sigma","title":"Decision Scientist","duration":"Sep 2022 - Present","location":"Bangalore, India","bullets":["Built demand forecasting model reducing inventory waste by 25% for top FMCG client","Fine-tuned LLaMA-2 for customer support automation cutting response time by 60%","Established ML platform with MLflow and Kubeflow serving 15 models in production"]},
   {"company":"Tiger Analytics","title":"Senior Analyst","duration":"Jul 2019 - Sep 2022","location":"Chennai, India","bullets":["Developed credit risk model improving bank loan approval accuracy by 18%","Built real-time fraud detection system with 99.2% precision","Mentored team of 4 analysts on model development best practices"]}],
 "projects":[{"name":"LLM Customer Support Bot","description":"Fine-tuned LLaMA-2 chatbot with RAG for enterprise customer support","tech_stack":["Python","LangChain","Pinecone","FastAPI"],"link":"github.com/nikhiljain/llm-support"},{"name":"Demand Forecasting Pipeline","description":"Multi-horizon time series forecasting with automated retraining","tech_stack":["Python","Prophet","MLflow","Kubeflow"],"link":"github.com/nikhiljain/forecasting"}],
 "education":[{"degree":"M.Tech Data Science","institution":"IISc Bangalore","year":"2019","gpa":"8.9/10"}],
 "certifications":["AWS Certified ML Specialty","Databricks Certified ML Professional"],
 "achievements":["Best Data Scientist – Mu Sigma 2023","Published 2 papers in NeurIPS ML Workshop"]},

# ── 20. AI/ML Engineer – Senior ────────────────────────────────────────
{"name":"Deepa Menon","email":"deepa.menon@google.com","phone":"+91-9922334455",
 "location":"Hyderabad, India","linkedin":"linkedin.com/in/deepamenon",
 "github":"github.com/deepamenon","role_title":"AI/ML Engineer",
 "category":"AI & Data","experience_level":"Senior",
 "summary":"10 years of ML research and engineering at Google DeepMind and top AI startups. Published 15 papers with 500+ citations. Led teams building state-of-the-art NLP and recommendation systems at billion-user scale.",
 "skills":{"technical":["Python","JAX","PyTorch","TensorFlow","Vertex AI","TPUs","Transformers","Reinforcement Learning","Distributed Training","Ray"],"soft":["Research Leadership","Cross-org Collaboration","Technical Mentoring"]},
 "experience":[
   {"company":"Google DeepMind","title":"Senior Research Engineer","duration":"Jan 2020 - Present","location":"London/Hyderabad","bullets":["Led development of large-scale recommendation model serving 2B+ YouTube users","Improved model quality by 12% through novel multi-task learning approach","Managed team of 8 ML engineers across India and UK"]},
   {"company":"Ola Electric (AI Lab)","title":"Principal ML Engineer","duration":"Mar 2016 - Jan 2020","location":"Bangalore, India","bullets":["Built route optimization engine saving Rs 200Cr in fuel costs annually","Developed driver behavior prediction model deployed on 1M+ devices","Established AI Lab from 0 to 25-person team"]},
   {"company":"Yahoo Labs India","title":"Research Scientist","duration":"Aug 2014 - Mar 2016","location":"Bangalore, India","bullets":["Published 6 papers on CTR prediction and online learning","Built real-time bidding system for Yahoo's ad exchange"]}],
 "projects":[{"name":"Efficient Transformer","description":"Research on efficient attention mechanisms for long-context models","tech_stack":["JAX","TPU","Python","Transformers"],"link":"github.com/deepamenon/efficient-transformer"},{"name":"RL Highway Planner","description":"Reinforcement learning-based autonomous driving path planner","tech_stack":["Python","Ray RLlib","PyTorch","Gym"],"link":"github.com/deepamenon/rl-planner"}],
 "education":[{"degree":"Ph.D. Machine Learning","institution":"IIT Madras","year":"2014","gpa":"9.5/10"}],
 "certifications":["Google Brain Research Residency (2020)","NeurIPS Reviewer"],
 "achievements":["15 papers published (500+ citations)","NeurIPS Best Paper Honorable Mention 2021","TEDx talk on AI Ethics – 200K views"]},

# ── 21. Data Engineer – Fresher ────────────────────────────────────────
{"name":"Harish Reddy","email":"harish.reddy@gmail.com","phone":"+91-9700001111",
 "location":"Hyderabad, India","linkedin":"linkedin.com/in/harishreddy",
 "github":"github.com/harishreddy","role_title":"Data Engineer",
 "category":"AI & Data","experience_level":"Fresher",
 "summary":"Data engineering fresher with solid SQL skills, Python proficiency, and project experience in ETL pipeline development. Familiar with Apache Spark and cloud data warehouses. Eager to build robust data infrastructure.",
 "skills":{"technical":["Python","SQL","Apache Spark","Pandas","PostgreSQL","Airflow (basics)","BigQuery","Git","Excel","Tableau"],"soft":["Analytical Mindset","Attention to Detail","Documentation"]},
 "experience":[{"company":"Deloitte India","title":"Data Engineering Intern","duration":"Jan 2024 - Jun 2024","location":"Hyderabad, India","bullets":["Built ETL pipeline ingesting 5GB+ daily data from 10 source systems","Created data quality checks reducing reporting errors by 90%","Developed SQL stored procedures for automated weekly business reports"]}],
 "projects":[{"name":"Sales Analytics Pipeline","description":"End-to-end ETL pipeline from MySQL to BigQuery with Airflow orchestration","tech_stack":["Python","Apache Airflow","BigQuery","SQL"],"link":"github.com/harishreddy/sales-pipeline"},{"name":"Twitter Trend Analyzer","description":"Real-time tweet ingestion and trend analysis using Kafka and Spark","tech_stack":["Python","Kafka","PySpark","Redis"],"link":"github.com/harishreddy/twitter-trends"}],
 "education":[{"degree":"B.Tech Computer Science","institution":"JNTU Hyderabad","year":"2024","gpa":"8.3/10"}],
 "certifications":["Google Data Analytics Professional Certificate","dbt Fundamentals"],
 "achievements":["Winner – Data Hack 2023 (National Level)","Dean's Merit List 2022-23"]},

# ── 22. Data Engineer – Mid-Level ──────────────────────────────────────
{"name":"Lakshmi Venkat","email":"lakshmi.venkat@accenture.com","phone":"+91-9111222333",
 "location":"Chennai, India","linkedin":"linkedin.com/in/lakshmvenkat",
 "github":"github.com/lakshmvenkat","role_title":"Data Engineer",
 "category":"AI & Data","experience_level":"Mid-Level",
 "summary":"4 years building scalable data platforms for retail and logistics clients. Expert in modern data stack (dbt, Airflow, Snowflake) and streaming architectures. Reduced data pipeline failures by 95% through robust monitoring.",
 "skills":{"technical":["Python","Apache Spark","Kafka","Airflow","dbt","Snowflake","AWS Glue","Terraform","SQL","Delta Lake"],"soft":["Data Quality Mindset","Stakeholder Management","Agile"]},
 "experience":[
   {"company":"Accenture","title":"Data Engineer","duration":"Apr 2022 - Present","location":"Chennai, India","bullets":["Built real-time supply chain data platform processing 500GB+ daily for a logistics client","Implemented data observability with Monte Carlo reducing pipeline incidents by 80%","Migrated 50+ legacy SSIS jobs to Airflow saving 40 engineering hours weekly"]},
   {"company":"Mindtree","title":"Junior Data Engineer","duration":"Jul 2020 - Apr 2022","location":"Bangalore, India","bullets":["Developed data warehouse on Snowflake serving 200+ retail stores","Built dbt models for customer 360 analytics reducing query time by 60%","Automated data quality testing with Great Expectations"]}],
 "projects":[{"name":"Real-time Supply Chain Platform","description":"Kafka + Spark streaming pipeline for logistics event processing","tech_stack":["Kafka","PySpark","Delta Lake","Airflow","Snowflake"],"link":"github.com/lakshmvenkat/supply-chain"},{"name":"dbt Analytics Hub","description":"Standardized dbt project template with testing and documentation","tech_stack":["dbt","Snowflake","Python","GitHub Actions"],"link":"github.com/lakshmvenkat/dbt-hub"}],
 "education":[{"degree":"B.Tech Information Technology","institution":"Anna University","year":"2020","gpa":"8.6/10"}],
 "certifications":["dbt Certified Developer","Snowflake SnowPro Core","Apache Airflow Fundamentals – Astronomer"],
 "achievements":["Accenture Tech Innovator Award 2023","Data Engineering Weekly newsletter contributor (10K+ subscribers)"]},

# ── 23. Data Engineer – Senior ─────────────────────────────────────────
{"name":"Vijay Krishnamurthy","email":"vijay.k@databricks.com","phone":"+91-9988001122",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/vijaykm",
 "github":"github.com/vijaykm","role_title":"Data Engineer",
 "category":"AI & Data","experience_level":"Senior",
 "summary":"10 years building enterprise data platforms at Databricks, Myntra, and consulting roles. Architected data lakehouses processing petabytes of data. Led data platform teams of 15+ engineers.",
 "skills":{"technical":["Apache Spark","Delta Lake","Databricks","Kafka","AWS/GCP","Terraform","Python","dbt","Flink","Iceberg"],"soft":["Data Architecture","Team Leadership","Vendor Negotiation"]},
 "experience":[
   {"company":"Databricks","title":"Senior Solutions Architect","duration":"Sep 2021 - Present","location":"Bangalore, India","bullets":["Designed lakehouse architectures for Fortune 500 clients processing 10PB+ data","Led pre-sales engineering for $50M+ Databricks contracts in APAC","Developed reference architectures adopted by 100+ enterprise clients"]},
   {"company":"Myntra","title":"Principal Data Engineer","duration":"Mar 2017 - Sep 2021","location":"Bangalore, India","bullets":["Built real-time recommendation data pipeline processing 200M+ user events daily","Led migration from Hadoop to Spark/Delta Lake cutting processing costs by 55%","Managed team of 12 data engineers across platform and product teams"]},
   {"company":"Mu Sigma","title":"Data Engineer","duration":"Aug 2014 - Mar 2017","location":"Bangalore, India","bullets":["Developed retail analytics pipelines for Walmart and Coca-Cola","Built automated data quality framework used across 20+ client projects"]}],
 "projects":[{"name":"Lakehouse Reference Architecture","description":"Open-source reference implementation of Delta Lake best practices","tech_stack":["Spark","Delta Lake","Databricks","Terraform"],"link":"github.com/vijaykm/lakehouse-ref"},{"name":"Stream Processor Framework","description":"Kafka + Flink streaming framework for real-time ML feature computation","tech_stack":["Flink","Kafka","Python","Delta Lake"],"link":"github.com/vijaykm/stream-processor"}],
 "education":[{"degree":"M.Tech Data Engineering","institution":"IIIT Hyderabad","year":"2014","gpa":"9.0/10"}],
 "certifications":["Databricks Certified Data Engineer Professional","Apache Spark Developer Certification","AWS Big Data Specialty"],
 "achievements":["DataEngConf keynote 2022","Lakehouse reference architecture used by 1,200+ organizations","Forbes 40 Under 40 Technology – 2023"]},

# ── 24. QA Tester Manual – Fresher ─────────────────────────────────────
{"name":"Swati Kulkarni","email":"swati.kulkarni@gmail.com","phone":"+91-9543210987",
 "location":"Pune, India","linkedin":"linkedin.com/in/swatikulkarni",
 "github":"github.com/swatikulkarni","role_title":"QA Tester (Manual)",
 "category":"QA & Testing","experience_level":"Fresher",
 "summary":"Detail-oriented CS graduate with strong foundation in manual testing methodologies, SDLC, and bug reporting. Completed ISTQB Foundation certification and eager to build a QA career in Agile teams.",
 "skills":{"technical":["Manual Testing","Test Case Design","JIRA","Postman","SQL","API Testing","Regression Testing","Smoke Testing","Bug Reporting"],"soft":["Attention to Detail","Methodical Thinking","Clear Communication"]},
 "experience":[{"company":"Persistent Systems","title":"QA Intern","duration":"Jan 2024 - Jun 2024","location":"Pune, India","bullets":["Executed 500+ test cases for e-commerce platform feature releases","Identified and documented 80+ bugs with clear reproduction steps in JIRA","Performed API testing using Postman for payment gateway integration"]}],
 "projects":[{"name":"Banking App Test Suite","description":"Comprehensive test plan and test cases for a digital banking app (academic project)","tech_stack":["Excel","JIRA","TestRail","Postman"],"link":"github.com/swatikulkarni/bank-test-suite"},{"name":"E-commerce Test Coverage","description":"Regression and smoke test suite for an open-source e-commerce project","tech_stack":["Manual Testing","Postman","JIRA"],"link":"github.com/swatikulkarni/ecom-tests"}],
 "education":[{"degree":"B.E. Computer Science","institution":"Savitribai Phule Pune University","year":"2024","gpa":"7.9/10"}],
 "certifications":["ISTQB Foundation Level Certified","Postman Student Expert"],
 "achievements":["Best QA Intern – Persistent Systems 2024","100% test execution rate with zero critical escapes"]},

# ── 25. QA Automation Engineer – Mid-Level ─────────────────────────────
{"name":"Ravi Shankar","email":"ravi.shankar@capgemini.com","phone":"+91-9432187654",
 "location":"Pune, India","linkedin":"linkedin.com/in/ravishankar",
 "github":"github.com/ravishankar","role_title":"Automation QA Engineer",
 "category":"QA & Testing","experience_level":"Mid-Level",
 "summary":"5 years of test automation expertise across web, mobile, and API layers. Built automation frameworks from scratch reducing regression time by 80%. Strong in Selenium, Cypress, and Appium.",
 "skills":{"technical":["Selenium WebDriver","Cypress","Appium","Python","Java","REST Assured","JIRA","Jenkins","Docker","Allure Reports"],"soft":["Framework Design","Process Improvement","Agile/Scrum"]},
 "experience":[
   {"company":"Capgemini","title":"Senior QA Engineer","duration":"Mar 2022 - Present","location":"Pune, India","bullets":["Built Cypress automation framework covering 1,200+ test cases for UK banking client","Reduced regression testing time from 5 days to 4 hours through full automation","Integrated test suite with Jenkins CI/CD running on every PR merge"]},
   {"company":"Zensar Technologies","title":"QA Engineer","duration":"Jul 2019 - Mar 2022","location":"Pune, India","bullets":["Developed Appium mobile test suite for iOS and Android apps","Created Page Object Model framework reducing test maintenance effort by 50%","Trained 6 manual QA engineers in automation basics"]}],
 "projects":[{"name":"Cypress E2E Framework","description":"Production-grade Cypress framework with custom commands, fixtures, and CI integration","tech_stack":["Cypress","JavaScript","Jenkins","Allure"],"link":"github.com/ravishankar/cypress-framework"},{"name":"API Test Suite","description":"Comprehensive REST Assured test suite for microservices","tech_stack":["Java","REST Assured","TestNG","Maven"],"link":"github.com/ravishankar/api-tests"}],
 "education":[{"degree":"B.Tech Computer Science","institution":"Pune University","year":"2019","gpa":"8.2/10"}],
 "certifications":["ISTQB Advanced Test Automation Engineer","Cypress.io Certified"],
 "achievements":["Zero production bugs for 6 consecutive releases","Capgemini Innovator Award 2023"]},

# ── 26. Product Manager – Mid-Level ────────────────────────────────────
{"name":"Ayesha Farooqui","email":"ayesha.farooqui@amazon.in","phone":"+91-9777888999",
 "location":"Delhi, India","linkedin":"linkedin.com/in/ayeshafarooqui",
 "github":"github.com/ayeshafarooqui","role_title":"Product Manager",
 "category":"Product & Business","experience_level":"Mid-Level",
 "summary":"5 years of product management experience building consumer fintech and e-commerce products. Data-driven PM who shipped 12+ features impacting 5M+ users. Strong in product discovery, A/B testing, and cross-functional collaboration.",
 "skills":{"technical":["Product Roadmapping","A/B Testing","SQL","Amplitude","Mixpanel","JIRA","Figma","User Research","PRD Writing","OKRs"],"soft":["Stakeholder Alignment","Data-Driven Decision Making","Customer Empathy"]},
 "experience":[
   {"company":"Amazon India","title":"Product Manager","duration":"Aug 2022 - Present","location":"Delhi, India","bullets":["Launched Amazon Pay Later feature growing active users by 45% in 6 months","Drove checkout conversion improvement from 68% to 79% through UX A/B tests","Managed roadmap across 3 engineering teams and 2 design partners"]},
   {"company":"PhonePe","title":"Associate Product Manager","duration":"Jun 2019 - Aug 2022","location":"Bangalore, India","bullets":["Built UPI autopay feature now used by 8M+ subscribers","Reduced KYC drop-off by 35% through redesigned onboarding flow","Defined product metrics dashboard used by C-suite for weekly reviews"]}],
 "projects":[{"name":"Pay Later Feature","description":"Buy Now Pay Later integration with risk scoring and UPI mandate","tech_stack":["Figma","SQL","Amplitude","PRD"],"link":"linkedin.com/in/ayeshafarooqui"},{"name":"UPI Autopay","description":"Subscription payment product with smart retry and notification system","tech_stack":["Figma","JIRA","Mixpanel"],"link":"linkedin.com/in/ayeshafarooqui"}],
 "education":[{"degree":"MBA (Finance & Marketing)","institution":"IIM Lucknow","year":"2019","gpa":"3.8/4.0"}],
 "certifications":["Pragmatic Marketing Certified","Product School – Product Analytics Certificate"],
 "achievements":["Amazon Best New PM 2023","PhonePe Product Impact Award 2021","Featured in YourStory 30 Under 30"]},

# ── 27. Product Manager – Senior ───────────────────────────────────────
{"name":"Sameer Khanna","email":"sameer.khanna@google.com","phone":"+91-9666555444",
 "location":"Hyderabad, India","linkedin":"linkedin.com/in/sameerkhanna",
 "github":"github.com/sameerkhanna","role_title":"Product Manager",
 "category":"Product & Business","experience_level":"Senior",
 "summary":"10 years leading product at Google, Snapdeal, and high-growth SaaS startups. Built products used by 100M+ users. Expert in 0-to-1 product development, platform thinking, and building world-class PM teams.",
 "skills":{"technical":["Product Strategy","Market Research","SQL","A/B Testing","OKR Framework","Roadmapping","Design Thinking","Platform Products","P&L Management","GTM Strategy"],"soft":["Visionary Thinking","Executive Presence","Team Building"]},
 "experience":[
   {"company":"Google India","title":"Senior Product Manager","duration":"Apr 2019 - Present","location":"Hyderabad, India","bullets":["Led Google Pay's merchant platform growing from 100K to 5M merchants","Drove 300% revenue growth through new B2B payment products","Built and managed team of 6 Associate PMs"]},
   {"company":"Snapdeal","title":"Director of Product","duration":"Jan 2015 - Apr 2019","location":"Delhi, India","bullets":["Revamped seller dashboard increasing seller NPS from 32 to 68","Launched Snapdeal Pro subscription generating Rs 50Cr annual revenue","Established PM guild with standardized hiring and career framework"]},
   {"company":"InMobi","title":"Product Manager","duration":"Jul 2013 - Jan 2015","location":"Bangalore, India","bullets":["Built mobile ad product generating $15M ARR","Designed self-serve advertiser platform reducing onboarding from 5 days to 1 hour"]}],
 "projects":[{"name":"Merchant Platform","description":"Self-serve merchant onboarding and analytics platform for Google Pay","tech_stack":["Figma","SQL","Looker","PRD"],"link":"linkedin.com/in/sameerkhanna"},{"name":"Seller Dashboard v2","description":"Redesigned seller tools with ML-powered inventory recommendations","tech_stack":["Figma","A/B Testing","SQL"],"link":"linkedin.com/in/sameerkhanna"}],
 "education":[{"degree":"MBA","institution":"IIM Ahmedabad","year":"2013","gpa":"3.9/4.0"}],
 "certifications":["Reforge Product Strategy & Roadmapping","Marty Cagan SVPG Practitioner"],
 "achievements":["Google VP Award 2022","Economic Times 40 Under 40 – 2020","Guest lecturer – IIM Ahmedabad"]},

# ── 28. Business Analyst – Fresher ─────────────────────────────────────
{"name":"Nandita Bose","email":"nandita.bose@gmail.com","phone":"+91-9321098765",
 "location":"Kolkata, India","linkedin":"linkedin.com/in/nanditabose",
 "github":"github.com/nanditabose","role_title":"Business Analyst",
 "category":"Product & Business","experience_level":"Fresher",
 "summary":"Recent MBA graduate with strong analytical skills and internship experience in requirements gathering and process documentation. Proficient in SQL, Excel, and Tableau. Passionate about bridging business and technology teams.",
 "skills":{"technical":["SQL","Excel","Tableau","PowerPoint","JIRA","Confluence","Business Process Modeling","Requirements Documentation","UAT"],"soft":["Analytical Thinking","Stakeholder Communication","Presentation"]},
 "experience":[{"company":"Tata Consultancy Services","title":"Business Analyst Intern","duration":"Feb 2024 - Jun 2024","location":"Kolkata, India","bullets":["Gathered and documented 150+ business requirements for ERP implementation","Created process flow diagrams reducing ambiguity in development by 40%","Facilitated UAT sessions with 25 business users"]}],
 "projects":[{"name":"Retail Inventory Optimization","description":"BA study on inventory management process improvement with ROI analysis","tech_stack":["Excel","Tableau","SQL","Visio"],"link":"github.com/nanditabose/inventory-ba"},{"name":"Customer Journey Mapping","description":"End-to-end customer journey analysis for insurance claim process","tech_stack":["Miro","PowerPoint","Excel"],"link":"github.com/nanditabose/journey-map"}],
 "education":[{"degree":"MBA Business Analytics","institution":"IIM Calcutta (Weekend Programme)","year":"2024","gpa":"3.6/4.0"},{"degree":"B.Com (Honours)","institution":"Calcutta University","year":"2022","gpa":"8.1/10"}],
 "certifications":["IIBA ECBA (Entry Certificate in BA)","Tableau Desktop Specialist"],
 "achievements":["Best Business Case Study – MBA 2024","1st place – Analytics Olympiad, IIM Calcutta"]},

# ── 29. Business Analyst – Senior ──────────────────────────────────────
{"name":"Rajesh Pillai","email":"rajesh.pillai@ibm.com","phone":"+91-9200111222",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/rajeshpillai",
 "github":"github.com/rajeshpillai","role_title":"Business Analyst",
 "category":"Product & Business","experience_level":"Senior",
 "summary":"12 years as a Business Analyst and Product Owner in BFSI and healthcare transformation programs. Delivered $200M+ IT transformation projects. Expert in Agile BA practices, data modelling, and stakeholder management.",
 "skills":{"technical":["Requirements Engineering","Data Modelling","SQL","Tableau","Process Mining","BPMN","SAP","Salesforce","Agile/SAFe","UML"],"soft":["Executive Stakeholder Management","Programme Governance","Workshop Facilitation"]},
 "experience":[
   {"company":"IBM India","title":"Senior Business Analyst / Product Owner","duration":"Mar 2019 - Present","location":"Bangalore, India","bullets":["Led business analysis for $80M core banking transformation for HDFC Bank","Authored 600+ user stories and acceptance criteria across 4 release trains","Reduced rework cost by 45% through early requirement validation workshops"]},
   {"company":"Accenture","title":"BA Lead","duration":"Jun 2015 - Mar 2019","location":"Mumbai, India","bullets":["Led requirements for Epic Care EMR implementation across 50+ hospitals","Facilitated 200+ workshops with C-suite and clinical staff","Established BA Centre of Excellence with 25 certified practitioners"]},
   {"company":"Wipro","title":"Systems Analyst","duration":"Aug 2012 - Jun 2015","location":"Pune, India","bullets":["Delivered functional specifications for insurance policy admin migration","Achieved 100% on-time delivery across 8 project milestones"]}],
 "projects":[{"name":"Core Banking Transformation","description":"End-to-end BA delivery for HDFC digital banking modernization","tech_stack":["SQL","BPMN","Confluence","SAFe"],"link":"linkedin.com/in/rajeshpillai"},{"name":"Hospital EMR Implementation","description":"Business analysis for Epic EHR across a hospital network","tech_stack":["Epic","SQL","UML","Tableau"],"link":"linkedin.com/in/rajeshpillai"}],
 "education":[{"degree":"MBA Information Systems","institution":"XLRI Jamshedpur","year":"2012","gpa":"3.8/4.0"}],
 "certifications":["IIBA CBAP (Certified Business Analysis Professional)","SAFe 5.0 Product Owner/Product Manager","PMP"],
 "achievements":["IBM Distinguished BA Award 2022","IIBA India Chapter President (2021-23)","Author: 'Agile BA Playbook' – published by BPB Publications"]},

# ── 30. IT Recruiter – Fresher ─────────────────────────────────────────
{"name":"Ananya Chatterjee","email":"ananya.chatterjee@gmail.com","phone":"+91-9887776665",
 "location":"Hyderabad, India","linkedin":"linkedin.com/in/ananyachatterjee",
 "github":"github.com/ananyachatterjee","role_title":"IT Recruiter",
 "category":"Non-Technical IT","experience_level":"Fresher",
 "summary":"Enthusiastic HR graduate with internship experience in talent acquisition. Strong in sourcing candidates via LinkedIn and Naukri, stakeholder communication, and candidate management. Looking to grow in IT/tech recruitment.",
 "skills":{"technical":["LinkedIn Recruiter","Naukri.com","Boolean Search","ATS (Zoho Recruit)","MS Excel","JD Writing","Candidate Screening","HR Analytics"],"soft":["Networking","Persuasion","Empathy","Time Management"]},
 "experience":[{"company":"Infosys BPM","title":"HR Recruitment Intern","duration":"Jan 2024 - Jun 2024","location":"Hyderabad, India","bullets":["Sourced and screened 300+ candidates for IT roles including Java, Python, and QA","Achieved 85% interview-to-offer conversion rate on assigned requisitions","Managed candidate pipeline in Zoho Recruit ATS with 100% data accuracy"]}],
 "projects":[{"name":"Campus Recruitment Drive","description":"Coordinated IT campus hiring for 50+ seats at JNTU and Osmania University","tech_stack":["LinkedIn","Excel","Zoho Recruit","MS Teams"],"link":"linkedin.com/in/ananyachatterjee"},{"name":"JD Optimization Study","description":"Analyzed 100 IT job descriptions to identify key skills and improve sourcing accuracy","tech_stack":["Excel","Word","LinkedIn Insights"],"link":"linkedin.com/in/ananyachatterjee"}],
 "education":[{"degree":"MBA Human Resources","institution":"ICFAI Business School Hyderabad","year":"2024","gpa":"3.5/4.0"}],
 "certifications":["LinkedIn Recruiter Certification","SHRM Student Member Certificate"],
 "achievements":["Fastest Placement Intern – Infosys BPM 2024","Placed in top 5% of MBA batch by campus placements"]},

# ── 31. IT Recruiter – Mid-Level ───────────────────────────────────────
{"name":"Prithviraj Gowda","email":"prithvi.gowda@wipro.com","phone":"+91-9778889990",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/prithvigowda",
 "github":"github.com/prithvigowda","role_title":"IT Recruiter",
 "category":"Non-Technical IT","experience_level":"Mid-Level",
 "summary":"5 years of technical recruitment experience at top IT services companies and product startups. Specialized in hiring engineering talent from SDE 1 to Engineering Manager level. Reduced time-to-hire by 40% through process improvements.",
 "skills":{"technical":["LinkedIn Recruiter Pro","Workday ATS","Boolean X-Ray Search","Technical Screening","Compensation Benchmarking","Sourcing Metrics","MS Excel","Employer Branding"],"soft":["Stakeholder Partnering","Negotiation","Market Intelligence","Candidate Experience"]},
 "experience":[
   {"company":"Wipro","title":"Senior Talent Acquisition Specialist","duration":"Apr 2022 - Present","location":"Bangalore, India","bullets":["Closed 180+ engineering positions across Java, Cloud, and DevOps in FY2023","Reduced average time-to-hire from 45 to 27 days through pipeline optimization","Built talent community of 5,000+ passive engineering candidates"]},
   {"company":"Freshworks","title":"Technical Recruiter","duration":"Aug 2019 - Apr 2022","location":"Chennai, India","bullets":["Hired 60+ engineers for product teams including ML and mobile roles","Implemented structured technical interview process improving hire quality by 30%","Partnered with 8 engineering managers for headcount planning"]}],
 "projects":[{"name":"Recruiter Dashboard","description":"Excel-based recruiter productivity and pipeline tracking dashboard","tech_stack":["Excel","Power BI","Workday"],"link":"linkedin.com/in/prithvigowda"},{"name":"Employer Branding Campaign","description":"LinkedIn content campaign generating 2K+ engineering followers in 3 months","tech_stack":["LinkedIn","Canva","Analytics"],"link":"linkedin.com/in/prithvigowda"}],
 "education":[{"degree":"MBA Human Resources","institution":"Symbiosis Institute of Business Management","year":"2019","gpa":"3.7/4.0"}],
 "certifications":["LinkedIn Recruiter Certification","NHRDN Certified HR Professional"],
 "achievements":["Wipro Star Recruiter Award 2023","Freshworks Recruiter Excellence Award 2021"]},

# ── 32. IT Recruiter – Senior ───────────────────────────────────────────
{"name":"Kavitha Rangaswamy","email":"kavitha.r@hcl.com","phone":"+91-9111000999",
 "location":"Chennai, India","linkedin":"linkedin.com/in/kavitharangaswamy",
 "github":"github.com/kavitharangaswamy","role_title":"IT Recruiter",
 "category":"Non-Technical IT","experience_level":"Senior",
 "summary":"12 years of talent acquisition leadership at HCL, Infosys, and tech startups. Led teams of 15+ recruiters and delivered 2,000+ hires across technical and non-technical roles. Expert in campus programs, executive search, and TA strategy.",
 "skills":{"technical":["SAP SuccessFactors","Workday","LinkedIn Talent Insights","Workforce Planning","Campus Recruitment Strategy","Executive Search","TA Analytics","Employer Branding","DEI Recruiting"],"soft":["TA Leadership","Executive Stakeholder Management","Team Development","Strategic Planning"]},
 "experience":[
   {"company":"HCL Technologies","title":"Senior Manager – Talent Acquisition","duration":"Jan 2019 - Present","location":"Chennai, India","bullets":["Led team of 18 recruiters delivering 1,200+ hires annually across APAC","Established HCL's engineering campus program at 50+ tier-1 colleges","Reduced cost-per-hire by 30% through employee referral program expansion"]},
   {"company":"Infosys","title":"Talent Acquisition Lead","duration":"Mar 2015 - Jan 2019","location":"Mysore, India","bullets":["Managed BFS and Healthcare lateral hiring delivering 600+ positions per year","Built first DEI-focused hiring playbook adopted across 5 geographies","Implemented video interviewing reducing interview scheduling time by 65%"]},
   {"company":"Mphasis","title":"Recruiter","duration":"Jun 2012 - Mar 2015","location":"Bangalore, India","bullets":["Sourced and closed 350+ candidates across Java, .NET, and testing domains","Established external agency management framework"]}],
 "projects":[{"name":"Campus Talent Program","description":"End-to-end campus recruitment program design for 50 engineering colleges","tech_stack":["SAP SuccessFactors","Excel","LinkedIn Campus"],"link":"linkedin.com/in/kavitharangaswamy"},{"name":"DEI Hiring Playbook","description":"Structured DEI hiring guide adopted across HCL APAC region","tech_stack":["PowerPoint","Workday Analytics"],"link":"linkedin.com/in/kavitharangaswamy"}],
 "education":[{"degree":"MBA Human Resources & Strategy","institution":"XLRI Jamshedpur","year":"2012","gpa":"3.8/4.0"}],
 "certifications":["SHRM-SCP (Senior Certified Professional)","LinkedIn Talent Insights Certification"],
 "achievements":["HCL TA Leader of the Year 2022","NASSCOM HR Excellence Award 2021","Speaker at LinkedIn Talent Connect India"]},

# ── 33. HR Business Partner – Mid-Level ────────────────────────────────
{"name":"Madhavi Latha","email":"madhavi.latha@microsoft.com","phone":"+91-9955443322",
 "location":"Hyderabad, India","linkedin":"linkedin.com/in/madhavitha",
 "github":"github.com/madhavitha","role_title":"HR Business Partner",
 "category":"Non-Technical IT","experience_level":"Mid-Level",
 "summary":"6 years as an HRBP supporting engineering and product organizations at Microsoft and Hyundai. Skilled in performance management, employee relations, and organizational design. Supported business units of 500+ employees.",
 "skills":{"technical":["Workday HCM","PeopleSoft","HR Analytics","Performance Management","Succession Planning","Employee Engagement","Labor Law Compliance","Excel","Power BI"],"soft":["Coaching","Confidentiality","Change Management","Conflict Resolution"]},
 "experience":[
   {"company":"Microsoft India","title":"HR Business Partner","duration":"Sep 2021 - Present","location":"Hyderabad, India","bullets":["Partnered with 3 engineering VPs supporting 600+ employees across Azure and Office","Drove 20% improvement in engagement scores through targeted retention programs","Led reorg of 2 product divisions affecting 150+ employees with zero attrition"]},
   {"company":"Hyundai Motor India","title":"HRBP","duration":"Jul 2018 - Sep 2021","location":"Chennai, India","bullets":["Managed performance cycle for 300+ IT staff","Developed leadership pipeline program promoting 15 high-potential employees","Resolved 90% of employee relations cases without escalation"]}],
 "projects":[{"name":"Engagement Index Improvement","description":"Designed and implemented engineering engagement program improving scores by 20 pts","tech_stack":["Workday","Power BI","Excel","Teams"],"link":"linkedin.com/in/madhavitha"},{"name":"Succession Planning Framework","description":"Built competency-based succession model for senior engineering roles","tech_stack":["Excel","PowerPoint","Workday"],"link":"linkedin.com/in/madhavitha"}],
 "education":[{"degree":"MBA Human Resources","institution":"XLRI Jamshedpur","year":"2018","gpa":"3.9/4.0"}],
 "certifications":["SHRM-CP","Workday HCM Certified"],
 "achievements":["Microsoft HR Excellence Award 2023","Invited speaker – SHRM India Annual Conference 2022"]},

# ── 34. IT Support Specialist – Fresher ────────────────────────────────
{"name":"Suresh Kumar Yadav","email":"suresh.yadav@gmail.com","phone":"+91-9432198765",
 "location":"Noida, India","linkedin":"linkedin.com/in/sureshyadav",
 "github":"github.com/sureshyadav","role_title":"IT Support Specialist",
 "category":"Non-Technical IT","experience_level":"Fresher",
 "summary":"IT graduate with solid foundation in hardware, networking, and Windows/Linux administration. Completed CompTIA A+ and eager to provide reliable technical support in a fast-paced IT environment.",
 "skills":{"technical":["Windows Server","Active Directory","Office 365","ServiceNow","Networking (TCP/IP)","Hardware Troubleshooting","Linux","ITIL","Remote Desktop","VPN"],"soft":["Patience","Customer Service","Problem Solving","Documentation"]},
 "experience":[{"company":"HCL Infosystems","title":"IT Support Intern","duration":"Jan 2024 - Jun 2024","location":"Noida, India","bullets":["Resolved 50+ daily IT tickets maintaining 95% SLA compliance","Configured and deployed 40+ workstations for new joiners","Managed user accounts and permissions in Active Directory for 200+ users"]}],
 "projects":[{"name":"IT Asset Tracker","description":"Excel-based IT asset management system for 500-user organization","tech_stack":["Excel","VBA","ServiceNow"],"link":"github.com/sureshyadav/asset-tracker"},{"name":"Network Monitoring Setup","description":"Set up Nagios monitoring for college network infrastructure","tech_stack":["Linux","Nagios","Bash"],"link":"github.com/sureshyadav/network-monitor"}],
 "education":[{"degree":"B.Sc. Information Technology","institution":"Amity University Noida","year":"2024","gpa":"7.8/10"}],
 "certifications":["CompTIA A+","ITIL 4 Foundation","Microsoft 365 Fundamentals (MS-900)"],
 "achievements":["Best Support Intern – HCL Infosystems 2024","Zero SLA breach in final 3 months of internship"]},

# ── 35. Software Engineering Intern ────────────────────────────────────
{"name":"Kaushik Bhattacharya","email":"kaushik.b@gmail.com","phone":"+91-9876001234",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/kaushikb",
 "github":"github.com/kaushikb","role_title":"Software Engineering Intern",
 "category":"Student/Intern","experience_level":"Intern",
 "summary":"3rd year CS student at IIT Bangalore with strong programming fundamentals in Java and Python. Active competitive programmer (Codeforces Rating: 1750). Looking for SWE internship to apply DSA and system design knowledge.",
 "skills":{"technical":["Java","Python","C++","Data Structures","Algorithms","SQL","Git","Spring Boot (basics)","Linux","REST APIs"],"soft":["Fast Learning","Competitive Spirit","Team Collaboration"]},
 "experience":[{"company":"Atlassian","title":"Software Engineering Intern","duration":"May 2024 - Jul 2024","location":"Bangalore, India","bullets":["Built internal developer tooling feature reducing build time by 15%","Wrote 40+ unit and integration tests using JUnit 5","Presented work to VP Engineering receiving outstanding intern feedback"]}],
 "projects":[{"name":"Distributed Key-Value Store","description":"Raft consensus-based distributed KV store (course project)","tech_stack":["Java","Raft Protocol","gRPC"],"link":"github.com/kaushikb/kvstore"},{"name":"OS Shell Implementation","description":"Custom Unix shell with piping, redirection, and job control","tech_stack":["C","Unix","Linux"],"link":"github.com/kaushikb/mini-shell"}],
 "education":[{"degree":"B.Tech Computer Science (3rd Year)","institution":"IIT Bangalore","year":"2025 (expected)","gpa":"9.2/10"}],
 "certifications":["AWS Cloud Practitioner","Competitive Programming – Codeforces Expert (1750 rating)"],
 "achievements":["ICPC Asia Regional 2023 – Qualified","Google Code Jam 2024 – Round 2","Academic Excellence Scholarship – IIT Bangalore"]},

# ── 36. Data Science Intern ────────────────────────────────────────────
{"name":"Ishita Sen","email":"ishita.sen@gmail.com","phone":"+91-9765432100",
 "location":"Kolkata, India","linkedin":"linkedin.com/in/ishitasen",
 "github":"github.com/ishitasen","role_title":"Data Science Intern",
 "category":"Student/Intern","experience_level":"Intern",
 "summary":"Statistics final-year student with strong ML and Python skills. Published Kaggle notebooks with 1K+ views. Seeking data science internship to apply academic knowledge in predictive modelling and NLP to real business problems.",
 "skills":{"technical":["Python","R","scikit-learn","Pandas","NumPy","Matplotlib","SQL","Tableau","NLTK","Jupyter"],"soft":["Statistical Thinking","Research Mindset","Visual Storytelling"]},
 "experience":[{"company":"Fractal Analytics","title":"Data Science Intern","duration":"Jun 2024 - Aug 2024","location":"Mumbai, India","bullets":["Built NPS prediction model achieving 78% accuracy for FMCG client","Performed EDA on 2M+ customer records identifying 5 key churn indicators","Presented findings to client's analytics team with actionable recommendations"]}],
 "projects":[{"name":"Customer Churn Predictor","description":"Random Forest model predicting telecom churn with SHAP explanations","tech_stack":["Python","scikit-learn","SHAP","Streamlit"],"link":"github.com/ishitasen/churn"},{"name":"News Classification","description":"Multi-class text classifier for news articles using TF-IDF and BERT","tech_stack":["Python","NLTK","Hugging Face","Streamlit"],"link":"github.com/ishitasen/news-classifier"}],
 "education":[{"degree":"B.Stat (Honours) – Final Year","institution":"Indian Statistical Institute Kolkata","year":"2025 (expected)","gpa":"8.9/10"}],
 "certifications":["IBM Data Science Professional Certificate","Kaggle Competitions Contributor (Top 8%)"],
 "achievements":["ISI Best Project Award 2024","Top 5 – DataVista National Hackathon 2024"]},

# ── 37. Cloud Architect – Senior ───────────────────────────────────────
{"name":"Prasanna Venkataraman","email":"prasanna.v@aws.amazon.com","phone":"+91-9800200300",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/prasannav",
 "github":"github.com/prasannav","role_title":"Cloud Architect",
 "category":"DevOps & Cloud","experience_level":"Senior",
 "summary":"11 years designing enterprise cloud architectures on AWS and GCP. AWS Hero and Solutions Architect Professional. Designed cloud infrastructure for 100+ enterprise migrations with zero downtime.",
 "skills":{"technical":["AWS","GCP","Terraform","CloudFormation","Kubernetes","Service Mesh","FinOps","WAF","Landing Zone","CDK"],"soft":["Architecture Advisory","Executive Consulting","Cost Optimization Mindset"]},
 "experience":[
   {"company":"Amazon Web Services","title":"Senior Solutions Architect","duration":"Jun 2019 - Present","location":"Bangalore, India","bullets":["Architected cloud landing zones for 50+ enterprise migrations to AWS","Designed multi-region HA architecture for RBI-compliant banking workloads","Saved clients average 45% on cloud costs through Well-Architected Reviews"]},
   {"company":"Google Cloud","title":"Cloud Architect","duration":"Jan 2016 - Jun 2019","location":"Hyderabad, India","bullets":["Led GCP adoption for 20+ media and retail enterprises in India","Designed BigQuery data warehouse for 10PB+ media analytics workload","Published 3 GCP reference architectures downloaded by 50K+ engineers"]},
   {"company":"IBM","title":"Cloud Engineer","duration":"Aug 2013 - Jan 2016","location":"Bangalore, India","bullets":["Migrated 200 on-premise apps to IBM Cloud and AWS","Established cloud security baseline adopted org-wide"]}],
 "projects":[{"name":"Banking Cloud Landing Zone","description":"Multi-account AWS landing zone with RBI compliance controls","tech_stack":["AWS Control Tower","Terraform","SCPs","CloudTrail"],"link":"github.com/prasannav/banking-lz"},{"name":"Multi-Cloud Cost Dashboard","description":"Unified cost visibility across AWS and GCP using open standards","tech_stack":["Python","Terraform","Grafana","FinOps SDK"],"link":"github.com/prasannav/cost-dashboard"}],
 "education":[{"degree":"M.Tech Cloud Computing","institution":"IIIT Hyderabad","year":"2013","gpa":"9.1/10"}],
 "certifications":["AWS Solutions Architect – Professional","AWS Security Specialty","GCP Professional Cloud Architect","AWS Hero (Community)"],
 "achievements":["AWS Hero designation (1 of 4 in India)","AWS re:Invent speaker 2022 and 2023","Cloud Architecture YouTube channel – 80K subscribers"]},

# ── 38. Site Reliability Engineer – Senior ─────────────────────────────
{"name":"Varun Kapoor","email":"varun.kapoor@netflix.com","phone":"+91-9988123456",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/varunkapoor",
 "github":"github.com/varunkapoor","role_title":"Site Reliability Engineer",
 "category":"DevOps & Cloud","experience_level":"Senior",
 "summary":"8 years SRE experience at Netflix and Zomato. Built reliability engineering practices achieving 99.99% availability for streaming and food delivery platforms serving tens of millions of users.",
 "skills":{"technical":["Kubernetes","Prometheus/Grafana","PagerDuty","Chaos Engineering","Go","Python","AWS","Istio","SLO/SLI/SLA","Terraform"],"soft":["Reliability Mindset","Incident Command","Blameless Culture","Mentoring"]},
 "experience":[
   {"company":"Netflix India","title":"Senior SRE","duration":"Apr 2020 - Present","location":"Bangalore, India","bullets":["Maintained 99.99% availability for Netflix India streaming platform","Led chaos engineering program running 500+ experiments annually","Built automated incident response reducing MTTR from 12 to 3 minutes"]},
   {"company":"Zomato","title":"SRE Lead","duration":"Jun 2016 - Apr 2020","location":"Gurugram, India","bullets":["Built SRE function from scratch during Zomato's hypergrowth phase","Designed on-call framework and escalation policies for 200+ microservices","Reduced false-positive alerts by 80% through intelligent alerting"]}],
 "projects":[{"name":"Chaos Engineering Platform","description":"Internal chaos engineering tool for controlled failure injection","tech_stack":["Go","Kubernetes","Prometheus","Chaos Mesh"],"link":"github.com/varunkapoor/chaos-platform"},{"name":"SLO Dashboard","description":"Automated SLO tracking and burn rate alerting system","tech_stack":["Prometheus","Grafana","Terraform","Python"],"link":"github.com/varunkapoor/slo-dashboard"}],
 "education":[{"degree":"B.Tech Computer Science","institution":"Delhi College of Engineering","year":"2016","gpa":"8.8/10"}],
 "certifications":["CKA + CKAD","Google SRE Certificate","AWS Advanced Networking"],
 "achievements":["Netflix Engineering Blog author","SREcon APAC speaker 2022","Chaos Engineering community lead – India"]},

# ── 39. Cybersecurity Analyst – Mid-Level ──────────────────────────────
{"name":"Arun Krishnaswamy","email":"arun.k@deloitte.com","phone":"+91-9600333444",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/arunkk",
 "github":"github.com/arunkk","role_title":"Cybersecurity Analyst",
 "category":"Security","experience_level":"Mid-Level",
 "summary":"5 years in cybersecurity with expertise in SIEM, SOC operations, and penetration testing. Certified CISM and CEH. Protected financial and healthcare clients against advanced threats.",
 "skills":{"technical":["SIEM (Splunk)","Vulnerability Assessment","Penetration Testing","OWASP","IDS/IPS","Firewall Management","Python","MITRE ATT&CK","Incident Response","ISO 27001"],"soft":["Threat Intelligence","Analytical Thinking","Security Awareness Training"]},
 "experience":[
   {"company":"Deloitte India","title":"Cybersecurity Analyst","duration":"Apr 2022 - Present","location":"Bangalore, India","bullets":["Monitored SIEM for 50+ enterprise clients detecting 200+ threats monthly","Led penetration tests identifying critical vulnerabilities in 3 banking apps","Developed security awareness training reducing phishing success rate by 70%"]},
   {"company":"Paladion Networks","title":"SOC Analyst","duration":"Aug 2019 - Apr 2022","location":"Bangalore, India","bullets":["Triaged and responded to 1,500+ security incidents per month","Built automated threat hunting playbooks reducing analyst workload by 35%","Achieved 99% SLA compliance on P1 incident response"]}],
 "projects":[{"name":"SIEM Automation Playbooks","description":"Automated Splunk SOAR playbooks for common threat response scenarios","tech_stack":["Splunk SOAR","Python","REST APIs","STIX/TAXII"],"link":"github.com/arunkk/siem-playbooks"},{"name":"Web App Pentest Framework","description":"Automated OWASP Top 10 testing framework for internal use","tech_stack":["Python","Burp Suite","OWASP ZAP"],"link":"github.com/arunkk/pentest-framework"}],
 "education":[{"degree":"B.E. Computer Science","institution":"RVCE Bangalore","year":"2019","gpa":"8.4/10"}],
 "certifications":["CEH – Certified Ethical Hacker","CISM – Certified Information Security Manager","CompTIA Security+"],
 "achievements":["Deloitte Cyber Security Star 2023","Bug bounty: Reported critical CVE in popular OSS project"]},

# ── 40. NLP Engineer – Senior ──────────────────────────────────────────
{"name":"Bhavani Shankar","email":"bhavani.s@anthropic.in","phone":"+91-9900888777",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/bhavanis",
 "github":"github.com/bhavanis","role_title":"NLP Engineer",
 "category":"AI & Data","experience_level":"Senior",
 "summary":"9 years in NLP research and engineering. PhD in Computational Linguistics. Built production NLP systems for search, conversational AI, and document understanding at Google and AI startups. 20+ publications and 800+ citations.",
 "skills":{"technical":["Python","PyTorch","Transformers","spaCy","LangChain","Hugging Face","RLHF","RAG","Elasticsearch","Triton Inference"],"soft":["Research Leadership","Cross-functional Communication","Technical Writing"]},
 "experience":[
   {"company":"AI Startup (NLP)","title":"Principal NLP Engineer","duration":"Mar 2021 - Present","location":"Bangalore, India","bullets":["Built multilingual document intelligence platform supporting 22 Indian languages","Designed RLHF pipeline for fine-tuning instruction-following LLMs","Reduced inference latency by 60% through quantization and Triton serving"]},
   {"company":"Google India","title":"Staff Research Engineer – NLP","duration":"Jul 2017 - Mar 2021","location":"Hyderabad, India","bullets":["Led Google Search query understanding for South Asian languages","Developed multilingual BERT variant achieving SOTA on 12 benchmarks","Mentored 6 NLP researchers and engineers"]}],
 "projects":[{"name":"Indic-NLP Suite","description":"OSS NLP toolkit for 22 Indian languages with tokenization, NER, POS","tech_stack":["Python","PyTorch","spaCy","Hugging Face"],"link":"github.com/bhavanis/indic-nlp"},{"name":"Multilingual RAG","description":"Cross-lingual retrieval-augmented generation system","tech_stack":["LangChain","Pinecone","FastAPI","Transformers"],"link":"github.com/bhavanis/multilingual-rag"}],
 "education":[{"degree":"PhD Computational Linguistics","institution":"IISc Bangalore","year":"2017","gpa":"9.4/10"}],
 "certifications":["ACL Rolling Review Reviewer","EMNLP Program Committee Member"],
 "achievements":["20+ publications, 800+ citations","Google Research Award 2019","Indic-NLP Suite – 3.5K GitHub stars"]},

# ── 41. MLOps Engineer – Mid-Level ─────────────────────────────────────
{"name":"Chirag Mehta","email":"chirag.mehta@startupai.com","phone":"+91-9870123456",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/chiragmehta",
 "github":"github.com/chiragmehta","role_title":"MLOps Engineer",
 "category":"AI & Data","experience_level":"Mid-Level",
 "summary":"4 years bridging ML research and production systems. Expert in ML pipelines, model monitoring, and feature stores. Built MLOps platforms serving 20+ production models with automated retraining and drift detection.",
 "skills":{"technical":["MLflow","Kubeflow","SageMaker","Feature Store (Feast)","DVC","Docker","Kubernetes","Python","Prometheus","Evidently AI"],"soft":["ML-Ops Mindset","Cross-team Collaboration","Process Design"]},
 "experience":[
   {"company":"StartupAI","title":"MLOps Engineer","duration":"Jun 2022 - Present","location":"Bangalore, India","bullets":["Built end-to-end ML platform serving 25 production models with 99.5% uptime","Implemented model monitoring detecting data drift 3 days before KPI impact","Reduced model deployment time from 2 weeks to 4 hours through CI/CD automation"]},
   {"company":"Wipro AI Lab","title":"ML Platform Engineer","duration":"Aug 2020 - Jun 2022","location":"Bangalore, India","bullets":["Set up Kubeflow pipelines for customer analytics models","Built feature store serving 100+ features to 8 ML models","Automated model retraining pipeline saving 20 engineering hours weekly"]}],
 "projects":[{"name":"ML Platform","description":"Kubeflow-based ML platform with feature store, model registry, and monitoring","tech_stack":["Kubeflow","Feast","MLflow","Prometheus","Evidently"],"link":"github.com/chiragmehta/ml-platform"},{"name":"Drift Detector","description":"Statistical drift detection library for tabular and text ML models","tech_stack":["Python","Evidently AI","MLflow","Kafka"],"link":"github.com/chiragmehta/drift-detector"}],
 "education":[{"degree":"M.Tech Artificial Intelligence","institution":"IIT Bombay","year":"2020","gpa":"8.8/10"}],
 "certifications":["AWS Certified ML Specialty","Kubeflow Foundations – Linux Foundation"],
 "achievements":["MLOps Community contributor (5K+ members)","Published MLOps best practices guide – 15K views on Medium"]},

# ── 42. Computer Vision Engineer – Senior ──────────────────────────────
{"name":"Rahul Negi","email":"rahul.negi@tesla.com","phone":"+91-9988445566",
 "location":"Hyderabad, India","linkedin":"linkedin.com/in/rahulnegi",
 "github":"github.com/rahulnegi","role_title":"Computer Vision Engineer",
 "category":"AI & Data","experience_level":"Senior",
 "summary":"9 years in computer vision for autonomous vehicles and robotics. PhD in Computer Vision from IIT. Built perception systems deployed in real-world AV and manufacturing environments. 12 published papers.",
 "skills":{"technical":["Python","PyTorch","OpenCV","CUDA","ONNX","TensorRT","3D Point Clouds","Object Detection (YOLO/DETR)","Semantic Segmentation","ROS"],"soft":["Research-to-Production","Systems Thinking","Technical Leadership"]},
 "experience":[
   {"company":"Tesla (India Engineering)","title":"Senior CV Engineer","duration":"May 2020 - Present","location":"Hyderabad, India","bullets":["Developed pedestrian detection model improving AV safety recall by 18%","Optimized TensorRT inference pipeline achieving 50ms latency on edge hardware","Led team of 5 CV engineers across 3D detection workstreams"]},
   {"company":"Ola Electric","title":"CV Research Engineer","duration":"Jul 2016 - May 2020","location":"Bangalore, India","bullets":["Built lane detection and road segmentation for Level 2 autonomy","Designed data augmentation pipeline 5x-ing rare scenario coverage","Filed 3 patents on efficient 3D object detection"]}],
 "projects":[{"name":"3D Object Detection SDK","description":"LiDAR + camera fusion detection SDK for industrial robotics","tech_stack":["Python","PyTorch","ROS","CUDA","TensorRT"],"link":"github.com/rahulnegi/cv-sdk"},{"name":"Edge Inference Optimizer","description":"Model compression tool for deploying CV models on edge devices","tech_stack":["ONNX","TensorRT","Python","CUDA"],"link":"github.com/rahulnegi/edge-optimizer"}],
 "education":[{"degree":"PhD Computer Vision","institution":"IIT Roorkee","year":"2016","gpa":"9.3/10"}],
 "certifications":["NVIDIA Deep Learning Institute Instructor","CVPR 2022 Area Chair"],
 "achievements":["12 papers (600+ citations)","3 patents in AV perception","CVPR Best Paper Nominee 2021"]},

# ── 43. Data Scientist – Mid-Level ─────────────────────────────────────
{"name":"Savitha Reddy","email":"savitha.reddy@zomato.com","phone":"+91-9655443322",
 "location":"Gurugram, India","linkedin":"linkedin.com/in/savithareddy",
 "github":"github.com/savithareddy","role_title":"Data Scientist",
 "category":"AI & Data","experience_level":"Mid-Level",
 "summary":"5 years applying machine learning to food-tech growth challenges. Built recommendation, pricing, and fraud detection models contributing $30M+ in incremental revenue. Strong communicator translating complex models to C-suite insights.",
 "skills":{"technical":["Python","SQL","PyTorch","XGBoost","A/B Testing","Spark","Looker","BigQuery","Tableau","Causal Inference"],"soft":["Business Storytelling","Experimentation Mindset","Stakeholder Management"]},
 "experience":[
   {"company":"Zomato","title":"Senior Data Scientist","duration":"Mar 2022 - Present","location":"Gurugram, India","bullets":["Built personalized restaurant recommendation engine improving CTR by 22%","Developed dynamic surge pricing model generating Rs 80Cr incremental annual revenue","Led 50+ A/B experiments using causal inference frameworks"]},
   {"company":"Practo","title":"Data Scientist","duration":"Jul 2019 - Mar 2022","location":"Bangalore, India","bullets":["Built appointment no-show prediction model reducing missed slots by 30%","Created doctor recommendation system improving booking conversion by 15%","Established data science experimentation standards across the team"]}],
 "projects":[{"name":"Restaurant Recommender","description":"Hybrid collaborative + content-based recommendation engine","tech_stack":["Python","Spark","Redis","BigQuery"],"link":"github.com/savithareddy/recommender"},{"name":"Surge Pricing Model","description":"Dynamic pricing engine with real-time demand forecasting","tech_stack":["Python","XGBoost","Kafka","Redis"],"link":"github.com/savithareddy/pricing"}],
 "education":[{"degree":"M.Sc. Statistics","institution":"IIT Kanpur","year":"2019","gpa":"9.0/10"}],
 "certifications":["Causal Inference for DS – Coursera","Databricks ML Associate"],
 "achievements":["Zomato Data Science Impact Award 2023","Speaker at DataHack Summit 2022"]},

# ── 44. Data Analyst – Fresher ─────────────────────────────────────────
{"name":"Tejaswini Rao","email":"tejaswini.rao@gmail.com","phone":"+91-9543219876",
 "location":"Hyderabad, India","linkedin":"linkedin.com/in/tejaswiniaro",
 "github":"github.com/tejaswiniaro","role_title":"Data Analyst",
 "category":"AI & Data","experience_level":"Fresher",
 "summary":"Statistics graduate with strong SQL, Python, and Tableau skills. Built 5+ analytical dashboards during internship and coursework. Eager to help companies make data-driven decisions through clear analysis and visualization.",
 "skills":{"technical":["SQL","Python","Pandas","Tableau","Power BI","Excel","Google Analytics","BigQuery","VLOOKUP/Pivot Tables","Statistical Analysis"],"soft":["Data Storytelling","Critical Thinking","Attention to Detail"]},
 "experience":[{"company":"KPMG India","title":"Data Analytics Intern","duration":"Jan 2024 - Jun 2024","location":"Hyderabad, India","bullets":["Created 8 Power BI dashboards for audit analytics used by senior managers","Automated monthly reporting reducing preparation time by 6 hours per report","Identified Rs 2Cr+ in billing discrepancies through SQL analysis"]}],
 "projects":[{"name":"COVID-19 India Analytics Dashboard","description":"Interactive Tableau dashboard tracking state-wise vaccination progress","tech_stack":["Tableau","Python","Pandas","Government APIs"],"link":"github.com/tejaswiniaro/covid-dashboard"},{"name":"E-Commerce Sales Analysis","description":"Exploratory analysis of 1M+ transaction records identifying seasonal patterns","tech_stack":["Python","Pandas","Matplotlib","SQL"],"link":"github.com/tejaswiniaro/ecom-analysis"}],
 "education":[{"degree":"B.Sc. Statistics (Honours)","institution":"Osmania University Hyderabad","year":"2024","gpa":"8.7/10"}],
 "certifications":["Google Data Analytics Professional Certificate","Tableau Desktop Specialist","Power BI Data Analyst (PL-300)"],
 "achievements":["Best Intern – KPMG Analytics Division 2024","1st place – Analytics Case Challenge, Osmania University"]},

# ── 45. SDET – Senior ──────────────────────────────────────────────────
{"name":"Ganesh Murthy","email":"ganesh.murthy@microsoft.com","phone":"+91-9877001234",
 "location":"Hyderabad, India","linkedin":"linkedin.com/in/ganeshmurthy",
 "github":"github.com/ganeshmurthy","role_title":"SDET",
 "category":"QA & Testing","experience_level":"Senior",
 "summary":"9 years as an SDET building test infrastructure for Azure and Office 365. Expert in large-scale test automation, performance testing, and quality engineering platforms. Led teams of 8 SDETs delivering releases to 300M+ users.",
 "skills":{"technical":["C#","Python","Azure DevOps","Playwright","JMeter","K6","Distributed Testing","Test Infra Design","API Testing","Performance Engineering"],"soft":["Quality Engineering Culture","Test Strategy","Team Leadership"]},
 "experience":[
   {"company":"Microsoft India","title":"Senior SDET","duration":"Jul 2018 - Present","location":"Hyderabad, India","bullets":["Led test automation for Azure Kubernetes Service release pipeline","Built performance testing harness handling 1M+ RPS load tests","Reduced release cycle time by 40% through intelligent test selection"]},
   {"company":"Oracle India","title":"SDET II","duration":"Aug 2015 - Jul 2018","location":"Hyderabad, India","bullets":["Developed Playwright-based E2E test suite for Oracle Cloud applications","Built test data management platform used by 30+ test teams","Improved flaky test rate from 15% to under 1%"]}],
 "projects":[{"name":"Distributed Test Runner","description":"Kubernetes-based distributed test execution platform","tech_stack":["Python","Kubernetes","Redis","Playwright"],"link":"github.com/ganeshmurthy/dist-test-runner"},{"name":"Performance Baseline Tool","description":"Automated performance regression detection with ML-based anomaly detection","tech_stack":["Python","K6","InfluxDB","Grafana"],"link":"github.com/ganeshmurthy/perf-baseline"}],
 "education":[{"degree":"B.Tech Computer Science","institution":"NIT Warangal","year":"2015","gpa":"8.9/10"}],
 "certifications":["ISTQB Test Manager","CKAD – Certified Kubernetes Application Developer","Performance Testing – BlazeMeter"],
 "achievements":["Microsoft Patent – Intelligent Test Selection Algorithm","Testing World Award 2022 – Best SDET"]},

# ── 46. Backend Engineer Node.js – Mid-Level ───────────────────────────
{"name":"Akash Tripathi","email":"akash.tripathi@meesho.com","phone":"+91-9111444555",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/akashtripathi",
 "github":"github.com/akashtripathi","role_title":"Backend Engineer (Node.js)",
 "category":"Engineering","experience_level":"Mid-Level",
 "summary":"4 years of Node.js backend engineering for social commerce and fintech. Expert in microservices, event-driven design, and high-concurrency APIs. Built systems handling 500K+ concurrent users during sale events.",
 "skills":{"technical":["Node.js","TypeScript","NestJS","MongoDB","PostgreSQL","Redis","Kafka","Docker","AWS","GraphQL"],"soft":["Performance-First Mindset","Code Quality","Agile"]},
 "experience":[
   {"company":"Meesho","title":"Backend Engineer","duration":"Jul 2022 - Present","location":"Bangalore, India","bullets":["Built seller catalog service handling 5M+ SKUs with sub-100ms search latency","Implemented distributed locking for flash sale inventory preventing overselling","Designed event-driven order notification system using Kafka and SNS"]},
   {"company":"CRED","title":"Software Engineer","duration":"Sep 2020 - Jul 2022","location":"Bangalore, India","bullets":["Developed credit card bill payment APIs processing Rs 500Cr monthly","Built rate limiting and fraud detection middleware protecting 5M+ user accounts","Optimized MongoDB aggregations reducing report generation from 30s to 2s"]}],
 "projects":[{"name":"Flash Sale Engine","description":"Distributed inventory management for high-concurrency flash sales","tech_stack":["Node.js","Redis","Kafka","PostgreSQL"],"link":"github.com/akashtripathi/flash-sale"},{"name":"GraphQL Gateway","description":"Federated GraphQL API gateway for microservices","tech_stack":["Node.js","Apollo Federation","Redis","Docker"],"link":"github.com/akashtripathi/gql-gateway"}],
 "education":[{"degree":"B.Tech Computer Science","institution":"IIT Patna","year":"2020","gpa":"8.6/10"}],
 "certifications":["Node.js Application Developer – OpenJS","AWS Developer – Associate"],
 "achievements":["Meesho Engineering Impact Award 2023","Handles 500K concurrent users with p99 < 150ms"]},

# ── 47. Frontend Engineer React – Senior ───────────────────────────────
{"name":"Nalini Krishnaswami","email":"nalini.k@razorpay.com","phone":"+91-9222333444",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/nalinik",
 "github":"github.com/nalinik","role_title":"Frontend Engineer (React)",
 "category":"Engineering","experience_level":"Senior",
 "summary":"8 years of React frontend engineering at Razorpay and Flipkart. Expert in micro-frontends, design systems, and web performance. Built frontend platforms consumed by millions of merchants and shoppers.",
 "skills":{"technical":["React","TypeScript","Next.js","Webpack","Micro-Frontends","Storybook","GraphQL","Web Performance","Accessibility (WCAG 2.1)","Jest/Cypress"],"soft":["Design Systems Thinking","Cross-functional Leadership","Performance Obsession"]},
 "experience":[
   {"company":"Razorpay","title":"Principal Frontend Engineer","duration":"Apr 2020 - Present","location":"Bangalore, India","bullets":["Architected Razorpay Dashboard micro-frontend platform used by 1M+ merchants","Built design system with 150+ components adopted by 20 product teams","Improved Core Web Vitals LCP from 4.2s to 1.1s across merchant portal"]},
   {"company":"Flipkart","title":"Senior Frontend Engineer","duration":"Jun 2016 - Apr 2020","location":"Bangalore, India","bullets":["Led React migration from legacy Backbone.js saving 40% in bundle size","Built product page A/B testing platform running 50+ simultaneous experiments","Established frontend performance culture and monitoring framework"]}],
 "projects":[{"name":"Blade Design System","description":"Razorpay's open-source React design system","tech_stack":["React","TypeScript","Storybook","Styled Components"],"link":"github.com/nalinik/blade-ds"},{"name":"Micro-Frontend Framework","description":"Module Federation-based micro-frontend orchestration system","tech_stack":["React","Webpack","Module Federation","TypeScript"],"link":"github.com/nalinik/micro-fe"}],
 "education":[{"degree":"B.Tech Computer Science","institution":"NIT Trichy","year":"2016","gpa":"8.9/10"}],
 "certifications":["Google Web Performance Certification","W3C Web Accessibility Specialist"],
 "achievements":["React India Conference keynote 2022","Blade Design System – 2.8K GitHub stars","Forbes 30 Under 30 Technology – 2021"]},

# ── 48. Technical Lead – Lead ──────────────────────────────────────────
{"name":"Deepak Shrivastava","email":"deepak.s@flipkart.com","phone":"+91-9900999888",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/deepaks",
 "github":"github.com/deepaks","role_title":"Technical Lead",
 "category":"Engineering","experience_level":"Lead",
 "summary":"12 years of engineering leadership at Flipkart and Ola. Led teams of 15+ engineers delivering distributed systems at massive scale. Expert in technical strategy, hiring, and building high-performance engineering cultures.",
 "skills":{"technical":["System Design","Java","Kafka","Kubernetes","AWS","Microservices","Technical Architecture","Engineering Processes","OKRs","Roadmapping"],"soft":["Engineering Leadership","Hiring","Cross-team Alignment","Conflict Resolution"]},
 "experience":[
   {"company":"Flipkart","title":"Engineering Manager / Technical Lead","duration":"Mar 2019 - Present","location":"Bangalore, India","bullets":["Led 15-engineer team delivering Flipkart's seller analytics platform (10M+ sellers)","Defined 3-year technical roadmap aligned to $500M business objectives","Grew team from 8 to 20 engineers through structured hiring and campus programs"]},
   {"company":"Ola Cabs","title":"Senior Tech Lead","duration":"Jun 2015 - Mar 2019","location":"Bangalore, India","bullets":["Technical lead for real-time ride matching system processing 100K+ bookings/hour","Architected city-level surge pricing engine cutting latency by 60%","Established engineering ladders and career growth framework"]}],
 "projects":[{"name":"Seller Analytics Platform","description":"Real-time analytics for 10M+ Flipkart sellers with custom dashboards","tech_stack":["Java","Kafka","Elasticsearch","React","AWS"],"link":"github.com/deepaks/seller-analytics"},{"name":"Ride Matching Engine v3","description":"ML-augmented ride matching reducing average wait time by 35%","tech_stack":["Java","Redis","Kafka","Python/ML"],"link":"github.com/deepaks/ride-matching"}],
 "education":[{"degree":"B.Tech Computer Science","institution":"IIT Guwahati","year":"2012","gpa":"9.0/10"}],
 "certifications":["AWS Solutions Architect – Professional","Executive Engineering Leadership (INSEAD)"],
 "achievements":["Flipkart Distinguished Engineer 2023","ETech Award – Best Engineering Leader 2022","Angel investor in 3 startups"]},

# ── 49. Engineering Manager – Lead ─────────────────────────────────────
{"name":"Geeta Ramachandran","email":"geeta.r@microsoft.com","phone":"+91-9855544433",
 "location":"Hyderabad, India","linkedin":"linkedin.com/in/geetar",
 "github":"github.com/geetar","role_title":"Engineering Manager",
 "category":"Engineering","experience_level":"Lead",
 "summary":"14 years of engineering and management experience at Microsoft and McKinsey. Manages org of 25 engineers building Azure Data products. Known for building inclusive, high-performing engineering cultures and exceptional product delivery.",
 "skills":{"technical":["Engineering Management","Technical Strategy","OKRs","Headcount Planning","Performance Management","AWS/Azure","System Design","Agile at Scale","Hiring","DEI Programs"],"soft":["Inclusive Leadership","Executive Presence","Coaching","Organizational Design"]},
 "experience":[
   {"company":"Microsoft India","title":"Senior Engineering Manager","duration":"Aug 2018 - Present","location":"Hyderabad, India","bullets":["Manages org of 25 engineers across 4 squads for Azure Data Explorer","Delivered 4 major product releases used by 10,000+ enterprise customers","Grew women in engineering from 18% to 38% through targeted DEI hiring"]},
   {"company":"McKinsey Digital","title":"Engagement Manager – Engineering","duration":"Jan 2015 - Aug 2018","location":"Bangalore, India","bullets":["Led digital transformation for a Top-5 Indian bank with 50+ engineers","Delivered $200M+ technology portfolio across cloud and data workstreams","Built McKinsey India's engineering talent pipeline"]},
   {"company":"Infosys","title":"Tech Lead","duration":"Jul 2010 - Jan 2015","location":"Mysore, India","bullets":["Led 10-person team delivering ERP integrations for Fortune 500 clients","Established test-driven development culture across the team"]}],
 "projects":[{"name":"Azure Data Explorer Feature","description":"Time series compression feature used by 10K+ enterprise customers","tech_stack":["C++","Azure","Kusto Query Language"],"link":"linkedin.com/in/geetar"},{"name":"Engineering Culture Playbook","description":"Comprehensive engineering culture guide adopted by Microsoft India org","tech_stack":["PowerPoint","OKR Framework"],"link":"linkedin.com/in/geetar"}],
 "education":[{"degree":"M.Tech Computer Science","institution":"IISc Bangalore","year":"2010","gpa":"9.2/10"}],
 "certifications":["Executive Leadership – IIM Bangalore","Certified Agile Leader (CAL)"],
 "achievements":["Microsoft Global Manager of the Year 2023","Named in Diversity in Tech 50 Most Influential – 2022","Board advisor – Women in Tech India"]},

# ── 50. Golang Developer – Senior ──────────────────────────────────────
{"name":"Kartik Balasubramanian","email":"kartik.b@uber.com","phone":"+91-9733221100",
 "location":"Hyderabad, India","linkedin":"linkedin.com/in/kartikb",
 "github":"github.com/kartikb","role_title":"Golang Developer",
 "category":"Engineering","experience_level":"Senior",
 "summary":"8 years of Go backend engineering at Uber and high-growth startups. Expert in high-performance services, concurrency patterns, and distributed systems. Built services handling millions of requests per second.",
 "skills":{"technical":["Go","gRPC","Kafka","PostgreSQL","Redis","Kubernetes","Prometheus","Jaeger","AWS","Protocol Buffers"],"soft":["Distributed Systems Thinking","Performance Engineering","Mentoring"]},
 "experience":[
   {"company":"Uber India Engineering","title":"Senior SDE – Go","duration":"Sep 2020 - Present","location":"Hyderabad, India","bullets":["Built real-time driver-rider matching service handling 2M+ RPM","Optimized Go garbage collection reducing P99 latency by 45%","Designed idempotent payment retry service achieving exactly-once delivery"]},
   {"company":"Dunzo","title":"Backend Engineer","duration":"Jul 2016 - Sep 2020","location":"Bangalore, India","bullets":["Rewrote Python monolith to Go microservices improving throughput 8x","Built hyperlocal delivery orchestration API serving 500K+ daily deliveries","Established Go coding standards and internal library ecosystem"]}],
 "projects":[{"name":"Idempotent Payment Retry","description":"Distributed payment retry system with exactly-once guarantees","tech_stack":["Go","PostgreSQL","Redis","Kafka"],"link":"github.com/kartikb/payment-retry"},{"name":"Go Concurrency Toolkit","description":"OSS library for common Go concurrency patterns","tech_stack":["Go","golangci-lint"],"link":"github.com/kartikb/go-concurrency"}],
 "education":[{"degree":"B.Tech Computer Science","institution":"NIT Surathkal","year":"2016","gpa":"8.8/10"}],
 "certifications":["Go Expert – Udemy Master","CKAD – Certified Kubernetes Application Developer"],
 "achievements":["GopherCon India speaker 2022","Go Concurrency Toolkit – 1.9K GitHub stars","Uber Engineering blog contributor"]},

# ── 51. Database Administrator – Senior ────────────────────────────────
{"name":"Mohan Narayanan","email":"mohan.n@oracle.com","phone":"+91-9855000111",
 "location":"Chennai, India","linkedin":"linkedin.com/in/mohannarayanan",
 "github":"github.com/mohannarayanan","role_title":"Database Administrator",
 "category":"Engineering","experience_level":"Senior",
 "summary":"14 years of DBA experience across Oracle, PostgreSQL, and AWS databases. Expert in performance tuning, high availability design, and database migrations. Managed databases storing $1B+ of business-critical data.",
 "skills":{"technical":["Oracle DB","PostgreSQL","MySQL","AWS RDS","Aurora","MongoDB","Query Optimization","Replication","Backup/Recovery","PL/SQL","Partitioning"],"soft":["Reliability Focus","Disaster Recovery Planning","Vendor Management"]},
 "experience":[
   {"company":"Oracle India","title":"Senior Database Administrator","duration":"Apr 2018 - Present","location":"Chennai, India","bullets":["Managed 500+ Oracle DB instances for banking clients with 99.999% uptime","Reduced query execution time by 70% through index optimization and partitioning","Led Oracle 12c to 19c migration for HDFC Bank with zero downtime"]},
   {"company":"IBM GBS","title":"Database Consultant","duration":"Jun 2013 - Apr 2018","location":"Bangalore, India","bullets":["Designed PostgreSQL HA architecture for healthcare data platform","Automated backup and recovery reducing RTO from 4 hours to 20 minutes","Delivered database performance tuning for 20+ client engagements"]}],
 "projects":[{"name":"Oracle Migration Toolkit","description":"Automated Oracle-to-PostgreSQL migration scripts with validation","tech_stack":["PL/SQL","Python","pgAdmin","AWS DMS"],"link":"github.com/mohannarayanan/ora-pg-migrate"},{"name":"DB Monitoring Suite","description":"Custom monitoring and alerting for PostgreSQL clusters","tech_stack":["Python","Prometheus","Grafana","pg_stat_statements"],"link":"github.com/mohannarayanan/db-monitor"}],
 "education":[{"degree":"B.E. Computer Science","institution":"Anna University","year":"2010","gpa":"8.2/10"}],
 "certifications":["Oracle Certified Master – DBA","AWS Database Specialty","PostgreSQL Professional (PGDBA)"],
 "achievements":["Oracle ACE Associate","OracleWorld speaker 2021","Managed largest Oracle DB in South Asia (50TB+)"]},

# ── 52. Solutions Architect – Senior ───────────────────────────────────
{"name":"Murali Krishnan","email":"murali.k@infosys.com","phone":"+91-9500200400",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/muralik",
 "github":"github.com/muralik","role_title":"Solutions Architect",
 "category":"Engineering","experience_level":"Senior",
 "summary":"13 years designing enterprise technology solutions across retail, banking, and manufacturing. Translates complex business requirements into robust technical architectures. Led $100M+ IT transformation programs.",
 "skills":{"technical":["Enterprise Architecture","AWS","Azure","Microservices","Integration Patterns","API Management","Salesforce","SAP","TOGAF","Archimate"],"soft":["Client Advisory","Executive Presentation","Programme Leadership","Pre-sales"]},
 "experience":[
   {"company":"Infosys","title":"Principal Solutions Architect","duration":"Jun 2017 - Present","location":"Bangalore, India","bullets":["Architected digital transformation for IKEA India ($40M programme)","Led pre-sales for 10+ deals generating $80M pipeline","Published Infosys retail reference architecture adopted by 15+ clients"]},
   {"company":"Cognizant","title":"Senior Architect","duration":"Mar 2013 - Jun 2017","location":"Chennai, India","bullets":["Designed omni-channel platform for Macy's reducing integration complexity 60%","Led team of 8 architects across e-commerce and supply chain domains","Created architecture review board reducing technical debt by 35%"]}],
 "projects":[{"name":"IKEA Digital Commerce Platform","description":"Microservices e-commerce platform with AI-powered product recommendations","tech_stack":["AWS","Microservices","Kafka","React","ElasticSearch"],"link":"linkedin.com/in/muralik"},{"name":"Retail Reference Architecture","description":"Infosys open retail architecture with cloud-native patterns","tech_stack":["AWS","Kubernetes","API Gateway","Terraform"],"link":"linkedin.com/in/muralik"}],
 "education":[{"degree":"M.Tech Software Systems","institution":"BITS Pilani","year":"2011","gpa":"8.7/10"}],
 "certifications":["TOGAF 9.2 Certified","AWS Solutions Architect Professional","PMP"],
 "achievements":["Infosys Architecture Excellence Award 2022","Published 2 whitepapers on retail digital transformation"]},

# ── 53. Scrum Master – Mid-Level ───────────────────────────────────────
{"name":"Lakshman Rajan","email":"lakshman.rajan@accenture.com","phone":"+91-9777123456",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/lakshmank",
 "github":"github.com/lakshmank","role_title":"Scrum Master",
 "category":"Product & Business","experience_level":"Mid-Level",
 "summary":"6 years as a Scrum Master and Agile Coach facilitating cross-functional teams in fintech and healthcare. Expert in removing impediments, fostering psychological safety, and scaling Agile practices using SAFe.",
 "skills":{"technical":["Scrum","SAFe 5.0","JIRA","Confluence","Lean Thinking","OKRs","Retrospective Facilitation","Kanban","Burndown Metrics","Risk Management"],"soft":["Servant Leadership","Facilitation","Conflict Mediation","Coaching"]},
 "experience":[
   {"company":"Accenture","title":"Scrum Master","duration":"May 2021 - Present","location":"Bangalore, India","bullets":["Facilitated 3 Scrum teams (25 engineers) delivering BFSI digital products","Improved sprint velocity by 30% through iterative retrospective improvements","Coached 10 Product Owners on backlog management and story writing"]},
   {"company":"Mphasis","title":"Agile Delivery Lead","duration":"Aug 2018 - May 2021","location":"Pune, India","bullets":["Led SAFe transformation for 100-person engineering program","Reduced defect escape rate by 40% through Definition of Done improvements","Established community of practice for Scrum Masters across 5 teams"]}],
 "projects":[{"name":"SAFe Transformation","description":"Scaled Agile transformation programme for a 100-person IT program","tech_stack":["JIRA","Confluence","SAFe","Miro"],"link":"linkedin.com/in/lakshmank"},{"name":"OKR Framework Implementation","description":"Deployed OKRs across 5 engineering teams with alignment to company strategy","tech_stack":["JIRA","Confluence","Lattice"],"link":"linkedin.com/in/lakshmank"}],
 "education":[{"degree":"B.Tech Computer Science","institution":"Manipal Institute of Technology","year":"2018","gpa":"7.9/10"}],
 "certifications":["CSM – Certified Scrum Master","SAFe 5.0 Scrum Master (SSM)","Certified Agile Coach (ICP-ACC)"],
 "achievements":["Accenture Agile Excellence Award 2023","Trained 50+ engineers in Agile fundamentals"]},

# ── 54. IT Operations Manager – Senior ─────────────────────────────────
{"name":"Subramaniam Pillai","email":"subramaniam.p@tcs.com","phone":"+91-9444333222",
 "location":"Mumbai, India","linkedin":"linkedin.com/in/subramaniamp",
 "github":"github.com/subramaniamp","role_title":"IT Operations Manager",
 "category":"Non-Technical IT","experience_level":"Senior",
 "summary":"15 years in IT operations and service management at TCS and Accenture. Expert in ITIL, ITSM platforms, and managing global infrastructure operations. Led NOC teams ensuring 99.9%+ uptime for mission-critical banking systems.",
 "skills":{"technical":["ITIL 4","ServiceNow","Nagios","SolarWinds","ITSM","Change Management","Incident Management","Capacity Planning","Vendor Management","Power BI"],"soft":["Ops Leadership","SLA Management","Stakeholder Communication","Team Development"]},
 "experience":[
   {"company":"TCS","title":"IT Operations Manager","duration":"Mar 2017 - Present","location":"Mumbai, India","bullets":["Managed 24x7 NOC team of 20 ensuring 99.95% uptime for HDFC Bank IT systems","Reduced MTTR by 55% through automation and runbook implementation","Managed Rs 50Cr annual infrastructure vendor contracts"]},
   {"company":"Accenture","title":"Senior IT Service Manager","duration":"Jun 2012 - Mar 2017","location":"Pune, India","bullets":["Managed ITIL operations for Barclays UK outsourcing (1,500+ CIs)","Implemented ServiceNow ITSM reducing ticket backlog by 70%","Led 3 major infrastructure migrations with zero SLA breach"]}],
 "projects":[{"name":"ServiceNow ITSM Implementation","description":"End-to-end ITSM deployment including incident, change, and problem management","tech_stack":["ServiceNow","Power BI","Nagios","Jira"],"link":"linkedin.com/in/subramaniamp"},{"name":"NOC Automation Platform","description":"Alert correlation and auto-remediation reducing manual intervention 60%","tech_stack":["Python","ServiceNow","Nagios","Bash"],"link":"linkedin.com/in/subramaniamp"}],
 "education":[{"degree":"B.E. Computer Science","institution":"University of Mumbai","year":"2009","gpa":"7.8/10"}],
 "certifications":["ITIL 4 Managing Professional","ServiceNow Certified Implementation Specialist","PMP"],
 "achievements":["TCS IT Excellence Award 2022","ITIL Expert certified since 2015","Built 24x7 NOC reducing incidents by 40% YoY"]},

# ── 55. Technical Program Manager – Senior ─────────────────────────────
{"name":"Sindhu Natarajan","email":"sindhu.n@amazon.com","phone":"+91-9322445566",
 "location":"Chennai, India","linkedin":"linkedin.com/in/sindhun",
 "github":"github.com/sindhun","role_title":"Technical Program Manager",
 "category":"Non-Technical IT","experience_level":"Senior",
 "summary":"10 years of TPM experience driving large-scale technology programs at Amazon and Samsung. Expert in cross-functional coordination, risk management, and program delivery from inception to launch. Delivered programs with $200M+ business impact.",
 "skills":{"technical":["Program Management","Roadmapping","Risk Management","JIRA/Confluence","SQL","Metrics & KPIs","Stakeholder Management","Budget Management","Agile/Waterfall","OKRs"],"soft":["Influence without Authority","Executive Communication","Ambiguity Navigation","Strategic Thinking"]},
 "experience":[
   {"company":"Amazon India","title":"Senior Technical Program Manager","duration":"May 2019 - Present","location":"Chennai, India","bullets":["Led Amazon India logistics tech program impacting 5M+ daily shipments","Coordinated 8 engineering teams and $50M program budget to deliver on time","Defined OKRs aligning 200+ engineers to 3-year business strategy"]},
   {"company":"Samsung R&D India","title":"Technical Program Manager","duration":"Aug 2014 - May 2019","location":"Bangalore, India","bullets":["Managed SmartThings IoT platform development across 5 countries","Delivered 3 major platform releases on time and within budget","Established global TPM community of practice for Samsung engineering"]}],
 "projects":[{"name":"Logistics Tech Transformation","description":"End-to-end Amazon India logistics technology modernization program","tech_stack":["JIRA","Confluence","SQL","Tableau","AWS"],"link":"linkedin.com/in/sindhun"},{"name":"SmartThings Platform","description":"IoT platform connecting 50M+ Samsung devices globally","tech_stack":["JIRA","Program Management","AWS IoT","Agile"],"link":"linkedin.com/in/sindhun"}],
 "education":[{"degree":"B.Tech Electronics & Communication","institution":"NIT Trichy","year":"2014","gpa":"8.9/10"}],
 "certifications":["PgMP – Program Management Professional","PMI-ACP – Agile Certified Practitioner"],
 "achievements":["Amazon TPM of the Year 2022","Keynote speaker – Project Management Institute India 2021"]},

# ── 56. Performance Test Engineer – Mid-Level ──────────────────────────
{"name":"Sanjay Verma","email":"sanjay.verma@infosys.com","phone":"+91-9677889900",
 "location":"Hyderabad, India","linkedin":"linkedin.com/in/sanjayverma",
 "github":"github.com/sanjayverma","role_title":"Performance Test Engineer",
 "category":"QA & Testing","experience_level":"Mid-Level",
 "summary":"5 years in performance engineering for banking and e-commerce. Expert in JMeter, Gatling, and AWS load testing. Uncovered and resolved performance bottlenecks preventing 3 production outages during high-traffic events.",
 "skills":{"technical":["JMeter","Gatling","K6","AWS CloudWatch","Grafana","InfluxDB","APM (Dynatrace)","SQL","Python","Load/Stress/Soak Testing"],"soft":["Bottleneck Analysis","Reporting","Cross-team Collaboration"]},
 "experience":[
   {"company":"Infosys","title":"Performance Test Engineer","duration":"Jun 2022 - Present","location":"Hyderabad, India","bullets":["Designed load test strategy for HDFC mobile banking app (2M+ users)","Identified critical DB connection pool bottleneck preventing outage on launch day","Built Grafana + InfluxDB performance monitoring dashboard shared with dev teams"]},
   {"company":"Capgemini","title":"QA Engineer – Performance","duration":"Aug 2019 - Jun 2022","location":"Pune, India","bullets":["Executed JMeter tests for retail client simulating 50K concurrent users","Reduced page load time from 8s to 2.1s by identifying N+1 query issues","Created performance regression test baseline protecting 3 quarterly releases"]}],
 "projects":[{"name":"Banking Load Test Suite","description":"JMeter-based comprehensive load test for core banking APIs","tech_stack":["JMeter","InfluxDB","Grafana","Python"],"link":"github.com/sanjayverma/banking-loadtest"},{"name":"Performance Dashboard","description":"Real-time performance metrics dashboard for test results","tech_stack":["Grafana","InfluxDB","Python","JMeter"],"link":"github.com/sanjayverma/perf-dashboard"}],
 "education":[{"degree":"B.Tech Information Technology","institution":"Osmania University","year":"2019","gpa":"8.0/10"}],
 "certifications":["ISTQB Performance Testing Specialist","JMeter Professional – BlazeMeter"],
 "achievements":["Prevented Rs 10Cr potential outage loss by catching DB bottleneck","Performance Testing community blog – 6K monthly readers"]},

# ── 57. Blockchain Developer – Senior ──────────────────────────────────
{"name":"Aryan Malhotra","email":"aryan.malhotra@consensys.com","phone":"+91-9555222111",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/aryanmalhotra",
 "github":"github.com/aryanmalhotra","role_title":"Blockchain Developer",
 "category":"Engineering","experience_level":"Senior",
 "summary":"8 years in blockchain engineering with deep expertise in Ethereum, Solidity, and Layer 2 solutions. Built DeFi protocols with $500M+ TVL and enterprise blockchain solutions for banking and supply chain.",
 "skills":{"technical":["Solidity","Ethereum","Hardhat","Foundry","EVM","Layer 2 (Optimism/Arbitrum)","Web3.js","ethers.js","IPFS","Zero-Knowledge Proofs"],"soft":["Protocol Design","Security-First Thinking","Open Source Leadership"]},
 "experience":[
   {"company":"ConsenSys","title":"Senior Blockchain Engineer","duration":"Feb 2020 - Present","location":"Bangalore, India","bullets":["Developed core smart contracts for DeFi lending protocol with $500M TVL","Identified and fixed critical reentrancy vulnerability preventing $20M exploit","Led security audit process for 5 major DeFi protocol partners"]},
   {"company":"IBM Blockchain","title":"Blockchain Developer","duration":"Jul 2016 - Feb 2020","location":"Bangalore, India","bullets":["Built Hyperledger Fabric trade finance platform for 3 major Indian banks","Developed supply chain provenance solution for pharma industry","Delivered 4 blockchain PoCs that converted to $5M+ production contracts"]}],
 "projects":[{"name":"DeFi Yield Optimizer","description":"Auto-compounding yield optimizer across 10+ DeFi protocols","tech_stack":["Solidity","Hardhat","ethers.js","The Graph"],"link":"github.com/aryanmalhotra/yield-optimizer"},{"name":"ZK Identity Protocol","description":"Zero-knowledge proof identity verification for Web3 apps","tech_stack":["Circom","snarkjs","Solidity","IPFS"],"link":"github.com/aryanmalhotra/zk-identity"}],
 "education":[{"degree":"B.Tech Computer Science","institution":"DTU Delhi","year":"2016","gpa":"8.7/10"}],
 "certifications":["Ethereum Developer Bootcamp – Alchemy University","Certified Blockchain Professional"],
 "achievements":["ETHIndia 2022 Winner ($10K prize)","Blockchain Innovation Award – IBM 2019","ZK Identity Protocol – 1.5K GitHub stars"]},

# ── 58. UX Designer – Mid-Level ────────────────────────────────────────
{"name":"Meghna Pillai","email":"meghna.pillai@swiggy.in","phone":"+91-9388822233",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/meghnapillai",
 "github":"github.com/meghnapillai","role_title":"UX Designer",
 "category":"Product & Business","experience_level":"Mid-Level",
 "summary":"5 years of UX design for consumer apps with 10M+ users. Expert in end-to-end product design from user research to high-fidelity prototypes. Reduced user drop-off by 35% through data-informed design redesigns.",
 "skills":{"technical":["Figma","Sketch","Adobe XD","Principle","Maze","Hotjar","UserTesting","Design Systems","Accessibility (WCAG)","Prototyping"],"soft":["User Research","Systems Thinking","Cross-functional Collaboration","Storytelling"]},
 "experience":[
   {"company":"Swiggy","title":"Senior UX Designer","duration":"Apr 2022 - Present","location":"Bangalore, India","bullets":["Led redesign of Swiggy order tracking reducing support tickets by 40%","Created Swiggy's mobile design system with 200+ components","Conducted 50+ user research sessions informing 5 major product decisions"]},
   {"company":"Cleartax","title":"UX Designer","duration":"Aug 2019 - Apr 2022","location":"Bangalore, India","bullets":["Redesigned ITR filing flow reducing drop-off from 45% to 12%","Built accessibility guidelines adopted across 3 product teams","Facilitated 20+ design sprints with engineering and product stakeholders"]}],
 "projects":[{"name":"Order Tracking Redesign","description":"Research-led redesign of Swiggy's real-time order tracking experience","tech_stack":["Figma","Maze","Hotjar","UserTesting"],"link":"meghnapillai.design/order-tracking"},{"name":"Tax Filing Simplification","description":"Simplified ITR filing flow for first-time taxpayers (65% non-technical)","tech_stack":["Figma","Principle","Maze"],"link":"meghnapillai.design/tax-filing"}],
 "education":[{"degree":"B.Des Interaction Design","institution":"NID Ahmedabad","year":"2019","gpa":"8.5/10"}],
 "certifications":["Google UX Design Professional Certificate","IxDA Certified Interaction Designer"],
 "achievements":["Swiggy Design Impact Award 2023","Featured in Design Week India Magazine","NID Best Graduation Project 2019"]},

# ── 59. Technical Writer – Mid-Level ───────────────────────────────────
{"name":"Padma Subramaniam","email":"padma.s@atlassian.com","phone":"+91-9210044033",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/padmas",
 "github":"github.com/padmas","role_title":"Technical Writer",
 "category":"Product & Business","experience_level":"Mid-Level",
 "summary":"6 years of technical writing for developer tools, APIs, and cloud platforms. Created documentation that reduced support tickets by 50% and accelerated developer onboarding. Passionate about making complex tech accessible.",
 "skills":{"technical":["API Documentation","Markdown","DITA","Confluence","Git","OpenAPI/Swagger","Docs-as-Code","Postman","MkDocs","Readthedocs"],"soft":["Clarity of Thought","Developer Empathy","Stakeholder Interviews","Editing"]},
 "experience":[
   {"company":"Atlassian","title":"Senior Technical Writer","duration":"Jul 2021 - Present","location":"Bangalore, India","bullets":["Wrote and maintained documentation for JIRA Cloud APIs (10M+ developer views/year)","Reduced developer support tickets by 50% through improved getting started guides","Led migration of 2,000+ pages from legacy wikis to Confluence using docs-as-code"]},
   {"company":"Postman","title":"Technical Writer","duration":"Sep 2018 - Jul 2021","location":"Bangalore, India","bullets":["Created Postman Learning Center tutorials used by 5M+ developers","Authored API testing guides translated into 8 languages","Reduced new user time-to-first-API-call from 30 to 8 minutes"]}],
 "projects":[{"name":"Postman Learning Center","description":"Comprehensive API testing tutorials for developers of all skill levels","tech_stack":["Markdown","Hugo","GitHub Actions","Postman"],"link":"padmas.com/postman-docs"},{"name":"Docs-as-Code Migration","description":"Migrated 2K+ pages from Confluence to MkDocs with automated checks","tech_stack":["MkDocs","Git","GitHub Actions","Vale"],"link":"padmas.com/docs-migration"}],
 "education":[{"degree":"B.A. English Literature","institution":"Madras Christian College","year":"2018","gpa":"8.6/10"}],
 "certifications":["Google Technical Writing Certificate","DITA Specialist – Oxygen"],
 "achievements":["Atlassian Docs Quality Award 2022","Write the Docs India speaker 2021","5M+ developer view on Postman Learning Center"]},

# ── 60. IT Compliance Analyst – Mid-Level ──────────────────────────────
{"name":"Vandana Mishra","email":"vandana.mishra@ernst-young.com","phone":"+91-9100200300",
 "location":"Delhi, India","linkedin":"linkedin.com/in/vandanam",
 "github":"github.com/vandanam","role_title":"IT Compliance Analyst",
 "category":"Non-Technical IT","experience_level":"Mid-Level",
 "summary":"6 years in IT governance, risk, and compliance at EY and Deloitte. Expert in ISO 27001, SOC 2, and RBI cybersecurity framework. Managed compliance programs for 30+ banking and fintech clients.",
 "skills":{"technical":["ISO 27001","SOC 2 Type II","GDPR","RBI Cybersecurity Framework","GRC Tools (MetricStream)","Risk Assessment","VAPT Coordination","Excel","Power BI","Audit Management"],"soft":["Regulatory Knowledge","Stakeholder Communication","Risk Mindset","Reporting"]},
 "experience":[
   {"company":"Ernst & Young","title":"IT Compliance Analyst","duration":"Apr 2021 - Present","location":"Delhi, India","bullets":["Led ISO 27001 implementation for 5 fintech clients achieving zero major findings","Coordinated 15+ SOC 2 Type II audits for SaaS and cloud clients","Developed RBI cybersecurity framework gap assessment for a Top-10 bank"]},
   {"company":"Deloitte","title":"GRC Analyst","duration":"Jul 2018 - Apr 2021","location":"Gurgaon, India","bullets":["Conducted GDPR compliance assessments for European data operations","Managed MetricStream GRC platform for 8 banking clients","Reduced audit preparation time by 40% through automated control evidence collection"]}],
 "projects":[{"name":"ISO 27001 Implementation","description":"End-to-end ISO 27001 ISMS implementation for a fintech startup","tech_stack":["MetricStream","Excel","PowerPoint"],"link":"linkedin.com/in/vandanam"},{"name":"SOC 2 Audit Management","description":"Coordinated multi-client SOC 2 audit evidence collection and response","tech_stack":["MetricStream","Drata","Excel"],"link":"linkedin.com/in/vandanam"}],
 "education":[{"degree":"MBA Information Security","institution":"Symbiosis Institute of Management","year":"2018","gpa":"3.7/4.0"}],
 "certifications":["CISA – Certified Information Systems Auditor","ISO 27001 Lead Implementer","CRISC"],
 "achievements":["EY Exceptional Client Service Award 2022","Published GDPR compliance guide – 8K downloads"]},

# ── 61. Kubernetes Engineer – Senior ───────────────────────────────────
{"name":"Raju Patel","email":"raju.patel@hotstar.com","phone":"+91-9677001122",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/rajupatel",
 "github":"github.com/rajupatel","role_title":"Kubernetes Engineer",
 "category":"DevOps & Cloud","experience_level":"Senior",
 "summary":"9 years of Kubernetes and container platform engineering. Operated multi-cluster Kubernetes platforms handling 100M+ streaming users on Disney+ Hotstar. CKA+CKAD+CKS triple certified.",
 "skills":{"technical":["Kubernetes","Helm","Istio","Kyverno","ArgoCD","Prometheus/Grafana","Cilium","Terraform","Go","OPA Gatekeeper"],"soft":["Platform Engineering","Security Hardening","Multi-cluster Operations","SRE"]},
 "experience":[
   {"company":"Disney+ Hotstar","title":"Staff Platform Engineer","duration":"Oct 2019 - Present","location":"Bangalore, India","bullets":["Operated 50-node Kubernetes clusters serving 100M+ concurrent users during IPL","Implemented Istio service mesh reducing cross-service latency by 30%","Built GitOps platform with ArgoCD managing 500+ application deployments"]},
   {"company":"Freshworks","title":"Senior DevOps Engineer","duration":"Jul 2015 - Oct 2019","location":"Chennai, India","bullets":["Migrated all services to Kubernetes reducing infrastructure cost by 40%","Built multi-tenant Kubernetes platform for 3 product lines","Implemented network policies with Cilium for PCI DSS compliance"]}],
 "projects":[{"name":"Multi-cluster Management Platform","description":"Centralized GitOps platform for managing 10+ Kubernetes clusters","tech_stack":["ArgoCD","Helm","Terraform","Kubernetes","Go"],"link":"github.com/rajupatel/multi-cluster"},{"name":"Policy-as-Code Framework","description":"OPA-based policy enforcement for Kubernetes security","tech_stack":["OPA","Kyverno","Go","Kubernetes"],"link":"github.com/rajupatel/k8s-policy"}],
 "education":[{"degree":"B.Tech Computer Engineering","institution":"L.D. College of Engineering Ahmedabad","year":"2015","gpa":"8.3/10"}],
 "certifications":["CKA + CKAD + CKS (Triple Certified)","CKAD Instructor – Linux Foundation"],
 "achievements":["KubeCon speaker 2022 and 2023","Served 100M+ concurrent users with zero K8s incidents during IPL 2024","CNCF Ambassador"]},

# ── 62. Cloud Engineer AWS – Mid-Level ─────────────────────────────────
{"name":"Bharat Sharma","email":"bharat.sharma@thoughtworks.com","phone":"+91-9422133244",
 "location":"Pune, India","linkedin":"linkedin.com/in/bharatsharma",
 "github":"github.com/bharatsharma","role_title":"Cloud Engineer (AWS)",
 "category":"DevOps & Cloud","experience_level":"Mid-Level",
 "summary":"4 years of AWS cloud engineering with expertise in infrastructure-as-code, serverless architectures, and cloud cost optimization. Achieved $800K annual savings through rightsizing and reserved instance strategy.",
 "skills":{"technical":["AWS","Terraform","CloudFormation","CDK","Lambda","ECS/EKS","RDS","S3","CloudWatch","Python"],"soft":["Cost Optimization Mindset","Documentation","Continuous Improvement"]},
 "experience":[
   {"company":"Thoughtworks","title":"Cloud Engineer","duration":"May 2022 - Present","location":"Pune, India","bullets":["Designed serverless event processing platform handling 10M+ events daily","Saved $400K annually through rightsizing and Savings Plans optimization","Built Terraform modules library adopted by 12 client teams"]},
   {"company":"Hexaware","title":"AWS Developer","duration":"Aug 2020 - May 2022","location":"Chennai, India","bullets":["Migrated monolithic app to ECS-based microservices reducing costs by 35%","Implemented CloudTrail + GuardDuty security monitoring for healthcare client","Automated infrastructure provisioning cutting setup time from 3 days to 2 hours"]}],
 "projects":[{"name":"Serverless Event Platform","description":"Lambda + SQS event processing with DLQ and monitoring","tech_stack":["AWS Lambda","SQS","DynamoDB","Terraform"],"link":"github.com/bharatsharma/serverless-events"},{"name":"Cost Optimization Toolkit","description":"Automated AWS cost analysis and rightsizing recommendations","tech_stack":["Python","AWS Cost Explorer","Lambda","Grafana"],"link":"github.com/bharatsharma/cost-toolkit"}],
 "education":[{"degree":"B.Tech Information Technology","institution":"Pune University","year":"2020","gpa":"8.4/10"}],
 "certifications":["AWS Solutions Architect – Associate","AWS Developer – Associate","AWS SysOps Administrator"],
 "achievements":["Thoughtworks Cloud Impact Award 2023","$800K annual savings identified through FinOps practices"]},

# ── 63. Product Analyst – Mid-Level ────────────────────────────────────
{"name":"Preethi Selvam","email":"preethi.selvam@flipkart.com","phone":"+91-9244123456",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/preethiselvm",
 "github":"github.com/preethiselvm","role_title":"Product Analyst",
 "category":"Product & Business","experience_level":"Mid-Level",
 "summary":"5 years translating data into product insights at Flipkart and Myntra. Expert in funnel analysis, cohort studies, and A/B experiment design. Identified growth opportunities generating $15M+ in additional GMV.",
 "skills":{"technical":["SQL","Python","Amplitude","Mixpanel","Tableau","BigQuery","A/B Testing","Cohort Analysis","Excel","Statistical Analysis"],"soft":["Data Storytelling","Product Intuition","Stakeholder Influence","Experiment Design"]},
 "experience":[
   {"company":"Flipkart","title":"Senior Product Analyst","duration":"Jul 2022 - Present","location":"Bangalore, India","bullets":["Identified checkout friction reducing conversion by 8% across 3 device segments","Designed 30+ A/B experiments generating Rs 50Cr cumulative GMV impact","Built Flipkart Fashion analytics dashboard consumed by VP and C-suite daily"]},
   {"company":"Myntra","title":"Product Analyst","duration":"Aug 2019 - Jul 2022","location":"Bangalore, India","bullets":["Analyzed 200M+ user events to identify personalisation opportunities","Quantified Rs 30Cr revenue impact of homepage personalisation feature","Reduced A/B experiment cycle time by 25% through standardized framework"]}],
 "projects":[{"name":"Checkout Funnel Analysis","description":"End-to-end checkout funnel analysis with segment breakdowns","tech_stack":["SQL","BigQuery","Tableau","Python"],"link":"github.com/preethiselvm/checkout-analysis"},{"name":"A/B Testing Framework","description":"Standardized Python framework for statistical significance testing","tech_stack":["Python","SciPy","Jupyter","SQL"],"link":"github.com/preethiselvm/ab-framework"}],
 "education":[{"degree":"M.Sc. Applied Statistics","institution":"IIT Madras","year":"2019","gpa":"8.9/10"}],
 "certifications":["Google Analytics Certified","Product Analytics – Mixpanel Certification"],
 "achievements":["Flipkart Product Analytics Impact Award 2023","Rs 50Cr GMV impact in 2023 alone"]},

# ── 64. Network Engineer – Mid-Level ───────────────────────────────────
{"name":"Vinod Nair","email":"vinod.nair@cisco.com","phone":"+91-9022334455",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/vinodnair",
 "github":"github.com/vinodnair","role_title":"Network Engineer",
 "category":"Security","experience_level":"Mid-Level",
 "summary":"5 years of enterprise network engineering with Cisco and Juniper platforms. Expert in SD-WAN, BGP routing, and network security. Designed and deployed campus and data center networks for 5,000+ user organizations.",
 "skills":{"technical":["Cisco IOS/IOS-XE","Juniper Junos","BGP/OSPF","SD-WAN","Firewall (Palo Alto)","MPLS","VPN","Python (Netmiko)","Wireshark","Network Automation"],"soft":["Systematic Troubleshooting","Documentation","24x7 On-Call"]},
 "experience":[
   {"company":"Cisco India","title":"Network Engineer","duration":"May 2022 - Present","location":"Bangalore, India","bullets":["Designed SD-WAN solution for 50-branch retail network reducing WAN costs by 45%","Implemented Palo Alto NGFW across 3 data centers improving threat detection","Automated network configuration with Python reducing change implementation from 2hr to 5min"]},
   {"company":"Tata Communications","title":"Network Operations Engineer","duration":"Aug 2019 - May 2022","location":"Mumbai, India","bullets":["Managed BGP peering for Tata's Tier-1 backbone network","Resolved P1 network outages within 15-minute SLA 98% of the time","Deployed MPLS VPN for 10 enterprise customers"]}],
 "projects":[{"name":"SD-WAN Deployment","description":"50-site SD-WAN with application-aware routing and zero-trust security","tech_stack":["Cisco Viptela","Python","Ansible","Palo Alto"],"link":"github.com/vinodnair/sd-wan-design"},{"name":"Network Automation","description":"Python-based network device configuration and compliance automation","tech_stack":["Python","Netmiko","Nornir","Ansible"],"link":"github.com/vinodnair/net-automation"}],
 "education":[{"degree":"B.Tech Electronics & Communication","institution":"Kerala Technological University","year":"2019","gpa":"8.1/10"}],
 "certifications":["CCNP Enterprise","Palo Alto PCNSE","Cisco DevNet Associate"],
 "achievements":["Cisco Partner Champion Award 2023","Network Automation workshop speaker – Cisco Live India"]},

# ── 65. Embedded Systems Engineer – Senior ─────────────────────────────
{"name":"Srinivas Murthy","email":"srinivas.murthy@qualcomm.com","phone":"+91-9033445566",
 "location":"Hyderabad, India","linkedin":"linkedin.com/in/srinivasmurthy",
 "github":"github.com/srinivasmurthy","role_title":"Embedded Systems Engineer",
 "category":"Engineering","experience_level":"Senior",
 "summary":"12 years in embedded systems engineering at Qualcomm and Bosch. Expert in RTOS, hardware-software co-design, and IoT platform development. Delivered silicon-level optimizations across Snapdragon platforms.",
 "skills":{"technical":["C","C++","FreeRTOS","Zephyr","ARM Cortex-M","UART/SPI/I2C","JTAG","Linux Device Drivers","Yocto","BLE/Wi-Fi Stacks"],"soft":["Hardware-Software Co-design","Debug Expertise","Technical Documentation"]},
 "experience":[
   {"company":"Qualcomm India","title":"Senior Engineer – Embedded","duration":"Mar 2018 - Present","location":"Hyderabad, India","bullets":["Developed modem firmware components for Snapdragon 8 Gen 2 chipset","Reduced firmware boot time by 35% through startup sequence optimization","Led team of 6 engineers delivering Wi-Fi 7 stack components"]},
   {"company":"Bosch India","title":"Embedded Software Engineer","duration":"Jun 2012 - Mar 2018","location":"Coimbatore, India","bullets":["Developed ECU firmware for AUTOSAR-compliant automotive systems","Implemented CAN bus communication stack for vehicle diagnostics","Ported embedded Linux to custom ARM hardware in 6 months"]}],
 "projects":[{"name":"Wi-Fi 7 Driver","description":"Linux kernel Wi-Fi 7 driver with MLO (Multi-Link Operation) support","tech_stack":["C","Linux Kernel","Wi-Fi 7","JTAG"],"link":"github.com/srinivasmurthy/wifi7-driver"},{"name":"RTOS Scheduler","description":"Deterministic RTOS scheduler for safety-critical embedded systems","tech_stack":["C","FreeRTOS","ARM Cortex-M","MISRA-C"],"link":"github.com/srinivasmurthy/rtos-scheduler"}],
 "education":[{"degree":"M.Tech VLSI Design","institution":"NIT Warangal","year":"2012","gpa":"9.0/10"}],
 "certifications":["ARM Accredited Engineer","AUTOSAR Expert Certification","FreeRTOS Certified"],
 "achievements":["Qualcomm Patent – Firmware Boot Optimization Algorithm","Embedded Systems Design Award 2021"]},

# ── 66. MBA Intern Product ─────────────────────────────────────────────
{"name":"Samarth Iyer","email":"samarth.iyer@gmail.com","phone":"+91-9177800900",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/samarthiyer",
 "github":"github.com/samarthiyer","role_title":"MBA Intern (Product)",
 "category":"Student/Intern","experience_level":"Intern",
 "summary":"MBA candidate (IIM Bangalore, Class of 2025) with 3 years of pre-MBA experience in strategy consulting. Seeking product management summer internship to transition into tech PM role. Strong in market research and product analytics.",
 "skills":{"technical":["Product Strategy","Market Research","SQL","Tableau","Excel","Figma (basics)","PowerPoint","A/B Testing (conceptual)","JIRA","Customer Interviews"],"soft":["Structured Thinking","Communication","Leadership","Stakeholder Alignment"]},
 "experience":[
   {"company":"Byju's","title":"Product Management Intern","duration":"Apr 2024 - Jun 2024","location":"Bangalore, India","bullets":["Defined PRD for gamification feature targeting 12% DAU improvement","Conducted 30 user interviews identifying top 3 learner pain points","Collaborated with engineering to scope MVP for A/B test launch"]},
   {"company":"McKinsey & Company","title":"Business Analyst","duration":"Jul 2020 - Jun 2023","location":"Delhi, India","bullets":["Led market entry analysis for US EdTech company entering India","Built business case securing $50M board approval for digital transformation","Managed workstreams with 5-person teams across 3 simultaneous engagements"]}],
 "projects":[{"name":"Gamification PRD","description":"Product requirements document for Byju's learning gamification feature","tech_stack":["Figma","JIRA","SQL","Google Analytics"],"link":"linkedin.com/in/samarthiyer"},{"name":"EdTech Market Analysis","description":"Comprehensive India EdTech market analysis for McKinsey client","tech_stack":["Excel","PowerPoint","Tableau"],"link":"linkedin.com/in/samarthiyer"}],
 "education":[{"degree":"MBA (Strategy & Marketing) – 1st Year","institution":"IIM Bangalore","year":"2025 (expected)","gpa":"3.9/4.0"},{"degree":"B.Tech Mechanical Engineering","institution":"IIT Kharagpur","year":"2020","gpa":"8.5/10"}],
 "certifications":["Reforge Product Management Fundamentals","SQL for Data Analysis – Mode Analytics"],
 "achievements":["McKinsey Leadership Program Scholarship","IIM Bangalore Merit Scholarship 2023"]},

# ── 67. QA Intern ──────────────────────────────────────────────────────
{"name":"Amrutha Sai","email":"amrutha.sai@gmail.com","phone":"+91-9100200400",
 "location":"Hyderabad, India","linkedin":"linkedin.com/in/amruthasai",
 "github":"github.com/amruthasai","role_title":"QA Intern",
 "category":"Student/Intern","experience_level":"Intern",
 "summary":"Final year CS student with ISTQB Foundation certification and academic project experience in manual and API testing. Eager to learn test automation and contribute to quality engineering teams.",
 "skills":{"technical":["Manual Testing","Postman","JIRA","SQL","Selenium (learning)","TestRail","Excel","Bug Reporting","API Testing","Python (basics)"],"soft":["Attention to Detail","Documentation","Learning Agility"]},
 "experience":[{"company":"Mphasis","title":"QA Intern","duration":"May 2024 - Jul 2024","location":"Hyderabad, India","bullets":["Executed 200+ functional test cases for a banking web application","Filed 40 bug reports with detailed reproduction steps and screenshots","Learned and practiced API testing with Postman on REST services"]}],
 "projects":[{"name":"E-Commerce Testing Project","description":"Test plan, test cases, and bug report for an open-source e-commerce app","tech_stack":["Excel","Postman","JIRA","TestRail"],"link":"github.com/amruthasai/ecom-testing"},{"name":"API Test Collection","description":"Postman collection testing 50+ endpoints of a REST API","tech_stack":["Postman","JSON","REST API"],"link":"github.com/amruthasai/api-collection"}],
 "education":[{"degree":"B.Tech Computer Science (Final Year)","institution":"JNTU Hyderabad","year":"2025 (expected)","gpa":"8.2/10"}],
 "certifications":["ISTQB Foundation Level","Postman Student Expert"],
 "achievements":["Best QA Intern – Mphasis Hyderabad 2024","Academic Excellence Award – 2023"]},

# ── 68. Web Development Intern ─────────────────────────────────────────
{"name":"Prabhash Singh","email":"prabhash.singh@gmail.com","phone":"+91-9388001002",
 "location":"Delhi, India","linkedin":"linkedin.com/in/prabhashsingh",
 "github":"github.com/prabhashsingh","role_title":"Web Development Intern",
 "category":"Student/Intern","experience_level":"Intern",
 "summary":"2nd year B.Tech student with solid HTML/CSS/JavaScript fundamentals and hands-on React project experience. Built 4 personal web projects and actively seeking internship to grow in full-stack development.",
 "skills":{"technical":["HTML","CSS","JavaScript","React","Node.js (basics)","MongoDB (basics)","Git","Tailwind CSS","REST APIs","Responsive Design"],"soft":["Initiative","Collaboration","Design Sensibility","Quick Learner"]},
 "experience":[{"company":"TechBridge Solutions","title":"Frontend Intern","duration":"Jun 2024 - Aug 2024","location":"Delhi, India","bullets":["Built 3 responsive React components for SaaS admin dashboard","Fixed 20 UI bugs improving mobile responsiveness across the application","Learned and applied Tailwind CSS reducing styling time by 50%"]}],
 "projects":[{"name":"Personal Portfolio Website","description":"Responsive portfolio with React, animations, and contact form","tech_stack":["React","Tailwind CSS","EmailJS","Vercel"],"link":"github.com/prabhashsingh/portfolio"},{"name":"Recipe Finder App","description":"Recipe search app using TheMealDB API with favourites and filters","tech_stack":["React","CSS","REST APIs","LocalStorage"],"link":"github.com/prabhashsingh/recipe-finder"}],
 "education":[{"degree":"B.Tech Computer Engineering (2nd Year)","institution":"DTU Delhi","year":"2027 (expected)","gpa":"8.5/10"}],
 "certifications":["React Developer – freeCodeCamp","Responsive Web Design – freeCodeCamp"],
 "achievements":["DTU Freshers Hackathon Winner 2023","Built portfolio with 500+ GitHub contributions"]},

# ── 69. DevOps Intern ──────────────────────────────────────────────────
{"name":"Aryan Gupta","email":"aryan.gupta@gmail.com","phone":"+91-9766554433",
 "location":"Noida, India","linkedin":"linkedin.com/in/aryangupta",
 "github":"github.com/aryangupta","role_title":"DevOps Intern",
 "category":"Student/Intern","experience_level":"Intern",
 "summary":"CS final year student with strong Linux and Docker skills. Completed AWS Cloud Practitioner certification. Built CI/CD pipelines for academic projects and eager to grow in cloud-native DevOps.",
 "skills":{"technical":["Linux","Docker","Git","AWS (basic)","Jenkins","Bash Scripting","YAML","Nginx","Python (scripting)","GitHub Actions"],"soft":["Problem Solving","Documentation","Team Player"]},
 "experience":[{"company":"Nagarro","title":"DevOps Intern","duration":"May 2024 - Jul 2024","location":"Noida, India","bullets":["Containerized 3 microservices with Docker and Docker Compose","Set up GitHub Actions CI pipeline for automated testing and builds","Deployed application on AWS EC2 with Nginx reverse proxy configuration"]}],
 "projects":[{"name":"CI/CD Pipeline Setup","description":"GitHub Actions pipeline for Node.js app with test, build, and deploy stages","tech_stack":["GitHub Actions","Docker","AWS EC2","Nginx"],"link":"github.com/aryangupta/nodejs-cicd"},{"name":"Infrastructure Monitoring","description":"Prometheus + Grafana monitoring for a 3-tier Docker application","tech_stack":["Docker","Prometheus","Grafana","Bash"],"link":"github.com/aryangupta/monitoring-stack"}],
 "education":[{"degree":"B.Tech Computer Science (Final Year)","institution":"Amity University Noida","year":"2025 (expected)","gpa":"8.0/10"}],
 "certifications":["AWS Cloud Practitioner","Docker Essentials – IBM"],
 "achievements":["Best Intern Project – Nagarro Noida 2024","Linux Foundation Open Source Contributor Badge"]},

# ── 70. ML Research Intern ─────────────────────────────────────────────
{"name":"Rishab Banerjee","email":"rishab.banerjee@gmail.com","phone":"+91-9655112233",
 "location":"Kolkata, India","linkedin":"linkedin.com/in/rishabbanerjee",
 "github":"github.com/rishabbanerjee","role_title":"ML Research Intern",
 "category":"Student/Intern","experience_level":"Intern",
 "summary":"M.Tech (AI) 1st year student at IIT Kharagpur with strong theoretical ML background and PyTorch skills. Published conference paper as undergrad. Seeking research internship in NLP or computer vision.",
 "skills":{"technical":["Python","PyTorch","NumPy","Pandas","scikit-learn","Hugging Face","Git","LaTeX","CUDA (basics)","Research Paper Writing"],"soft":["Research Rigor","Intellectual Curiosity","Scientific Communication"]},
 "experience":[{"company":"TIFR Mumbai","title":"ML Research Intern","duration":"May 2024 - Jul 2024","location":"Mumbai, India","bullets":["Implemented and evaluated 3 efficient attention mechanisms for long documents","Reproduced results from 5 recent NLP papers achieving within 1% of reported metrics","Co-authored workshop paper on linear attention approximations (under review)"]}],
 "projects":[{"name":"Long-Context Summarization","description":"Comparison of efficient attention methods for long document summarization","tech_stack":["Python","PyTorch","Hugging Face","Weights & Biases"],"link":"github.com/rishabbanerjee/long-context"},{"name":"Cross-lingual NER","description":"Named Entity Recognition for low-resource Indian languages using multilingual BERT","tech_stack":["Python","Hugging Face","PyTorch","scikit-learn"],"link":"github.com/rishabbanerjee/cross-lingual-ner"}],
 "education":[{"degree":"M.Tech Artificial Intelligence (1st Year)","institution":"IIT Kharagpur","year":"2026 (expected)","gpa":"9.1/10"},{"degree":"B.Tech Computer Science","institution":"Jadavpur University","year":"2023","gpa":"9.3/10"}],
 "certifications":["Deep Learning Specialization – Coursera","Fast.ai Practical Deep Learning"],
 "achievements":["1st author – EMNLP Student Research Workshop 2023","IIT Kharagpur Academic Excellence Fellowship","Kaggle NLP Competition – Top 3%"]},

# ── 71. Cloud Intern ───────────────────────────────────────────────────
{"name":"Namrata Goel","email":"namrata.goel@gmail.com","phone":"+91-9533221100",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/namratagoel",
 "github":"github.com/namratagoel","role_title":"Cloud Intern",
 "category":"Student/Intern","experience_level":"Intern",
 "summary":"Final year IT student with AWS and Azure fundamentals certifications. Built cloud projects deploying web apps on EC2 and Azure App Service. Passionate about cloud infrastructure and eager to contribute to cloud engineering teams.",
 "skills":{"technical":["AWS EC2/S3/RDS","Azure App Service","Terraform (basics)","Docker","Linux","Python","Git","CloudWatch","IAM","VS Code"],"soft":["Initiative","Documentation","Fast Learner"]},
 "experience":[{"company":"Capgemini","title":"Cloud Intern","duration":"Jun 2024 - Aug 2024","location":"Bangalore, India","bullets":["Provisioned AWS infrastructure for a Node.js microservice using CloudFormation","Configured S3 lifecycle policies reducing storage costs by 20%","Set up CloudWatch alarms and dashboards for 3 EC2 instances"]}],
 "projects":[{"name":"3-Tier Web App on AWS","description":"Deployed a 3-tier web application using EC2, RDS, and ELB","tech_stack":["AWS EC2","RDS","ELB","CloudFormation"],"link":"github.com/namratagoel/3tier-aws"},{"name":"Terraform AWS Starter","description":"Reusable Terraform modules for common AWS resources","tech_stack":["Terraform","AWS","GitHub Actions"],"link":"github.com/namratagoel/tf-aws-starter"}],
 "education":[{"degree":"B.Tech Information Technology (Final Year)","institution":"RVCE Bangalore","year":"2025 (expected)","gpa":"8.4/10"}],
 "certifications":["AWS Cloud Practitioner","Azure Fundamentals (AZ-900)"],
 "achievements":["Best Cloud Project – Capgemini 2024","AWS re/Start Graduate Badge"]},

# ── 72. Cybersecurity Intern ───────────────────────────────────────────
{"name":"Tejas Kulkarni","email":"tejas.kulkarni@gmail.com","phone":"+91-9422003300",
 "location":"Pune, India","linkedin":"linkedin.com/in/tejaskulkarni",
 "github":"github.com/tejaskulkarni","role_title":"Cybersecurity Intern",
 "category":"Student/Intern","experience_level":"Intern",
 "summary":"Final year CS student with strong interest in ethical hacking and network security. CompTIA Security+ certified. Active CTF player (top 5% on HackTheBox) and self-taught in penetration testing fundamentals.",
 "skills":{"technical":["Kali Linux","Nmap","Metasploit","Wireshark","Burp Suite","Python","CTF Solving","OWASP Top 10","Network Scanning","Log Analysis"],"soft":["Analytical Thinking","Ethical Mindset","Continuous Learning"]},
 "experience":[{"company":"Symantec India","title":"Cybersecurity Intern","duration":"Jun 2024 - Aug 2024","location":"Pune, India","bullets":["Assisted in vulnerability assessment for 3 internal web applications","Analyzed 500+ firewall logs identifying 3 suspicious activity patterns","Learned and practiced threat hunting using SIEM tools"]}],
 "projects":[{"name":"CTF Write-ups Portfolio","description":"Documented solutions for 50+ CTF challenges across web, crypto, and forensics","tech_stack":["Kali Linux","Python","Burp Suite","Wireshark"],"link":"github.com/tejaskulkarni/ctf-writeups"},{"name":"Home Lab SIEM","description":"Personal SIEM lab with Splunk for log analysis and threat detection practice","tech_stack":["Splunk","Kali Linux","VirtualBox","Snort"],"link":"github.com/tejaskulkarni/home-siem"}],
 "education":[{"degree":"B.Tech Computer Science (Final Year)","institution":"PICT Pune","year":"2025 (expected)","gpa":"8.6/10"}],
 "certifications":["CompTIA Security+","CEH Student Edition","eJPT – Junior Penetration Tester"],
 "achievements":["HackTheBox Top 5% (Pro Hacker rank)","1st place – CyberHunt CTF 2024 (Regional)","OWASP Pune Chapter contributor"]},

# ── 73. HR Business Partner – Senior ───────────────────────────────────
{"name":"Rekha Sundar","email":"rekha.sundar@google.com","phone":"+91-9177234567",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/rekhasundar",
 "github":"github.com/rekhasundar","role_title":"HR Business Partner",
 "category":"Non-Technical IT","experience_level":"Senior",
 "summary":"14 years of HRBP and HR leadership at Google, Infosys, and GE. Partnered with C-suite to deliver people strategies for engineering organizations of 1,000+ employees. Expert in org design, executive coaching, and cultural transformation.",
 "skills":{"technical":["Workday HCM","People Analytics","Org Design","Succession Planning","Executive Coaching","Performance Management","Compensation Benchmarking","HR Strategy","DEI Leadership","Change Management"],"soft":["Executive Influence","Strategic Thinking","Coaching","Org Transformation"]},
 "experience":[
   {"company":"Google India","title":"Senior HRBP – Engineering","duration":"Jun 2018 - Present","location":"Bangalore, India","bullets":["Strategic HRBP for 1,200 Google Cloud engineers in India","Led reorg of 3 major engineering divisions with 92% retention rate","Designed Google India's first Engineering Leadership Development Program"]},
   {"company":"GE Digital India","title":"HR Director","duration":"Sep 2013 - Jun 2018","location":"Hyderabad, India","bullets":["Led HR for 600-person GE Digital India engineering center","Reduced voluntary attrition from 28% to 14% through targeted retention programs","Built DEI Council growing women in tech from 22% to 35%"]}],
 "projects":[{"name":"Engineering Leadership Program","description":"12-month leadership development program for Senior Engineers to Engineering Managers","tech_stack":["Workday Learning","Degreed","PowerPoint"],"link":"linkedin.com/in/rekhasundar"},{"name":"Attrition Reduction Strategy","description":"Data-driven retention strategy reducing voluntary attrition by 50%","tech_stack":["Workday Analytics","Power BI","Excel"],"link":"linkedin.com/in/rekhasundar"}],
 "education":[{"degree":"MBA Human Resources","institution":"XLRI Jamshedpur","year":"2010","gpa":"3.9/4.0"}],
 "certifications":["SHRM-SCP","ICF Professional Coach (PCC)","Workday HCM Pro"],
 "achievements":["Google HR Excellence Award 2022","SHRM India Board Member","Named in Economic Times Top 40 Under 40 HR Leaders"]},

# ── 74. IT Support Specialist – Mid-Level ──────────────────────────────
{"name":"Gopal Krishnan","email":"gopal.krishnan@infosys.com","phone":"+91-9312345678",
 "location":"Chennai, India","linkedin":"linkedin.com/in/gopalkrishnan",
 "github":"github.com/gopalkrishnan","role_title":"IT Support Specialist",
 "category":"Non-Technical IT","experience_level":"Mid-Level",
 "summary":"5 years in IT support and service desk operations at Infosys and HCL. Expert in O365 administration, Active Directory, and VDI environments. Built knowledge base reducing repeat incidents by 60%.",
 "skills":{"technical":["Windows Server 2019","Active Directory","Office 365 Admin","Azure AD","ServiceNow","VDI (Citrix)","PowerShell","ITIL","Remote Support (TeamViewer)","Network Troubleshooting"],"soft":["Customer Service Excellence","Documentation","SLA Management","Escalation Management"]},
 "experience":[
   {"company":"Infosys","title":"IT Support Engineer","duration":"Jun 2022 - Present","location":"Chennai, India","bullets":["Managed L2 IT support for 3,000-user banking client with 98% SLA compliance","Resolved complex AD and O365 issues reducing ticket escalations by 45%","Built ServiceNow knowledge base with 200+ articles reducing repeat incidents 60%"]},
   {"company":"HCL Infosystems","title":"Desktop Support Engineer","duration":"Aug 2019 - Jun 2022","location":"Coimbatore, India","bullets":["Supported 1,500 users across 5 office locations","Deployed Windows 10 rollout to 400 PCs in 6 weeks","Trained 15 new L1 support staff on tools and processes"]}],
 "projects":[{"name":"Knowledge Base Platform","description":"ServiceNow knowledge base with 200+ IT support articles and self-service portal","tech_stack":["ServiceNow","Confluence","HTML"],"link":"linkedin.com/in/gopalkrishnan"},{"name":"PowerShell Automation Suite","description":"AD user provisioning and deprovisioning automation scripts","tech_stack":["PowerShell","Active Directory","Office 365 API"],"link":"github.com/gopalkrishnan/ps-automation"}],
 "education":[{"degree":"B.Sc. Computer Science","institution":"Bharathiar University","year":"2019","gpa":"8.0/10"}],
 "certifications":["ITIL 4 Foundation","Microsoft 365 Certified: Modern Desktop Administrator","CompTIA Network+"],
 "achievements":["Best Support Engineer – Infosys Chennai 2023","Zero SLA breach for 18 consecutive months"]},

# ── 75. Talent Acquisition Specialist – Mid-Level ──────────────────────
{"name":"Shweta Agrawal","email":"shweta.agrawal@amazon.in","phone":"+91-9500667788",
 "location":"Delhi, India","linkedin":"linkedin.com/in/shwetaagrawal",
 "github":"github.com/shwetaagrawal","role_title":"Talent Acquisition Specialist",
 "category":"Non-Technical IT","experience_level":"Mid-Level",
 "summary":"5 years specializing in hiring tech talent for product companies. Closed 250+ tech roles across SDE, ML, and product domains. Built structured hiring process reducing bad hires by 40% and improving candidate NPS.",
 "skills":{"technical":["LinkedIn Recruiter","Workday ATS","Technical Assessment Platforms (HackerRank)","Compensation Analytics","DEI Sourcing","Employer Branding","Offer Management","Candidate CRM","HR Analytics","Boolean Search"],"soft":["Candidate Experience","Market Mapping","Negotiation","Stakeholder Partnering"]},
 "experience":[
   {"company":"Amazon India","title":"Technical Recruiter","duration":"Mar 2022 - Present","location":"Delhi, India","bullets":["Closed 120+ SDE and product roles in FY2023-24 against 95% hiring plan","Reduced time-to-offer from 40 to 22 days through process streamlining","Built Amazon India campus program at IITs and NITs hiring 40 new grads"]},
   {"company":"Zomato","title":"Technical Talent Acquisition","duration":"Sep 2019 - Mar 2022","location":"Gurugram, India","bullets":["Hired 80+ engineers during Zomato's hypergrowth phase (Series J)","Implemented HackerRank coding assessments reducing unqualified phone screens by 55%","Created candidate experience framework improving offer acceptance rate from 72% to 88%"]}],
 "projects":[{"name":"Campus Hiring Program","description":"IIT/NIT campus internship and PPO program for Amazon India engineering","tech_stack":["LinkedIn Campus","Workday","HackerRank","Excel"],"link":"linkedin.com/in/shwetaagrawal"},{"name":"TA Metrics Dashboard","description":"Workday-based TA metrics dashboard for leadership review","tech_stack":["Workday","Power BI","Excel"],"link":"linkedin.com/in/shwetaagrawal"}],
 "education":[{"degree":"MBA Human Resources","institution":"MDI Gurgaon","year":"2019","gpa":"3.8/4.0"}],
 "certifications":["LinkedIn Recruiter Certification","HackerRank Platform Administrator"],
 "achievements":["Amazon TA Excellence Award 2023","120+ hires against 95% plan in FY23-24"]},

# ── 76. BI Analyst – Mid-Level ─────────────────────────────────────────
{"name":"Mithun Chakraborty","email":"mithun.chakraborty@deloitte.com","phone":"+91-9266778899",
 "location":"Kolkata, India","linkedin":"linkedin.com/in/mithunchakraborty",
 "github":"github.com/mithunchakraborty","role_title":"BI Analyst",
 "category":"AI & Data","experience_level":"Mid-Level",
 "summary":"5 years in business intelligence for retail and manufacturing. Expert in Power BI, Tableau, and data warehousing. Built BI solutions enabling $20M+ in data-driven cost savings.",
 "skills":{"technical":["Power BI","Tableau","SQL","SSRS","Azure Synapse","DAX","Python","ETL","Data Modeling","Excel Advanced"],"soft":["Business Acumen","Visual Storytelling","Stakeholder Workshops","Training"]},
 "experience":[
   {"company":"Deloitte India","title":"BI Analyst","duration":"Apr 2022 - Present","location":"Kolkata, India","bullets":["Built supply chain analytics dashboards identifying Rs 15Cr in cost reduction opportunities","Created executive C-suite reporting suite in Power BI for a manufacturing client","Migrated 30+ SSRS reports to Power BI improving loading time by 70%"]},
   {"company":"Cognizant","title":"Business Intelligence Developer","duration":"Aug 2019 - Apr 2022","location":"Chennai, India","bullets":["Developed retail sales analytics platform for 500+ store network","Built automated daily reporting reducing analyst work by 3 hours/day","Trained 20 business users on Power BI self-service reporting"]}],
 "projects":[{"name":"Supply Chain Dashboard","description":"End-to-end Power BI dashboard for supply chain cost visibility","tech_stack":["Power BI","SQL","Azure Synapse","Python"],"link":"github.com/mithunchakraborty/sc-dashboard"},{"name":"SSRS to Power BI Migration","description":"Automated migration tool converting SSRS reports to Power BI","tech_stack":["Python","Power BI","SQL Server","REST API"],"link":"github.com/mithunchakraborty/ssrs-migrate"}],
 "education":[{"degree":"B.Tech Computer Science","institution":"Jadavpur University","year":"2019","gpa":"8.5/10"}],
 "certifications":["Microsoft Certified: Power BI Data Analyst (PL-300)","Tableau Desktop Specialist"],
 "achievements":["Deloitte Analytics Excellence Award 2023","Power BI community contributor – 15K DAX template downloads"]},

# ── 77. IT Finance Analyst – Mid-Level ─────────────────────────────────
{"name":"Sonia Bhatia","email":"sonia.bhatia@tcs.com","phone":"+91-9100044055",
 "location":"Noida, India","linkedin":"linkedin.com/in/soniabhatia",
 "github":"github.com/soniabhatia","role_title":"IT Finance Analyst",
 "category":"Non-Technical IT","experience_level":"Mid-Level",
 "summary":"5 years managing IT budgets, vendor contracts, and financial reporting for large IT services organizations. Expert in FinOps, cost allocation, and IT chargeback models. Managed Rs 200Cr+ IT spend portfolios.",
 "skills":{"technical":["SAP Finance","Oracle Financials","Power BI","Excel Advanced","Budget Modelling","FinOps","Vendor Contract Management","IT Cost Allocation","CAPEX/OPEX","Forecasting"],"soft":["Financial Acumen","Analytical Thinking","Executive Reporting","Negotiation"]},
 "experience":[
   {"company":"TCS","title":"IT Finance Analyst","duration":"May 2022 - Present","location":"Noida, India","bullets":["Managed Rs 150Cr IT infrastructure spend for a Top-5 bank client","Implemented FinOps practices reducing AWS costs by Rs 20Cr annually","Built automated budget variance reporting reducing close process from 5 to 2 days"]},
   {"company":"Infosys","title":"Finance Analyst – Technology","duration":"Jul 2019 - May 2022","location":"Bangalore, India","bullets":["Developed IT chargeback model for 8 business units","Negotiated vendor contracts achieving 12% average savings","Created consolidated IT financial dashboard for CFO reporting"]}],
 "projects":[{"name":"FinOps Dashboard","description":"AWS cost allocation and optimization dashboard for multi-account setup","tech_stack":["Power BI","AWS Cost Explorer","Python","Excel"],"link":"linkedin.com/in/soniabhatia"},{"name":"IT Chargeback Model","description":"Activity-based IT cost allocation model for 8 business units","tech_stack":["Excel","SAP","Power BI"],"link":"linkedin.com/in/soniabhatia"}],
 "education":[{"degree":"MBA Finance","institution":"IIM Indore","year":"2019","gpa":"3.7/4.0"}],
 "certifications":["FinOps Foundation Practitioner","SAP Financial Accounting Certified","CPA (in progress)"],
 "achievements":["TCS Finance Excellence Award 2023","Rs 20Cr annual AWS cost reduction through FinOps"]},

# ── 78. Platform Engineer – Mid-Level ──────────────────────────────────
{"name":"Kiran Babu","email":"kiran.babu@razorpay.com","phone":"+91-9544001122",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/kiranbabu",
 "github":"github.com/kiranbabu","role_title":"Platform Engineer",
 "category":"DevOps & Cloud","experience_level":"Mid-Level",
 "summary":"5 years building internal developer platforms (IDPs) and golden paths for engineering teams. Expert in Backstage, Kubernetes, and developer experience tooling. Reduced developer onboarding time from 2 weeks to 1 day.",
 "skills":{"technical":["Backstage","Kubernetes","Helm","Terraform","GitHub Actions","Python","Go","Crossplane","ArgoCD","Vault"],"soft":["Developer Empathy","Platform Thinking","Documentation","Collaboration"]},
 "experience":[
   {"company":"Razorpay","title":"Platform Engineer","duration":"Jun 2022 - Present","location":"Bangalore, India","bullets":["Built Razorpay's Internal Developer Platform on Backstage serving 500+ engineers","Reduced developer onboarding from 2 weeks to 1 day through golden path templates","Implemented secrets management with Vault reducing credential incidents to zero"]},
   {"company":"Curefit","title":"DevOps Engineer","duration":"Aug 2019 - Jun 2022","location":"Bangalore, India","bullets":["Built GitOps deployment platform for 30+ microservices","Set up Kubernetes multi-tenancy with namespaces and RBAC","Automated certificate management with cert-manager eliminating manual renewals"]}],
 "projects":[{"name":"Internal Developer Platform","description":"Backstage-based IDP with service catalog, templates, and TechDocs","tech_stack":["Backstage","Kubernetes","Terraform","GitHub Actions"],"link":"github.com/kiranbabu/idp-platform"},{"name":"Golden Path Templates","description":"Opinionated service templates for Go, Node.js, and Python microservices","tech_stack":["Backstage","Helm","Kubernetes","ArgoCD"],"link":"github.com/kiranbabu/golden-paths"}],
 "education":[{"degree":"B.E. Computer Science","institution":"DSCE Bangalore","year":"2019","gpa":"8.3/10"}],
 "certifications":["CKA – Certified Kubernetes Administrator","HashiCorp Vault Associate"],
 "achievements":["PlatformCon speaker 2023","Developer onboarding reduced from 2 weeks to 1 day","Backstage community contributor"]},

# ── 79. Data Platform Engineer – Senior ────────────────────────────────
{"name":"Karthik Seshadri","email":"karthik.seshadri@uber.com","phone":"+91-9400500600",
 "location":"Hyderabad, India","linkedin":"linkedin.com/in/karthikseshadri",
 "github":"github.com/karthikseshadri","role_title":"Data Platform Engineer",
 "category":"AI & Data","experience_level":"Senior",
 "summary":"10 years building large-scale data platforms at Uber and LinkedIn India. Architected data mesh and real-time streaming platforms handling petabytes of data. Open-source contributor to Apache Flink and Hudi.",
 "skills":{"technical":["Apache Flink","Apache Hudi","Kafka","Spark","Presto","Kubernetes","Go","Python","Data Mesh","Terraform"],"soft":["Data Architecture","OSS Leadership","Platform Strategy","Mentoring"]},
 "experience":[
   {"company":"Uber India Engineering","title":"Senior Staff Engineer – Data Platform","duration":"Apr 2018 - Present","location":"Hyderabad, India","bullets":["Architected Uber's real-time data platform processing 10PB/day","Built streaming ETL framework adopted by 300+ Uber data pipelines","Led 12-person data platform team across Hyderabad and Amsterdam"]},
   {"company":"LinkedIn India","title":"Senior Data Engineer","duration":"Jul 2014 - Apr 2018","location":"Bangalore, India","bullets":["Built LinkedIn India analytics data warehouse from scratch","Developed streaming pipeline for feed personalisation signals","Contributed 20+ features to Apache Kafka open-source project"]}],
 "projects":[{"name":"Real-time Data Platform","description":"Flink + Hudi-based real-time data lakehouse for operational analytics","tech_stack":["Flink","Hudi","Kafka","Kubernetes","Presto"],"link":"github.com/karthikseshadri/rt-data-platform"},{"name":"Data Mesh Framework","description":"Self-serve data mesh platform with automated data product registration","tech_stack":["Python","Backstage","Kafka","Terraform"],"link":"github.com/karthikseshadri/data-mesh"}],
 "education":[{"degree":"M.Tech Computer Science","institution":"IIT Madras","year":"2014","gpa":"9.1/10"}],
 "certifications":["Apache Flink Committer","Apache Hudi PMC Member"],
 "achievements":["Apache Flink Committer (core contributor)","Data+AI Summit keynote 2023","Uber Infra Platform Award 2022"]},

# ── 80. Security Tester – Mid-Level ────────────────────────────────────
{"name":"Nishant Dixit","email":"nishant.dixit@ibm.com","phone":"+91-9344556677",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/nishantdixit",
 "github":"github.com/nishantdixit","role_title":"Security Tester",
 "category":"QA & Testing","experience_level":"Mid-Level",
 "summary":"5 years in application security testing and vulnerability assessments. Expert in web app pentesting, OWASP Top 10, and security regression automation. Discovered 100+ critical vulnerabilities helping protect enterprise applications.",
 "skills":{"technical":["Burp Suite Pro","OWASP ZAP","Nmap","Metasploit","SQLMap","Python","SAST/DAST","API Security Testing","Threat Modeling","CVSS Scoring"],"soft":["Analytical Thinking","Report Writing","Developer Collaboration","Ethical Practice"]},
 "experience":[
   {"company":"IBM India","title":"Application Security Tester","duration":"May 2022 - Present","location":"Bangalore, India","bullets":["Conducted 30+ VAPT assessments for banking and healthcare clients","Discovered and responsibly disclosed 12 critical CVE-rated vulnerabilities","Built DAST integration into 5 client CI/CD pipelines automating security checks"]},
   {"company":"KPMG India","title":"Penetration Tester","duration":"Aug 2019 - May 2022","location":"Bangalore, India","bullets":["Delivered web and mobile app penetration tests for 20+ enterprise clients","Automated OWASP Top 10 test scripts reducing manual effort by 60%","Trained 50+ developers in secure coding practices through workshops"]}],
 "projects":[{"name":"DAST Pipeline Integration","description":"Automated DAST scanning integrated into Jenkins CI/CD for 5 clients","tech_stack":["OWASP ZAP","Python","Jenkins","Burp Suite"],"link":"github.com/nishantdixit/dast-pipeline"},{"name":"Security Test Automation","description":"Python framework for automated API security testing","tech_stack":["Python","Burp Suite","REST API","pytest"],"link":"github.com/nishantdixit/sec-test-auto"}],
 "education":[{"degree":"B.Tech Computer Science","institution":"NMIMS Mumbai","year":"2019","gpa":"8.2/10"}],
 "certifications":["OSCP – Offensive Security Certified Professional","CEH v12","Web Application Hacker's Handbook Certified"],
 "achievements":["IBM Cyber Hero 2022","12 responsible disclosures with CVE credits","Bug bounty: Rs 5L+ total rewards from programs"]},

# ── 81. Mobile QA Engineer – Mid-Level ─────────────────────────────────
{"name":"Jyothi Reddy","email":"jyothi.reddy@phonepe.com","phone":"+91-9655000001",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/jyothireddy",
 "github":"github.com/jyothireddy","role_title":"Mobile QA Engineer",
 "category":"QA & Testing","experience_level":"Mid-Level",
 "summary":"5 years specializing in mobile app quality for fintech and payments. Expert in Appium, XCTest, and Espresso. Built mobile test automation frameworks reducing regression time by 75%.",
 "skills":{"technical":["Appium","XCTest","Espresso","iOS/Android Testing","BrowserStack","TestFlight","Firebase Test Lab","Python","JIRA","Charles Proxy"],"soft":["Mobile-First Thinking","Bug Reproduction","Cross-platform Knowledge","Agile"]},
 "experience":[
   {"company":"PhonePe","title":"Senior QA Engineer – Mobile","duration":"Jul 2022 - Present","location":"Bangalore, India","bullets":["Built Appium automation framework covering 800+ mobile test cases","Reduced mobile regression cycle from 3 days to 6 hours through parallel BrowserStack execution","Led QA for PhonePe's UPI Lite launch achieving zero P0 bugs post-release"]},
   {"company":"Flipkart","title":"Mobile QA Engineer","duration":"Aug 2019 - Jul 2022","location":"Bangalore, India","bullets":["Developed Espresso UI test suite for Flipkart Android app","Implemented deep link and push notification testing for 20+ notification flows","Achieved 4.7 Play Store rating by reducing crash rate from 0.8% to 0.05%"]}],
 "projects":[{"name":"Mobile Test Framework","description":"Cross-platform Appium framework for iOS and Android with parallel execution","tech_stack":["Appium","Python","BrowserStack","TestNG"],"link":"github.com/jyothireddy/mobile-test-fw"},{"name":"Network Condition Testing","description":"Automated network condition simulation for offline and low-bandwidth scenarios","tech_stack":["Charles Proxy","Python","Appium","iOS Network Link Conditioner"],"link":"github.com/jyothireddy/network-test"}],
 "education":[{"degree":"B.Tech Computer Science","institution":"Osmania University","year":"2019","gpa":"8.3/10"}],
 "certifications":["ISTQB Mobile Tester","BrowserStack Certified Tester"],
 "achievements":["PhonePe Zero-Bug Launch Award – UPI Lite","Reduced crash rate from 0.8% to 0.05% on Flipkart Android"]},

# ── 82. Ruby on Rails Developer – Mid-Level ────────────────────────────
{"name":"Rahel Habtezion","email":"rahel.h@freshworks.com","phone":"+91-9788001001",
 "location":"Chennai, India","linkedin":"linkedin.com/in/rahelh",
 "github":"github.com/rahelh","role_title":"Ruby on Rails Developer",
 "category":"Engineering","experience_level":"Mid-Level",
 "summary":"5 years building SaaS platforms in Ruby on Rails at Freshworks and early-stage startups. Expert in convention-over-configuration design, ActiveRecord optimization, and background job processing with Sidekiq.",
 "skills":{"technical":["Ruby","Ruby on Rails","PostgreSQL","Sidekiq","Redis","RSpec","Docker","Heroku","AWS","GraphQL (graphql-ruby)"],"soft":["Convention-driven Development","Clean Code","Startup Mindset"]},
 "experience":[
   {"company":"Freshworks","title":"Software Engineer – Ruby","duration":"Apr 2022 - Present","location":"Chennai, India","bullets":["Developed CRM feature modules used by 60K+ businesses","Optimized ActiveRecord queries reducing N+1 issues improving page load by 40%","Built Sidekiq async job system processing 5M+ background tasks daily"]},
   {"company":"YourStory (startup)","title":"Rails Developer","duration":"Aug 2019 - Apr 2022","location":"Bangalore, India","bullets":["Built content management APIs serving 30M+ monthly readers","Implemented full-text search with Elasticsearch reducing search latency by 60%","Deployed and maintained Rails app on Heroku with zero-downtime releases"]}],
 "projects":[{"name":"Multi-tenant CRM Engine","description":"Rails engine for white-label CRM with tenant-aware data isolation","tech_stack":["Ruby on Rails","PostgreSQL","Redis","Sidekiq"],"link":"github.com/rahelh/crm-engine"},{"name":"GraphQL API for CMS","description":"GraphQL API for headless CMS serving mobile and web clients","tech_stack":["Ruby on Rails","graphql-ruby","PostgreSQL"],"link":"github.com/rahelh/cms-graphql"}],
 "education":[{"degree":"B.E. Computer Science","institution":"SSN College of Engineering","year":"2019","gpa":"8.4/10"}],
 "certifications":["Ruby Association Certified Ruby Programmer","PostgreSQL DBA Fundamentals"],
 "achievements":["Freshworks Hack to Hire Winner 2022","RailsConf speaker (virtual) – 2021"]},

# ── 83. PHP Developer – Mid-Level ──────────────────────────────────────
{"name":"Vijay Shetty","email":"vijay.shetty@yodlee.com","phone":"+91-9566443322",
 "location":"Bangalore, India","linkedin":"linkedin.com/in/vijayshetty",
 "github":"github.com/vijayshetty","role_title":"PHP Developer",
 "category":"Engineering","experience_level":"Mid-Level",
 "summary":"5 years of PHP development with Laravel and Symfony for fintech and travel sectors. Expert in REST API design, microservices in PHP, and high-traffic web application optimization.",
 "skills":{"technical":["PHP","Laravel","Symfony","MySQL","Redis","REST APIs","Docker","Elasticsearch","Composer","PHPUnit"],"soft":["Code Quality","Performance Optimization","Agile"]},
 "experience":[
   {"company":"Yodlee","title":"Software Engineer – PHP","duration":"Mar 2022 - Present","location":"Bangalore, India","bullets":["Developed financial data aggregation APIs consumed by 500+ fintech clients","Built queue-based data processing pipeline handling 2M+ bank transactions daily","Reduced API response time from 800ms to 150ms through Redis caching"]},
     {"company":"MakeMyTrip","title":"PHP Developer","duration":"Jul 2019 - Mar 2022","location":"Gurgaon, India","bullets":["Built hotel search and booking APIs handling 5M+ monthly searches","Implemented Elasticsearch for hotel discovery reducing search time 5x","Developed promo code engine supporting 200+ concurrent campaigns"]}],
   "projects":[
     {"name":"Financial Data Aggregation API","description":"Multi-bank data aggregation with OAuth2 and data normalization","tech_stack":["PHP","Laravel","MySQL","Redis","RabbitMQ"],"link":"github.com/vijayshetty/findata-api"},
     {"name":"Hotel Search Engine","description":"Elasticsearch-powered hotel search with faceted filtering","tech_stack":["PHP","Elasticsearch","Symfony"],"link":"github.com/vijayshetty/hotel-search"}
   ],
   "education":[{"degree":"B.E. Computer Science","institution":"PES University Bangalore","year":"2019","gpa":"8.2/10"}],
   "certifications":["Zend Certified PHP Engineer","AWS Certified Developer – Associate"],
   "achievements":["Yodlee Tech Star Award 2023","Built hotel search engine with 5x speedup"]
  }
  ]

# ── MAIN BLOCK FOR PDF GENERATION ─────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1].lower() == "all":
      for idx, candidate in enumerate(RESUMES):
        name = candidate.get("name", f"resume_{idx}").replace(" ", "_").lower()
        out_path = f"{name}_resume.pdf"
        print(f"Generating PDF for: {candidate['name']} → {out_path}")
        make_pdf(candidate, out_path)
        print(f"PDF generated: {out_path}")
    else:
      try:
        idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
      except Exception:
        idx = 0
      if idx < 0 or idx >= len(RESUMES):
        print(f"Invalid index {idx}. There are {len(RESUMES)} resumes.")
        sys.exit(1)
      candidate = RESUMES[idx]
      name = candidate.get("name", f"resume_{idx}").replace(" ", "_").lower()
      out_path = f"{name}_resume.pdf"
      print(f"Generating PDF for: {candidate['name']} → {out_path}")
      make_pdf(candidate, out_path)
      print(f"PDF generated: {out_path}")


