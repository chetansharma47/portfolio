"""Content extracted from the original static portfolio.

This is the starting state of the database. After the first seed the admin
panel is the source of truth; re-running the seed only fills in records that
are missing, it never overwrites edited content.
"""

from __future__ import annotations

SITE_SETTINGS = {
    "owner_name": "Chetan Sharma",
    "role_title": "Java Full Stack & AI Engineer",
    "meta_title": "Chetan Sharma | Full Stack & AI Engineer",
    "meta_description": (
        "Java Full Stack and AI Engineer building scalable enterprise backends, "
        "cloud-native infrastructure and AI agent integrations."
    ),
    "email": "chetansharmap7@gmail.com",
    "phone": "+91 8708982388",
    "location": "Mohali, Punjab, India",
    "linkedin_url": "https://linkedin.com/in/chetan-sharma-dev47",
    "github_url": "https://github.com/chetansharma47",
    "resume_url": "",
    "profile_image": "assets/images/profile.jpg",
    "availability_note": "Available for Senior / Lead Full Stack & AI Roles",
    "default_theme": "dark",
    "analytics_enabled": True,
}

SECTIONS = [
    {
        "key": "hero",
        "nav_label": "",
        "heading": "Java Full Stack Engineer & AI Engineer",
        "subheading": (
            "I build enterprise backends and cloud-native systems in Java and Spring Boot, "
            "modernise legacy frontends, and integrate AI agents into real production workflows."
        ),
        "body": {
            "primary_label": "Explore Projects",
            "primary_href": "#projects",
            "secondary_label": "Request Resume",
            "secondary_href": "mailto:chetansharmap7@gmail.com?subject=Resume%20Request",
        },
        "position": 10,
        "show_in_nav": False,
    },
    {
        "key": "metrics",
        "nav_label": "",
        "heading": "Impact",
        "subheading": "",
        "body": {},
        "position": 20,
        "show_in_nav": False,
    },
    {
        "key": "vision",
        "nav_label": "Mission",
        "heading": "The Mission",
        "subheading": (
            "My aim is to work across every layer of the software stack rather than one corner of "
            "it: backend, frontend, data and infrastructure.<br><br>"
            "With a foundation in <span class=\"vision-highlight\">Java, Spring Boot and full stack "
            "development</span>, I am now focused on applying "
            "<span class=\"vision-highlight\">AI agents</span> inside enterprise workflows, and on "
            "building systems that meet today's requirements while staying ready for what comes next."
            "<br><br><span class=\"vision-highlight\">Get in touch</span> if you are building "
            "something where that mix is useful."
        ),
        "body": {},
        "position": 30,
    },
    {
        "key": "skills",
        "nav_label": "Arsenal",
        "heading": "Technical Arsenal",
        "subheading": "",
        "body": {},
        "position": 40,
    },
    {
        "key": "projects",
        "nav_label": "Projects",
        "heading": "Featured Projects & Systems",
        "subheading": "",
        "body": {},
        "position": 50,
    },
    {
        "key": "experience",
        "nav_label": "Execution",
        "heading": "Execution History",
        "subheading": "",
        "body": {},
        "position": 60,
    },
    {
        "key": "bucket",
        "nav_label": "Bucket",
        "heading": "Bucket & Roadmap",
        "subheading": (
            "The <span class=\"vision-highlight\">skills I am learning next</span> and the "
            "<span class=\"vision-highlight\">goals I am working towards</span>, with honest "
            "progress against each one. I keep this list current instead of writing it once and "
            "forgetting it."
        ),
        "body": {},
        "position": 70,
    },
    {
        "key": "adboard",
        "nav_label": "Ad Board",
        "heading": "Advertisement Board",
        "subheading": (
            "Ad space on this portfolio is open to brands. Every panel below is an available slot, "
            "marked <span class=\"vision-highlight\">TO-LET</span> the way a hoarding is on the "
            "street. Pick a panel, send your budget, and the creative goes live once we agree terms."
        ),
        "body": {
            "marquee": (
                "SPACE TO LET &middot; ADVERTISE HERE &middot; ENQUIRE FOR RATES &middot; "
                "SPACE TO LET &middot; ADVERTISE HERE &middot; ENQUIRE FOR RATES"
            ),
            "cta_title": "Full board sponsorship",
            "cta_desc": (
                "One brand across every panel, including placement inside the terminal console. "
                "Suited to a longer campaign rather than a single month."
            ),
            "cta_button": "Enquire About Sponsorship",
        },
        "position": 80,
    },
    {
        "key": "contact",
        "nav_label": "Connect",
        "heading": "Get In Touch",
        "subheading": "",
        "body": {},
        "position": 90,
    },
]

METRICS = [
    {"value": "3+", "label": "Years System Ownership", "numeric_target": 3, "suffix": "+", "position": 10},
    {"value": "99.9%", "label": "Production System Uptime", "numeric_target": 99.9, "suffix": "%", "position": 20},
    {"value": "100+", "label": "Hours/Month Automated", "numeric_target": 100, "suffix": "+", "position": 30},
    {"value": ">80%", "label": "Automated Code Coverage", "numeric_target": 80, "prefix": ">", "suffix": "%", "position": 40},
]

SKILL_GROUPS = [
    {
        "title": "Core Java & Backend",
        "accent": "cyan",
        "position": 10,
        "skills": [
            ("Java 8 - 21+", [
                "Streams, Lambdas & Functional Interfaces",
                "Optional & CompletableFuture",
                "Records, Sealed Classes & Virtual Threads (Java 21)",
                "Memory Management & JVM Tuning",
            ]),
            ("Spring Boot 3.x", [
                "Spring Core & Spring MVC",
                "Spring Boot Actuator & Micrometer",
                "Spring Security (JWT, OAuth2, Keycloak)",
                "Spring Data JPA / MongoDB",
            ]),
            ("Spring Cloud", ["API Gateway & Eureka", "Config Server", "Resilience4j & OpenFeign"]),
            ("Microservices", ["Saga & CQRS Patterns", "Event-Driven Architecture", "Service Mesh Basics"]),
            ("REST & GraphQL", ["API Design & Versioning", "Swagger / OpenAPI Integration", "Postman Automation"]),
        ],
    },
    {
        "title": "AI & Future Tech",
        "accent": "purple",
        "position": 20,
        "skills": [
            ("AI Agent Architecture", ["Autonomous Task Agents", "Multi-Agent Workflows", "Context Memory Management"]),
            ("Spring AI", ["LLM Orchestration in Java", "Vector Database Integration", "Retrieval-Augmented Generation (RAG)"]),
            ("LangChain4j", ["Java-based LLM Tooling", "Function Calling", "Semantic Search"]),
            ("GenAI Integration", ["Claude / OpenAI API Integration", "Enterprise Chatbots", "Automated Content Generation"]),
            ("Prompt Engineering", ["Few-Shot Prompting", "Chain-of-Thought", "System Prompt Optimization"]),
        ],
    },
    {
        "title": "Frontend Excellence",
        "accent": "cyan",
        "position": 30,
        "skills": [
            ("React.js", ["Hooks & Context API", "Redux & Redux Toolkit", "React Query / SWR", "Performance Optimization"]),
            ("Next.js", ["App Router", "Server Components (RSC)", "Static Site Generation (SSG)", "API Routes"]),
            ("Angular 20", ["Standalone Components", "RxJS & Signals", "Dependency Injection", "Enterprise Migrations"]),
            ("TypeScript", ["Strict Typing & Interfaces", "Generics & Utility Types", "Advanced Compilation Targets"]),
            ("Tailwind CSS", ["Utility-First Design", "Custom Design Systems", "Responsive & Dark Mode Implementation"]),
        ],
    },
    {
        "title": "Data Engineering",
        "accent": "cyan",
        "position": 40,
        "skills": [
            ("PostgreSQL", ["Advanced Queries & Joins", "Indexing Strategies", "Stored Procedures", "Query Execution Optimization"]),
            ("MongoDB", ["Aggregation Pipelines", "Document Modeling", "Indexing & Sharding Basics"]),
            ("Redis", ["In-Memory Caching", "Session Management", "Rate Limiting"]),
            ("Hibernate / JPA", ["Advanced Entity Mapping", "L1 / L2 Caching", "N+1 Problem Resolution", "Criteria API"]),
        ],
    },
    {
        "title": "Cloud & DevOps",
        "accent": "cyan",
        "position": 50,
        "skills": [
            ("Docker & Kubernetes", ["Containerization Strategies", "Helm Charts", "Pod Scaling & Management"]),
            ("AWS", ["EC2 & RDS", "S3 & CloudFront", "Lambda (Serverless)", "ECS / EKS Deployments"]),
            ("Jenkins & GitHub Actions", ["Jenkins Automation", "GitHub Actions", "GitLab CI", "Automated Testing Gates"]),
            ("Kafka", ["Event Streaming", "Pub/Sub Architectures", "Kafka Streams Basics"]),
        ],
    },
    {
        "title": "Architecture & QA",
        "accent": "cyan",
        "position": 60,
        "skills": [
            ("System Design", ["High & Low Level Design", "Scalability Patterns", "Distributed Systems Basics"]),
            ("Clean Architecture", ["Domain-Driven Design (DDD)", "SOLID Principles", "GoF Design Patterns"]),
            ("Testing Mastery", ["JUnit 5 & Mockito", "Testcontainers for DBs", "Cucumber (BDD)", "Code Coverage > 80%"]),
        ],
    },
]

PROJECTS = [
    {
        "title": "WhiteLabel Enterprise Web Platform",
        "badge": "Production SaaS",
        "description": (
            "Live multi-tenant WhiteLabel web platform supporting per-client customization across "
            "PostgreSQL, MySQL and MSSQL backends across 5+ client deployments. Migrated legacy "
            "AngularJS to Angular 20 with zero downtime (35-45% load time improvement) and "
            "optimized PostgreSQL queries by 80% (2.0s to 400ms)."
        ),
        "tech": ["Java 21", "Spring MVC", "Angular 20", "Multi-DB", "AspectJ", "iText"],
        "tag_label": "Master Software Solutions",
        "position": 10,
    },
    {
        "title": "Illuminate Health Cloud Platform & ETL Automation",
        "badge": "US Cloud Healthcare",
        "description": (
            "Cloud healthcare product serving US clients on AWS (Lambda ~10K jobs/day, SES, "
            "Cognito). Engineered Apache Superset dashboards and KNIME / UiPath ETL pipelines "
            "saving 100+ hours/month of manual reporting, plus Jitsi/Jibri telehealth video "
            "conferencing with recording."
        ),
        "tech": ["Spring Boot", "AWS Lambda", "Apache Superset", "UiPath / KNIME", "Jitsi Video"],
        "link_url": "https://illuminate.health/",
        "link_label": "Live Product",
        "position": 20,
    },
    {
        "title": "Revelex Global Travel Reservation Engine",
        "badge": "US Travel-Tech",
        "description": (
            "High-availability US travel technology platform powering airlines, hotels, car "
            "rentals, cruise lines and travel agencies globally. Architected scalable Spring Boot "
            "REST APIs and modernized legacy enterprise components under strict SLAs."
        ),
        "tech": ["Java", "Spring Boot", "REST APIs", "Servlets / JSP", "MySQL"],
        "link_url": "https://www.revelex.com/en",
        "link_label": "Live Platform",
        "position": 30,
    },
    {
        "title": "Enterprise AI Agent & Prompt Engineering Lab",
        "badge": "AI Engineering",
        "description": (
            "Internal AI Team initiative driving GenAI adoption across engineering groups: Claude "
            "API setups, prompt engineering frameworks, Spring AI / LangChain4j integration "
            "patterns and autonomous agent workflows."
        ),
        "tech": ["Claude API", "Spring AI", "Prompt Engineering", "LangChain4j", "Java 21"],
        "tag_label": "AI Task Force",
        "position": 40,
    },
]

EXPERIENCES = [
    {
        "role": "Full Stack Developer - WhiteLabel Platform",
        "company": "Master Software Solutions",
        "location": "Mohali, Punjab, India",
        "period": "Jan 2024 - Present",
        "tech": [
            "Java 21", "Spring 5.3", "Spring MVC", "Hibernate 5.6", "AspectJ", "Angular 20",
            "TypeScript", "PostgreSQL", "MySQL", "MSSQL", "iText", "JUnit 5", "Mockito",
            "Maven", "Tomcat",
        ],
        "bullets": [
            "Hold <strong>end-to-end ownership</strong> of a live production WhiteLabel web application supporting per-client customization across multiple databases, covering architecture, backend, frontend, deployment and direct client support.",
            "Executed a <strong>complete frontend migration from AngularJS to Angular 20 (TypeScript)</strong> with <strong>zero production downtime</strong>, delivering a <strong>35-45% improvement in initial page load speed</strong>.",
            "Designed and shipped business modules in Spring MVC + JSP with <strong>multi-DB support (PostgreSQL, MySQL, MSSQL)</strong>, enabling each of 5+ client deployments to run against its own database backend.",
            "<strong>Optimized PostgreSQL queries</strong> through targeted composite indexing and query refactoring, reducing response time on critical screens from <strong>~2.0s to ~400ms (-80% latency)</strong>.",
            "Engineered <strong>PDF reporting using iText</strong>, applied <strong>AspectJ</strong> for cross-cutting concerns (logging, audit trails, transaction boundaries), and enforced <strong>JUnit 5 + Mockito</strong> coverage on core business logic.",
            "Engaged directly with enterprise clients for requirement discovery, sprint demos, change management and post-go-live support.",
            "Selected as a member of the company's <strong>internal AI Team</strong>, mentoring developers on Claude setup, prompt-engineering practice and enterprise GenAI integration patterns.",
        ],
        "impact": (
            "End-to-end production ownership for the WhiteLabel SaaS platform | 35-45% page load "
            "acceleration via the Angular 20 migration | 80% query latency reduction (2.0s to "
            "400ms) | Internal AI Team mentor."
        ),
        "position": 10,
    },
    {
        "role": "Senior Java Software Engineer - Cloud Healthcare Product",
        "company": "Master Software Solutions (Illuminate Health, USA Client)",
        "location": "Mohali, India",
        "period": "Oct 2022 - Jan 2024",
        "tech": [
            "Java 8", "Spring Boot 2.3", "AWS (SES, Lambda, Cognito)", "MySQL", "PostgreSQL",
            "Apache Superset", "KNIME / UiPath", "JasperReports", "Swagger", "Freemarker",
            "LDAP SSO", "Jitsi / Jibri",
        ],
        "bullets": [
            "Architected REST APIs in Spring MVC + Spring Boot for <a href=\"https://illuminate.health/\" target=\"_blank\" rel=\"noopener\">Illuminate Health (USA)</a>, a cloud healthcare platform, documenting contracts via <strong>Swagger</strong> for frontend and QA teams.",
            "Integrated <strong>AWS services</strong>: <strong>SES</strong> for transactional notifications, <strong>Lambda</strong> for serverless background jobs (~10K executions/day) and <strong>Cognito</strong> for identity management.",
            "Built <strong>JasperReports</strong> reporting screens and customized <strong>Freemarker</strong> email templates; configured Maven shade/war plugins for AWS Lambda packaging.",
            "Designed an <strong>Apache Superset</strong> reporting platform and <strong>KNIME / UiPath ETL pipelines</strong>, eliminating <strong>100+ hours/month</strong> of manual reporting across the organisation.",
            "Configured <strong>LDAP integration</strong> for single sign-on into Apache Superset using enterprise credentials.",
            "<strong>Optimized MySQL queries</strong> on high-traffic healthcare screens, removing page-load latency spikes and user-reported timeouts.",
            "Integrated <strong>Jitsi + Jibri</strong> for secure in-application video conferencing with automated session recording.",
            "Participated in weekly US client calls for sprint reviews, defect triage and roadmap discussions.",
        ],
        "impact": (
            "Maintained a US cloud healthcare platform processing ~10K AWS Lambda jobs/day | Saved "
            "100+ hours/month via Apache Superset and UiPath ETL | Shipped Jitsi video and LDAP SSO."
        ),
        "position": 20,
    },
    {
        "role": "Java Developer - Revelex Travel Technology Platform",
        "company": "ToXSL Technologies Pvt Ltd",
        "location": "Sahibzada Ajit Singh Nagar, Punjab, India",
        "period": "Jan 2022 - Sep 2022",
        "tech": ["Java", "Spring", "Spring Boot", "Servlets", "JSP", "MySQL", "REST APIs"],
        "bullets": [
            "Contributed to <a href=\"https://www.revelex.com/en\" target=\"_blank\" rel=\"noopener\">Revelex</a>, a US travel technology platform serving airlines, hotels, car rentals, cruise lines and travel agencies globally.",
            "<strong>Self-learned Spring and Spring Boot</strong> on the job and applied them to design and ship new production REST API modules.",
            "Maintained and enhanced legacy Java enterprise codebases, resolving production defects and client tickets within SLA.",
            "Participated in weekly US client syncs for status reporting, defect triage and feature clarification.",
        ],
        "impact": (
            "Shipped core REST API modules for a global US travel platform powering airline, cruise "
            "and hotel reservation systems."
        ),
        "position": 30,
    },
]

BUCKET_ITEMS = [
    ("skill", "Kubernetes CKA Certification", "Q1 2027", "Own cluster-level deployments end-to-end, not just Docker images.", 35, 10),
    ("skill", "Spring AI + RAG in Production", "Q4 2026", "Ship a real enterprise RAG service on a vector DB with Java 21.", 60, 20),
    ("skill", "AWS Solutions Architect - Associate", "Q2 2027", "Formalise the AWS work already done on Lambda, SES and Cognito.", 20, 30),
    ("skill", "Kafka Streams & Event-Driven Design", "Q3 2026", "Move from request/response thinking to streaming-first architecture.", 45, 40),
    ("skill", "Distributed System Design at Scale", "Ongoing", "HLD / LLD for multi-region, million-user systems.", 55, 50),
    ("goal", "Grow into a Lead / Architect Role", "2027", "Own architecture decisions and mentor a full engineering pod.", 40, 60),
    ("goal", "Launch My Own SaaS Product", "2027", "One product, real paying users, built and operated solo.", 15, 70),
    ("goal", "Speak at a Java / AI Tech Conference", "2027", "Talk on bridging classic Java backends with AI agents.", 10, 80),
    ("goal", "Meaningful Open Source Contribution", "Q4 2026", "Merged PRs into a Spring / LangChain4j ecosystem project.", 25, 90),
    ("goal", "Work With a Global Distributed Team", "Achieved", "Weekly US client ownership on healthcare and travel-tech platforms.", 100, 100),
]

AD_SLOTS = [
    {
        "key": "prime-billboard",
        "name": "Prime Billboard",
        "size": "970 x 250 - Full Width",
        "placement": "Top panel, full width across the board",
        "reach": "Highest visibility on the page",
        "tier": "premium",
        "position": 10,
    },
    {
        "key": "panel-a",
        "name": "Panel A",
        "size": "468 x 200 - Half Width",
        "placement": "Left board panel, upper row",
        "reach": "Recruiters and engineering leads",
        "position": 20,
    },
    {
        "key": "panel-b",
        "name": "Panel B",
        "size": "468 x 200 - Half Width",
        "placement": "Right board panel, upper row",
        "reach": "Dev-tool and SaaS audience",
        "position": 30,
    },
    {
        "key": "strip-c",
        "name": "Strip C",
        "size": "320 x 140 - Compact",
        "placement": "Lower board strip, left",
        "reach": "Startups and local businesses",
        "position": 40,
    },
    {
        "key": "strip-d",
        "name": "Strip D",
        "size": "320 x 140 - Compact",
        "placement": "Lower board strip, centre",
        "reach": "Bootcamps, courses and communities",
        "position": 50,
    },
    {
        "key": "strip-e",
        "name": "Strip E",
        "size": "320 x 140 - Compact",
        "placement": "Lower board strip, right",
        "reach": "Agencies and freelance networks",
        "position": 60,
    },
]
